# 14. Study D results: a static check on the changed lines finds one violation in four

Date: 2026-11-17. Protocol: [trials/studyD/PROTOCOL.md](../trials/studyD/PROTOCOL.md) (committed before any check existed).
Data: [trials/studyD](../trials/studyD/). Study D uses no new coding-agent runs. It examines the 444 runs of
Study A and Study B, of which 156 are violations.

## Summary

- **H5 is refuted.** General static checks, written from the rule texts only, found 41 of 156 violations (26.3%)
  when they examined the changed lines. The limit in the protocol was 30%. The false-alarm rate was 12.2%.
- **The result is very different for each rule.** One rule had 100% recall. One rule had 0%.
- **The largest cause of a miss is old code.** In 61 violations (39%), the changed lines contain no forbidden form.
  The violation comes from old code in the same file, which the change uses again or copies in a form that the
  check cannot prove.
- **When the checks examine the complete touched files, they find 102 of 156 violations (65.4%).** But then they
  also report the old violations, so they cannot say if the change is good.
- **The same checks find the wrong precedent before the change.** For four of the six rules, they report the old
  violation in the files of each run at a contradicting site.
- **54 violations (35%) have no static form.** For these, only a test found the violation.

## Method

1. A fresh agent (Claude Opus) wrote one static check for each of the six rules. It got the rule texts of the
   `prose` arm of Study B and a clean copy of the codebase. It did not get tickets, graders, rule tests, runs or results.
2. A check reads files only. It reports a finding only for a line that the change added or modified, in a non-test file.
3. The checks were evaluated one time, as delivered, on the change of each run. Each run was examined with the
   check for its own rule.
4. All six checks have the class `pattern` (text and syntax tree). The author made no `import` check and gave
   up on no rule. No check stopped with an error.

## Result as delivered (the pre-specified analysis)

| Rule | Rule type | Violations found (recall) | Runs without violation that got a finding |
|---|---|---|---|
| N1 webhooks through `call_event` | pattern | 23 / 23 (100%) | 2 / 46 (4.3%) |
| N3 `pk`, not `id` | pattern | 3 / 23 (13.0%) | 0 / 46 (0%) |
| P3 no `settings.SITE_ID` | pattern | 1 / 23 (4.3%) | 0 / 56 (0%) |
| N2 thumbnail rounding default | behaviour | 3 / 37 (8.1%) | 13 / 42 (31.0%) |
| P1 gift card stays restricted | behaviour | 0 / 30 (0%) | 0 / 49 (0%) |
| P5 race-safe gift card balance | behaviour | 11 / 20 (55.0%) | 20 / 49 (40.8%) |
| **All rules** | | **41 / 156 (26.3%)** | **35 / 288 (12.2%)** |

- Recall is almost the same for each study and model (21% to 30%).
- With only the runs that did their task: N1 23 of 23, N3 2 of 22, P3 1 of 22, N2 0 of 3, P1 0 of 23, P5 1 of 1.

## Why the checks missed violations

| Cause | Rules | Violations | Share of 156 |
|---|---|---|---|
| Found on the changed lines | N1 23, P5 11, N2 3, N3 3, P3 1 | 41 | 26% |
| Not found on the changed lines, found when the complete touched files are examined | P3 22, N3 20, N2 19 | 61 | 39% |
| Not found in the two modes | P1 30, N2 15, P5 9 | 54 | 35% |

The second row has two mechanisms. I read samples of each.

- **The change uses an old violation again (P3).** The old code has the line
  `site_settings = Site.objects.get(pk=settings.SITE_ID).settings`. The violating runs did not write `SITE_ID`.
  They used the variable `site_settings` from that old line in their new code. No changed line contains the
  forbidden form. All 23 violating runs kept the old line. All 26 runs without a violation at these sites removed it.
- **The change copies the form, but the check cannot prove it (N3).** The violating runs wrote
  `channel.id for channel in channels`. The check reports `.id` only when it can prove that the variable is a
  Django model object. Here the variable has no type annotation. A check that reports each `.id` would find these
  lines, with more false alarms.

The third row is the behaviour rules. "The card stays restricted after the customer is deleted" (P1) has no
code form that a general check can look for. The author's P1 check found nothing in 79 runs.

## The false alarms

35 runs without a violation got a finding. I read samples of each group. They were not all read.

| Rule | Runs | What the samples show |
|---|---|---|
| P5 | 20 | An error of the check. The code locks the rows through a project helper (`gift_card_qs_select_for_update`), and the check does not recognise the helper as a lock. (2 samples read) |
| N2 | 13 | The new field passes `NEAREST` directly to a helper. The hidden grader accepts these runs. I did not decide if the check or the grader is correct. (1 sample read) |
| N1 | 2 | The code is `transaction.on_commit(lambda: manager.category_updated(instance))`. This breaks the text of the rule ("always use `call_event`"), but it passes the hidden test, which examines the time of the event. The check is more strict than the grader. (2 samples read) |

## Not pre-specified: the checks on the complete touched files

In this mode, all lines of each changed file count as changed.

| Rule | Violations found | Runs without violation that got a finding |
|---|---|---|
| N1 | 23 / 23 | 26 / 46 |
| N3 | 23 / 23 | 27 / 46 |
| P3 | 23 / 23 | 0 / 56 |
| N2 | 22 / 37 | 27 / 42 |
| P1 | 0 / 30 | 0 / 49 |
| P5 | 11 / 20 | 20 / 49 |
| All rules | 102 / 156 (65.4%) | 100 / 288 (34.7%) |

A finding in a run without a violation is not an error of the check in this mode (P5 excepted). It is an old
violation in a file that the change touched. This is the wrong precedent of Study A:

- For N1, N2 and N3, each run without a violation at a contradicting site has a finding in its touched files
  (26 of 26, 27 of 27, 27 of 27). No such run at a consistent, control or none site has one.
- For P3, the runs without a violation have no finding, because they removed the old line.
- For P1 and P5, the checks do not see the wrong precedent.

So a static check can show where the risk is before the change, for four of the six rules. It cannot say, after
the change, if the change is good, because the old violation stays in the file.

## The cheapest detector for each violation

| Detector | Violations that it finds | Evidence |
|---|---|---|
| General static check on the changed lines | 41 of 156 (26%) | This study |
| The same check on the complete touched files | 61 more (39%), together with the old violations | This study, not pre-specified |
| The existing tests of the project | Almost none: 83% violations with the tests in the loop, 87% with nothing | Study B, arm `gen` |
| A test written for the rule and the ticket | All: 0 violations in 87 runs with Haiku and 18 with Sonnet | Study B, arms with a rule test |

## Tool improvements

The study gives five improvements for a tool that checks changes of agents, for example `ucn`. The share shows
how many of the 156 violations each one addresses.

1. **A precedent scan before the change (addresses the cause of 90 violations: the contradicting sites of four of
   six rules).** The tool runs the rule checks on the files that the task will touch, and reports old violations.
   The report can go to the agent ("this file contains code that breaks rule X at line N; do not copy it") or to
   the team (a list of places to repair). Study D shows that the scan is possible. It does not show that the
   report changes the behaviour of the agent. That is an experiment (see "Decision for Study C").
2. **A check that follows data from old violations into new code (22 violations, P3).** A changed line that uses
   a value from an old violating line must count as a finding. A check of the changed lines only does not see this.
3. **A ratchet for touched files (61 violations).** The rule is: a change must not leave a violation in a function
   that it touches. Then the agent must repair the precedent together with its change. The runs without a
   violation did this for P3 without an instruction.
4. **A project profile for the checks (20 false alarms, P5).** The check must know the helpers of the project that
   implement a rule, such as the lock helper. A general author cannot know them all. The tool needs a place to
   declare them.
5. **A rule test for behaviour rules (54 violations).** No static check found the violations of P1, and it found
   few of N2 and P5. For such a rule the tool cannot supply a check. It can demand that a rule has an executable
   test, and it can show which rules have none.

A less important improvement: a strict mode for forms that the check cannot prove (20 violations, N3). It reports
each `.id` on a changed line and accepts more false alarms.

## Decision for Study C

The plan had Study C as a cost study (check cost against the number of rules). Study B made it unnecessary:
the rule test cost no more tokens than no check. Two replacements were possible.

- **C1: a general check in the loop, in place of the ticket-specific rule test.** Study D predicts the result:
  the agent gets a useful signal for N1 only, and wrong alarms for P5. The experiment would mostly confirm Study D.
- **C2: change the precedent, not the check.** Study D shows that the wrong precedent is in the touched files, and
  that a tool can find it for four of six rules. Study A showed that the precedent is the cause. The cheapest
  measures are at the precedent: repair it, mark it in the code, or tell the agent about it.

**The decision is C2.** Proposed arms at the six contradicting sites, to be pre-registered before any run:

| Arm | What changes |
|---|---|
| `none` | Nothing (new baseline) |
| `mark` | A short comment at the old violation in the code: it does not follow the rule, do not copy it |
| `warn` | A paragraph in the ticket from the precedent scan: the place of the old violation and the rule text |
| `repair` | The old violation is repaired in the base before the agent starts |

The comparison with the `prose` arm of Study B (20%) shows if the place of the information is important: the same
rule, given at the wrong code or given in the ticket.

## Limits

- Six rules and one codebase. One author wrote the checks, one time. A different author can write better or worse checks.
- The author is a model of the same supplier as the coding agents.
- The hidden grader of a run examines one rule. The checks also gave findings for other rules (N3 on 43 runs of
  N2 and P5). These are not confirmed and not counted.
- The false alarms were read as samples, not all.
- The whole-file analysis and the causes of the misses were made after the results were known.
- The protocol named a second, corrected version of the checks as an upper limit. It was not made.

## Files

| File | Contents |
|---|---|
| `trials/studyD/PROTOCOL.md` | The protocol, committed before the checks existed |
| `trials/studyD/briefs/detector-author.md`, `rules/` | What the author of the checks got |
| `trials/studyD/checks/` | The six checks as delivered |
| `trials/studyD/extract_changes.py`, `evaluate.py` | Tools: changed lines of each run, evaluation |
| `trials/studyD/results/analysis-as-delivered.md`, `findings-as-delivered.json` | The pre-specified analysis and the findings of each run |
| `trials/studyD/results/analysis-whole-files.md`, `findings-whole-files.json` | The analysis on complete touched files |
