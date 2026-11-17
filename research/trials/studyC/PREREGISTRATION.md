# Study C pre-registration: does information about the wrong precedent prevent the violation?

Date: 2026-11-17. Committed and pushed before any run of Study C.

Study C replaces the Study C of the plan ([11-next-phase.md](../../docs/11-next-phase.md), a cost study). The reason
is in [14-study-d-results.md](../../docs/14-study-d-results.md), section "Decision for Study C".

## Background

- Study A: when the code near a change breaks a rule, the agent breaks the rule again (87% Haiku, 97% Sonnet).
- Study B: the rule text in the ticket decreases this to about 20%. A test for the rule decreases it to 0%.
- Study D: a static check finds the old violation in the touched files for four of six rules. It finds only 26%
  of the new violations on the changed lines.

A team can thus find the wrong precedent with a tool, at a low cost. Study C tests if this information, given to
the agent, prevents the violation.

## Design

- Repository, tasks and graders: the six contradicting tasks of Study A, as in Study B. Same base, same hidden
  graders, same prompt frame, no test command, no project documentation.
- Arms:

  | Arm | What the agent gets |
  |---|---|
  | `none` | The ticket only (new baseline, same as the `none` arm of Study B) |
  | `mark` | The ticket only. The code has a comment above each place of old code that breaks the rule |
  | `warn` | The ticket, with a paragraph that gives the same sentence and the list of the places |

- The comment of the `mark` arm (two lines above the statement or the function):

  ```
  # NOTE: the code below breaks a project rule and stays only until it is repaired. Do not copy it.
  # Rule: <one sentence>
  ```

- The paragraph of the `warn` arm: "A scan of the project found old code near this change that breaks a project
  rule. That code stays only until it is repaired. Do not copy it.", then `Rule: <the same sentence>`, then the list
  of places (`path:line (in function)`).
- The sentence of each rule is in [sentences.json](sentences.json). Each one is taken from the documentation text of
  the rule (the `prose` text of Study B), shortened to one sentence. `mark` and `warn` use the same sentence. They
  differ only in the place of the information: in the code, or in the ticket.
- The places ([rules/&lt;rule&gt;/places.json](rules/)) are made by [build_material.py](build_material.py):
  - N1, N2, N3, P3: the findings of the Study D static check on the complete non-test Python files that the naive
    solution of the task modifies. One place for each function with a finding (N1: 12 places, N2: 2, N3: 2, P3: 2).
  - P1, P5: the check finds nothing there. Three places for each rule are given by hand
    ([hand_places.json](hand_places.json)): the old code that the naive solution copies. The text for the agent is
    the same ("a scan found").
- The comments are part of the base commit of the workspace. They do not change behaviour, so the hidden graders
  and their proofs stay valid.
- Runs: Claude Haiku, 5 runs for each task and arm: 90 runs. Replication with Claude Sonnet, 3 runs for each task
  and arm: 54 runs.
- Run order and isolation: as in Study B. Each run has its own workspace with a neutral name.

## Hypotheses and decisions

The measure is the violation rate (hidden grader, the definition of Study A). The interval is a 95% cluster
bootstrap over the six rules (10,000 samples, fixed seed). The p-value is a permutation test within rules.
Each model is analysed separately. The decisions are made for Haiku. The Sonnet results get the same decisions,
reported as a replication.

| # | Role | Hypothesis | Decision |
|---|---|---|---|
| H6 | primary | `mark` has a lower violation rate than `none` | EFFECTIVE if the upper bound of `mark` − `none` is below 0. NOT EFFECTIVE in other cases |
| H7 | primary | `warn` has a lower violation rate than `none` | The same rule for `warn` − `none` |
| H8 | secondary | The place of the information is important (`mark` − `warn`, no direction predicted) | DIFFERENT if the interval does not include 0 |

- If the `none` arm is below 60%, the baseline did not reproduce, and H6 and H7 are INCONCLUSIVE.
- If the two rates of a comparison are both at 10% or less, or both at 90% or more, the comparison is INCONCLUSIVE.

## Other analyses (descriptive)

1. Result for each rule and arm, and leave-one-rule-out for the three differences.
2. Sensitivity 1: only runs with task success.
3. Sensitivity 2: without P1 and P5 (places given by hand).
4. Comparison with the `prose` arm of Study B (20.0% Haiku, 22.2% Sonnet). It is not a concurrent arm, so it gets no decision.
5. Repair: for N1, N2, N3 and P3, the share of runs in which the static check finds no old violation in the
   marked functions after the run. This shows if the agent repaired the precedent without an instruction.
6. `mark` arm: runs that removed or changed a comment.
7. Cost: median tokens and tool calls for each arm.

Analysis script: [studyc_eval.py](../../harness/studyc_eval.py).

## Exclusions

As in Study B:

- A run that reads experiment material outside its workspace is excluded. Results are reported with and without it.
- A run whose transcript does not have the exact prompt of the run is done again one time. The first attempt is kept.
- A run that stops because of a usage limit or a tool failure before it changes code is done again. This is recorded.
- A run for which the hidden grader does not run is an error, not a clean run.

## Deviations from the plan, known before the start

- This study is not the Study C of the plan.
- No `repair` arm (the old violation repaired before the agent starts). It needs new reference solutions and new
  grader proofs for five tasks. The consistent sites of Study A (17%) are the available evidence for repaired code.
- No non-Claude model.
- The places of P1 and P5 are made by hand. The text for the agent says "a scan found" for all rules.
- The N1 task has 12 places in one file. The other tasks have 2 or 3.

## Pinned files

SHA-256 of the files at the time of the pre-registration (line endings as committed):

| File | SHA-256 |
|---|---|
| `research/harness/recon.py` | `2a48edbfd4a63c844be3fcc47765a59d8eee2ca0a463c709f84b75a9201fc677` |
| `research/harness/studyc_eval.py` | `6400273eb0c79e45b994afa2a8244bb91672b28eaee1de896fd00ec36c165f15` |
| `research/trials/studyC/build_material.py` | `f0b6feed0fcc64c03656c5879ee9ff8713add88d5df3d1e1b58a09a1a299a8bc` |
| `research/trials/studyC/hand_places.json` | `ee28f92b3e803c2ed929de23ea393d3d050ca20bf29ffb9e4e9bcf9b370babc5` |
| `research/trials/studyC/rules/N1/mark.patch` | `16a83a928681fb0de5b9b8cfee889e645c2ace6425a792fd04f2fb2cfe6bf647` |
| `research/trials/studyC/rules/N1/places.json` | `f6425e8dcb251037362df887a4001c2b7a986158581edfddb84a4f03be9321ae` |
| `research/trials/studyC/rules/N1/warn.md` | `1661efe797433a28bd03dc396b5411f5e7222a50c42415de00600714340d732e` |
| `research/trials/studyC/rules/N2/mark.patch` | `28e671fa0d66da9118c5509c3faf6074cd159d2f6efdae2be5d7d6c9b20958ec` |
| `research/trials/studyC/rules/N2/places.json` | `67e439d78dfefa56c0da8fe5e535de3a9ba80b8c246408173faff2160ae39343` |
| `research/trials/studyC/rules/N2/warn.md` | `5c39a7dd053baf4796980156adf795a19f325beca1ff0e80e05615810546b928` |
| `research/trials/studyC/rules/N3/mark.patch` | `5a4097b8e35400cbd734b25492260141cb5eb5f210830b73270cce3f3e1018db` |
| `research/trials/studyC/rules/N3/places.json` | `0d7b358b419560934e9fc81b68af45f4fbcfd59610cabc9b0963853a99291cd7` |
| `research/trials/studyC/rules/N3/warn.md` | `53e0bdc214481671d654aee349806e2b6423048e1ef9f1f22e6b1035d6ea6183` |
| `research/trials/studyC/rules/P1/mark.patch` | `971aab26ee69ea50d922e3249cb02ec1b816010b4d46c65a4a25489301846871` |
| `research/trials/studyC/rules/P1/places.json` | `d7c79c1526efa07f14733002b146a4fafd378eb2f76deff9dc37c73e2e37d489` |
| `research/trials/studyC/rules/P1/warn.md` | `e6c08f7a0742a464188cf86aeac0992a4c0f9e6bb678e153cb4aace9b353be9d` |
| `research/trials/studyC/rules/P3/mark.patch` | `5cd5ddc7c905997beba8946265af75b75ea138c3ac2671a024816ad89190e47f` |
| `research/trials/studyC/rules/P3/places.json` | `fa0faf6b97e4963fcbc1379fd979f288fb24ef80050ba00173719cc1c0e108d9` |
| `research/trials/studyC/rules/P3/warn.md` | `9bddf31c0489fefe27e640c93e8b783c3fcf1ba892152d80bc72160da32dd360` |
| `research/trials/studyC/rules/P5/mark.patch` | `7358bc29f85ec1114946ef711cea0b5c2aa42394265ffca84c728eaf85db53b0` |
| `research/trials/studyC/rules/P5/places.json` | `afa7cb9ce5dbec33ce1f1b0b658e9670ee695cce459cafc96c9f3cad4a631310` |
| `research/trials/studyC/rules/P5/warn.md` | `a6907aca7574420b36108b95d9b2c6ef5ababfff74356f84fd30cc4993ea4f86` |
| `research/trials/studyC/sentences.json` | `aae0dd2262517edad0bf1876e0fdb5cac7251be792dab2fb7b9034b525ca2c01` |
| `research/trials/studyC/spec.json` | `7af09a942a74a76103fe4b94a9d93e74b6107005679a239399276cfcbb6f0197` |
| `research/trials/studyD/checks/N1.py` | `0559f8914e51618ac5e8b730c1552bff564e682f10301daf009260a66b2e8899` |
| `research/trials/studyD/checks/N2.py` | `d753a4c3fbd4adeb3ed7263eab0da39b12770ab279468796e2563242fca5907e` |
| `research/trials/studyD/checks/N3.py` | `49e2825ff68cc1724ef215a1422ad4f33bb20ca5cddddcdb7616e181ce788eee` |
| `research/trials/studyD/checks/P1.py` | `cf3b01f04d4f41a40073be6e74c5654e2a699e7aa7510f5214edd55e0f2bb9bf` |
| `research/trials/studyD/checks/P3.py` | `1ce692246b0e8a73734b47ac07977a1ff95e9b6fd232748a517026e93f62e130` |
| `research/trials/studyD/checks/P5.py` | `ee489a7307e003e5d84aeedf299edbf62db7b9a0f0ca25df7bcc0a3b75a0ed32` |
