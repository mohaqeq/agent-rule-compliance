"""Reconstruction harness (after Ensemble's fresh-student test, adapted to changes in existing code).

An agent gets a task and its condition's context; a HIDDEN grader (behavioral tests the agent never sees) decides
whether the behavior was built, and the project's own architecture checker plus the UCN validator decide whether
the architecture was kept. All third-party code (the project's tests, import-linter) runs in containers.

  python tools/recon.py prepare SPEC.json OUT_DIR      # workspaces + prompt.txt per (task, condition, run)
  python tools/recon.py grade   SPEC.json OUT_DIR      # results.json + pilot.json (input for tools/pilot_eval.py)

SPEC.json:
  {"repo": "path to a clean clone", "rev": "commit", "model": "path to the deny-list UCN model",
   "tasks": "dir with one sub-dir per task: task.md, grader/test_*.py, meta.json {kind, rule}",
   "conditions": {"C": 1, "L": 2, "B": 2}, "budget": 2500,
   "grader_image": "ucn-sqlfluff-tests", "lint_image": "ucn-il", "validator": "path to tools/ucn_validate.py",
   "usage": "optional JSON {run_id: [tokens, seconds, tool_calls]}", "model_name": "optional label, e.g. haiku",
   "squash_base": "optional bool: each workspace gets a fresh .git with one commit of the prepared tree (hides the seed)"}
A task dir may hold seed.patch (applied to every workspace right after checkout; it is part of the base, never of the
agent's change) and meta.json may carry rule_id, site, seeded, half: grade copies them (and model_name as
agent_model) into each row of results.json.
Conditions: C = no agent docs; L = the project's AGENTS.md + its import-linter in the loop;
            B = UCN projection (context.ucn) + the validator in the loop.
"""
import json
import re
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ucn"))
import ucn_project  # noqa: E402
import ucn_validate  # noqa: E402

SUFFIX = ("Make the change in the code under src/, and add or update tests under test/ where it makes sense. The "
          "project's dependencies are not installed on this machine: do not install packages and do not run the "
          "project's test suite; reason carefully about the code instead. Do not create git commits. Only modify "
          "files inside that repository directory.\n\nWhen you are done, reply with a short summary: files changed and why.")


CONTRACT_FILES = ("pyproject.toml", "setup.cfg", ".importlinter", ".dependency-cruiser.js", ".dependency-cruiser.cjs")


def sha(path):
    import hashlib
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def prose_excerpt(repo, task, size):
    """The AGENTS.md sections and docs/adr records that share the most words with the task, cut to `size` characters."""
    words = lambda t: {w for w in re.findall(r"[a-z][a-z_]{3,}", t.lower())}
    want, parts = words(task), []
    agents = os.path.join(repo, "AGENTS.md")
    if os.path.exists(agents):
        parts += ["## " + p if i else p for i, p in enumerate(open(agents, encoding="utf-8").read().split("\n## "))]
    adr = os.path.join(repo, "docs", "adr")
    for n in sorted(os.listdir(adr)) if os.path.isdir(adr) else []:
        if n.endswith(".md"):
            parts.append(open(os.path.join(adr, n), encoding="utf-8").read())
    ranked = sorted(parts, key=lambda p: -len(want & words(p)) / (1 + len(words(p))) ** 0.5)
    out = "# Excerpts from the project's AGENTS.md and docs/adr relevant to this task\n\n"
    for p in ranked:
        if len(out) >= size:
            break
        out += p.strip()[: max(0, size - len(out))] + "\n\n"
    return out


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)


def apply_seed(ws, task_dir):
    """Apply the task's seed.patch (if any) to a fresh checkout. Returns {path: sha256 or None (deleted)} of the files
    the seed touched, so grading can tell the seed from the agent's change."""
    patch = os.path.join(task_dir, "seed.patch")
    if not os.path.exists(patch):
        return {}
    r = run(["git", "-C", ws, "apply", "--whitespace=nowarn", os.path.abspath(patch)])
    if r.returncode != 0:
        raise SystemExit(f"seed.patch does not apply in {ws}: {r.stderr.strip()[-300:]}")
    return status_paths(ws, hashes=True)


def status_paths(ws, hashes=False):
    st = run(["git", "-C", ws, "status", "--porcelain", "--untracked-files=all"]).stdout
    paths = [l[3:].strip().strip('"') for l in st.splitlines() if l.strip()]
    if not hashes:
        return paths
    return {c: (sha(os.path.join(ws, c)) if os.path.isfile(os.path.join(ws, c)) else None) for c in paths}


def not_seed(paths, ws, seeded):
    """Drop the paths whose state is still exactly the seeded one."""
    def same(c):
        if c not in seeded:
            return False
        p = os.path.join(ws, c)
        return (sha(p) if os.path.isfile(p) else None) == seeded[c]
    return [c for c in paths if not same(c)]


SQUASH_ENV = {"GIT_AUTHOR_NAME": "dev", "GIT_AUTHOR_EMAIL": "dev@example.com", "GIT_COMMITTER_NAME": "dev",
              "GIT_COMMITTER_EMAIL": "dev@example.com", "GIT_AUTHOR_DATE": "2000-01-01T00:00:00+0000",
              "GIT_COMMITTER_DATE": "2000-01-01T00:00:00+0000"}


def squash_base(ws):
    """Replace ws/.git with a fresh repository holding one commit of the prepared tree (no seed diff, no history).
    Returns the commit id."""
    def onexc(func, path, exc):  # git marks object files read-only on Windows
        os.chmod(path, 0o700)
        func(path)
    gd = os.path.join(ws, ".git")
    if os.path.isdir(gd):
        shutil.rmtree(gd, onerror=onexc)
    env = dict(os.environ, **SQUASH_ENV)
    g = ["git", "-c", "core.autocrlf=false", "-c", "core.safecrlf=false", "-c", "core.longpaths=true", "-C", ws]
    for cmd in (["init", "-q"], ["config", "core.autocrlf", "false"], ["add", "-A"],
                ["commit", "-q", "--allow-empty", "-m", "Initial import"]):
        r = run(g + cmd, env=env)
        if r.returncode != 0:
            raise SystemExit(f"squash_base failed in {ws}: git {cmd[0]}: {r.stderr.strip()[-300:]}")
    return run(g + ["rev-parse", "HEAD"]).stdout.strip()


def changed_since(ws, commit):
    """Paths that differ from `commit`: committed, staged, unstaged and untracked changes all count."""
    tracked = run(["git", "-C", ws, "diff", "--name-only", "-z", commit]).stdout
    untracked = run(["git", "-C", ws, "ls-files", "--others", "--exclude-standard", "-z"]).stdout
    return sorted({p for p in (tracked + untracked).split("\0") if p})


def tasks_of(spec):
    out = []
    for name in sorted(os.listdir(spec["tasks"])):
        d = os.path.join(spec["tasks"], name)
        if os.path.isfile(os.path.join(d, "task.md")):
            meta = json.load(open(os.path.join(d, "meta.json"), encoding="utf-8")) if os.path.exists(os.path.join(d, "meta.json")) else {}
            out.append({"id": name, "dir": d, "text": open(os.path.join(d, "task.md"), encoding="utf-8").read().strip(), **meta})
    if spec.get("kinds"):  # e.g. ["tempting"] for the screening runs
        out = [t for t in out if t.get("kind") in spec["kinds"]]
    return out


def instructions(cond, ws, spec):
    ws = ws.replace("\\", "/")
    if cond == "C":
        return "Read the code for context."
    if cond == "S":
        return ("Read context.md first: it holds the parts of the project's architecture and decision documents that are "
                "relevant to this task. Follow them; if you think one of them should change, say so in your summary instead.")
    if cond == "L" and not spec.get("lint_image"):
        return ("Read AGENTS.md (in the repository root, and the AGENTS.md files in subdirectories) first: it describes the "
                "conventions and rules you must follow; the decision records it points to are in docs/adr.")
    if cond == "L":
        return ("Read AGENTS.md (in the repository root, and the AGENTS.md files in subdirectories) first: they describe the "
                "conventions and architecture rules you must follow. The architecture contracts are enforced in CI with "
                "import-linter. Before you finish, run this command (it runs import-linter in a container against this "
                "repository) and fix every BROKEN contract by changing the code:\n"
                f'MSYS_NO_PATHCONV=1 docker run --rm -v "{ws}:/repo:ro" {spec["lint_image"]} --no-cache\n'
                "Do not edit the import-linter contracts in pyproject.toml; if you think they should change, say so in your summary instead.")
    return ("Read context.ucn first: it is the part of the project's architecture model that is relevant to this task, in UCN "
            "format (indentation means containment; `forbids`, `layers` and `independent` are enforced rules; `deviation` "
            "blocks are approved exceptions; `req`, `decision` and `rule` lines are requirements and decisions you must "
            "respect; `more:` lines name what was left out; the policy is deny-list: anything not forbidden is allowed). The architecture is enforced in CI. Before you finish, run "
            f"`python {spec['validator']} model.ucn` from the repository root and fix every VIOLATION by changing the code "
            "(KNOWN-CONFLICT lines are pre-existing and not yours to fix). Do not edit model.ucn or context.ucn; if you think "
            "the architecture itself should change, say so in your summary instead.")


def prepare(spec, out):
    spec = dict(spec, validator=os.path.abspath(spec["validator"]))  # prompts must name a path that works anywhere
    os.makedirs(out, exist_ok=True)
    index = []
    for t in tasks_of(spec):
        for cond, k in spec["conditions"].items():
            for r in range(1, k + 1):
                rid = f"{t['id']}-{cond}{r}"
                ws = os.path.abspath(os.path.join(out, rid))
                if spec.get("anonymous_workspaces"):  # the path must not tell the agent its task or condition
                    import hashlib
                    ws = os.path.abspath(os.path.join(out, "ws", "w" + hashlib.sha256(rid.encode()).hexdigest()[:10]))
                    os.makedirs(os.path.dirname(ws), exist_ok=True)
                if not os.path.exists(ws):
                    run(["git", "-c", "core.symlinks=false", "-c", "core.longpaths=true", "clone", "-q", "--no-tags", spec["repo"], ws])
                    run(["git", "-C", ws, "checkout", "-q", spec["rev"]])
                    seeded = apply_seed(ws, t["dir"])
                    with open(os.path.join(out, f"{rid}.seed.json"), "w") as fh:
                        json.dump(seeded, fh)
                else:
                    sf = os.path.join(out, f"{rid}.seed.json")
                    seeded = json.load(open(sf)) if os.path.exists(sf) else {}
                if cond in ("C", "B", "S"):
                    for d, _, names in os.walk(ws):
                        if ".git" in d.split(os.sep):
                            continue
                        for n in names:
                            if n in ("AGENTS.md", "CLAUDE.md"):
                                os.remove(os.path.join(d, n))
                for rel in spec.get("remove", {}).get(cond, []):  # e.g. {"C": ["docs/adr"]}: no decision docs at all
                    p = os.path.join(ws, rel)
                    shutil.rmtree(p) if os.path.isdir(p) else (os.remove(p) if os.path.exists(p) else None)
                if cond == "S":  # size-matched prose: the most relevant doc sections, cut to the size of the UCN context
                    size = len(ucn_project.project(spec["model"], t["text"], spec.get("budget", 2500))[0])
                    with open(os.path.join(ws, "context.md"), "w", encoding="utf-8", newline="\n") as fh:
                        fh.write(prose_excerpt(spec["repo"], t["text"], size))
                if cond == "B":
                    shutil.copy(spec["model"], os.path.join(ws, "model.ucn"))
                    text, errs = ucn_project.project(os.path.join(ws, "model.ucn"), t["text"], spec.get("budget", 2500))
                    if errs:
                        raise SystemExit(f"{rid}: projection failed: {errs}")
                    with open(os.path.join(ws, "context.ucn"), "w", encoding="utf-8", newline="\n") as fh:
                        fh.write(text)
                base_commit = squash_base(ws) if spec.get("squash_base") else None
                guarded = {n: sha(os.path.join(ws, n)) for n in ("context.ucn", "context.md") if os.path.exists(os.path.join(ws, n))}
                prompt = (f"You are a developer working in the git repository at {ws.replace(chr(92), '/')} (Windows; use forward "
                          f"slashes). {instructions(cond, ws, spec)}\n\nTask: {t['text']}\n\n{spec.get('suffix', SUFFIX)}")
                with open(os.path.join(out, f"{rid}.prompt.txt"), "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(prompt)
                index.append({"run": rid, "task": t["id"], "cond": cond, "workspace": ws, "guarded": guarded, "seeded_files": seeded,
                              **({"base_commit": base_commit} if base_commit else {}),
                              "validator_sha": sha(spec["validator"]) if os.path.exists(spec["validator"]) else None})
    json.dump(index, open(os.path.join(out, "index.json"), "w"), indent=1)
    return index


def grade_one(spec, entry, task, baseline):
    ws = entry["workspace"]
    res = {"run": entry["run"], "task": entry["task"], "cond": entry["cond"]}
    for k in ("rule_id", "site", "seeded", "half"):
        if k in task:
            res[k] = task[k]
    if spec.get("model_name"):
        res["agent_model"] = spec["model_name"]
    seeded = entry.get("seeded_files", {})
    # 1. hidden grader (behavior)
    junit_dir = os.path.join(os.path.dirname(ws), "_junit")
    os.makedirs(junit_dir, exist_ok=True)
    old = os.path.join(junit_dir, f"{entry['run']}.xml")
    if os.path.exists(old):  # never re-read a previous grading's results if the container fails to start
        os.remove(old)
    g = run(["docker", "run", "--rm", *spec.get("grader_docker_args", []), "-v", f"{ws}:/repo:ro",
             "-v", f"{os.path.join(task['dir'], 'grader')}:/grader:ro", "-v", f"{junit_dir}:/out", spec["grader_image"],
             f"--junitxml=/out/{entry['run']}.xml", *spec.get("grader_args", [])])
    cases = ucn_validate.load_test_results([os.path.join(junit_dir, f"{entry['run']}.xml")]) if os.path.exists(
        os.path.join(junit_dir, f"{entry['run']}.xml")) else []
    res["grader"] = {"passed": sum(c["status"] == "passed" for c in cases), "total": len(cases)}
    behavior = [c for c in cases if c["name"].startswith("test_behavior")]
    rules = [c for c in cases if c["name"].startswith("test_rule")]
    if behavior or rules:  # graders that separate "task done" from "documented rule kept"
        res["success"] = int(bool(behavior) and all(c["status"] == "passed" for c in behavior))
        res["rule_failed"] = sorted(c["name"] for c in rules if c["status"] != "passed")
    else:
        res["success"] = int(bool(cases) and all(c["status"] == "passed" for c in cases))
        res["rule_failed"] = []
    # 2. the project's own import-linter contracts
    il = run(["docker", "run", "--rm", "-v", f"{ws}:/repo:ro", spec["lint_image"], "--no-cache"]) if spec.get("lint_image") else None
    line = next((l for l in il.stdout.splitlines() if l.startswith("Contracts:")), "") if il else ""
    res["import_linter"] = line
    if il is None:
        broken = 0
    elif "broken" in line:
        kept, broken = int(line.split()[1]), int(line.split("kept,")[1].split("broken")[0])
        if spec.get("contracts") and kept + broken != spec["contracts"]:  # a contract went missing: fail closed
            broken = max(broken, 1)
            res["grading_error"] = f"expected {spec['contracts']} contracts, import-linter saw {kept + broken}"
    else:  # fail closed: no result line means the check did not run (or the code no longer imports)
        broken = 1
        res["grading_error"] = "import-linter produced no 'Contracts:' line: " + (il.stdout + il.stderr)[-300:]
    # 3. the UCN validator with the pristine model (new findings only)
    gm = os.path.join(ws, "_grade_model.ucn")
    shutil.copy(spec["model"], gm)
    r = ucn_validate.validate(gm, today=spec.get("today"))
    r.pop("_model")
    os.remove(gm)
    found = {f["message"] for f in r["findings"] if f["class"] in ("VIOLATION", "CONFLICT") and f["check"] in ("architecture", "conventions")}
    res["validator_new"] = sorted(found - baseline)
    res["violations"] = int(bool(res["validator_new"]) or broken > 0 or bool(res["rule_failed"]))
    # 4. tampering and scope
    if entry.get("base_commit"):  # squashed base: everything that differs from that one commit is the agent's
        changed = changed_since(ws, entry["base_commit"])
    else:
        changed = not_seed(status_paths(ws), ws, seeded)  # the seed is part of the base, not the agent's change
    res["changed"] = [c for c in changed if c not in ("model.ucn", "context.ucn") and not c.endswith("AGENTS.md") and c != "CLAUDE.md"]
    tampered = [c for c in changed if c.rsplit("/", 1)[-1] in CONTRACT_FILES]  # the project's own contracts, any arm
    if entry["cond"] == "B":
        mp = os.path.join(ws, "model.ucn")
        if not os.path.exists(mp) or sha(mp) != sha(spec["model"]):
            tampered.append("model.ucn")
        for name, digest in entry.get("guarded", {}).items():
            p = os.path.join(ws, name)
            if not os.path.exists(p) or sha(p) != digest:
                tampered.append(name)
    if entry.get("validator_sha") and os.path.exists(spec["validator"]) and sha(spec["validator"]) != entry["validator_sha"]:
        tampered.append(spec["validator"])
    res["tampered"] = sorted(set(tampered))
    if res["tampered"]:
        res["violations"] = 1
    return res


def grade(spec, out):
    spec = dict(spec, validator=os.path.abspath(spec["validator"]))
    index = json.load(open(os.path.join(out, "index.json")))
    tasks = {t["id"]: t for t in tasks_of(spec)}
    baselines = {}

    def baseline_of(task):  # validator findings on the (seeded) base; one per task that has a seed
        key = task["id"] if os.path.exists(os.path.join(task["dir"], "seed.patch")) else ""
        if key not in baselines:
            base_ws = os.path.join(out, "_baseline" + (f"-{key}" if key else ""))
            if not os.path.exists(base_ws):
                run(["git", "-c", "core.longpaths=true", "clone", "-q", "--no-tags", spec["repo"], base_ws])
                run(["git", "-C", base_ws, "checkout", "-q", spec["rev"]])
                apply_seed(base_ws, task["dir"])
            gm = os.path.join(base_ws, "_m.ucn")
            shutil.copy(spec["model"], gm)
            b = ucn_validate.validate(gm, today=spec.get("today"))
            b.pop("_model")
            os.remove(gm)
            baselines[key] = {f["message"] for f in b["findings"] if f["class"] in ("VIOLATION", "CONFLICT")}
        return baselines[key]
    usage = json.load(open(spec["usage"])) if spec.get("usage") and os.path.exists(spec["usage"]) else {}
    results = []
    for e in index:
        res = grade_one(spec, e, tasks[e["task"]], baseline_of(tasks[e["task"]]))
        if e["run"] in usage:
            res["tokens"], res["seconds"], res["tool_calls"] = usage[e["run"]]
        res["kind"] = tasks[e["task"]].get("kind", "change")
        results.append(res)
        print(f"{e['run']:12} success={res['success']} grader={res['grader']['passed']}/{res['grader']['total']} "
              f"violations={res['violations']} {res['import_linter']} {'TAMPERED ' + str(res['tampered']) if res['tampered'] else ''}", flush=True)
    json.dump(results, open(os.path.join(out, "results.json"), "w"), indent=1)
    # pilot_eval input: pair run r of L ("light") with run r of B ("ucn") per task
    pilot = {"criteria": spec.get("criteria", {}), "tasks": []}
    by = {(r["task"], r["cond"], r["run"].rsplit("-", 1)[1][1:]): r for r in results}
    for t in tasks:
        for k in range(1, max(spec["conditions"].get("L", 0), spec["conditions"].get("B", 0)) + 1):
            l, u = by.get((t, "L", str(k))), by.get((t, "B", str(k)))
            if l and u:
                kind = tasks[t].get("kind", "change")
                pilot["tasks"].append({"id": f"{t}-r{k}", "kind": "tempting" if kind == "tempting" else "change", "cluster": t,
                                       "results": {c: {"success": x["success"], "violations": x["violations"],
                                                       **({"tokens": x["tokens"], "seconds": x["seconds"]} if "tokens" in x else {})}
                                                   for c, x in (("light", l), ("ucn", u))}})
    json.dump(pilot, open(os.path.join(out, "pilot.json"), "w"), indent=1)
    return results


if __name__ == "__main__":
    cmd, spec_path, out = sys.argv[1], sys.argv[2], sys.argv[3]
    spec = json.load(open(spec_path, encoding="utf-8"))
    if cmd == "prepare":
        idx = prepare(spec, out)
        print(f"prepared {len(idx)} workspaces in {out}")
    elif cmd == "grade":
        grade(spec, out)
