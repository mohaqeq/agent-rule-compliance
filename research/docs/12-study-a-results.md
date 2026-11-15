# 12. Study A results: the code around a change causes rule violations

Date: 2026-11-15. Pre-registration: [trials/studyA/PREREGISTRATION.md](../trials/studyA/PREREGISTRATION.md).
Data: [trials/studyA/results](../trials/studyA/results/).

## Summary

Study A tested hypothesis H1 of the [phase 2 plan](11-next-phase.md): the code around a change controls rule
violations by an agent that has no documentation.

- **Contradicting sites:** H1 is supported. When the code near the change breaks a rule, the agent breaks the rule
  too. The violation rate was 87% (Haiku) and 97% (Sonnet). At consistent sites it was 17% for the two models.
- **Sites with no precedent:** H1 is refuted. The violation rate was not higher than at consistent sites.
- **Stronger model:** Sonnet did not resist the contradicting code better than Haiku.
- **Decision:** Study B follows, as the plan specifies.

## Method in short

- Repository: saleor at `1d707dc`. The agent got no `AGENTS.md`, no `CLAUDE.md` and no ADR folder.
- Rules: 6 (three from phase 1, three new).
- Tasks: 21. Each rule has a ticket at a consistent site, at a site with no precedent and at a contradicting site.
  Four rules also have a control ticket (a consistent site on a base with a neutral patch).
- Runs: 5 for each task and model. This gives 105 runs for Haiku (primary) and 105 runs for Sonnet (replication).
- The agents did not run tests. A hidden grader made the decision for each run.
- A run is a violation when a rule test fails, the validator finds a new rule finding, or the agent changes a grader file.

## Primary result

Violations and runs for each site condition (pre-registered analysis):

| Site condition | Haiku | Sonnet |
|---|---|---|
| consistent | 5 / 30 (16.7%) | 5 / 30 (16.7%) |
| control | 2 / 15 (13.3%) | 2 / 15 (13.3%) |
| none | 7 / 30 (23.3%) | 4 / 30 (13.3%) |
| contradicting | 26 / 30 (86.7%) | 29 / 30 (96.7%) |

Differences to the consistent condition, in percentage points (pp):

| Difference | Model | Estimate | 95% cluster-bootstrap interval | Permutation p | Odds ratio (95% interval) | H1 |
|---|---|---|---|---|---|---|
| contradicting - consistent | Haiku | +70.0 pp | +36.7 to +100.0 | 0.0001 | 35.2 (13.0 to 95.0) | supported |
| contradicting - consistent | Sonnet | +80.0 pp | +60.0 to +96.7 | 0.0001 | 95.2 (24.2 to 374.0) | supported |
| none - consistent | Haiku | +6.7 pp | 0.0 to +13.3 | 0.66 | 1.12 (0.45 to 2.79) | refuted |
| none - consistent | Sonnet | -3.3 pp | -13.3 to +6.7 | 1.00 | 0.52 (0.18 to 1.50) | refuted |
| control - consistent | Haiku | -3.3 pp | -16.0 to +16.7 | 1.00 | not fitted | no effect of the patch |
| control - consistent | Sonnet | -3.3 pp | -20.0 to +20.0 | 1.00 | not fitted | no effect of the patch |

The decision rule refutes H1 for a level when the lower bound of the interval is not above 0.

## Result for each rule

Each cell shows violations of 5 runs. The number in parentheses is the number of runs that also passed the behaviour tests.

**Haiku**

| Rule | consistent | control | none | contradicting |
|---|---|---|---|---|
| N1 webhooks through `call_event` | 0 (5) | | 0 (5) | 5 (5) |
| N2 thumbnail rounding default | 4 (1) | 2 (3) | 4 (0) | 4 (1) |
| N3 `pk`, not `id` | 0 (5) | | 1 (2) | 5 (5) |
| P1 gift card stays restricted | 0 (5) | 0 (4) | 0 (5) | 5 (3) |
| P3 no `settings.SITE_ID` | 0 (5) | 0 (5) | 0 (5) | 5 (5) |
| P5 race-safe gift card balance | 1 (4) | | 2 (3) | 2 (3) |

**Sonnet**

| Rule | consistent | control | none | contradicting |
|---|---|---|---|---|
| N1 webhooks through `call_event` | 0 (5) | | 0 (5) | 5 (5) |
| N2 thumbnail rounding default | 2 (3) | 2 (2) | 1 (4) | 4 (2) |
| N3 `pk`, not `id` | 0 (5) | | 0 (5) | 5 (5) |
| P1 gift card stays restricted | 1 (4) | 0 (3) | 0 (5) | 5 (4) |
| P3 no `settings.SITE_ID` | 0 (5) | 0 (5) | 0 (5) | 5 (4) |
| P5 race-safe gift card balance | 2 (2) | | 3 (2) | 5 (0) |

For four rules (N1, N3, P1, P3) the result is the same for the two models: 0 or 1 violation at consistent sites, 5 of 5
at contradicting sites. N2 and P5 are less clear. Their tasks are more difficult, and many runs failed the behaviour tests.

## Robustness

**Leave one rule out.** The contradicting difference stays large when any one rule is removed:
+64 to +84 pp (Haiku) and +76 to +88 pp (Sonnet).

**Natural and seeded sites.** Some contradicting sites exist in saleor (natural). For the others, a seed patch made the site.

| Contradicting cells | Haiku | Sonnet |
|---|---|---|
| natural | 10 / 10 | 10 / 10 |
| seeded | 16 / 20 | 19 / 20 |

The effect is not an artefact of the seed patches.

**Sensitivity 1: rule tests that no external reviewer flagged.** Two non-Claude models reviewed the graders. This
analysis ignores each rule test that one of them flagged.

| Model | consistent | none | contradicting | contradicting - consistent | none - consistent |
|---|---|---|---|---|---|
| Haiku | 3.3% | 6.7% | 73.3% | +70.0 pp (+36.7 to +100.0) | inconclusive (floor) |
| Sonnet | 10.0% | 0.0% | 80.0% | +70.0 pp (+40.0 to +93.3) | inconclusive (floor) |

**Sensitivity 2: only runs that passed the behaviour tests.**

| Model | consistent | control | none | contradicting | contradicting - consistent |
|---|---|---|---|---|---|
| Haiku | 0 / 25 | 0 / 12 | 0 / 20 | 18 / 22 (81.8%) | +81.8 pp (+44.4 to +100.0) |
| Sonnet | 0 / 24 | 0 / 10 | 0 / 26 | 19 / 20 (95.0%) | +95.0 pp (+80.0 to +100.0) |

This is the clearest view of the result. A run that did the task correctly never broke a rule at a consistent site,
a control site or a site with no precedent. At a contradicting site, almost all correct runs broke the rule.
All violations outside contradicting sites came from runs that also failed the task (rules N2, N3 and P5).

## Cost

Median for each run:

| Site condition | Haiku tokens | Haiku tool calls | Sonnet tokens | Sonnet tool calls |
|---|---|---|---|---|
| consistent | 88,000 | 43 | 57,900 | 14.5 |
| control | 82,100 | 53 | 57,100 | 17 |
| none | 84,700 | 38.5 | 54,600 | 13.5 |
| contradicting | 78,100 | 29 | 57,700 | 22 |

The token values come from the records of the runner agents, which are not fully reliable for single runs (see below).
The tool-call counts come from the transcripts.

## Corrections and incidents

1. **Validator line numbers.** The validator compares findings before and after the change. In files with seeded
   `SITE_ID` reads, an edit moved the line numbers, and old findings looked new. A correction compares findings
   without line numbers ([validator_fix.json](../trials/studyA/results/haiku/validator_fix.json)). The pre-registered
   table above does not use the correction. With the correction, Haiku does not change, and Sonnet contradicting
   changes from 29 / 30 to 28 / 30 (difference +76.7 pp, interval +60.0 to +93.3). The decisions do not change.
2. **Paths outside the workspace.** Five Haiku runs and two Sonnet runs used a path outside their workspace. In each
   case the agent wrote its own helper script in a temporary folder, or tried to read a path that does not exist.
   No run read material of the experiment, thus no run was excluded. Without these seven runs the results are
   almost the same (Haiku +71.9 pp, Sonnet +79.8 pp; files `analysis-no-outside.md`).
3. **Runner records.** One runner agent recorded the agent ids of two runs in the wrong order. The mapping from
   transcript to run thus uses the exact prompt text, not the runner records (`tools/check.py`). All 210 transcripts
   map to one run each. All agents used the specified model (`claude-haiku-5-5`, `claude-sonnet-5-5`).
4. **Rule N2.** The two external reviewers flagged a rule test of N2, and the task success for N2 is low. N2 has
   violations in all conditions, which decreases the measured difference. Without N2 the contradicting difference
   is +84 pp (Haiku) and +88 pp (Sonnet).
5. **Workspace names and ticket hints.** These were corrected before the first run. The pre-registration records them.

## Limits

- One repository (saleor), one language, 6 rules. The interval is over rules, and 6 rules is a small number.
- The two agent models are from one supplier. A subset with a model from a different supplier is not done.
- The agents did not run tests. An agent that runs tests can get different results for rules that existing tests examine.
- P5 has seeded sites for the consistent and the contradicting condition, and low task success. Its cells are weak evidence.
- The "none" condition is refuted as a cause, but its rates are low. The study cannot show small differences.

## What this means

- An agent with no documentation follows the code that is near the change. This agrees with phase 1.
- A rule that the near code follows is safe without documentation.
- A rule that the near code breaks is almost always broken again, also by the stronger model.
- A missing precedent is not a risk by itself. The risk is a wrong precedent.

Thus the useful question for Study B is narrow: what is the cheapest context that prevents a violation at a
contradicting site?

## Files

| File | Contents |
|---|---|
| `results/<model>/results-prereg.json` | One row for each run, as graded |
| `results/<model>/results-corrected.json` | With the validator correction |
| `results/<model>/results-unflagged.json` | Sensitivity 1 |
| `results/<model>/results-success-only.json` | Sensitivity 2 |
| `results/<model>/results-no-outside.json` | Without the runs that used a path outside the workspace |
| `results/<model>/analysis-*.md`, `analysis-*.json` | Output of [studya_eval.py](../harness/studya_eval.py) for each result file |
| `results/<model>/runlog.json` | Transcript mapping, model, tool-call count, outside paths for each run |
| `results/<model>/tool-calls.jsonl` | Tool name and target of each tool call of each run |
| `results/tools/` | Scripts for grading, checks, correction, tables and export |
