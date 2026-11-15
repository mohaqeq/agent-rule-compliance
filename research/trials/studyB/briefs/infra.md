# Brief: infrastructure for Study B

Repository: `D:/personal/repos/agent-rule-compliance`. Read `research/docs/11-next-phase.md` (section "Study B" only),
`research/harness/recon.py`, `research/harness/prove.py` and `research/trials/studyA/spec.json`. Do not read the
Study A results. Write all text (comments, documents) in short, simple sentences.

Study B gives each coding agent one **arm**: a type of guidance and a type of check. You make the harness do this.
Do not change the behaviour of the existing conditions (`C`, `S`, `L`, `B`): Study A must stay reproducible.

## 1. Arms in `recon.py`

A spec can contain `"arms"` in place of `"conditions"`:

```json
"arms": {"none":  {"guidance": "none",  "check": "none",    "runs": 5},
         "prose": {"guidance": "prose", "check": "none",    "runs": 5},
         "gen":   {"guidance": "none",  "check": "generic", "runs": 5},
         "rule":  {"guidance": "none",  "check": "rule",    "runs": 5},
         "prule": {"guidance": "prose", "check": "rule",    "runs": 5},
         "urule": {"guidance": "ucn",   "check": "rule",    "runs": 5}},
"rules_dir": "research/trials/studyB/rules"
```

- Run id: `<task id>-<arm>-<k>`. Results get the fields `arm`, `guidance`, `check`.
- All arms remove the same documentation as condition `C` (spec `remove`), use `squash_base` and `anonymous_workspaces`.
- `guidance: prose`: put the text of `<rules_dir>/<rule_id>/prose.md` in the prompt, after a neutral line such as
  "Project documentation that can be relevant:". Do not use `prose_excerpt()`.
- `guidance: ucn`: make `context.ucn` in the workspace as condition `B` does, and name it in the prompt. Do not tell
  the agent to run the validator.
- `check: generic`: the prompt tells the agent how to run the project's tests (section 2).
- `check: rule`: as `generic`, and also copy `<rules_dir>/<rule_id>/rule_test.py` into the workspace at the path given in
  `<rules_dir>/<rule_id>/meta.json` (`"rule_test_path"`). The file is part of the squashed base commit. The prompt says
  that this file is a test for a project rule, that it must pass at the end, and how to run it.
- `check: none`: the prompt keeps the sentence that forbids test runs. For the other two values the prompt says
  that the agent must use only the given command to run tests. Make the two suffix texts spec options.
- The prompt must not contain the arm name, the word "experiment", or the rule id.

## 2. The test command for agents: `research/harness/agent_tests.py`

`python agent_tests.py RUNS_DIR RUN_TOKEN [pytest arguments]`

- `RUN_TOKEN` is the anonymous workspace name. The tool finds the workspace from `RUNS_DIR/index.json`.
- It runs pytest in the image `ucn-saleor-tests` with the workspace mounted, as `prove.py` does for the seed tests.
- Many agents run at the same time. Two invocations must not use the same database. Find a safe method (for example
  one database name for each invocation) and prove it with two parallel invocations.
- Accept only pytest paths and node ids inside the repository, and `-k`, `-x`, `-q`. Refuse all other options.
- Time limit: 15 minutes for each invocation. Print the last 150 lines of the pytest output.
- Write one JSON line for each invocation to `RUNS_DIR/checks/<run id>.jsonl`:
  `{"ts", "args", "exit_code", "passed", "failed", "errors", "seconds", "ran_rule_test"}`.
  `ran_rule_test` is true when the selected tests include the rule test of that run.
- The agent must not be able to change the log through the workspace.

## 3. Grading additions in `recon.py`

For runs with arms, add to each result:

- `check_runs`: the number of invocations;
- `failed_check_runs`: invocations with an exit code that is not 0;
- `rule_test_runs_before_first_pass`: for `check: rule`, invocations with `ran_rule_test` before the first one that passed (null if none passed);
- `rule_test_changed`: true if the agent changed or deleted the rule test file. Such a file does not count as a change of the agent in `changed`.

The hidden grader and the violation rule stay as they are.

## 4. Verification that you must do

1. Unit tests for all new code in `tests/test_harness.py`. All tests pass: `python -m unittest discover -s tests`.
2. A real check: prepare one workspace for the task `P3-contradicting` with an arm that has `check: generic`
   (saleor clone: `C:/Users/mohaq/AppData/Local/Temp/claude/1d11edbaacebcf92/a36fd43d-7e35-4353-a3ad-ea5859286a7a/scratchpad/sal-base`, revision `1d707dc`;
   output under `D:/ucn-studyb-runs/smoke`). Run `agent_tests.py` on one small existing test file two times in parallel. Show the log lines.
3. Report whether `research/trials/saleor/model.ucn` contains the rules N1 (webhooks through `call_event`),
   N2 (thumbnail `sizeRounding`, ADR 0011) and N3 (`pk`, not `id`). Do not change the model.

## Rules for you

- Do not create git commits. Do not push.
- Do not start coding agents.
- Final message: at most 150 words: what you made, the result of each verification step, and each open problem.
