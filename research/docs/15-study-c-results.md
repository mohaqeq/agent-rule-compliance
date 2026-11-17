# 15. Study C results: information about the wrong precedent prevents most violations

Date: 2026-11-17. Pre-registration: [trials/studyC/PREREGISTRATION.md](../trials/studyC/PREREGISTRATION.md)
(pushed before any run). Data: [trials/studyC/results](../trials/studyC/results/).

## Summary

Study A showed that the agent copies old code that breaks a rule. Study D showed that a tool can find that old code.
Study C tested if the information "this old code breaks the rule, do not copy it" prevents the violation.

- **A comment at the old code (`mark`) prevents most violations.** Haiku: 87% to 20%. Sonnet: 94% to 18%.
- **The same information in the ticket (`warn`) also prevents most violations.** Haiku: 87% to 7%. Sonnet: 94% to 33%.
- **H6 and H7 are supported for the two models.** The difference between `mark` and `warn` is not shown (H8).
- **The two measures are as effective as the full rule text of Study B** (20% Haiku, 22% Sonnet), but they need
  one sentence and a list of places, and a tool can make them.
- **With the warning, Haiku also repaired the old code in all 20 scanned runs.** Sonnet did this less often.
- **The measures fail where the agent uses the old code without a copy of its form.** Example: P3 with `mark`
  for Haiku (4 of 5).

## Method in short

- The six contradicting tasks of Study A, the same base, prompt frame and hidden graders as Study B. No test command.
- `none`: the ticket only. `mark`: a two-line comment above each place of old code that breaks the rule ("the code
  below breaks a project rule and stays only until it is repaired. Do not copy it." and the rule in one sentence).
  `warn`: the same text in the ticket, with the list of places.
- The places of N1, N2, N3 and P3 come from the static checks of Study D. The places of P1 and P5 were given by hand.
- Haiku: 5 runs for each task and arm (90). Sonnet: 3 runs for each task and arm (54).

## Primary result (Haiku, 90 runs, no exclusion)

| Arm | Violations | Rate | Task success |
|---|---|---|---|
| `none` | 26 / 30 | 86.7% | 80.0% |
| `mark` | 6 / 30 | 20.0% | 93.3% |
| `warn` | 2 / 30 | 6.7% | 96.7% |

| Difference | Estimate | 95% cluster-bootstrap interval | Permutation p | Decision |
|---|---|---|---|---|
| `mark` − `none` (H6) | −66.7 pp | −93.3 to −40.0 | 0.0001 | **effective** |
| `warn` − `none` (H7) | −80.0 pp | −100.0 to −46.7 | 0.0001 | **effective** |
| `mark` − `warn` (H8) | +13.3 pp | −13.3 to +43.3 | 0.23 | no difference shown |

The `none` arm reproduced the baseline of Study B (86.7% there also).

| Rule | `none` | `mark` | `warn` |
|---|---|---|---|
| N1 webhooks through `call_event` | 5/5 (5) | 0/5 (5) | 0/5 (5) |
| N2 thumbnail rounding default | 5/5 (1) | 0/5 (5) | 0/5 (5) |
| N3 `pk`, not `id` | 5/5 (5) | 2/5 (5) | 0/5 (5) |
| P1 gift card stays restricted | 5/5 (5) | 0/5 (4) | 1/5 (5) |
| P3 no `settings.SITE_ID` | 5/5 (4) | 4/5 (4) | 0/5 (5) |
| P5 race-safe gift card balance | 1/5 (4) | 0/5 (5) | 1/5 (4) |

Each cell shows violations of the runs. The number in parentheses is the number of runs with task success.

- Leave one rule out: `mark` − `none` −60 to −76 pp, `warn` − `none` −76 to −96 pp.
- Sensitivity 1 (only runs with task success): `none` 83.3%, `mark` 21.4%, `warn` 3.4%. The same decisions.
- Sensitivity 2 (without P1 and P5): `none` 100%, `mark` 30%, `warn` 0%. The same decisions.
- Cost: the median tokens are almost equal (`none` 89,400, `mark` 92,200, `warn` 90,400).

## Sonnet replication (54 runs, one run without a measure)

| Arm | Violations | Rate | Task success |
|---|---|---|---|
| `none` | 17 / 18 | 94.4% | 61.1% |
| `mark` | 3 / 17 | 17.6% | 88.2% |
| `warn` | 6 / 18 | 33.3% | 55.6% |

| Difference | Estimate | 95% cluster-bootstrap interval | Permutation p | Decision |
|---|---|---|---|---|
| `mark` − `none` | −76.8 pp | −100.0 to −36.7 | 0.0001 | effective |
| `warn` − `none` | −61.1 pp | −94.4 to −16.7 | 0.0008 | effective |
| `mark` − `warn` | −15.7 pp | −38.2 to 0.0 | 0.31 | no difference shown |

| Rule | `none` | `mark` | `warn` |
|---|---|---|---|
| N1 | 3/3 (3) | 0/3 (3) | 0/3 (3) |
| N2 | 3/3 (0) | 0/3 (3) | 0/3 (3) |
| N3 | 3/3 (3) | 0/3 (3) | 0/3 (3) |
| P1 | 3/3 (1) | 1/3 (3) | 1/3 (0) |
| P3 | 3/3 (3) | 0/3 (3) | 2/3 (1) |
| P5 | 2/3 (1) | 2/2 (0) | 3/3 (0) |

- For the four scanned rules, Sonnet had 0 of 12 violations with `mark` and 2 of 12 with `warn`.
- For P1 and P5 (places given by hand), the measures helped less. Sonnet with `warn` had no task success for P1 and P5.
- One run (`P5-contradicting-mark-1`) has no measure. The code of the agent breaks the GraphQL schema at import,
  so no test of the hidden grader can start. The run counts as a task failure, and its violation is unknown.
  The analysis leaves it out. The grading tool reported it, as required.

## Repair of the old code (descriptive, pre-registered item 5)

For N1, N2, N3 and P3, the Study D check ran on the files of the places after each run.

| Arm | Haiku: old code fully repaired | Sonnet: fully repaired | Sonnet: partly repaired |
|---|---|---|---|
| `none` | 0 / 20 | 0 / 12 | 0 / 12 |
| `mark` | 1 / 20 | 3 / 12 | 6 / 12 |
| `warn` | 20 / 20 | 3 / 12 | 3 / 12 |

- With the warning, each Haiku run repaired all the old violations in the listed places. The text says that the
  code "stays only until it is repaired", and Haiku took this as part of the task.
- This makes the change larger: the median number of changed files was 6.5 with `warn` against 5.5 with `none`.
- A repaired precedent removes the cause for the next change also. But a team that uses such a warning must expect
  changes outside the ticket.

Comments (item 6): 1 of 30 Haiku runs and 4 of 18 Sonnet runs removed a mark comment. Each of these runs also
repaired all or part of the marked code, and none had a violation.

## Where the measures failed

- **P3 with `mark` (Haiku 4 of 5).** The mark is above the old line `Site.objects.get(pk=settings.SITE_ID)`.
  The agents did not copy that line. They used its variable `site_settings` in the new code. The comment says
  "do not copy", and the agents did not copy. This is the same mechanism that Study D found for the static check.
  With `warn`, Haiku repaired the line, and no run broke the rule.
- **N3 with `mark` (Haiku 2 of 5).** The two marked places stayed as they were, and the new code used `id`.
  I did not examine which code the agents copied.
- **P1 and P5.** The places were given by hand, and the behaviour rules have no simple form to avoid. Sonnet had
  more violations and less task success there with `warn`.

## Comparison with Study B (not a concurrent arm)

| Measure | Haiku | Sonnet |
|---|---|---|
| Nothing | 87% (B), 87% (C) | 94% (C) |
| The full rule text in the ticket (Study B `prose`) | 20% | 22% |
| A comment at the old code (`mark`) | 20% | 18% |
| A scan warning in the ticket (`warn`) | 7% | 33% |
| A test for the rule (Study B `rule`) | 0% | 0% |

## What this means

- The cheapest effective measure is at the precedent. A one-sentence warning at the old code, or a list of the
  old code in the ticket, prevents most violations. It does not need the full documentation of the rule.
- A tool can make this information. For four of six rules the static checks of Study D found the places, and with
  those places both models had 0 to 2 violations in 12 to 20 runs for each arm.
- It is not sufficient. A test for the rule stays the only measure with 0%.
- For a team the order is now: (1) make the rule executable where it is possible; (2) scan for old violations and
  mark or repair them; (3) document the rule.

## Limits

- One codebase, six rules, models of one supplier. The intervals are over six rules.
- The places of P1 and P5 were given by hand. The text said "a scan found" for all rules.
- The warning text invites repair ("stays only until it is repaired"). A different text can give less repair and
  a different violation rate.
- The Sonnet part has 3 runs for each cell, and one run has no measure.
- No `repair` arm. The consistent sites of Study A (17%) are the evidence for repaired code.

## Files

| File | Contents |
|---|---|
| `trials/studyC/PREREGISTRATION.md`, `spec.json` | Pre-registration and specification |
| `trials/studyC/rules/<rule>/` | Places, mark patch and warning text of each rule |
| `trials/studyC/build_material.py`, `repair_check.py` | Tools for the material and for the repair analysis |
| `trials/studyC/results/<model>/results-*.json` | One row for each run |
| `trials/studyC/results/<model>/analysis-prereg.*` | Output of [studyc_eval.py](../harness/studyc_eval.py) |
| `trials/studyC/results/<model>/repair.json` | Repair and comment analysis for each run |
| `trials/studyC/results/<model>/runlog.json`, `tool-calls.jsonl` | Transcript mapping and tool calls |
