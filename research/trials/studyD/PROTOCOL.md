# Study D protocol: which cheap check finds the rule violations?

Date: 2026-11-17. Written and committed before the detector author starts and before any check is evaluated.
Study D uses no new coding-agent runs. It is a descriptive study of the 444 runs of Study A and Study B.

## Question

Hypothesis H5 of the plan ([11-next-phase.md](../../docs/11-next-phase.md)): a few cheap local checks find a large
share of the violations. H5 is refuted if fewer than 30% of the violations are found by an import check or a
pattern check.

Study B showed that a test written for the rule prevents the violation. That test was written with knowledge of the
ticket. Study D asks if a **general** check, written from the rule text only, finds the same violations.

## Data

- All runs of Study A (`results-prereg.json`, Haiku and Sonnet, 210 runs) and Study B (`results-all.json`, Haiku
  and Sonnet, 234 runs). The first attempts that are not valid are not used.
- A run is a violation by the definition of the studies (the hidden grader). 156 runs are violations.
- For each run, the change is the difference between the workspace and its base commit: changed files and the
  line numbers of added lines. Old code is not part of the change.

## Detectors

1. **General static checks (the main measure).** One check for each of the six rules.
   - The author is a fresh agent. It gets the six rule texts (the same text as the `prose` arm of Study B) and a
     clean copy of the codebase. It does not get the tickets, the graders, the rule tests of Study B, the runs or
     any result.
   - A check is static: it reads files, it does not run the project. It examines only added lines of non-test files.
   - The author gives each check a class: `import` (module dependencies), `pattern` (text or syntax tree),
     or `none` (the author decides that no static check of acceptable precision is possible).
   - The checks are evaluated one time, as delivered. There is no correction after the results are known.
     A check that stops with an error counts as "nothing found" for that run, and the error is reported.
2. **Existing project tests.** From Study B, arm `gen`: a violation is "found" if the run had a failed test invocation
   that the agent corrected. This is reported from the Study B data, not measured again.
3. **Ticket-specific rule test.** From Study B, arm `rule`. Reported from the Study B data.

## Measures

For each rule, and for all rules together:

- **Recall:** the share of violating runs in which the check for the rule of the run reports one or more findings.
- **False alarms:** the share of runs without a violation in which the check for the rule of the run reports a finding.
- The two measures for each site type (consistent, control, none, contradicting) and for each study.
- **Cross-rule alarms:** the findings of the five checks that are not for the rule of the run. These are reported
  as a count only, because the grader of a run examines one rule.

## Decision

- H5 is **refuted** if recall of the `import` and `pattern` checks, over all 156 violations, is below 30%.
- H5 is **supported** if recall is 30% or more **and** the false-alarm rate is 10% or less.
- Other results are **inconclusive**.
- A rule with class `none` counts as recall 0 for its violations.

## Taxonomy

Each violating run gets these labels:

- rule type: `pattern` (N1, N3, P3: the rule names a code form) or `behaviour` (N2, P1, P5: the rule is about
  what the code does). This assignment is made here, before the evaluation.
- site type, study, model and arm (from the data);
- the cheapest detector that found it, in this order: general static check, existing project test,
  ticket-specific test, none.

## After the evaluation (labelled as not pre-specified)

A second version of each check, corrected with knowledge of the misses and false alarms, can be reported as an
upper limit. It is not used for the H5 decision.

## Limits known before the start

- Six rules and one codebase. The author of the checks is a model of the same supplier as the coding agents.
- The grader of a run examines one rule. A finding for a different rule cannot be confirmed.
- A false alarm can be a real violation that the hidden grader did not see. A sample of false alarms is read.
