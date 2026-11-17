# 16. Study E status: stopped before the main runs

Date: 2026-11-17. Pre-registration: [trials/studyE/PREREGISTRATION.md](../trials/studyE/PREREGISTRATION.md).

The owner of the project stopped Study E on 2026-11-17, before the runs of E1 and E2. Study E can continue later
from the material in this repository. This document records what exists and the partial result of E3.

## What was planned

| Part | Question | State |
|---|---|---|
| E1 `onewrong` | Does one wrong precedent among correct ones make the violation more probable? | Task variants made; 5 of 6 proven. No run |
| E2 `repaired` | Does a repaired precedent prevent the violation? | Task variants made; 5 of 6 proven. No run |
| E3 | Do the results hold for a model of a different supplier? | 19 of 36 restricted runs done, graded. Inconclusive |

## Task variants (E1 and E2)

The variants are in [trials/studyE/tasks](../trials/studyE/tasks/). Each has a seed patch, the task and grader of its
source task, and (if proven) a `proof.json` from `prove.py`.

| Rule | `onewrong` (source: consistent task) | `repaired` (source: contradicting task) |
|---|---|---|
| N1 | proven | proven |
| N2 | proven | proven |
| N3 | not made | proven |
| P1 | proven | proven |
| P3 | proven | made, proof not finished |
| P5 | made, proof not finished | made, proof not finished |

The variants were not pinned with hashes, because no E1 or E2 run was made. A later study must review and pin them
before any run.

## E3: partial result

- Model: `nvidia/nemotron-3-ultra-550b-a55b:free` through OpenRouter, with the agent loop
  [openrouter_agent.py](../harness/openrouter_agent.py) (maximum 50 turns). The free models allow 1,000 requests
  each day. The runs stopped at that limit and then at the decision to stop the study.
- Before the change to a free model, 9 runs started with a paid model. They were stopped, not graded, and are not
  part of the study (see the pre-registration).
- Runs done: 19 (contradicting 5, mark 4, consistent 10). 18 of 19 ended at the turn limit, not with a final answer.

| Cell | Runs | Task success | Violations among runs with task success |
|---|---|---|---|
| contradicting | 5 | 2 | 2 of 2 |
| mark | 4 | 0 | none |
| consistent | 10 | 3 | 0 of 3 |

- For 5 runs the hidden grader could not run (the code of the agent stopped the test collection). They count as task
  failures with an unknown violation.
- A run without task success cannot show a violation in a reliable way: the rule tests also fail when the feature is
  missing. So only the runs with task success are shown.
- Three runs listed the folder that holds all workspaces. The names there are neutral hashes, and no run read
  another workspace.
- **Conclusion: inconclusive.** The direction (2 of 2 against 0 of 3) agrees with Study A, but five runs are no
  evidence. The free model did the task in 5 of 19 runs within 50 turns, so a valid E3 needs a stronger model, more
  turns, or more days of free requests.

## Cost

- Claude usage: the authoring of the variants and the orchestration.
- OpenRouter: $0.60 for the 9 stopped paid runs. This spend was not permitted, and the harness now refuses any model
  that is not free. The free runs cost $0.

## Files

| Path | Contents |
|---|---|
| `trials/studyE/PREREGISTRATION.md`, `spec-e3-*.json` | Pre-registration (with the change to a free model) and E3 specifications |
| `trials/studyE/briefs/author.md` | The brief for the authors of the variants |
| `trials/studyE/tasks/` | The variants of E1 and E2 |
| `trials/studyE/results/e3/` | Results, run records and tool calls of the 19 E3 runs |
| `harness/openrouter_agent.py`, `openrouter_batch.py` | The agent loop and the batch tool (free models only) |
| `harness/studye_eval.py` | The analysis script (not used, because E1 and E2 have no runs) |
