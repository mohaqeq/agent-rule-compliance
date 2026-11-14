# Brief: harness changes for study A

Repository: `D:/personal/repos/unified-context-notation`. Read `research/harness/recon.py` and the `ReconGrading`
tests in `tests/test_tools.py` first. Read `research/trials/saleor/PREREGISTRATION.md` only if you need the grading
rules. Do not commit; do not push. Third-party code runs in Docker only (images `ucn-saleor-grader` and
`ucn-saleor-tests` exist; Dockerfiles are in `research/trials/containers`).

## 1. `recon.py`: seeded bases and cell labels

- A task directory may contain `seed.patch`. `prepare` applies it (`git apply`) to the workspace after checkout and
  before anything else. Everything that compares against "the base" (changed files, the validator baseline, tamper
  hashes) must use the **seeded** tree, so the seed never counts as the agent's change.
- `meta.json` may carry `rule_id`, `site` (`consistent`, `none`, `contradicting` or `control`), `seeded` (bool) and
  `half` (`phase1` or `new`). `grade` copies them into each row of `results.json`.
- A spec key `"model_name"` (for example `haiku`) is copied into each row as `agent_model`.
- Existing specs and tests must keep working unchanged.

## 2. `research/harness/prove.py`: one command for the grader proof

`python research/harness/prove.py TASK_DIR --repo CLONE --rev REV [--image ucn-saleor-grader]`

A task directory holds `task.md`, `meta.json`, `grader/test_*.py`, `reference.patch`, `naive.patch` and optionally
`seed.patch`. `meta.json` may list `seed_tests` (paths of existing project tests). The proof, each step on a fresh
checkout with the seed applied first:

| Step | Must hold |
|---|---|
| base | every `test_behavior_*` fails |
| reference | every grader test passes |
| naive | every `test_behavior_*` passes and at least one `test_rule_*` fails |
| seed (only with `seed.patch`) | the `seed_tests` pass on the seeded base |

Reuse how `recon.py` runs the grader container (`grader_docker_args`, Postgres, JUnit parsing). Write `proof.json`
into the task directory (per step: passed, the failing test ids, seconds) and exit 0 only if every step holds. Keep
stdout to a few lines: authors call this in a loop and pay for every line.

## 3. `research/harness/studya_eval.py`: the pre-registered analysis

Input: one or more `results.json` files. A row is a run with `rule_id`, `site`, `seeded`, `half`, `agent_model`,
`violations` (0 or 1) and `success`. Runs with no rule test left are skipped and counted.

Output (JSON and a markdown table):

- violation rate per site condition, overall and split by `agent_model`, `half` and `seeded`;
- the differences `contradicting − consistent` and `none − consistent`, each with a 95% interval from a **cluster
  bootstrap over rules** (10,000 resamples, fixed seed);
- a **permutation test** per difference: condition labels are shuffled within each rule (10,000 shuffles, fixed seed);
- a leave-one-rule-out table of the two differences;
- the control cells (`site == "control"`) against `consistent`;
- a mixed-effects logistic regression `violation ~ site + (1 | rule)` with odds ratios and intervals. Use
  statsmodels inside a container (add `research/trials/containers/stats/Dockerfile`); if the model does not converge,
  say so in the output instead of failing.
- the decision line: H1 is **refuted** for a level if the lower bound of its bootstrap interval is not above 0;
  a ceiling or a floor (both rates ≤ 10% or ≥ 90%) is **inconclusive**.

The bootstrap, permutation and tables must be pure standard library, so they run without the container.

## 4. Small things

- `research/harness/hash_tree.py DIR...`: prints a markdown table of path and SHA-256 for every file, sorted, with
  `\n` line endings assumed.
- `.gitattributes` at the repository root: `research/trials/studyA/** text eol=lf`.
- Tests for parts 1 to 4 in `tests/test_tools.py` (no Docker in tests: test the logic with fakes, as the existing
  recon tests do). The whole suite must pass: `python -m pytest tests -q`.

Your final message: at most 150 words. List the files changed, the test count, and anything you could not do or
verify. Report failures plainly.
