# Study B: pre-registration

Pinned on 2026-11-15, before any Study B run. Plan: [docs/11-next-phase.md](../../docs/11-next-phase.md).
Study A results: [docs/12-study-a-results.md](../../docs/12-study-a-results.md).

## Question

Study A showed that an agent breaks a rule in 87% to 97% of runs when the code near the change breaks that rule.
Study B asks: **what is the cheapest context or check that prevents the violation at such a site?**

## Design

- **Repository:** saleor at `1d707dc`. The agent gets no `AGENTS.md`, no `CLAUDE.md` and no `docs/adr`.
- **Tasks:** the six contradicting tasks of Study A, one for each rule (N1, N2, N3, P1, P3, P5). The tickets, the seed
  patches and the hidden graders are the same files as in Study A, with the same hashes.
- **Arms:**

  | Arm | Guidance | Check that the agent can run |
  |---|---|---|
  | `none` | none | none |
  | `prose` | the documentation text that states the rule | none |
  | `gen` | none | the tests that the project has |
  | `rule` | none | the project tests and one visible test for the rule |
  | `prule` | the documentation text | the project tests and the visible rule test |
  | `urule` | a UCN context that contains the rule | the project tests and the visible rule test |

- **Runs:** 5 for each task and arm with Claude Haiku. This gives 180 runs (primary).
- **Replication:** Claude Sonnet, arms `prose`, `gen` and `rule`, 3 runs for each task. This gives 54 runs.
- **Workspace:** one squashed commit, a folder name that does not show the task or the arm, as in Study A.
- **Prompts:** they do not contain the arm name, the rule id or the word "experiment".
- **Specification:** [spec.json](spec.json).

### Guidance

- **Prose:** [rules/R/prose.md](rules/) is the text of the saleor documentation that states the rule, word for word
  (46 to 216 words). The prompt contains it after one neutral line. The source comment in the first line is not in the prompt.
- **UCN:** the file `context.ucn` in the workspace. It is the projection of [model.ucn](model.ucn) for the ticket at a
  budget of 2,500. The rule of the task is a forced seed of the projection, so the context always contains the rule.

### Checks

- An agent with a check runs tests with one command. Each run starts a new database container, and takes 30 to 60 seconds.
- Each invocation is recorded outside the workspace (time, arguments, exit code, counts).
- **Visible rule test:** [rules/R/rule_test.py](rules/). A separate author wrote it from the ticket and the rule.
  The author did not open the hidden grader. The test is in the workspace as part of the base commit.
- Proof for each visible rule test, made by the author and made again by an independent agent through the real
  command: it passes on the reference solution, and it fails on the naive solution in a `test_rule_` function.
- Arms without a check keep the Study A instruction: do not run tests.

## Measures

- **Violation** (primary): as in Study A. A hidden rule test fails, or the validator has a new finding, or the agent
  changed a grader file. The validator comparison ignores line numbers (the correction from Study A).
- **Task success:** all hidden behaviour tests pass.
- **Cost:** tokens and tool calls for each run.
- **Check use:** the number of invocations, the number of failed invocations, and the number of rule-test
  invocations before the first one that passed.
- **Rule test changed:** true if the agent changed or deleted the visible rule test.

## Hypotheses and decision rules

All differences are differences of violation rates in percentage points. The interval is a 95% cluster bootstrap
over the six rules (10,000 samples, fixed seed), as in Study A.

| # | Role | Hypothesis | Decision rule |
|---|---|---|---|
| H2 | primary | The existing project tests in the loop (`gen`) prevent fewer violations than written guidance (`prose`) | **Refuted** if the rate of `gen` is 15 points or more below the rate of `prose`. **Supported** if the lower bound of (`gen` − `prose`) is above 0. Otherwise **inconclusive** |
| H2b | primary | Each arm decreases violations against `none` | For each arm: **effective** if the upper bound of (arm − `none`) is below 0 |
| H3 | secondary | With the rule test in the loop, guidance decreases cost | **Refuted** if the median tokens and the median failed check runs of `prule` are not lower than those of `rule` |
| UCN | secondary | The UCN context is not better than prose when the rule test is in the loop | Reported as the difference `urule` − `prule` for violations, tokens and failed check runs. No threshold |

- A ceiling or a floor (the two rates of a comparison are both 10% or less, or both 90% or more) is **inconclusive**.
- The `none` arm repeats the Study A contradicting cells. If its rate is below 60%, the baseline did not
  reproduce, and all comparisons against `none` are inconclusive.

## Analysis reported with it

- The violation rate and the task success for each arm and for each rule and arm.
- A permutation test for each difference (labels shuffled within each rule).
- A leave-one-rule-out table for the H2 difference.
- A mixed-effects logistic regression, violation ~ arm + (1 | rule). It is descriptive.
- Sensitivity 1: only the runs with task success.
- Sensitivity 2: without the rules N2 and P1 (see "Known limits").
- Sensitivity 3: runs in which the agent changed the visible rule test are counted as violations.
- For the check arms: the share of runs that ended with a passing visible rule test, and the violation rate of those runs.
  This shows how much of a violation the visible test can see.
- Cost for each arm: median tokens, tool calls and check invocations.
- The Sonnet replication is reported separately, with the same tables for its three arms.

The analysis script is committed before the first result is graded.

## Contamination and exclusions

- The mapping from transcript to run uses the exact prompt text.
- A run that reads experiment material outside its workspace is excluded and reported. This includes the run index,
  the harness and this repository. The test command is the only permitted use of a path outside the workspace.
- A run that fails to start, or that stops because of a usage limit, is started again one time with the same prompt
  in a new workspace. The first attempt is reported.

## Deviations from the plan

| Plan ([docs/11](../../docs/11-next-phase.md)) | What is done | Why |
|---|---|---|
| Sites: the none and the contradicting cells of Study A | The contradicting cells only | Study A found almost no violations at sites with no precedent. An arm cannot decrease a rate that is near zero |
| Generic check: the project tests and the validator | The project tests only | A project that does not use UCN has no validator, and the validator output would show the rule to the agent |
| Prose: the relevant excerpt, size-matched | The full rule statement, 327 to 1,321 characters. The UCN contexts have 2,099 to 3,405 characters | The rule statements are short. More text to get the same size would be noise |
| UCN context: the usual projection | The rule of the task is a forced seed | For N2 the usual projection did not select the rule. The prose arm gets the correct text always, so the UCN arm must get the correct rule always |
| Model: the saleor model of phase 1 | A copy with two more rules (N1, N3) | The phase 1 model did not contain them |
| A non-Claude model on a subset | Not planned in this pre-registration | No test command path exists for an agent that is not Claude Code. Reported as a limit |

## Known limits, found before any run

1. **N2 and P1:** the visible rule test is almost the same as a hidden rule test, although the author did not see
   the hidden test. The rule is narrow, and two independent tests examine the same cases. For these rules, a passing
   visible test almost guarantees no violation. Sensitivity 2 removes them.
2. **N1:** the visible rule test shows part of the mechanism (`on_commit`). This is more than the rule text says.
3. **N3:** the visible rule test reads the source code of the new function, because `id` and `pk` give the same
   database query.
4. **Source references:** the UCN context refers to `docs/adr` files that are not in the workspace.
5. **Test time:** a check run takes 30 to 60 seconds, and many agents run at the same time. A slow machine can
   change how many times an agent runs the tests.
6. **Study A limits stay:** one repository, six rules, low task success for N2 and P5, agents from one supplier.

## Hashes (SHA-256)

Line endings are LF (see `.gitattributes`). The tasks, the seed patches and the hidden graders have the hashes of the
[Study A pre-registration](../studyA/PREREGISTRATION.md).

| Path | SHA-256 |
|---|---|
| research/trials/studyB/rules/N1/meta.json | cbb8987255d974a5b6c24aa4548fbdf66765d24a7ebd21a7ad82f0f6a0a0bbab |
| research/trials/studyB/rules/N1/prose.md | 8e37cccde06bbbaafabe6a6b2e81f8350ebde17eaec9d51fdfb328f296f1b2f3 |
| research/trials/studyB/rules/N1/rule_test.py | fb7677d8d519b81221be338899d877fcd38bf6a8567bafddc1003ed6e4e33049 |
| research/trials/studyB/rules/N2/meta.json | 2df7465f818f6b978a09daec6fc7bf3f1d12e040dde6174b255509fdc0dfc3e1 |
| research/trials/studyB/rules/N2/prose.md | 5bec05681c05f32886b6c4d3e76f2401e68dde48bd573cdf9e298b151b5785cf |
| research/trials/studyB/rules/N2/rule_test.py | d409772404238656533e93c3fd4269a36005ab93145c1d016d8011d3f57235ed |
| research/trials/studyB/rules/N3/meta.json | e93ceec3e2bb7caf9d61e5e83901b6bce78c6129f4194a5956401d6e30e3026a |
| research/trials/studyB/rules/N3/prose.md | 04d002057c0a610ebc37bc898db94f2f634b9cd230103c4d56633100e5c82564 |
| research/trials/studyB/rules/N3/rule_test.py | 8d9833287488ee375a8c503b88f27d45966c7f0df3e4c95fc8ada0440fb22d09 |
| research/trials/studyB/rules/P1/meta.json | 6a940e530dd2323cf36a611a4ad6df495aab9b6026c942d7ca6f03fb5fb6cf97 |
| research/trials/studyB/rules/P1/prose.md | 948c54c3ea19c01ed5f718b981192a23e4ae9e45c6aa85481f569905ee06e90e |
| research/trials/studyB/rules/P1/rule_test.py | 5c856337ca5dda48d2c6befc82a9c479b95762a94e9fd68a546b9f3c7a553f4f |
| research/trials/studyB/rules/P3/meta.json | 0fa6111abc23ab5b733764002b44623bf14800eff1f9d327457bd398e91ff646 |
| research/trials/studyB/rules/P3/prose.md | f06157f4302e49269c1c9a14fa3d540bd44cd5c885feda6197dd4e0b6e45f921 |
| research/trials/studyB/rules/P3/rule_test.py | 2adc02af878f422c03af67bcf8f7dfab8d9980218d609be45e41a752e4ffd977 |
| research/trials/studyB/rules/P5/meta.json | 54f9ab8eee6ef040bd2b5bae06b28961dc926aba95a9150cb0922140f643ccf9 |
| research/trials/studyB/rules/P5/prose.md | e471576477053af3c59aa997fdf5e66ed620712619dce793ea593518eea0027f |
| research/trials/studyB/rules/P5/rule_test.py | c40bfafbff1c90fb4c4baf3643770bb70f1ca3a2c79ddaa609ab2d0f40f999c0 |

Harness at the time of pinning:

| Path | SHA-256 |
|---|---|
| research/harness/agent_tests.py | 83b34703bff917f5911458ba7720fb3c2773ac75ab55c896a32cc53f55983fc1 |
| research/harness/recon.py | 55331c43799987464600269e01237090b9a7b36ae1b0ac7f8cc508a1beb0cd0c |
| research/harness/ucn_dep.py | 4e593ee2c78a6ca7b7aafe6f6e1650b4bf5ead31f0a1feb467df699990c11d3b |

