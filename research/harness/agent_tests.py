"""The test command that coding agents use in Study B (arms with a check).

  python agent_tests.py RUNS_DIR RUN_TOKEN [-k EXPR] [-x] [-q] [PATH_OR_NODE_ID ...]

RUN_TOKEN is the name of the anonymous workspace of one run. The tool finds the workspace in RUNS_DIR/index.json.
It runs pytest in the image ucn-saleor-tests. The container gets a copy of the workspace, so the agent's files never change.

Each invocation starts its own Postgres container and joins its network. So two invocations never share a database,
also when many agents run at the same time. The container is removed at the end, also after a timeout.

Only these arguments are accepted: paths and node ids inside the repository, -k EXPR, -x and -q.
The tool refuses everything else.

Each invocation adds one JSON line to RUNS_DIR/checks/<run id>.jsonl. That file is outside the workspace.
The tool uses only the Python standard library.
"""
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import uuid
import xml.etree.ElementTree as ET

IMAGE = "ucn-saleor-tests"
PG_IMAGE = "postgres:16"
PG_BASE_IMAGE = "ucn-saleor-pg-base"  # Postgres with the migrated test database of the base revision (see
# research/trials/containers/saleor-tests-db). Without it, every run migrates a new database (about 5 minutes).
TIME_LIMIT = 15 * 60
TAIL_LINES = 150
FLAGS = ("-x", "-q")


class Refused(Exception):
    pass


def check_args(args, workspace):
    """Return the validated pytest arguments, or raise Refused with a reason."""
    root = os.path.realpath(workspace)
    out, i = [], 0
    while i < len(args):
        a = args[i]
        if a in FLAGS:
            out.append(a)
        elif a == "-k":
            if i + 1 >= len(args):
                raise Refused("-k needs an expression")
            out += ["-k", args[i + 1]]
            i += 1
        elif a.startswith("-"):
            raise Refused(f"option not allowed: {a}. Allowed options: -k EXPR, -x, -q.")
        else:
            path = a.split("::", 1)[0]
            if not path or os.path.isabs(path) or ":" in path or "\\" in path:
                raise Refused(f"use a relative path with forward slashes: {a}")
            real = os.path.realpath(os.path.join(root, path))
            if os.path.commonpath([root, real]) != root:
                raise Refused(f"path is outside the repository: {a}")
            out.append(a)
        i += 1
    return out


def find_entry(runs_dir, token):
    with open(os.path.join(runs_dir, "index.json"), encoding="utf-8") as fh:
        index = json.load(fh)
    for e in index:
        if os.path.basename(os.path.normpath(e["workspace"])) == token:
            return e
    raise Refused(f"unknown run token: {token}")


def module_of(path):
    """tests/test_x.py -> tests.test_x (the classname prefix that pytest writes to the JUnit file)."""
    return path[:-3].replace("/", ".") if path.endswith(".py") else path.replace("/", ".")


def read_junit(path, rule_test_path=None):
    """(passed, failed, errors, ran_rule_test) from a JUnit file."""
    passed = failed = errors = 0
    ran = False
    mod = module_of(rule_test_path) if rule_test_path else None
    if not os.path.exists(path):
        return passed, failed, errors, ran
    for case in ET.parse(path).getroot().iter("testcase"):
        if case.find("failure") is not None:
            failed += 1
        elif case.find("error") is not None:
            errors += 1
        elif case.find("skipped") is None:
            passed += 1
        cls = case.get("classname", "")
        if mod and (cls == mod or cls.startswith(mod + ".")):
            ran = True
    return passed, failed, errors, ran


SKIP_DIRS = (".git", "__pycache__")
# The container reads the workspace from a tar stream. A bind mount of the workspace read each file through the
# Windows file share, which took 140 seconds for the saleor tree. The stream takes a few seconds.
RUN_SCRIPT = 'mkdir -p /repo && tar -x -C /repo && exec pytest -p no:cacheprovider -n 0 -q "$@"'


def send_tree(workspace, stream):
    """Write the workspace (without .git and bytecode) as a tar stream. Symbolic links stay links."""
    root = os.path.abspath(workspace)
    walk_root = "\\\\?\\" + root if os.name == "nt" and not root.startswith("\\\\") else root  # long paths on Windows
    with tarfile.open(fileobj=stream, mode="w|") as tar:
        for d, dirs, names in os.walk(walk_root):
            dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
            rel = os.path.relpath(d, walk_root)
            for n in names:
                tar.add(os.path.join(d, n), arcname=n if rel == "." else (rel.replace(os.sep, "/") + "/" + n), recursive=False)


def docker(cmd, workspace=None, timeout=None):
    """Run a docker command. With `workspace`, the tree of that folder goes to the standard input as a tar stream."""
    if workspace is None:
        return subprocess.run(["docker", *cmd], capture_output=True, text=True, encoding="utf-8", errors="replace",
                              timeout=timeout)
    with tempfile.TemporaryFile() as out:
        proc = subprocess.Popen(["docker", *cmd], stdin=subprocess.PIPE, stdout=out, stderr=subprocess.STDOUT)

        def feed():
            try:
                send_tree(workspace, proc.stdin)
            except (OSError, ValueError):
                pass  # the container ended before it read everything
            finally:
                try:
                    proc.stdin.close()
                except OSError:
                    pass
        threading.Thread(target=feed, daemon=True).start()
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            out.seek(0)
            raise subprocess.TimeoutExpired(cmd, timeout, output=out.read())
        out.seek(0)
        return subprocess.CompletedProcess(cmd, proc.returncode, out.read().decode("utf-8", "replace"), "")


def has_base_image():
    return docker(["image", "inspect", PG_BASE_IMAGE]).returncode == 0


def start_postgres(name, base_image=False):
    """Start a fresh Postgres container. With base_image, its data already holds the migrated test database."""
    if base_image:
        r = docker(["run", "-d", "--rm", "--name", name, PG_BASE_IMAGE, "-c", "fsync=off", "-c", "max_connections=200"])
    else:
        r = docker(["run", "-d", "--rm", "--name", name, "--tmpfs", "/var/lib/postgresql/data",
                    "-e", "POSTGRES_USER=saleor", "-e", "POSTGRES_PASSWORD=saleor", "-e", "POSTGRES_DB=saleor",
                    PG_IMAGE, "-c", "fsync=off", "-c", "max_connections=200"])
    if r.returncode != 0:
        raise RuntimeError("cannot start postgres: " + r.stderr.strip()[-200:])
    for _ in range(90):
        if docker(["exec", name, "pg_isready", "-U", "saleor", "-d", "saleor"]).returncode == 0:
            time.sleep(1)  # the init server restarts once before it is really up
            if docker(["exec", name, "pg_isready", "-U", "saleor", "-d", "saleor"]).returncode == 0:
                return
        time.sleep(1)
    raise RuntimeError("postgres did not become ready")


def run_pytest(workspace, pytest_args, rule_test_path, time_limit=TIME_LIMIT):
    """Run pytest in a fresh Postgres network. Returns (exit_code, output, passed, failed, errors, ran_rule_test)."""
    tag = uuid.uuid4().hex[:12]
    pg, tests = f"ucn-agent-pg-{tag}", f"ucn-agent-tests-{tag}"
    out_dir = tempfile.mkdtemp(prefix="ucn-agent-junit-")
    deadline = time.time() + time_limit
    try:
        base = has_base_image()
        try:
            start_postgres(pg, base)
        except RuntimeError as exc:
            return 125, str(exc), 0, 0, 0, False
        left = max(1, int(deadline - time.time()))
        try:
            r = docker(["run", "-i", "--rm", "--name", tests, "--network", f"container:{pg}", "-v", f"{out_dir}:/out",
                        "--entrypoint", "sh", IMAGE, "-c", RUN_SCRIPT, "sh", "--junitxml=/out/r.xml",
                        *(["--reuse-db"] if base else []), *pytest_args], workspace=workspace, timeout=left)
            code, text = r.returncode, (r.stdout or "") + (r.stderr or "")
        except subprocess.TimeoutExpired as exc:
            docker(["rm", "-f", tests])
            part = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            code, text = 124, part + f"\nTIME LIMIT: the run took more than {time_limit // 60} minutes and was stopped.\n"
        p, f, e, ran = read_junit(os.path.join(out_dir, "r.xml"), rule_test_path)
        return code, text, p, f, e, ran
    finally:
        docker(["rm", "-f", pg])
        for n in os.listdir(out_dir):
            os.remove(os.path.join(out_dir, n))
        os.rmdir(out_dir)


def log_line(runs_dir, run_id, record):
    d = os.path.join(runs_dir, "checks")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, f"{run_id}.jsonl"), "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(record) + "\n")


def main(argv=None, time_limit=TIME_LIMIT):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) < 2:
        print(__doc__.split("\n\n")[0], file=sys.stderr)
        return 2
    runs_dir, token, args = os.path.abspath(argv[0]), argv[1], argv[2:]
    try:
        entry = find_entry(runs_dir, token)
        pytest_args = check_args(args, entry["workspace"])
    except Refused as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    t0 = time.time()
    code, text, passed, failed, errors, ran = run_pytest(entry["workspace"], pytest_args, entry.get("rule_test_path"), time_limit)
    seconds = round(time.time() - t0, 1)
    print("\n".join(text.splitlines()[-TAIL_LINES:]))
    log_line(runs_dir, entry["run"], {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "args": args, "exit_code": code,
                                      "passed": passed, "failed": failed, "errors": errors, "seconds": seconds,
                                      "ran_rule_test": ran})
    return code


if __name__ == "__main__":
    sys.exit(main())
