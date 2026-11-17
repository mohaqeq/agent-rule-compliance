"""Build the image ucn-saleor-pg-base: Postgres with the migrated Django test database of one saleor revision.

  python research/trials/containers/saleor-tests-db/build.py --repo CLONE --rev 1d707dc

Why: a saleor test run needs a test database. Django creates it with all migrations at the start of each run.
That step took 273 seconds of a 276 second run. With this image, the test database exists already. A test run
uses `pytest --reuse-db`: Django applies only the migrations that are not yet applied.

Steps:
  1. Check out REV from CLONE in a temporary folder.
  2. Start Postgres with its data in /pgdata (the postgres image keeps /var/lib/postgresql/data in a volume,
     and a volume is not saved in an image).
  3. Run one small test file with --reuse-db in the image ucn-saleor-tests. This creates and keeps test_saleor.
  4. Stop Postgres cleanly, commit the container as the image, and remove the container.

The image ucn-saleor-tests must exist (see the folder saleor-tests). Run this command again when the base
revision changes.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time

IMAGE = "ucn-saleor-pg-base"
TESTS_IMAGE = "ucn-saleor-tests"
PG_IMAGE = "postgres:16"
SMALL_TEST = "saleor/graphql/product/tests/mutations/test_product_variant_stocks_delete.py"


def docker(*cmd, check=True, **kw):
    r = subprocess.run(["docker", *cmd], capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)
    if check and r.returncode != 0:
        raise SystemExit(f"docker {cmd[0]} failed: {(r.stderr or r.stdout).strip()[-400:]}")
    return r


def rmtree(d):
    def onexc(func, path, exc):  # git marks object files read-only on Windows
        os.chmod(path, 0o700)
        func(path)
    shutil.rmtree(d, onerror=onexc)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo", required=True, help="a clone of saleor")
    ap.add_argument("--rev", required=True, help="the base revision, for example 1d707dc")
    ap.add_argument("--test", default=SMALL_TEST, help="the test file that creates the database")
    a = ap.parse_args(argv)
    name = f"ucn-pg-build-{os.getpid()}"
    work = tempfile.mkdtemp(prefix="ucn-pg-build-")
    t0 = time.time()
    try:
        ws = os.path.join(work, "repo")
        subprocess.run(["git", "-c", "core.symlinks=false", "-c", "core.longpaths=true", "clone", "-q", "--no-tags",
                        a.repo, ws], check=True)
        subprocess.run(["git", "-c", "core.longpaths=true", "-C", ws, "checkout", "-q", a.rev], check=True)
        docker("run", "-d", "--name", name, "-e", "PGDATA=/pgdata", "-e", "POSTGRES_USER=saleor",
               "-e", "POSTGRES_PASSWORD=saleor", "-e", "POSTGRES_DB=saleor", PG_IMAGE,
               "-c", "fsync=off", "-c", "max_connections=200")
        for _ in range(90):
            if docker("exec", name, "pg_isready", "-U", "saleor", "-d", "saleor", check=False).returncode == 0:
                time.sleep(1)  # the init server restarts once before it is really up
                if docker("exec", name, "pg_isready", "-U", "saleor", "-d", "saleor", check=False).returncode == 0:
                    break
            time.sleep(1)
        else:
            raise SystemExit("postgres did not become ready")
        print("creating the test database (several minutes) ...", flush=True)
        r = docker("run", "--rm", "--network", f"container:{name}", "-v", f"{ws}:/repo:ro", TESTS_IMAGE,
                   "--reuse-db", a.test, check=False)
        print("\n".join(r.stdout.splitlines()[-5:]))
        if r.returncode != 0:
            raise SystemExit("the test run failed; no image was built")
        docker("stop", "-t", "120", name)
        docker("commit", "--change", "ENV PGDATA=/pgdata", name, IMAGE)
        print(f"built {IMAGE} in {round(time.time() - t0)} seconds")
    finally:
        docker("rm", "-f", name, check=False)
        rmtree(work)
    return 0


if __name__ == "__main__":
    sys.exit(main())
