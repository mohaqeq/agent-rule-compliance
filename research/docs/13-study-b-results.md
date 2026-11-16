# 13. Study B results: a test for the rule prevents the violation, the existing tests do not

Date: 2026-11-15 (Haiku), 2026-11-17 (Sonnet). Pre-registration: [trials/studyB/PREREGISTRATION.md](../trials/studyB/PREREGISTRATION.md).
Data: [trials/studyB/results](../trials/studyB/results/). This document reports the primary part (Claude Haiku, 180 runs) and the replication (Claude Sonnet, 54 runs).

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
- **The stronger model gave the same result.** Sonnet: project tests 83%, documentation text 22%, rule test 0%.

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

## Sonnet replication

Three arms (`prose`, `gen`, `rule`), 3 runs for each task and arm, Claude Sonnet: 54 runs. No run is excluded.
The replication has no `none` arm, so only H2 has a decision. The 36 runs of the check arms are second attempts
(see "Exclusions and incidents", item 6).

| Arm | Guidance | Check | Violations | Rate | Task success |
|---|---|---|---|---|---|
| `prose` | documentation text | none | 4 / 18 | 22.2% | 83.3% |
| `gen` | none | project tests | 15 / 18 | 83.3% | 83.3% |
| `rule` | none | project tests and rule test | 0 / 18 | 0.0% | 100.0% |

| Difference | Estimate | 95% cluster-bootstrap interval | Permutation p | Decision |
|---|---|---|---|---|
| `gen` − `prose` (H2) | +61.1 pp | +16.7 to +100.0 | 0.0004 | H2 **supported** |

| Rule | `prose` | `gen` | `rule` |
|---|---|---|---|
| N1 webhooks through `call_event` | 0/3 (3) | 3/3 (3) | 0/3 (3) |
| N2 thumbnail rounding default | 0/3 (3) | 3/3 (0) | 0/3 (3) |
| N3 `pk`, not `id` | 0/3 (3) | 3/3 (3) | 0/3 (3) |
| P1 gift card stays restricted | 3/3 (1) | 3/3 (3) | 0/3 (3) |
| P3 no `settings.SITE_ID` | 0/3 (3) | 3/3 (3) | 0/3 (3) |
| P5 race-safe gift card balance | 1/3 (2) | 0/3 (3) | 0/3 (3) |

- The rates are almost the same as the Haiku rates (`prose` 20.0%, `gen` 83.3%, `rule` 0.0%).
- The documentation text failed for P1 in all three runs. Haiku failed there in 3 of 5 runs. For this rule the
  near code is a stronger signal than the text, for the two models.
- All 18 `rule` runs ran the rule test and ended with a passing rule test. No agent changed the rule test.
- Leave one rule out: the H2 difference is +53 to +80 pp.
- Sensitivity 1 (only runs with task success): `prose` 6.7%, `gen` 80.0%, `rule` 0%. H2 supported (+73.3 pp, interval +33.3 to +100.0).
- Sensitivity 2 (without N2 and P1): `prose` 8.3%, `gen` 75.0%, `rule` 0%. The difference is +66.7 pp, but the
  interval is 0.0 to +100.0, so H2 is **inconclusive** in this analysis. Four rules with 3 runs give a wide interval.
- Sensitivity 3: no change.
- Cost, median for each run: `prose` 59,500 tokens and 17 tool calls; `gen` 58,200 and 18.5; `rule` 57,800 and 15.
  The agents ran the tests 1.7 times (`gen`) and 1.8 times (`rule`) in a run, as a mean.

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
6. **Sonnet: the test command ran on the wrong workspace, and 36 runs were done again.** This is a deviation from
   the pre-registration, which permits a second attempt only for a wrong prompt.
   - Cause: the harness made the workspace name from the run id only. The Haiku and Sonnet runs have the same run ids,
     so they had the same workspace names. The test command searched the Haiku runs first.
   - Effect: in the first Sonnet attempts of the `gen` and `rule` arms, each test run examined the completed Haiku
     code of the same run id, not the code of the Sonnet agent. The manipulation of these arms was not valid.
   - The 18 `prose` runs have no test command and are not affected. The Haiku runs are not affected, because the
     Haiku workspaces were the only ones at that time. The test command does not change a workspace.
   - How it was found: the Sonnet runs wrote no check log in their own folder.
   - Action: the 36 workspaces were restored with `git reset` and `git clean`, the test command was corrected and
     proved on a Sonnet workspace, and the 36 runs were started again with the same prompts.
   - The decision to repeat was made after the first attempts were graded. Their rates were `gen` 17 of 18 and
     `rule` 1 of 18. They are not used in any analysis. Their results and check log are in
     [first-attempts](../trials/studyB/results/sonnet/first-attempts/).
   - The harness now makes the workspace name from the runs folder and the run id, and the test command stops
     when one name is in two runs folders.
7. **Sonnet checks.** All 54 transcripts map to one run each, and all agents used `claude-sonnet-5-5`. No second
   attempt read the test wrapper file. Eight runs used a temporary folder of the agent session for test output.
   Two runs started the test command from the folder above the tools folder and read nothing there.

## Limits

- The Sonnet replication has 3 runs for each cell and no `none` arm. Its check arms are second attempts (incident 6).
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
| `results/sonnet/` | The same files for the Sonnet replication, and `first-attempts/` with the 36 runs that are not valid |
| `results/tools/` | Scripts for grading and for the transcript check |
