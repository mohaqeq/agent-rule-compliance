"""Grader proof for one task: does the hidden grader tell "built the behavior" from "kept the rule"?

  python research/harness/prove.py TASK_DIR --repo CLONE --rev REV [--image ucn-saleor-grader]

TASK_DIR holds task.md, meta.json, grader/test_*.py, reference.patch, naive.patch and optionally seed.patch.
meta.json may list "seed_tests" (existing project tests). Each step runs on a fresh checkout with the seed applied:

  base       every test_behavior_* fails
  reference  every grader test passes
  naive      every test_behavior_* passes and at least one test_rule_* fails
  seed       (only with seed.patch) the seed_tests pass on the seeded base

Writes TASK_DIR/proof.json and exits 0 only if every step holds. Postgres runs in a throwaway container whose network
the grader container joins (saleor's pytest-socket only allows 127.0.0.1).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recon  # noqa: E402

ucn_validate = recon.ucn_validate
PG_IMAGE = "postgres:16"


def rmtree(d):
    def onexc(func, path, exc):
        os.chmod(path, 0o700)
        func(path)
    if sys.version_info >= (3, 12):
        shutil.rmtree(d, onexc=onexc, ignore_errors=False)
    else:
        shutil.rmtree(d, onerror=onexc)


def checkout(repo, rev, task_dir, dest):
    recon.run(["git", "-c", "core.symlinks=false", "-c", "core.longpaths=true", "clone", "-q", "--no-tags", repo, dest])
    r = recon.run(["git", "-C", dest, "checkout", "-q", rev])
    if r.returncode != 0:
        raise SystemExit(f"cannot check out {rev}: {r.stderr.strip()[-200:]}")
    recon.apply_seed(dest, task_dir)


def apply_patch(ws, patch):
    r = recon.run(["git", "-C", ws, "apply", "--whitespace=nowarn", os.path.abspath(patch)])
    return r.returncode == 0, r.stderr.strip()[-300:]


def junit_cases(path):
    return ucn_validate.load_test_results([path]) if os.path.exists(path) else []


def failing(cases):
    return sorted(c["name"] for c in cases if c["status"] != "passed")


def judge(step, cases):
    """(holds, failing test ids, note) for one step given the JUnit cases."""
    behavior = [c for c in cases if c["name"].startswith("test_behavior")]
    rules = [c for c in cases if c["name"].startswith("test_rule")]
    bad = failing(cases)
    if not cases:
        return False, [], "no test results (container failed?)"
    if step == "base":
        ok = bool(behavior) and all(c["status"] != "passed" for c in behavior)
        return ok, bad, "" if ok else "some test_behavior_* passed on the base" if behavior else "no test_behavior_* found"
    if step == "reference":
        return not bad, bad, "" if not bad else "grader tests fail on the reference"
    if step == "naive":
        ok = bool(behavior) and all(c["status"] == "passed" for c in behavior) and any(c["status"] != "passed" for c in rules)
        note = "" if ok else ("no test_behavior_* found" if not behavior else
                              "a test_behavior_* fails on the naive patch" if any(c["status"] != "passed" for c in behavior)
                              else "no test_rule_* fails on the naive patch")
        return ok, bad, note
    return not bad, bad, "" if not bad else "seed tests fail on the seeded base"  # seed


class Postgres:
    def __init__(self):
        self.name = f"ucn-prove-pg-{os.getpid()}"

    def __enter__(self):
        r = recon.run(["docker", "run", "-d", "--rm", "--name", self.name, "-e", "POSTGRES_USER=saleor",
                       "-e", "POSTGRES_PASSWORD=saleor", "-e", "POSTGRES_DB=saleor", PG_IMAGE])
        if r.returncode != 0:
            raise SystemExit("cannot start postgres: " + r.stderr.strip()[-200:])
        for _ in range(60):
            if recon.run(["docker", "exec", self.name, "pg_isready", "-U", "saleor", "-d", "saleor"]).returncode == 0:
                time.sleep(1)  # the init server restarts once before it is really up
                if recon.run(["docker", "exec", self.name, "pg_isready", "-U", "saleor", "-d", "saleor"]).returncode == 0:
                    return self
            time.sleep(1)
        raise SystemExit("postgres did not become ready")

    def __exit__(self, *exc):
        recon.run(["docker", "rm", "-f", self.name])

    @property
    def args(self):
        return ["--network", f"container:{self.name}"]


LOG_TASK = [""]


def log_dir(task_dir):
    """Where the containers' full output goes: outside the task directory, so it is never hashed or published."""
    return os.path.join(tempfile.gettempdir(), "ucn-prove-logs", os.path.basename(os.path.abspath(task_dir)))


def save_log(task_dir, tag, r):
    d = log_dir(task_dir)
    os.makedirs(d, exist_ok=True)
    out = getattr(r, "stdout", "") or ""
    err = getattr(r, "stderr", "") or ""
    if isinstance(out, bytes):
        out = out.decode("utf-8", "replace")
    if isinstance(err, bytes):
        err = err.decode("utf-8", "replace")
    with open(os.path.join(d, f"{tag}.log"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(out + "\n" + err)


def run_grader(ws, task_dir, image, pg, junit_dir, tag):
    x = os.path.join(junit_dir, f"{tag}.xml")
    if os.path.exists(x):
        os.remove(x)
    r = recon.run(["docker", "run", "--rm", *pg.args, "-v", f"{ws}:/repo:ro",
                   "-v", f"{os.path.join(task_dir, 'grader')}:/grader:ro", "-v", f"{junit_dir}:/out", image,
                   f"--junitxml=/out/{tag}.xml"])
    save_log(task_dir, tag, r)
    return junit_cases(x)


def run_seed_tests(ws, tests, tests_image, pg, junit_dir):
    x = os.path.join(junit_dir, "seed.xml")
    if os.path.exists(x):
        os.remove(x)
    r = recon.run(["docker", "run", "--rm", *pg.args, "-v", f"{ws}:/repo:ro", "-v", f"{junit_dir}:/out", tests_image,
                   "--junitxml=/out/seed.xml", *tests])
    save_log(LOG_TASK[0], "seed", r)
    return junit_cases(x)


def prove(task_dir, repo, rev, image="ucn-saleor-grader", tests_image="ucn-saleor-tests"):
    task_dir = os.path.abspath(task_dir)
    LOG_TASK[0] = task_dir
    meta = json.load(open(os.path.join(task_dir, "meta.json"), encoding="utf-8"))
    has_seed = os.path.exists(os.path.join(task_dir, "seed.patch"))
    steps = ["base", "reference", "naive"] + (["seed"] if has_seed else [])
    work = tempfile.mkdtemp(prefix="ucn-prove-")
    junit_dir = os.path.join(work, "_junit")
    os.makedirs(junit_dir)
    proof = {}
    try:
        with Postgres() as pg:
            for step in steps:
                t0 = time.time()
                ws = os.path.join(work, step)
                checkout(repo, rev, task_dir, ws)
                note = ""
                if step in ("reference", "naive"):
                    patch = os.path.join(task_dir, f"{step}.patch")
                    if not os.path.exists(patch):
                        proof[step] = {"passed": False, "failing": [], "seconds": 0, "note": f"{step}.patch is missing"}
                        rmtree(ws)
                        continue
                    ok, err = apply_patch(ws, patch)
                    if not ok:
                        proof[step] = {"passed": False, "failing": [], "seconds": round(time.time() - t0, 1),
                                       "note": f"{step}.patch does not apply: {err}"}
                        rmtree(ws)
                        continue
                if step == "seed":
                    tests = meta.get("seed_tests") or []
                    cases = run_seed_tests(ws, tests, tests_image, pg, junit_dir) if tests else []
                    if not tests:
                        note = "meta.json has no seed_tests"
                else:
                    cases = run_grader(ws, task_dir, image, pg, junit_dir, step)
                holds, bad, why = judge(step, cases)
                proof[step] = {"passed": holds, "failing": bad, "seconds": round(time.time() - t0, 1)}
                if note or why:
                    proof[step]["note"] = note or why
                rmtree(ws)
    finally:
        rmtree(work)
    proof["ok"] = all(proof.get(s, {}).get("passed") for s in steps)
    with open(os.path.join(task_dir, "proof.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(proof, fh, indent=1)
        fh.write("\n")
    return proof


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("task_dir")
    ap.add_argument("--repo", required=True)
    ap.add_argument("--rev", required=True)
    ap.add_argument("--image", default="ucn-saleor-grader")
    ap.add_argument("--tests-image", default="ucn-saleor-tests", help="image for the seed_tests step")
    a = ap.parse_args(argv)
    proof = prove(a.task_dir, a.repo, a.rev, a.image, a.tests_image)
    print(f"container output per step: {log_dir(a.task_dir)}")
    for step, r in proof.items():
        if step != "ok":
            print(f"{step:9} {'ok  ' if r['passed'] else 'FAIL'} {r['seconds']}s"
                  + (f"  {r['note']}" if r.get("note") else "") + (f"  failing: {', '.join(r['failing'][:4])}" if r["failing"] else ""))
    print("PROOF " + ("HOLDS" if proof["ok"] else "FAILS"))
    return 0 if proof["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
