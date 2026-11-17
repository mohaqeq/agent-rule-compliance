# Research record

This folder contains the plan, the pre-registrations, the tasks, the tools and the results of phase 2.
The record of phase 1 (documents 01 to 10, the pilot and the first trials) is in the
[unified-context-notation](https://github.com/mohaqeq/unified-context-notation/tree/phase1-and-study-a/research) project.

## Documents

| # | Document | Contents |
|---|---|---|
| 11 | [11 Next phase](docs/11-next-phase.md) | The plan of phase 2: where agents break rules (the code around the change) and what prevents it at a low cost. A second model reviewed it |
| 12 | [Study A pre-registration](trials/studyA/PREREGISTRATION.md) | Pinned before any run: 6 rules, 21 tasks at consistent, none and contradicting sites, proven graders, blind precedent counts, two non-Claude grader reviews |
| 13 | [12 Study A results](docs/12-study-a-results.md) | 210 runs, two models: code that breaks a rule near the change causes violations in 87% (Haiku) and 97% (Sonnet) of runs, against 17% at consistent sites. A site with no precedent is not a risk |
| 14 | [Study B pre-registration](trials/studyB/PREREGISTRATION.md) | Pinned before any run: six arms of guidance and checks at the six contradicting sites, visible rule tests with proofs, decision rules, hashes |
| 15 | [13 Study B results](docs/13-study-b-results.md) | 180 Haiku runs and 54 Sonnet runs at the contradicting sites: project tests in the loop do not prevent violations (83% against 87%), the documentation text prevents most (20%), a test for the rule prevents all (0%). Sonnet gave the same rates (83%, 22%, 0%) |
| 16 | [Study D protocol](trials/studyD/PROTOCOL.md) | Written before any check existed: general static checks from the rule texts only, evaluated one time on the 444 runs |
| 17 | [14 Study D results](docs/14-study-d-results.md) | Static checks on the changed lines find 26% of the violations (H5 refuted). 39% come from old code in the touched files, 35% have no static form. Tool improvements, and the decision for Study C |
| 18 | [Study C pre-registration](trials/studyC/PREREGISTRATION.md) | Pushed before any run: a comment at the old wrong code, or a scan warning in the ticket, against no information |
| 19 | [15 Study C results](docs/15-study-c-results.md) | 144 runs: a comment at the precedent (Haiku 20%, Sonnet 18%) or a warning in the ticket (7%, 33%) prevents most violations (no information: 87%, 94%). The warning also made Haiku repair the old code |
| 20 | [Study E pre-registration](trials/studyE/PREREGISTRATION.md) | One wrong precedent, a repaired precedent, and a model of a different supplier |
| 21 | [16 Study E status](docs/16-study-e-status.md) | Stopped before the main runs. Task variants kept for later. E3 partial result (19 runs, free model): inconclusive |

## Data and tools

| Path | Contents |
|---|---|
| [trials/studyA](trials/studyA/PREREGISTRATION.md) | Pre-registration, 21 tasks with graders, site counts, grader reviews, results of 210 runs with analysis and tool-call logs |
| [trials/studyB](trials/studyB/PREREGISTRATION.md) | Pre-registration, specification, rule material (documentation text, visible rule test) for six rules, the UCN model |
| [trials/saleor](trials/saleor/NOTES.md) | Model of 12 ADRs of saleor, the phase 1 saleor tasks and their screening results |
| [trials/containers](trials/containers/README.md) | Container images |
| [harness](harness/) | `recon.py` (workspaces and grading), `prove.py` (grader proof), `studya_eval.py` (analysis), `studya_pin.py` (pinning), and smaller tools |

## Note about links

Some links in these documents go to the unified-context-notation project at the tag `phase1-and-study-a`.
Those files are part of the phase 1 record, and they are not copied here.
