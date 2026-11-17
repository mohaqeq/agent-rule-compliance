# Brief: make task variants for Study E

Study E changes the old code near the change site and keeps the ticket and the hidden grader of an existing task.
You make the variants and prove each one. You do not run coding agents, and you do not see any result of them.

## Inputs

- The repository `D:/personal/repos/agent-rule-compliance`. Read only these parts:
  - `research/trials/studyA/tasks/<task>/` (the source tasks),
  - `research/trials/studyC/rules/<rule>/places.json` and `research/trials/studyC/sentences.json`,
  - `research/trials/studyD/checks/<rule>.py` (static checks you can use to find code that breaks a rule),
  - `research/harness/prove.py` (run it; read its help).
  Do not read result files, analysis files, transcripts or other briefs.
- A clean saleor clone: `D:/work/d/saleor`, revision `1d707dc`. Do not change it. Work in your own copy if you
  need one (under the folder named in your prompt).

## What to make

For each rule in your prompt, make the folder `research/trials/studyE/tasks/<rule>-<variant>/` with:

| File | Contents |
|---|---|
| `task.md`, `grader/` | Copied unchanged from the source task |
| `seed.patch` | The variant (see below), as one patch against `1d707dc`. If the source task has a `seed.patch`, the new patch contains it as well. Existing tests that the change breaks are adjusted in the same patch, and only as much as necessary |
| `reference.patch`, `naive.patch` | From the source task. If they do not apply on top of the new seed, rebase them with the smallest change. The naive patch must still do the task and break the rule |
| `meta.json` | The source `meta.json` with `"site"` set to the variant name, `"seeded": true`, `"source_task"`, `"seed_tests"` (existing test files that cover the code that the seed changes), and `"variant_note"` (one or two sentences: what the seed changed, with file and function) |
| `proof.json` | Written by `prove.py` |

### Variant `repaired` (source: `<rule>-contradicting`)

Repair the old code that breaks the rule at each place in `research/trials/studyC/rules/<rule>/places.json`.
These are the places that Study C marked. Repair each listed function so that it follows the rule, with the same
behaviour for its callers. Do not repair other code. Use the form that the rule text asks for
(`research/trials/studyC/sentences.json`) and the form that the reference patch of the task uses.

### Variant `onewrong` (source: `<rule>-consistent`)

At the consistent site, most code near the change follows the rule. Change exactly **one** place so that it breaks
the rule: the place that follows the rule and that a developer of the ticket would most probably read and copy
(normally the nearest function of the same kind as the ticket asks for). Break the rule in the same way as the naive
patch of the task does, and keep the other behaviour of that function. Write the place in `variant_note`.

## Proof

Run for each folder:

```
python D:/personal/repos/agent-rule-compliance/research/harness/prove.py <task folder> --repo D:/work/d/saleor --rev 1d707dc
```

All steps must hold (base fails the behaviour tests, reference passes all, naive passes behaviour and fails a rule
test, seed keeps the `seed_tests` green). If a step fails, correct the seed or the rebased patches and run again.
Never change `task.md` or the grader. If a variant cannot be proven, stop for that rule and say why.

Each proof run takes some minutes. Run at most two proofs at the same time.

## Report

For each rule: the variant, what the seed changed (file and function), the changes to the reference or naive patch
(if any), the existing tests that you adjusted, and the result of `prove.py`.
