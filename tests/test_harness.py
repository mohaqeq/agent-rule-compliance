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
