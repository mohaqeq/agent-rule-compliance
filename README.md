# Agent rule compliance

Experiments on one question: **when does an AI coding agent break the rules of a project, and what prevents it at a low cost?**

A project has rules that its tests do not always examine: architecture decisions, security rules, conventions.
This repository measures how often coding agents break such rules in a real codebase, and which context or check
prevents the violation.

## Results until now

**Study A (complete, 210 runs, two models).** The code near a change controls the behaviour of the agent.

| Code near the change | Violation rate, Haiku | Violation rate, Sonnet |
|---|---|---|
| Follows the rule (consistent) | 17% | 17% |
| No precedent (none) | 23% | 13% |
| Breaks the rule (contradicting) | 87% | 97% |

- When the near code breaks a rule, the agent breaks it again. The stronger model does this too.
- A missing precedent is not a risk by itself. The risk is a wrong precedent.
- A run that did its task correctly never broke a rule at a site without a wrong precedent (0 of 117 runs).

Full report: [research/docs/12-study-a-results.md](research/docs/12-study-a-results.md).
Limits: one repository (saleor), six rules, models from one supplier.

**Study B (primary part complete, 180 runs).** What prevents the violation at a site where the near code breaks the rule?

| What the agent gets | Violation rate |
|---|---|
| Nothing | 87% |
| The project tests to run | 83% |
| The documentation text of the rule | 20% |
| One test written for the rule (with or without guidance) | 0% |

- Existing tests do not help: they pass, and the violation stays.
- Text that states the rule helps much, but it is not sufficient.
- A test that fails when the rule is broken was sufficient in all runs.

Full report: [research/docs/13-study-b-results.md](research/docs/13-study-b-results.md). A replication with a stronger model is not done yet.

## Where this work comes from

This repository continues [unified-context-notation](https://github.com/mohaqeq/unified-context-notation). That
project tested a notation (UCN) that gives requirements and architecture to agents. Phase 1 showed that the notation
gave no benefit, and that agents copy the code near the change. This repository examines that second finding.

- The history of this repository starts from the tag
  [`phase1-and-study-a`](https://github.com/mohaqeq/unified-context-notation/tree/phase1-and-study-a) of that project.
- The `ucn` tool, its article and the phase 1 record stay in that project. This repository installs `ucn` as a dependency.
- Study A was pre-registered and pushed in that project before any run. The commit there is the proof of the date.

## Contents

| Path | Contents |
|---|---|
| [research/docs](research/docs/) | The phase 2 plan and the Study A results |
| [research/trials/studyA](research/trials/studyA/PREREGISTRATION.md) | Pre-registration, 21 tasks with graders, results, analysis output, tool-call logs |
| [research/trials/saleor](research/trials/saleor/NOTES.md) | The model of the saleor rules and the phase 1 saleor tasks |
| [research/trials/containers](research/trials/containers/README.md) | Container images for grading and statistics |
| [research/harness](research/harness/) | Tools that prepare workspaces, grade runs, prove graders and do the analysis |
| [tests](tests/) | Tests of the harness |

## Use

1. Install Python 3.10 or a later version, and Docker.
2. Install the dependency: `pip install .`
3. Run the tests: `python -m unittest discover -s tests`
4. To do the Study A analysis again:
   `python research/harness/studya_eval.py research/trials/studyA/results/haiku/results-prereg.json`

## Licence and citation

- **Code** (`research/harness`, `tests`): [MIT](LICENSE).
- **Research record, tasks and data:** [CC BY 4.0](LICENSE-docs.md). You can use them again with a reference to this repository.
- To cite the work, use the "Cite this repository" button on GitHub ([CITATION.cff](CITATION.cff)).
