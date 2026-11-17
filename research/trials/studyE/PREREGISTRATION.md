# Study E pre-registration: the dose of the wrong precedent, and a model of a different supplier

Date: 2026-11-17. This file is committed and pushed before any run of Study E. The task variants of E1 and E2 are
pinned in a second commit after their proofs and before any E1 or E2 run (section "Pinned files").

Study E does the three options of [ideas-for-later-studies.md](../../docs/ideas-for-later-studies.md) in a smaller
form that reuses the tasks and graders of Studies A to C.

## E1: one wrong precedent

Question: does **one** wrong precedent, among precedents that follow the rule, make the violation more probable?
This is the mechanism of accumulation: if one bad change is sufficient to change the behaviour of the next agent,
violations spread change by change.

- The proposal had a chain of four live changes. That design has a low base rate (Study A: 17% at clean sites), so
  most chains stay clean and give little information. E1 tests the same mechanism with control: it makes the one
  wrong precedent by a seed.
- Tasks: the six consistent tasks of Study A. Variant `onewrong`: a seed changes exactly one place, the precedent
  that a developer of the ticket would most probably copy, so that it breaks the rule in the way of the naive patch.
  The place of each rule is in `tasks/<rule>-onewrong/meta.json`.
- Cells: `consistent` (the source task) and `onewrong`. The same prompt frame as Studies B and C, no documentation,
  no test command.
- Runs: Haiku 5 for each task and cell (60). Sonnet 3 for each task and cell (36).

## E2: the repaired precedent

Question: does a repaired precedent prevent the violation, and how does it compare with a mark or a warning?

- Tasks: the six contradicting tasks of Study A. Variant `repaired`: a seed repairs the old code at the places of
  Study C (`studyC/rules/<rule>/places.json`), with the same behaviour for callers.
- Cell: `repaired`. The comparison is the `none` arm of Study C (`contradicting`), done on the same day with the
  same frame and the same model versions. The `mark` and `warn` arms of Study C are descriptive comparisons.
- Runs: Haiku 5 for each task (30). Sonnet 3 for each task (18).

## E3: a model of a different supplier

Question: do the main results hold for a model that is not a Claude model?

- Model: `deepseek/deepseek-v4.1-flash-1017` through OpenRouter. Reason: a different supplier, a coding model, and a
  low price (the available credit is $10). It is not chosen as an equal of any Claude model.
- Agent loop: [openrouter_agent.py](../../harness/openrouter_agent.py), with four tools (read_file, write_file,
  edit_file, bash), a maximum of 80 turns and 40 minutes. This loop is not the Claude Code loop. A difference of E3
  from Studies A to C is thus an effect of the model and the loop together.
- Cells on the six contradicting tasks: `contradicting` (no information), `prose` (Study B text), `rule` (project
  tests and the rule test of Study B, with the same test command), `mark` and `warn` (Study C material).
  Cell on the six consistent tasks: `consistent`.
- Runs: 3 for each task and cell: 108. All with the same prompt frame as Studies B and C.
- One pilot run (`N3-contradicting-none-1`) was made before this pre-registration to test the loop. Its result was
  not graded. It is moved out of the study, the workspace is reset, and the run is done again in the study.
- Cost limit: $8. If the limit stops the runs, the missing runs are reported.

## Hypotheses and decisions

The measure is the violation rate of the hidden grader, as in Studies A to C. The interval is a 95% cluster
bootstrap over the six rules (10,000 samples, fixed seed). The p-value is a permutation test within rules.
Analysis script: [studye_eval.py](../../harness/studye_eval.py). Each model is analysed separately.

| # | Study | Contrast | Decision |
|---|---|---|---|
| H9 | E1 | `onewrong` − `consistent` | SUPPORTED if the lower bound is above 0 |
| H10 | E2 | `repaired` − `contradicting` (Study C `none`) | EFFECTIVE if the upper bound is below 0 |
| H11a | E3 | `contradicting` − `consistent` | SUPPORTED if the lower bound is above 0 (the Study A result) |
| H11b | E3 | `prose`, `rule`, `mark`, `warn`, each − `contradicting` | EFFECTIVE if the upper bound is below 0 (Studies B and C) |
| H11c | E3 | `rule` − `prose` | descriptive (Study B: the rule test is the strongest measure) |

- A comparison with both rates at 10% or less, or both at 90% or more, is INCONCLUSIVE.
- H9 and H10 are decided for Haiku. The Sonnet results get the same decisions as a replication.
- Descriptive: `repaired` against Study C `mark` and `warn`; each contrast with only the runs with task success;
  results for each rule.

## Exclusions and errors

As in Studies B and C:

- A run that reads experiment material outside its workspace is excluded. Results are reported with and without it.
- A Claude run whose transcript does not have the exact prompt is done again one time.
- A run that stops because of a usage limit, a credit limit or a tool failure before it changes code is done again.
- A run for which the grader cannot run is an error. If the code of the agent stops the grader (for example, the
  project does not load), the run counts as a task failure with an unknown violation, and it is reported.
- E3: a run that stops at the turn or time limit is graded as it is.

## Deviations from the proposal

- E1 uses one seeded wrong precedent in place of a live chain of four changes (reason above).
- E2 uses Study C `none` as the comparison, not a concurrent arm.
- E3 uses a cheap model because of the credit, and a new agent loop.

## Pinned files

SHA-256 of the files at the time of this commit (line endings as committed):

| File | SHA-256 |
|---|---|
| `research/harness/openrouter_agent.py` | `f19b657dda3605d47f37acd8e6bbdd1b62c49de13cd30957fee186fb99263da7` |
| `research/harness/openrouter_batch.py` | `c657098b38daea49f418e5ec0f15c0d1248d088685a8bd54c7634e6fa1f2dd18` |
| `research/harness/studye_eval.py` | `606b63394fba9c5c3318e13e2a4dbca62bf58145b1d59393e2f069c6c232d797` |
| `research/trials/studyE/briefs/author.md` | `e394388c087405097c54131495f74aad1273658708a27532f29613dafe808981` |
| `research/trials/studyE/spec-e3-contradicting.json` | `472d6c364f2b5c8d87c9ab3fedc41d9aa710918ab60682cd7cf0bdaa23527315` |
| `research/trials/studyE/spec-e3-consistent.json` | `cbf931ebe4f55fb66fdc7b64976d4b7dca2141edcbeb3ea313666ef9333ed5eb` |
| `research/harness/recon.py` | `2a48edbfd4a63c844be3fcc47765a59d8eee2ca0a463c709f84b75a9201fc677` |

The E1 and E2 task variants (`tasks/`) are pinned in the next commit, before any E1 or E2 run.
