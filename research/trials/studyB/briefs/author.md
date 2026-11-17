# Brief: author of rule material for Study B

Repository: `D:/personal/repos/agent-rule-compliance`. Your prompt gives you a list of rule ids.
Write all text in short, simple sentences.

For each rule id `R`, the task is in `research/trials/studyA/tasks/R-contradicting/`. You can read `task.md`,
`meta.json`, `reference.patch`, `naive.patch` and `seed.patch` there. **Do not open the folder `grader/`.** Your test
must be independent of the hidden tests in it. Do not read `research/trials/studyA/results` or `research/docs/12-*`.

The saleor clone is at
`C:/Users/mohaq/AppData/Local/Temp/claude/1d11edbaacebcf92/a36fd43d-7e35-4353-a3ad-ea5859286a7a/scratchpad/sal-base`
(revision `1d707dc`). Do not change that clone: make your own copy or worktree if you need one.

Make three files in `research/trials/studyB/rules/R/`:

## 1. `prose.md`

The part of the saleor documentation that states the rule, word for word (from `docs/adr`, `AGENTS.md` or a
different document in the clone). 250 words maximum. The first line is a comment with the source path and the line
range. The text must not refer to the ticket. If no document states the rule, write the rule in 3 to 5 neutral
sentences and say this in the first line.

## 2. `rule_test.py`

A pytest file that a maintainer could write to protect the rule for the feature of the ticket. Use the fixtures and
the style of the saleor tests in the same package.

- It examines the rule only, not the full behaviour of the feature.
- It passes on the base with `seed.patch` (if the task has one) and `reference.patch`.
- It fails on the base with `seed.patch` and `naive.patch`.
- Its test functions have names that start with `test_rule_`.
- It contains no comment that tells the reader how to implement the feature.

## 3. `meta.json`

`{"rule_id": "R", "rule_test_path": "<path in the saleor repository where the test file must be put>",
  "prose_source": "<path and lines, or 'written'>", "proof": {"reference": "passed", "naive": "failed: <test names>"}}`

## Proof

Prove the two conditions in the container `ucn-saleor-tests` or `ucn-saleor-grader`. `research/harness/prove.py` shows
how to run pytest against a workspace with a Postgres container. You can use a temporary copy of the task folder in
which `grader/` contains only your test. One proof step takes about 4 minutes. Run the steps one after the other, not
in parallel. Record the result in `meta.json`. If you cannot make a test that separates the two patches, say so
and explain the reason: do not weaken the test.

## Rules for you

- Do not create git commits. Change only files in `research/trials/studyB/rules/`.
- Final message: at most 120 words: for each rule, the test path, the proof result, and the source of the prose.
