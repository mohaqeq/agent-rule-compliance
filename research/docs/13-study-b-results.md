# 13. Study B results: a test for the rule prevents the violation, the existing tests do not

Date: 2026-11-15. Pre-registration: [trials/studyB/PREREGISTRATION.md](../trials/studyB/PREREGISTRATION.md).
Data: [trials/studyB/results](../trials/studyB/results/). This document reports the primary part (Claude Haiku, 180 runs).
The Sonnet replication (54 runs) is not done yet.

## Summary

Study A showed that an agent repeats a rule violation when the code near the change contains it.
Study B tested what prevents this at the six contradicting sites.

- **The tests that the project has prevent almost nothing.** With the project tests in the loop, the violation rate
  was 83%. With no guidance and no check, it was 87%.
- **The documentation text of the rule prevents most violations.** The rate was 20%.
- **One test written for the rule prevents all violations.** The rate was 0% in the three arms with a rule test.
- **Hypothesis H2 is supported:** existing checks prevent fewer violations than written guidance.
- **The rule test costs no more than the other arms.** The median tokens of a run are almost the same in all arms.
- **The UCN context gave no measurable benefit** against the documentation text when the rule test was in the loop.

## Method in short

- Repository: saleor at `1d707dc`, without `AGENTS.md`, `CLAUDE.md` and `docs/adr`.
- Tasks: the six contradicting tasks of Study A, one for each rule.
- Six arms, 5 runs for each task and arm, Claude Haiku: 180 runs.
- Agents in the check arms ran tests with one command (30 to 60 seconds for each run of the command).
- The hidden graders are the graders of Study A. A run is a violation by the same definition.

## Primary result

Pre-registered analysis. Three runs are excluded (see "Exclusions").

| Arm | Guidance | Check | Violations | Rate | Task success |
|---|---|---|---|---|---|
| `none` | none | none | 26 / 30 | 86.7% | 80.0% |
| `prose` | documentation text | none | 6 / 30 | 20.0% | 86.7% |
| `gen` | none | project tests | 25 / 30 | 83.3% | 90.0% |
| `rule` | none | project tests and rule test | 0 / 30 | 0.0% | 100.0% |
| `prule` | documentation text | project tests and rule test | 0 / 28 | 0.0% | 100.0% |
| `urule` | UCN context | project tests and rule test | 0 / 29 | 0.0% | 100.0% |

The `none` arm repeats the Study A contradicting cells (87% there also), so the baseline reproduced.

| Difference | Estimate | 95% cluster-bootstrap interval | Permutation p | Decision |
|---|---|---|---|---|
| `gen` − `prose` (H2) | +63.3 pp | +26.7 to +93.3 | 0.0002 | H2 **supported** |
| `prose` − `none` | −66.7 pp | −96.7 to −30.0 | 0.0001 | effective |
| `gen` − `none` | −3.3 pp | −10.0 to 0.0 | 1.00 | **not effective** |
| `rule` − `none` | −86.7 pp | −100.0 to −60.0 | 0.0001 | effective |
| `prule` − `none` | −86.7 pp | −100.0 to −60.0 | 0.0001 | effective |
| `urule` − `none` | −86.7 pp | −100.0 to −60.0 | 0.0001 | effective |
| `urule` − `prule` (UCN) | 0.0 pp | 0.0 to 0.0 | 1.00 | no difference |

**H3 (guidance decreases cost when the rule test is in the loop): inconclusive.** The median tokens are almost equal
(`prule` 76,800, `rule` 76,300). The median of failed check runs is 0 for `prule` and 0.5 for `rule`.
One median is lower and the other is not, which the pre-registration defines as inconclusive.

## Result for each rule

Each cell shows violations of the runs in the cell. The number in parentheses is the number of runs that passed the behaviour tests.

| Rule | `none` | `prose` | `gen` | `rule` | `prule` | `urule` |
|---|---|---|---|---|---|---|
| N1 webhooks through `call_event` | 5/5 (5) | 0/5 (5) | 5/5 (5) | 0/5 (5) | 0/4 (4) | 0/5 (5) |
| N2 thumbnail rounding default | 5/5 (0) | 1/5 (4) | 5/5 (2) | 0/5 (5) | 0/5 (5) | 0/4 (4) |
| N3 `pk`, not `id` | 5/5 (5) | 0/5 (5) | 4/5 (5) | 0/5 (5) | 0/5 (5) | 0/5 (5) |
| P1 gift card stays restricted | 5/5 (5) | 3/5 (4) | 5/5 (5) | 0/5 (5) | 0/5 (5) | 0/5 (5) |
| P3 no `settings.SITE_ID` | 5/5 (5) | 0/5 (5) | 5/5 (5) | 0/5 (5) | 0/4 (4) | 0/5 (5) |
| P5 race-safe gift card balance | 1/5 (4) | 2/5 (3) | 1/5 (5) | 0/5 (5) | 0/5 (5) | 0/5 (5) |

- For five rules, the `gen` arm is as bad as the `none` arm. The agents ran the project tests, the tests passed, and
  the violation stayed.
- The documentation text failed most for P1 (3 of 5). The text of P1 says why the rule exists, but the near code
  shows a different pattern, and the agents followed the code in three runs.
- P5 was low in the `none` arm in this study (1 of 5; 2 of 5 in Study A). It gives little information about the arms.
- The rule test also increased the task success: N2 went from 0 of 5 to 5 of 5.

## Robustness

**Leave one rule out (H2 difference).** +56 to +80 pp. No one rule makes the result.

**Sensitivity 1: only runs with task success.** `none` 83.3%, `prose` 7.7%, `gen` 81.5%, rule-test arms 0%.
The H2 difference is +73.8 pp (interval +46.5 to +96.3).

**Sensitivity 2: without N2 and P1.** For these two rules the visible rule test is almost a copy of a hidden test.
Without them: `none` 80%, `prose` 10%, `gen` 75%, rule-test arms 0%. All decisions stay the same.

**Sensitivity 3: a changed rule test counts as a violation.** No agent changed or deleted the rule test. No change.

**With the three excluded runs included.** All three had no violation. The rates and decisions are the same
([analysis-all.md](../trials/studyB/results/haiku/analysis-all.md)).

## How the agents used the checks

| Arm | Mean test invocations | Mean failed invocations | Runs that ended with a passing rule test |
|---|---|---|---|
| `gen` | 2.5 | 0.5 | not applicable |
| `rule` | 2.9 | 0.9 | 29 of 30 |
| `prule` | 2.8 | 0.5 | 27 of 28 |
| `urule` | 3.0 | 0.8 | 29 of 29 |

- An agent ran the tests about three times in a run.
- Two runs never ran the rule test (one in `rule`, one in `prule`). They had no violation also.
- Agents with guidance had fewer failed test runs (0.5 against 0.9). The difference is small.

## Cost

Median for each run:

| Arm | Tokens | Tool calls | Test invocations |
|---|---|---|---|
| `none` | 82,300 | 36.5 | none |
| `prose` | 84,900 | 41.5 | none |
| `gen` | 77,900 | 33.5 | 2 |
| `rule` | 76,300 | 34 | 2 |
| `prule` | 76,800 | 33.5 | 2 |
| `urule` | 72,700 | 34 | 2 |

The arms with a check did not use more tokens than the arms without a check. An agent that can run a test reads
less code to make sure of its change. The token values come from the records of the runner agents, which are not
fully reliable for single runs. The tool-call counts come from the transcripts.

## Exclusions and incidents

1. **Three runs read the test wrapper file** (`run_tests.py`), which names the harness repository:
   `N1-contradicting-prule-4`, `N2-contradicting-urule-5`, `P3-contradicting-prule-2`. Each one looked at the file to
   find why a test run gave no output. The pre-registration excludes a run that reads experiment material outside its
   workspace. None of the three read the harness or the run index after that, and none had a violation.
2. **One run got a wrong prompt.** The runner agent gave `P5-contradicting-prule-1` the last paragraph of a different
   arm (no test command). That attempt had a violation and no task success. The run was started again one time with
   the exact prompt, as the pre-registration specifies, and the second attempt had no violation. The first attempt
   is in [first-attempts](../trials/studyB/results/haiku/first-attempts/). The check of exact prompts found this error.
   The workspace of the second attempt was restored with `git reset`, and it showed one file as changed because of
   line endings.
3. **Paths outside the workspace.** 33 runs used a path outside their workspace. Three are the runs of item 1.
   One run tried to read a file path that does not exist. One run wrote a temporary file in the folder above its
   workspace. One more run wrote a file list in the root folder of the drive. The other 28 runs used a temporary folder
   of the agent session for their own helper scripts and test output. The check classified these runs by path.
   The single commands of the 28 runs were not all read by a person or a second agent. The tool-call log is published.
4. **Grading error, corrected before any result was used.** The first grading start gave Docker a relative path,
   and the hidden grader did not run. Such a run looks like a run with no violation. Those results were deleted, and
   the grading script now reports each run for which the grader did not run. This is a weakness of the harness:
   a grader that does not run must be an error.
5. **All 180 transcripts map to one run each,** and all agents used `claude-haiku-5-5`.

## Limits

- The Sonnet replication is not done. Study A showed no benefit of the stronger model, but that is not evidence for Study B.
- One repository, six rules, one model supplier. The interval is over six rules.
- The rule test was written with knowledge of the ticket. It examines the rule for the new feature, not for all code.
  A project must write such a test before the change, or have a general check for the rule.
- For N2 and P1 the visible rule test is almost the same as a hidden test. Sensitivity 2 removes them.
- The N1 rule test shows part of the mechanism, and the N3 rule test reads the source code.
- The documentation text was the correct text for the rule each time. In a real project the agent must find it first.
- The UCN context contained the rule each time by a forced seed. The usual projection missed the rule for N2.

## What this means

- An agent that can run the tests is not safer by that fact. Existing tests almost never examine a rule at a new site,
  so they pass, and the agent takes the pass as confirmation.
- Text that states the rule is effective and cheap, but not sufficient. It failed in 20% of runs, and most where the
  near code was a strong example of the opposite.
- A test that fails when the rule is broken was sufficient in all runs, and it needed no explanation.
  The agents read the failure and corrected the code.
- With such a test, more guidance changed nothing that this study can measure. This is true for prose and for UCN.
- For a team, the practical order is: first make the rule executable, then document it.

## Files

| File | Contents |
|---|---|
| `results/haiku/results-prereg.json` | One row for each run, without the three excluded runs |
| `results/haiku/results-all.json` | All 180 runs |
| `results/haiku/analysis-*.md`, `analysis-*.json` | Output of [studyb_eval.py](../harness/studyb_eval.py) |
| `results/haiku/check-log.jsonl` | Each test invocation of each run |
| `results/haiku/runlog.json` | Transcript mapping, model, tool-call count, outside paths |
| `results/haiku/tool-calls.jsonl` | Tool name and target of each tool call |
| `results/haiku/first-attempts/` | The first attempt of the run that got a wrong prompt |
| `results/tools/` | Scripts for grading and for the transcript check |
