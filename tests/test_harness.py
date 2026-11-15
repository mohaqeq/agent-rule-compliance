"""Tests for the experiment harness. Run: python -m unittest discover -s tests"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "research", "harness"))
import ucn_dep  # noqa: E402,F401
import pilot_eval  # noqa: E402
import ucn_validate  # noqa: E402

TODAY = "2026-11-05"


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def write(p, text):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(textwrap.dedent(text).lstrip("\n"))


def run(path, **kw):
    kw.setdefault("today", TODAY)
    r = ucn_validate.validate(path, **kw)
    r.pop("_model")
    return r


def classes(r, check=None):
    return sorted((f["class"], f["message"].split(" ")[0]) for f in r["findings"]
                  if f["class"] != "INFO" and (check is None or f["check"] == check))


def has(r, cls, text):
    return any(f["class"] == cls and text in f["message"] for f in r["findings"])


GENERIC = """
ucn 0.4 system: S origin: stated mode: forward root: src
system S [derived]: s
  container App: app
    code: app/**
    component A: a
      code: app/a/**
    component B: b
      code: app/b/**
    component C: c
      code: app/c/**
      uses B
"""


def rmtree(d):
    def onexc(func, path, exc):  # git marks object files read-only on Windows
        os.chmod(path, 0o700)
        func(path)
    if sys.version_info >= (3, 12):
        shutil.rmtree(d, onexc=onexc)
    else:  # Python 3.10/3.11 only know onerror
        shutil.rmtree(d, onerror=onexc)


class Tmp(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(rmtree, self.d)

    def project(self, model=GENERIC, files=None, extra=""):
        write(os.path.join(self.d, "model.ucn"), model + textwrap.dedent(extra))
        for rel, text in (files or {}).items():
            write(os.path.join(self.d, "src", rel), text)
        return os.path.join(self.d, "model.ucn")


def junit(cases):
    rows = []
    for cls, name, status, f in cases:
        attrs = f'classname="{cls}" name="{name}"' + (f' file="{f}"' if f else "")
        body = {"failed": "<failure message='x'/>", "skipped": "<skipped/>"}.get(status, "")
        rows.append(f"<testcase {attrs}>{body}</testcase>")
    return '<testsuites><testsuite name="s">' + "".join(rows) + "</testsuite></testsuites>"


# ------------------------------------------------------------------------------------------- harness
class ReconGrading(Tmp):
    """recon.grade_one with the containers faked: it must fail closed and catch tampering (review v0.6)."""

    def setUp(self):
        super().setUp()
        import recon
        self.recon = recon
        self.model = self.project(files={"app/a/x.ts": "export const x = 1;\n"})
        for cmd in (["init", "-q"], ["add", "-A"], ["-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "base"]):
            subprocess.run(["git", "-C", self.d, *cmd], capture_output=True, check=True)
        self.pristine = os.path.join(self.d, "..", os.path.basename(self.d) + "-pristine.ucn")
        shutil.copy(self.model, self.pristine)
        self.addCleanup(os.remove, self.pristine)
        os.makedirs(os.path.join(self.d, "_task", "grader"))
        self.spec = {"model": self.pristine, "validator": ucn_dep.resolve("ucn/ucn_validate.py"),
                     "grader_image": "G", "lint_image": "L"}

    def grade(self, lint_stdout, cond="L", guarded=None):
        real = self.recon.run

        def fake(cmd, **kw):
            if cmd[0] != "docker":
                return real(cmd, **kw)
            if "G" in cmd:  # the hidden grader: one passing case
                out = [a for a in cmd if a.endswith(":/out")][0].rsplit(":", 1)[0]
                write(os.path.join(out, "r1.xml"), junit([("test_t", "test_ok", "passed", "")]))
            return subprocess.CompletedProcess(cmd, 0, lint_stdout if "L" in cmd else "", "")
        self.recon.run = fake
        self.addCleanup(setattr, self.recon, "run", real)
        entry = {"run": "r1", "task": "t", "cond": cond, "workspace": self.d, "guarded": guarded or {},
                 "validator_sha": self.recon.sha(self.spec["validator"])}
        return self.recon.grade_one(self.spec, entry, {"dir": os.path.join(self.d, "_task")}, set())

    def test_validator_without_line_numbers_reports_nothing_on_a_clean_run(self):
        self.spec["validator_no_lines"] = True
        r = self.grade("Contracts: 4 kept, 0 broken.")
        self.assertEqual(r["validator_new"], [])
        self.assertEqual(r["violations"], 0)

    def test_clean_run(self):
        r = self.grade("Contracts: 4 kept, 0 broken.")
        self.assertEqual((r["success"], r["violations"], r["tampered"]), (1, 0, []))

    def test_missing_import_linter_result_fails_closed(self):
        r = self.grade("Traceback: something broke")
        self.assertEqual(r["violations"], 1)
        self.assertIn("grading_error", r)

    def test_missing_contract_fails_closed_and_old_results_are_not_reused(self):
        self.spec["contracts"] = 4
        self.assertEqual(self.grade("Contracts: 3 kept, 0 broken.")["violations"], 1)
        real = self.recon.run  # second grading: the grader container "fails" and writes nothing
        self.recon.run = lambda cmd, **kw: (subprocess.CompletedProcess(cmd, 125, "", "") if cmd[0] == "docker" else real(cmd, **kw))
        try:
            entry = {"run": "r1", "task": "t", "cond": "L", "workspace": self.d}
            r = self.recon.grade_one(self.spec, entry, {"dir": os.path.join(self.d, "_task")}, set())
        finally:
            self.recon.run = real
        self.assertEqual(r["success"], 0)

    def test_tampering_with_model_context_or_contracts(self):
        ctx = os.path.join(self.d, "context.ucn")
        write(ctx, "ucn 0.4 system: S\n")
        guarded = {"context.ucn": self.recon.sha(ctx)}
        shutil.copy(self.pristine, os.path.join(self.d, "model.ucn"))
        self.assertEqual(self.grade("Contracts: 4 kept, 0 broken.", "B", guarded)["tampered"], [])
        write(ctx, "ucn 0.4 system: S\n# edited\n")
        write(os.path.join(self.d, "model.ucn"), read(self.pristine) + "\n# loosened\n")
        write(os.path.join(self.d, "pyproject.toml"), "[tool.importlinter]\n")
        r = self.grade("Contracts: 4 kept, 0 broken.", "B", guarded)
        self.assertEqual(r["tampered"], ["context.ucn", "model.ucn", "pyproject.toml"])
        self.assertEqual(r["violations"], 1)

    def test_seed_is_part_of_the_base_and_labels_are_copied(self):
        def git(*a):
            return subprocess.run(["git", "-C", self.d, *a], capture_output=True, text=True, check=True).stdout
        write(os.path.join(self.d, "src", "app", "a", "x.ts"), "export const x = 2;\n")
        patch = git("diff")
        git("checkout", "--", ".")
        task_dir = tempfile.mkdtemp()
        self.addCleanup(rmtree, task_dir)
        with open(os.path.join(task_dir, "seed.patch"), "w", newline="\n") as fh:
            fh.write(patch)
        seeded = self.recon.apply_seed(self.d, task_dir)
        self.assertEqual(list(seeded), ["src/app/a/x.ts"])
        self.spec["model_name"] = "haiku"
        task = {"dir": os.path.join(self.d, "_task"), "rule_id": "R1", "site": "none", "seeded": True, "half": "new"}
        real = self.recon.run

        def fake(cmd, **kw):
            if cmd[0] != "docker":
                return real(cmd, **kw)
            if "G" in cmd:
                out = [a for a in cmd if a.endswith(":/out")][0].rsplit(":", 1)[0]
                write(os.path.join(out, "r1.xml"), junit([("test_t", "test_ok", "passed", "")]))
            return subprocess.CompletedProcess(cmd, 0, "Contracts: 1 kept, 0 broken." if "L" in cmd else "", "")
        self.recon.run = fake
        self.addCleanup(setattr, self.recon, "run", real)
        entry = {"run": "r1", "task": "t", "cond": "L", "workspace": self.d, "seeded_files": seeded}
        r = self.recon.grade_one(self.spec, entry, task, set())
        self.assertEqual(r["changed"], [])
        self.assertEqual((r["rule_id"], r["site"], r["seeded"], r["half"], r["agent_model"]),
                         ("R1", "none", True, "new", "haiku"))
        write(os.path.join(self.d, "src", "app", "a", "x.ts"), "export const x = 3;\n")  # the agent edits the seeded file
        write(os.path.join(self.d, "src", "app", "a", "y.ts"), "export const y = 1;\n")
        r = self.recon.grade_one(self.spec, entry, task, set())
        self.assertEqual(r["changed"], ["src/app/a/x.ts", "src/app/a/y.ts"])

    def test_squashed_base_hides_the_seed_and_counts_every_kind_of_change(self):
        def git(*a):
            return subprocess.run(["git", "-C", self.d, *a], capture_output=True, text=True, check=True).stdout
        write(os.path.join(self.d, "src", "app", "a", "x.ts"), "export const x = 2;\n")  # the seed, uncommitted
        base = self.recon.squash_base(self.d)
        self.assertEqual(git("status", "--porcelain"), "")
        self.assertEqual(git("log", "--format=%an <%ae> %s %at").splitlines(), ["dev <dev@example.com> Initial import 946684800"])
        self.assertEqual(git("rev-parse", "HEAD").strip(), base)
        self.assertEqual(self.recon.changed_since(self.d, base), [])
        write(os.path.join(self.d, "src", "app", "a", "x.ts"), "export const x = 3;\n")
        git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qam", "agent commits despite instructions")
        write(os.path.join(self.d, "staged.ts"), "1\n")
        git("add", "staged.ts")
        write(os.path.join(self.d, "src", "app", "a", "new.ts"), "2\n")
        os.remove(os.path.join(self.d, "model.ucn"))
        self.assertEqual(self.recon.changed_since(self.d, base),
                         ["model.ucn", "src/app/a/new.ts", "src/app/a/x.ts", "staged.ts"])
        real = self.recon.run

        def fake(cmd, **kw):
            if cmd[0] != "docker":
                return real(cmd, **kw)
            if "G" in cmd:
                out = [a for a in cmd if a.endswith(":/out")][0].rsplit(":", 1)[0]
                write(os.path.join(out, "r1.xml"), junit([("test_t", "test_ok", "passed", "")]))
            return subprocess.CompletedProcess(cmd, 0, "Contracts: 1 kept, 0 broken." if "L" in cmd else "", "")
        self.recon.run = fake
        self.addCleanup(setattr, self.recon, "run", real)
        entry = {"run": "r1", "task": "t", "cond": "L", "workspace": self.d, "base_commit": base}
        r = self.recon.grade_one(self.spec, entry, {"dir": os.path.join(self.d, "_task")}, set())
        self.assertEqual(r["changed"], ["src/app/a/new.ts", "src/app/a/x.ts", "staged.ts"])  # model.ucn is filtered as before

    def test_squashed_base_without_agent_changes_is_clean(self):
        base = self.recon.squash_base(self.d)
        entry = {"run": "r1", "task": "t", "cond": "L", "workspace": self.d, "base_commit": base}
        real = self.recon.run

        def fake(cmd, **kw):
            if cmd[0] != "docker":
                return real(cmd, **kw)
            return subprocess.CompletedProcess(cmd, 0, "Contracts: 1 kept, 0 broken.", "")
        self.recon.run = fake
        self.addCleanup(setattr, self.recon, "run", real)
        r = self.recon.grade_one(self.spec, entry, {"dir": os.path.join(self.d, "_task")}, set())
        self.assertEqual((r["changed"], r["tampered"]), ([], []))

    def test_existing_specs_add_no_labels(self):
        r = self.grade("Contracts: 4 kept, 0 broken.")
        self.assertFalse({"agent_model", "rule_id", "site", "seeded", "half"} & set(r))


class Prove(unittest.TestCase):
    def setUp(self):
        import prove
        self.prove = prove

    def cases(self, **status):
        return [{"classname": "", "name": n, "file": "", "status": s} for n, s in status.items()]

    def test_base_needs_every_behavior_test_to_fail(self):
        self.assertTrue(self.prove.judge("base", self.cases(test_behavior_a="failed", test_rule_a="passed"))[0])
        self.assertFalse(self.prove.judge("base", self.cases(test_behavior_a="failed", test_behavior_b="passed"))[0])
        self.assertFalse(self.prove.judge("base", [])[0])

    def test_reference_needs_everything_to_pass(self):
        self.assertTrue(self.prove.judge("reference", self.cases(test_behavior_a="passed", test_rule_a="passed"))[0])
        ok, bad, _ = self.prove.judge("reference", self.cases(test_behavior_a="passed", test_rule_a="failed"))
        self.assertEqual((ok, bad), (False, ["test_rule_a"]))

    def test_naive_builds_the_behavior_and_breaks_a_rule(self):
        self.assertTrue(self.prove.judge("naive", self.cases(test_behavior_a="passed", test_rule_a="failed"))[0])
        self.assertFalse(self.prove.judge("naive", self.cases(test_behavior_a="passed", test_rule_a="passed"))[0])
        self.assertFalse(self.prove.judge("naive", self.cases(test_behavior_a="failed", test_rule_a="failed"))[0])

    def test_seed_tests_must_pass(self):
        self.assertTrue(self.prove.judge("seed", self.cases(test_x="passed"))[0])
        self.assertFalse(self.prove.judge("seed", self.cases(test_x="failed"))[0])

    def test_missing_patch_is_reported_and_proof_written(self):
        d = tempfile.mkdtemp()
        self.addCleanup(rmtree, d)
        write(os.path.join(d, "meta.json"), "{}")
        pv = self.prove

        class FakePg:
            args = []

            def __enter__(self):
                return self

            def __exit__(self, *a):
                pass
        saved = (pv.Postgres, pv.checkout, pv.run_grader)
        self.addCleanup(lambda: (setattr(pv, "Postgres", saved[0]), setattr(pv, "checkout", saved[1]),
                                 setattr(pv, "run_grader", saved[2])))
        pv.Postgres, pv.checkout = FakePg, lambda repo, rev, task, dest: os.makedirs(dest)
        pv.run_grader = lambda *a: self.cases(test_behavior_a="failed")
        proof = pv.prove(d, "repo", "rev")
        self.assertTrue(proof["base"]["passed"])
        self.assertEqual(proof["naive"]["note"], "naive.patch is missing")
        self.assertFalse(proof["ok"])
        self.assertFalse(json.loads(read(os.path.join(d, "proof.json")))["ok"])


class StudyAEval(unittest.TestCase):
    def setUp(self):
        import studya_eval
        self.ev = studya_eval

    def rows(self, rates, rules=6, n=8):
        out = []
        for i in range(rules):
            for site, k in rates.items():
                out += [{"rule_id": f"R{i}", "site": site, "violations": int(j < k), "agent_model": "m",
                         "half": "new", "seeded": False} for j in range(n)]
        return out

    def test_skips_and_counts_runs_without_rule_test(self):
        rows = self.rows({"consistent": 1, "none": 4, "contradicting": 7}) + [
            {"rule_id": "R0", "site": "none", "violations": None}]
        res = self.ev.analyse(rows)
        self.assertEqual((res["analysed"], res["skipped_no_rule_test"]), (144, 1))

    def test_strong_effect_is_supported_and_deterministic(self):
        rows = self.rows({"consistent": 1, "none": 4, "contradicting": 7, "control": 1})
        a, b = self.ev.analyse(rows), self.ev.analyse(rows)
        self.assertEqual(a, b)
        c = a["contrasts"][0]
        self.assertAlmostEqual(c["diff"], 0.75)
        self.assertGreater(c["ci"][0], 0)
        self.assertLess(c["p"], 0.01)
        self.assertEqual(a["decision"], {"contradicting": "SUPPORTED", "none": "SUPPORTED"})
        self.assertEqual(len(a["leave_one_rule_out"]["none"]), 6)
        self.assertAlmostEqual(a["control_vs_consistent"]["diff"], 0.0)
        self.assertFalse(a["mixed_model"]["run"])

    def test_no_difference_is_refuted(self):
        res = self.ev.analyse(self.rows({"consistent": 4, "none": 4, "contradicting": 4}))
        self.assertEqual(res["decision"], {"contradicting": "REFUTED", "none": "REFUTED"})

    def test_ceiling_and_floor_are_inconclusive(self):
        res = self.ev.analyse(self.rows({"consistent": 0, "none": 0, "contradicting": 1}))
        self.assertTrue(res["decision"]["none"].startswith("INCONCLUSIVE"))
        res = self.ev.analyse(self.rows({"consistent": 8, "none": 8, "contradicting": 8}))
        self.assertTrue(res["decision"]["contradicting"].startswith("INCONCLUSIVE"))

    def test_markdown_renders(self):
        md = self.ev.markdown(self.ev.analyse(self.rows({"consistent": 1, "none": 4, "contradicting": 7})))
        self.assertIn("contradicting - consistent", md)
        self.assertIn("Not run", md)


class SmallTools(unittest.TestCase):
    def test_hash_tree_is_sorted_markdown(self):
        import hash_tree
        d = tempfile.mkdtemp()
        self.addCleanup(rmtree, d)
        with open(os.path.join(d, "b.txt"), "wb") as fh:
            fh.write(b"b\n")
        os.makedirs(os.path.join(d, "a"))
        with open(os.path.join(d, "a", "z.txt"), "wb") as fh:
            fh.write(b"abc")
        lines = hash_tree.table([d]).splitlines()
        self.assertEqual(lines[:2], ["| Path | SHA-256 |", "|---|---|"])
        self.assertTrue(lines[2].endswith("a/z.txt | ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad |"))
        self.assertIn("b.txt", lines[3])

    def test_gitattributes_pins_study_a_line_endings(self):
        self.assertIn("research/trials/studyA/** text eol=lf", read(os.path.join(ROOT, ".gitattributes")).splitlines())


class StudyBChecks(Tmp):
    """agent_tests.py: argument rules, JUnit reading, one log line per invocation, one database per invocation."""

    def setUp(self):
        super().setUp()
        import agent_tests
        self.at = agent_tests
        self.ws = os.path.join(self.d, "ws", "wabc")
        write(os.path.join(self.ws, "tests", "test_a.py"), "def test_a(): pass\n")
        self.runs = os.path.join(self.d, "runs")
        write(os.path.join(self.runs, "index.json"), json.dumps(
            [{"run": "T-rule-1", "workspace": self.ws, "rule_test_path": "tests/test_rule.py"}]))

    def patch(self, obj, name, value):
        self.addCleanup(setattr, obj, name, getattr(obj, name))
        setattr(obj, name, value)

    def test_arguments(self):
        ok = self.at.check_args(["tests/test_a.py::test_a", "-k", "a and not b", "-x", "-q", "tests"], self.ws)
        self.assertEqual(ok, ["tests/test_a.py::test_a", "-k", "a and not b", "-x", "-q", "tests"])
        for bad in (["--pdb"], ["-s"], ["-p", "x"], ["--rootdir=/"], ["-xq"], ["-kfoo"], ["-k"], ["../x.py"],
                    ["tests/../../x.py"], ["C:/x.py"], ["/etc/passwd"], ["tests\\..\\..\\x"], ["-c", "x.ini"],
                    ["--junitxml=/repo/x"]):
            with self.assertRaises(self.at.Refused, msg=str(bad)):
                self.at.check_args(bad, self.ws)

    def test_junit_counts_and_rule_test_detection(self):
        x = os.path.join(self.d, "r.xml")
        write(x, junit([("tests.test_rule", "test_r", "passed", ""), ("tests.test_rule.TestC", "test_c", "failed", ""),
                        ("tests.test_a", "test_a", "passed", ""), ("tests.test_rule_other", "test_o", "skipped", "")]))
        self.assertEqual(self.at.read_junit(x, "tests/test_rule.py"), (2, 1, 0, True))
        self.assertEqual(self.at.read_junit(x, "tests/test_zzz.py")[3], False)
        self.assertEqual(self.at.read_junit(x), (2, 1, 0, False))
        self.assertEqual(self.at.read_junit(os.path.join(self.d, "none.xml")), (0, 0, 0, False))

    def fake_pytest(self, code=0):
        calls = []

        def fake(workspace, args, rule_test_path, time_limit=0):
            calls.append((workspace, args, rule_test_path))
            return code, "\n".join(f"line {i}" for i in range(400)), 3, 1, 0, True
        self.patch(self.at, "run_pytest", fake)
        return calls

    def test_main_logs_one_line_per_invocation_and_prints_the_tail(self):
        import io
        import contextlib
        calls = self.fake_pytest(1)
        for _ in range(2):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                self.assertEqual(self.at.main([self.runs, "wabc", "tests/test_a.py", "-x"]), 1)
        self.assertEqual(len(buf.getvalue().splitlines()), 150)
        self.assertTrue(buf.getvalue().startswith("line 250"))
        rows = [json.loads(l) for l in read(os.path.join(self.runs, "checks", "T-rule-1.jsonl")).splitlines()]
        self.assertEqual(len(rows), 2)
        self.assertEqual(sorted(rows[0]), sorted(["ts", "args", "exit_code", "passed", "failed", "errors", "seconds", "ran_rule_test"]))
        self.assertEqual((rows[0]["args"], rows[0]["exit_code"], rows[0]["passed"], rows[0]["failed"], rows[0]["ran_rule_test"]),
                         (["tests/test_a.py", "-x"], 1, 3, 1, True))
        self.assertEqual(calls[0][2], "tests/test_rule.py")

    def test_refusals_run_nothing_and_log_nothing(self):
        import io
        import contextlib
        calls = self.fake_pytest()
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(self.at.main([self.runs, "wabc", "--pdb"]), 2)
            self.assertEqual(self.at.main([self.runs, "unknown"]), 2)
        self.assertEqual(calls, [])
        self.assertFalse(os.path.exists(os.path.join(self.runs, "checks")))

    def test_each_invocation_has_its_own_postgres_and_removes_it(self):
        seen = []

        kws = []

        def fake_docker(cmd, **kw):
            seen.append(cmd)
            kws.append(kw)
            return subprocess.CompletedProcess(cmd, 0, "ok\n", "")
        self.patch(self.at, "docker", fake_docker)
        self.patch(self.at.time, "sleep", lambda s: None)
        self.at.run_pytest(self.ws, ["tests"], None)
        self.at.run_pytest(self.ws, ["tests"], None)
        pgs = [c[c.index("--name") + 1] for c in seen if c[0] == "run" and "-d" in c]
        nets = [c[c.index("--network") + 1] for c in seen if c[0] == "run" and "--network" in c]
        self.assertEqual(len(set(pgs)), 2)
        self.assertEqual(sorted(nets), sorted(f"container:{p}" for p in pgs))
        removed = [c[2] for c in seen if c[:2] == ["rm", "-f"]]
        self.assertTrue(all(p in removed for p in pgs))
        runs = [(c, k) for c, k in zip(seen, kws) if "--network" in c]
        self.assertTrue(all(k.get("workspace") == self.ws for _, k in runs))  # the tree goes in as a stream, no mount
        self.assertFalse(any(":/repo" in a for c, _ in runs for a in c))
        self.assertTrue(all("--reuse-db" in c for c, _ in runs))  # the fake docker has the base image
        self.assertTrue(all(self.at.PG_BASE_IMAGE in c for c in seen if c[0] == "run" and "-d" in c))

    def test_without_the_base_image_postgres_is_new_and_the_db_is_not_reused(self):
        seen = []

        def fake_docker(cmd, **kw):
            seen.append(cmd)
            return subprocess.CompletedProcess(cmd, 1 if cmd[:2] == ["image", "inspect"] else 0, "ok\n", "")
        self.patch(self.at, "docker", fake_docker)
        self.patch(self.at.time, "sleep", lambda s: None)
        self.at.run_pytest(self.ws, ["tests"], None)
        self.assertTrue(any(self.at.PG_IMAGE in c for c in seen if c[0] == "run"))
        self.assertFalse(any("--reuse-db" in c for c in seen))

    def test_tree_stream_skips_git_and_bytecode_and_keeps_paths(self):
        import io
        import tarfile
        write(os.path.join(self.ws, ".git", "HEAD"), "x\n")
        write(os.path.join(self.ws, "pkg", "__pycache__", "m.pyc"), "x\n")
        write(os.path.join(self.ws, "pkg", "m.py"), "x = 1\n")
        buf = io.BytesIO()
        self.at.send_tree(self.ws, buf)
        buf.seek(0)
        self.assertEqual(sorted(tarfile.open(fileobj=buf).getnames()), ["pkg/m.py", "tests/test_a.py"])

    def test_timeout_removes_the_test_container(self):
        seen = []

        def fake_docker(cmd, **kw):
            seen.append(cmd)
            if "--network" in cmd:
                raise subprocess.TimeoutExpired(cmd, 1, output=b"partial")
            return subprocess.CompletedProcess(cmd, 0, "", "")
        self.patch(self.at, "docker", fake_docker)
        self.patch(self.at.time, "sleep", lambda s: None)
        code, text, *_ = self.at.run_pytest(self.ws, ["tests"], None, time_limit=5)
        self.assertEqual(code, 124)
        self.assertIn("TIME LIMIT", text)
        self.assertTrue(any(c[:2] == ["rm", "-f"] and c[2].startswith("ucn-agent-tests-") for c in seen))


class StudyBArms(Tmp):
    """recon.prepare with arms, and the grading additions."""

    def setUp(self):
        super().setUp()
        import recon
        self.recon = recon
        self.repo = os.path.join(self.d, "repo")
        write(os.path.join(self.repo, "src", "app", "a", "x.ts"), "export const x = 1;\n")
        write(os.path.join(self.repo, "AGENTS.md"), "agents\n")
        write(os.path.join(self.repo, "docs", "adr", "0001.md"), "adr\n")
        for cmd in (["init", "-q"], ["add", "-A"], ["-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "base"]):
            subprocess.run(["git", "-C", self.repo, *cmd], capture_output=True, check=True)
        self.rev = subprocess.run(["git", "-C", self.repo, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        self.model = os.path.join(self.d, "model.ucn")
        write(self.model, GENERIC + "\nrule QuietNames: names stay in lower case\n  src: README.md\n")
        self.tasks = os.path.join(self.d, "tasks")
        write(os.path.join(self.tasks, "T1", "task.md"), "Change component A so that it exports y.\n")
        write(os.path.join(self.tasks, "T1", "meta.json"), json.dumps({"kind": "tempting", "rule_id": "Q7", "site": "none"}))
        self.rules = os.path.join(self.d, "rules")
        write(os.path.join(self.rules, "Q7", "prose.md"),
              "<!-- docs/adr/0042-names.md lines 1-3 -->\nComponents exports are named in lower case.\n")
        write(os.path.join(self.rules, "Q7", "rule_test.py"), "def test_rule(): pass\n")
        write(os.path.join(self.rules, "Q7", "meta.json"),
              json.dumps({"rule_test_path": "src/app/a/tests/test_rule.py", "ucn_rule": "QuietNames"}))
        self.out = os.path.join(self.d, "out")
        arms = {"none": ("none", "none"), "prose": ("prose", "none"), "gen": ("none", "generic"),
                "rule": ("none", "rule"), "prule": ("prose", "rule"), "urule": ("ucn", "rule")}
        self.spec = {"repo": self.repo, "rev": self.rev, "model": self.model, "tasks": self.tasks, "rules_dir": self.rules,
                     "arms": {n: {"guidance": g, "check": c, "runs": 1} for n, (g, c) in arms.items()},
                     "remove": {"C": ["docs/adr"]}, "squash_base": True, "anonymous_workspaces": True,
                     "validator": "ucn/ucn_validate.py", "today": TODAY, "grader_image": "G"}
        self.index = {e["cond"]: e for e in self.recon.prepare(self.spec, self.out)}

    def prompt(self, arm):
        return read(os.path.join(self.out, f"T1-{arm}-1.prompt.txt"))

    def test_run_ids_workspaces_and_fields(self):
        self.assertEqual(sorted(self.index), sorted(self.spec["arms"]))
        e = self.index["urule"]
        self.assertEqual((e["run"], e["arm"], e["guidance"], e["check"]), ("T1-urule-1", "urule", "ucn", "rule"))
        self.assertRegex(os.path.basename(e["workspace"]), r"^w[0-9a-f]{10}$")
        ws = e["workspace"]
        self.assertFalse(os.path.exists(os.path.join(ws, "docs", "adr")))
        self.assertFalse(os.path.exists(os.path.join(ws, "AGENTS.md")))
        self.assertTrue(os.path.exists(os.path.join(ws, "context.ucn")))
        self.assertFalse(os.path.exists(os.path.join(ws, "model.ucn")))
        self.assertEqual(self.recon.changed_since(ws, e["base_commit"]), [])

    def test_prompts(self):
        for arm in self.spec["arms"]:
            text = self.prompt(arm)
            self.assertNotIn("Q7", text)
            self.assertNotIn("xperiment", text)
            if arm in ("prule", "urule", "gen"):
                self.assertNotRegex(text, rf"\b{arm}\b")
        self.assertIn("do not run the project's test suite", self.prompt("none"))
        self.assertNotIn("agent_tests.py", self.prompt("prose"))
        self.assertIn("Project documentation that can be relevant:\n\nComponents exports", self.prompt("prose"))
        self.assertIn("agent_tests.py", self.prompt("gen"))
        self.assertIn(os.path.basename(self.index["gen"]["workspace"]), self.prompt("gen"))
        self.assertNotIn("test for a project rule", self.prompt("gen"))
        self.assertNotIn("do not run the project's test suite", self.prompt("gen"))
        for arm in ("rule", "prule", "urule"):
            t = self.prompt(arm)
            self.assertIn("src/app/a/tests/test_rule.py is a test for a project rule. It must pass at the end", t)
            self.assertIn("agent_tests.py", t)
        self.assertIn("Read context.ucn first", self.prompt("urule"))
        self.assertNotIn("ucn_validate", self.prompt("urule"))
        self.assertNotIn("model.ucn", self.prompt("urule"))

    def test_prose_has_no_source_comment_and_its_size_is_recorded(self):
        for arm in ("prose", "prule"):
            self.assertNotIn("<!--", self.prompt(arm))
            self.assertNotIn("0042", self.prompt(arm))
            self.assertIn("\n\nComponents exports are named in lower case.\n\nTask:", self.prompt(arm))
            self.assertEqual(self.index[arm]["prose_chars"], len("Components exports are named in lower case."))
        self.assertNotIn("prose_chars", self.index["none"])

    def test_ucn_context_holds_the_rule_and_records_budget_and_size(self):
        e = self.index["urule"]
        ctx = read(os.path.join(e["workspace"], "context.ucn"))
        self.assertIn("QuietNames", ctx)
        self.assertEqual((e["ucn_budget"], e["ucn_chars"]), (2500, len(ctx)))
        self.assertNotIn("ucn_budget", self.index["rule"])

    def test_ucn_context_grows_the_budget_in_steps_and_stops_if_the_rule_is_missing(self):
        calls = []

        def fake(model, task, budget, explicit=()):
            calls.append((budget, explicit))
            return ("has R" if budget >= 5000 else "none"), []
        real = self.recon.ucn_project.project
        self.recon.ucn_project.project = fake
        self.addCleanup(setattr, self.recon.ucn_project, "project", real)
        self.assertEqual(self.recon.ucn_context("m", "t", {"budget": 2500}, "R"), ("has R", 5000))
        self.assertEqual(calls, [(2500, ("R",)), (3500, ("R",)), (5000, ("R",))])
        with self.assertRaises(SystemExit) as cm:
            self.recon.ucn_context("m", "t", {"budget": 2500}, "Missing")
        self.assertIn("Missing", str(cm.exception))
        self.assertEqual(self.recon.ucn_context("m", "t", {"budget": 6000, "ucn_budgets": (3500, 9000)}, "R")[1], 6000)

    def test_a_ucn_arm_without_ucn_rule_is_refused(self):
        write(os.path.join(self.rules, "Q7", "meta.json"), json.dumps({"rule_test_path": "src/app/a/tests/test_rule.py"}))
        with self.assertRaises(SystemExit) as cm:
            self.recon.prepare(self.spec, os.path.join(self.d, "out4"))
        self.assertIn("ucn_rule", str(cm.exception))

    def test_workspaces_come_from_one_base_copy_and_are_identical_to_a_direct_checkout(self):
        self.assertTrue(os.path.isdir(os.path.join(self.out, "_base", "T1")))
        direct = os.path.join(self.d, "direct")
        subprocess.run(["git", "-c", "core.symlinks=false", "clone", "-q", "--no-tags", self.repo, direct], check=True)
        subprocess.run(["git", "-C", direct, "checkout", "-q", self.rev], check=True)
        self.recon.strip_docs(direct, ["docs/adr"])
        direct_base = self.recon.squash_base(direct)

        def files(root):
            return {os.path.relpath(os.path.join(d, n), root): self.recon.sha(os.path.join(d, n))
                    for d, ds, ns in os.walk(root) for n in ns if ".git" not in os.path.relpath(d, root).split(os.sep)}
        e = self.index["none"]
        self.assertEqual(files(e["workspace"]), {k: v for k, v in files(direct).items() if not k.endswith("AGENTS.md")
                                                  and not k.startswith("docs" + os.sep + "adr")})
        g = lambda ws, *a: subprocess.run(["git", "-C", ws, *a], capture_output=True, text=True).stdout
        self.assertEqual(g(e["workspace"], "status", "--porcelain"), "")
        self.assertEqual(len(g(e["workspace"], "log", "--format=%H").split()), 1)
        self.assertEqual(e["base_commit"], direct_base)  # the same commit id as a direct checkout and squash
        self.assertEqual(self.recon.changed_since(e["workspace"], e["base_commit"]), [])

    def test_rule_test_is_in_the_base_commit(self):
        e = self.index["rule"]
        p = os.path.join(e["workspace"], "src", "app", "a", "tests", "test_rule.py")
        self.assertEqual(read(p), "def test_rule(): pass\n")
        tracked = subprocess.run(["git", "-C", e["workspace"], "ls-files"], capture_output=True, text=True).stdout.split()
        self.assertIn("src/app/a/tests/test_rule.py", tracked)
        self.assertFalse(os.path.exists(os.path.join(self.index["gen"]["workspace"], "src", "app", "a", "tests")))

    def test_suffix_texts_are_spec_options(self):
        self.spec["suffix_generic"] = "GEN {cmd}"
        self.spec["suffix_rule"] = "RULE {cmd} {rule_test}"
        self.recon.prepare(self.spec, self.out)
        self.assertRegex(self.prompt("gen"), r"GEN python .*agent_tests\.py .* w[0-9a-f]{10}$")
        self.assertRegex(self.prompt("rule"), r"RULE python .*agent_tests\.py .* w[0-9a-f]{10} src/app/a/tests/test_rule\.py$")

    def test_prompt_with_the_rule_id_is_refused(self):
        write(os.path.join(self.rules, "Q7", "prose.md"), "Rule q7 says: lower case.\n")
        with self.assertRaises(SystemExit):
            self.recon.prepare(self.spec, os.path.join(self.d, "out2"))

    def test_conditions_still_work_in_a_conditions_spec(self):
        spec = dict(self.spec, conditions={"C": 1})
        del spec["arms"]
        idx = self.recon.prepare(spec, os.path.join(self.d, "out3"))
        self.assertEqual([e["run"] for e in idx], ["T1-C1"])
        self.assertNotIn("arm", idx[0])

    def grade(self, arm, edit=None, log=None):
        e = dict(self.index[arm])
        if edit:
            edit(e["workspace"])
        if log is not None:
            os.makedirs(os.path.dirname(e["checks_log"]), exist_ok=True)
            with open(e["checks_log"], "w") as fh:
                fh.write("".join(json.dumps(r) + "\n" for r in log))
        real = self.recon.run

        def fake(cmd, **kw):
            if cmd[0] != "docker":
                return real(cmd, **kw)
            out = [a for a in cmd if a.endswith(":/out")][0].rsplit(":", 1)[0]
            write(os.path.join(out, f"{e['run']}.xml"), junit([("test_t", "test_ok", "passed", "")]))
            return subprocess.CompletedProcess(cmd, 0, "", "")
        self.recon.run = fake
        self.addCleanup(setattr, self.recon, "run", real)
        spec = dict(self.spec, validator=ucn_dep.resolve("ucn/ucn_validate.py"))
        task = {"id": "T1", "dir": os.path.join(self.tasks, "T1"), "rule_id": "Q7"}
        return self.recon.grade_one(spec, e, task, set())

    def test_grading_fields_without_agent_changes(self):
        r = self.grade("rule")
        self.assertEqual((r["arm"], r["guidance"], r["check"]), ("rule", "none", "rule"))
        self.assertEqual((r["check_runs"], r["failed_check_runs"], r["rule_test_runs_before_first_pass"]), (0, 0, None))
        self.assertEqual((r["rule_test_changed"], r["changed"], r["tampered"]), (False, [], []))

    def test_check_log_counts(self):
        rows = [{"exit_code": 1, "ran_rule_test": False}, {"exit_code": 1, "ran_rule_test": True},
                {"exit_code": 0, "ran_rule_test": False}, {"exit_code": 1, "ran_rule_test": True},
                {"exit_code": 0, "ran_rule_test": True}, {"exit_code": 0, "ran_rule_test": True}]
        r = self.grade("rule", log=rows)
        self.assertEqual((r["check_runs"], r["failed_check_runs"], r["rule_test_runs_before_first_pass"]), (6, 3, 2))
        r = self.grade("gen", log=rows[:2])
        self.assertEqual((r["check_runs"], r["failed_check_runs"], r["rule_test_runs_before_first_pass"], r["rule_test_changed"]),
                         (2, 2, None, False))
        r = self.grade("rule", log=rows[:2])
        self.assertIsNone(r["rule_test_runs_before_first_pass"])

    def test_rule_test_change_or_delete_is_reported_apart(self):
        tp = lambda ws: os.path.join(ws, "src", "app", "a", "tests", "test_rule.py")
        r = self.grade("rule", edit=lambda ws: write(tp(ws), "def test_rule(): assert True\n"))
        self.assertTrue(r["rule_test_changed"])
        self.assertEqual(r["changed"], [])
        r = self.grade("prule", edit=lambda ws: (os.remove(tp(ws)), write(os.path.join(ws, "src", "new.ts"), "1\n")))
        self.assertTrue(r["rule_test_changed"])
        self.assertEqual(r["changed"], ["src/new.ts"])

    def test_ucn_arm_context_is_guarded(self):
        self.assertEqual(self.grade("urule")["tampered"], [])
        r = self.grade("urule", edit=lambda ws: write(os.path.join(ws, "context.ucn"), "edited\n"))
        self.assertEqual((r["tampered"], r["violations"]), (["context.ucn"], 1))


class Pilot(unittest.TestCase):
    def data(self, light, ucn, n=40, tempting=None, upkeep=(30, 1000), absent=0):
        tasks = [{"id": f"T{i}", "kind": "change",
                  "results": {"light": {"success": int(i < light * n)}, "ucn": {"success": int(i < ucn * n)}}}
                 for i in range(n)]
        for i, (vl, vu) in enumerate(tempting or []):
            tasks.append({"id": f"X{i}", "kind": "tempting",
                          "results": {"light": {"success": 1, "violations": vl}, "ucn": {"success": 1, "violations": vu}}})
        facts = [{"task": "T0", "fact": f"F{i}", "ucn": "absent" if i < absent else "present"} for i in range(100)]
        up = [{"week": w, "model_minutes": upkeep[0], "review_minutes": upkeep[1]} for w in range(1, 5)]
        return {"tasks": tasks, "facts": facts, "upkeep": up}

    def test_go_on_clear_gain(self):
        self.assertEqual(pilot_eval.evaluate(self.data(0.4, 0.8))["decision"], "GO")

    def test_go_on_fewer_violations(self):
        r = pilot_eval.evaluate(self.data(0.5, 0.5, tempting=[(1, 0)] * 12 + [(0, 0)] * 4))
        self.assertEqual(r["decision"], "GO")

    def test_kill_on_upkeep(self):
        self.assertEqual(pilot_eval.evaluate(self.data(0.4, 0.8, upkeep=(200, 1000)))["decision"], "KILL")

    def test_kill_when_no_better(self):
        self.assertEqual(pilot_eval.evaluate(self.data(0.6, 0.6, n=60))["decision"], "KILL")

    def test_extend_when_inconclusive(self):
        self.assertEqual(pilot_eval.evaluate(self.data(0.5, 0.6, n=20))["decision"], "EXTEND")

    def test_silent_absence_blocks_go(self):
        r = pilot_eval.evaluate(self.data(0.4, 0.8, absent=10))
        self.assertEqual(r["decision"], "EXTEND")

    def test_template_runs(self):
        with open(os.path.join(ROOT, "research", "harness", "pilot_template.json")) as f:
            self.assertIn(pilot_eval.evaluate(json.load(f))["decision"], ("GO", "KILL", "EXTEND"))


if __name__ == "__main__":
    unittest.main()
