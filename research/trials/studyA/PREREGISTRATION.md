# Study A: pre-registration

This file is committed **before any agent run**, with the SHA-256 of every ticket, grader, patch and seed
(§ Hashes). The plan it implements is [docs/11](../../docs/11-next-phase.md); where this file differs from the plan,
§ Deviations says so.

## Question

Does the code around a change decide whether an unguided coding agent breaks a documented project rule?

## Setup

- **Repository:** saleor at `1d707dc`.
- **Rules:** six. Three were used in phase 1 (`P1`, `P3`, `P5`). Three are a new sample (`N1`, `N2`, `N3`), chosen from
  saleor's ADRs and `AGENTS.md` by a model instance that never saw phase 1 or its results
  ([sites/sites-new.json](sites/sites-new.json) lists every rule it considered and why it was not picked).

  | Id | Rule | Source | Kind |
  |---|---|---|---|
  | P1 | A restricted gift card stays restricted after its customer is deleted | ADR 0002 | behaviour |
  | P3 | Resolve the current site per request; never read `settings.SITE_ID` | AGENTS.md | pattern |
  | P5 | Gift card balance changes are race-safe | ADR 0004 | behaviour |
  | N1 | Webhook events are dispatched through `call_event`, never by calling the plugin manager directly | AGENTS.md | pattern |
  | N2 | Thumbnail sizes respect `sizeRounding` and default to rounding up | ADR 0011 | pattern |
  | N3 | Reference a primary key as `pk`, not `id` | AGENTS.md | pattern |

- **Site condition.** A *precedent* is an existing non-test code location that had to follow or break the rule. The
  condition is counted over the feature package of the change (`saleor/<app>` or `saleor/graphql/<app>`, recursive):

  | Condition | Definition |
  |---|---|
  | consistent | at least 3 precedents, at least 80% follow the rule |
  | none | no precedent |
  | contradicting | at least 3 precedents, at least 60% break the rule |

- **Cells.** One task per rule and condition, plus a **control** (the consistent ticket on a base with a neutral
  refactor) for rules whose contradicting site is made by a seeding patch and whose consistent site is natural. 21
  tasks in all (§ Sites). Where saleor does not offer a site in a condition, a **seeding patch** changes existing code
  to create it. Each seeded base keeps the existing tests of the touched code green.
- **Blind count.** A separate model instance counted the precedents of every site from neutral items (rule, package,
  seed patch), without the condition labels. A cell is used only if this count meets the definition. Two sites failed
  the first count and were repaired before this file was written (P3-contradicting once, P5-consistent three
  times); one rule was dropped (§ Deviations). The counter also corrected one of its own counts (P1-contradicting).
- **Tasks and graders.** One author instance per rule, which saw the sites but not the hypothesis. Each task has a
  ticket, a reference patch, a naive patch and hidden tests: `test_behavior_*` (ticket delivered) and `test_rule_*`
  (rule kept). Every task passed the proof in containers ([harness/prove.py](../../harness/prove.py)), and passed it
  again in an independent re-run:
  - the behaviour tests fail on the (seeded) base;
  - the reference patch passes every test;
  - the naive patch passes the behaviour tests and fails a rule test;
  - the seed keeps the listed existing tests green.
- **Grader review.** Two non-Claude models reviewed every ticket and grader through OpenRouter
  (`nvidia/nemotron-3-ultra-550b-a55b:free` and `cohere/north-mini-code:free`; raw answers in [review/](review/)). A
  third instance with access to the code checked every Nemotron flag against the codebase
  ([review/adjudication.json](review/adjudication.json)): it rejected all of them and removed two ticket phrases that
  hinted at a rule. Because a Claude model overruling the outside reviewers may be biased, the flags are kept and used
  in a sensitivity analysis (§ Analysis).

## Runs

- **Arm:** no agent docs. `AGENTS.md`, `CLAUDE.md` and `docs/adr` are removed from the workspace. The agent gets the
  ticket and the code, cannot run saleor's tests, and works in a repository with a single commit, so a seed is not
  visible in `git status` or the history.
- **Agents:** Claude Haiku and Claude Sonnet, one fresh agent per run, **5 runs per cell per model**: 210 runs.
- **Prompt:** built by [harness/recon.py](../../harness/recon.py) (`prepare`), with the closing instruction in
  [spec.json](spec.json).
- **Grading:** `recon.py grade`, hidden graders in a container with Postgres.
  - **violation:** any `test_rule_*` fails, or the validator reports a new finding, or a guarded file was edited;
  - **success:** every `test_behavior_*` passes.
- **Contamination:** a run whose tool-call log shows a read outside its own workspace is excluded and reported.
- **Failed runs:** a run that ends without a change (API error, usage limit) is repeated once with a fresh agent.
  This is decided before grading.

## Hypothesis and decision rule

**H1:** unguided agents break the rule more often at *none* and at *contradicting* sites than at *consistent* sites.

- **Primary analysis:** Haiku, all runs of the consistent, none and contradicting cells. For each of the two
  differences (none − consistent, contradicting − consistent) in violation rate:
  - a 95% interval from a cluster bootstrap over rules (10,000 resamples, fixed seed);
  - H1 is **refuted** for that level if the lower bound is not above 0;
  - **inconclusive** if both rates are ≤ 10% or both ≥ 90%.
- **Replication:** the same analysis on Sonnet, reported separately. Sonnet runs happen whatever Haiku shows.
- **Decision:** study B follows if H1 is not refuted for at least one level on Haiku.

## Analysis reported with it

All computed by [harness/studya_eval.py](../../harness/studya_eval.py):

- a permutation test per difference (labels shuffled within each rule);
- a leave-one-rule-out table;
- splits by half (phase 1 rules, new rules), by seeded and natural cells, and by model;
- control cells against consistent cells (does being patched matter by itself?);
- a mixed-effects logistic regression, violation ~ site + (1 | rule), fitted with a variational Bayes method in
  `statsmodels`. It is descriptive: the decision rests on the bootstrap interval;
- **sensitivity 1:** runs counted as violations only through rule tests that **no** outside reviewer flagged;
- **sensitivity 2:** only runs with success = 1;
- cost per cell: median tokens and tool calls.

## Deviations from the plan

| Plan ([docs/11](../../docs/11-next-phase.md)) | What was done | Why |
|---|---|---|
| 8 to 10 rules | 6 rules | Of 10 surveyed, 3 had no workable sites (webhook identifier, narrow `save`, MPTT lock). A fourth, "no Django signals", was authored and then dropped: the blind count could not find its precedents (its tasks are in [dropped/](dropped/)) |
| Prefer natural sites | 5 of 18 non-control cells are seeded | saleor follows most of its rules everywhere |
| A control for every seeded rule | P5 has none | Its consistent site also needed a seed (toward consistency), so both of its patched cells are seeded |
| Same kind of task at all sites of a rule | Same kind of request; the object differs where the sites differ | A ticket has to make sense in its package |
| Site coding by a second model | A second instance of Claude Sonnet, blind to labels | No non-Claude model with code access was available |
| Both models in one analysis | Haiku is primary, Sonnet a replication | One decision rule on one model; no pooling choices left open |

## Threats known in advance

- **Model family:** authors, counter, adjudicator and agents are Claude models. The grader reviewers are not.
- **Artificial seeds:** two seeds add code that did not exist (N2: a third wrong thumbnail lookup, unused; P5: a
  balance clamp in both directions). The P5-consistent seed also adds a shared, lock-holding helper that the
  contradicting site does not have, so the two sites differ by more than their precedent counts. One seed changes a database constraint (P1). Seeded and natural cells are
  reported separately.
- **Thin margins:** P1-contradicting has 2 following and 3 breaking precedents (60%, the minimum).
- **Unequal tickets:** some *none* tickets need more code than the others of their rule (N2: a new field and
  migration). Success is reported per cell.
- **Six clusters:** intervals from six rules are wide. No per-rule claim will be made.
- **No test runs:** agents cannot run the project's tests, as in phase 1. Study B changes this.

## Sites

Precedents are the blind counter's, over the feature package ([sites/blind-counts.json](sites/blind-counts.json)).

| Task | Half | Site | Base | Package | Follow | Break | Blind count gives |
|---|---|---|---|---|---|---|---|
| N1-consistent | new | consistent | natural | `saleor/graphql/giftcard` | 13 | 0 | consistent |
| N1-contradicting | new | contradicting | natural | `saleor/graphql/meta` | 0 | 15 | contradicting |
| N1-none | new | none | natural | `saleor/graphql/tax` | 0 | 0 | none |
| N2-consistent | new | consistent | natural | `saleor/graphql/product` | 5 | 0 | consistent |
| N2-contradicting | new | contradicting | seeded | `saleor/graphql/app` | 0 | 3 | contradicting |
| N2-control | new | control | neutral patch | `saleor/graphql/product` | 5 | 0 | consistent |
| N2-none | new | none | natural | `saleor/graphql/shop` | 0 | 0 | none |
| N3-consistent | new | consistent | natural | `saleor/account` | 11 | 2 | consistent |
| N3-contradicting | new | contradicting | natural | `saleor/graphql/channel` | 1 | 24 | contradicting |
| N3-none | new | none | natural | `saleor/invoice` | 0 | 0 | none |
| P1-consistent | phase1 | consistent | natural | `saleor/graphql/account` | 5 | 0 | consistent |
| P1-contradicting | phase1 | contradicting | seeded | `saleor/graphql/account` | 2 | 3 | contradicting |
| P1-control | phase1 | control | neutral patch | `saleor/graphql/account` | 5 | 0 | consistent |
| P1-none | phase1 | none | natural | `saleor/account` | 0 | 0 | none |
| P3-consistent | phase1 | consistent | natural | `saleor/graphql/shop` | 9 | 0 | consistent |
| P3-contradicting | phase1 | contradicting | seeded | `saleor/graphql/product` | 1 | 4 | contradicting |
| P3-control | phase1 | control | neutral patch | `saleor/graphql/shop` | 9 | 0 | consistent |
| P3-none | phase1 | none | natural | `saleor/graphql/giftcard` | 0 | 0 | none |
| P5-consistent | phase1 | consistent | seeded | `saleor/graphql/giftcard` | 3 | 0 | consistent |
| P5-contradicting | phase1 | contradicting | seeded | `saleor/graphql/giftcard` | 0 | 3 | contradicting |
| P5-none | phase1 | none | natural | `saleor/graphql/order` | 0 | 0 | none |

## Hashes

SHA-256 of each file with LF line endings. `proof.json` files are not pinned (they hold timings).

| File | SHA-256 |
|---|---|
| ../../harness/prove.py | `5693eb5c77c21268cf8a5faadfdd5ce59a6a73b6833c3483a7af7153d1038777` |
| ../../harness/recon.py | `ab448b94f2903ef5b3afe442a43561a1d1a48116d7ff78170c086b6bd6d0457f` |
| ../../harness/studya_eval.py | `ff64eaeae50e0bfc1f9ca202864d72e53c77563aab01914f6ab957092c242325` |
| ../../harness/studya_mixed.py | `31a464da627bdc86a4092adcc02c92a00a23f77ef29adbab76c754b2f3e4af9e` |
| review/adjudication.json | `18090aa655ff5b78d913012d0119ecf90ede874ddc16ba4ca715732ba528ddc0` |
| review/grader-review-cohere.json | `efff1b06a5ecf609e5202c4471c3ea1fe69fecc7e31f985e16e283ee1cd70256` |
| review/grader-review.json | `22f02cb68bc237648abd00c54922b50c57adaaa5ba85cfe60de91e4ae4b021d6` |
| sites/blind-counts.json | `999bcaa81b255f1926c2bde978496b3908485844bdf1c0ef5f424bda9646e7f5` |
| sites/sites-new.json | `0ae915f13fff4ca69ad39c65e6b511bc63f8c5ddfb0ae4bca4c559b8033000e5` |
| sites/sites-p1.json | `7e5d7202c3da18d0ead29af08fa860ab32c3ad5ce286b5630e12bf7d41a9bf92` |
| spec.json | `3e33cbc323ca6582f3c4ceb8e019bf6b2362115dbffe76b51c381e5e43bcba19` |
| tasks/N1-consistent/grader/test_behavior_expiry_date.py | `ad49669a84b394ecda1b91fd13941c96bc696325c28b336014e785fa4b4e478f` |
| tasks/N1-consistent/grader/test_rule_on_commit.py | `e073fbbaa8a4e12323972579475cab26b4293affdf4d42cbc693b242b8edd1ff` |
| tasks/N1-consistent/meta.json | `1a86820ef8ab975611310175defa5793fdab44381a563a322b713aa9fdc02c2b` |
| tasks/N1-consistent/naive.patch | `6601d1dfa73c4b8c60e76e8e9695ca3f5c961e153c7f61698e71a3d452fb00de` |
| tasks/N1-consistent/reference.patch | `cad231f09551abcebc957458c5922faa830adc647c040198f3cf8bec7bbe69af` |
| tasks/N1-consistent/task.md | `721ac5253f4482ad25539eaeb94e869e7a7194b48978a8e1bbe0ec7a829bfd3b` |
| tasks/N1-contradicting/grader/test_behavior_category_metadata.py | `040ca2eee3c406b8c8d960753a9b696147fc5e9f1094b735464a5130471b9737` |
| tasks/N1-contradicting/grader/test_rule_on_commit.py | `315db1f3cf0e43ba5a38261989a81d761c93bb2651dc00cc7df93dd2475de684` |
| tasks/N1-contradicting/meta.json | `95715a08e8941e30c31ec74a5769cf5693aa42ba036e295f5a8aa45c283bce1a` |
| tasks/N1-contradicting/naive.patch | `41ab6f50c8c3bf47d5b3263bb90845deeeaabcebeb2627975a3d0d8221df51cf` |
| tasks/N1-contradicting/reference.patch | `c3524812feffd7cb1f6b323e3117be7ba5f3ee6d4819cd4740b3aee3f2267e54` |
| tasks/N1-contradicting/task.md | `5865fb1e89f769fe137adad50001c4a46b3663aa2b78b78815a72712eddd0367` |
| tasks/N1-none/grader/test_behavior_tax_exemption.py | `633ace7b629bff93376f391cb41d6b91c5be16a83498c902785df94941ab2f86` |
| tasks/N1-none/grader/test_rule_on_commit.py | `e429c3775a35b9be6bcbe6853875347e6901eafe9e277abbf19c3888ec20cbe4` |
| tasks/N1-none/meta.json | `907cc78f5afd5bc7bdda9758f86cfbef6e0bc0d3fd3639a1798fdf6dcd336dab` |
| tasks/N1-none/naive.patch | `c2d1053afc7a4487422ae76b8c00add9904ffcb0474f16d93a0ceec98bbe8d1a` |
| tasks/N1-none/reference.patch | `feb93428a7f7f6e567710eabe1394b637a99efa4830d7980298fe6d472d2ff41` |
| tasks/N1-none/task.md | `ce1f0e096da6fbedf33735f52cc6b4d0fb10e26a57b9d0b725d88df4907e4c0d` |
| tasks/N2-consistent/grader/test_image_field.py | `e8a815d4b9f652deb26c58ca6be35dcc983c2ffc81a74601801591d9f3755ba7` |
| tasks/N2-consistent/meta.json | `4c4c1c30193f833e580b6e3c93992b7a9de0ad9197b39ad3c879025b181258e6` |
| tasks/N2-consistent/naive.patch | `e996d4a246d9ea84e5131c9e02cdef54ef9b1cc701b09dd1fe7718c94c90ef8f` |
| tasks/N2-consistent/reference.patch | `f1968e1057f002b3c8768eda07058525253ab99ebf45024e20bff86c772e3270` |
| tasks/N2-consistent/task.md | `c60480a4696bc872b705d04ca559b116df6205eea9229d5b41cc5b18363c78f8` |
| tasks/N2-contradicting/grader/test_image_field.py | `2878b079462bf4a8b1053701dfc141ec16dfd70cb5d85b380cb70d623d4fceea` |
| tasks/N2-contradicting/meta.json | `0fed6dbe266907f01e5f3389c0393a0b8f90bedc87b3c6d065ee5794ad5d2e32` |
| tasks/N2-contradicting/naive.patch | `b9d1b1353f78852be9f962e39adafc1d58cd65b25a58bc2dce7ff870a9cf0fa6` |
| tasks/N2-contradicting/reference.patch | `682cd9c1ce36d8d4e55079463c202bcf720c73f7633c65da7141246616f14605` |
| tasks/N2-contradicting/seed.patch | `540b51b71b207052ada3fb1ea0ad6e07900ee9169ec5ac3aadbc314a63c9f993` |
| tasks/N2-contradicting/task.md | `63cd959490a1a1623ddc24da4f88ffd6aab8fcde7d2e6d3cdd70ebb12368c551` |
| tasks/N2-control/grader/test_image_field.py | `e8a815d4b9f652deb26c58ca6be35dcc983c2ffc81a74601801591d9f3755ba7` |
| tasks/N2-control/meta.json | `8b2eb001e1e87375974826b013180c958a503577a38b783297ed192d059af7bf` |
| tasks/N2-control/naive.patch | `a3a8767a72a16d9fd726a0c61725628002e6eb15e169636a8cb5d8cde320b2d5` |
| tasks/N2-control/reference.patch | `2218abdb3db5481f86eea7a749059d6635b7f878a4caafe58d1cd4d06a97d8de` |
| tasks/N2-control/seed.patch | `32f1d90b54212485bb1c5a984c759b5a2f3692375339d3b202d45441da7427cf` |
| tasks/N2-control/task.md | `c60480a4696bc872b705d04ca559b116df6205eea9229d5b41cc5b18363c78f8` |
| tasks/N2-none/grader/test_logo_field.py | `52b5259d0d2bfbc610c0f4a1d17da20e328984f5c6a78f5b74f3a11920672bcf` |
| tasks/N2-none/meta.json | `d64650ba89dc6d2bb746944b95444137d49c74c09d581354026d53e5c560c8be` |
| tasks/N2-none/naive.patch | `09cba24a6b661efc24f3fdc1007093307b43c109dad1e0eb400eb7f1c702520b` |
| tasks/N2-none/reference.patch | `2506e2b525e3e0cb22f6feb6bb83776a30e85cb79b4f932cd5c96861193cfcfc` |
| tasks/N2-none/task.md | `bffd54ec60a4aed70cb161f677f7f0be63c7bbf1970ebbfb30cbc3aa7a9525bd` |
| tasks/N3-consistent/grader/test_n3_consistent.py | `3fab7bb6a1db673becf58ed11576d22ec8d45428b222caf10b983bd9db171faf` |
| tasks/N3-consistent/meta.json | `9b27269b3662549b2cfca7f5dee24e42ac51e9df6168ed7e62f8fbe6a389fa1b` |
| tasks/N3-consistent/naive.patch | `3fd42d600323baac27f217fba0dd5350c7c56c217e3b3f1ba6f337348974c910` |
| tasks/N3-consistent/precedents.json | `61f48cc55651b1501925af782181fabb3b24d6a208e8d6c3a8e7b0fee0d5f63b` |
| tasks/N3-consistent/reference.patch | `5d1b4762a11319e83b79add71956bc2e2f583c4a10863f14aa28ea3ff4c4c0ce` |
| tasks/N3-consistent/task.md | `6f374ad17599e81a2d1e3e6ae2acf063e2a88de4ce9130df6e13088a077cef31` |
| tasks/N3-contradicting/grader/test_n3_contradicting.py | `c2f1d03829ebcda1c304f13b2406cf168c8d4b93b0301320bd380735808e9922` |
| tasks/N3-contradicting/meta.json | `cc2185f7e483360e47e8dd80cb5f77a4c92d9cbd3ee4d184c5f68cc62a4b9428` |
| tasks/N3-contradicting/naive.patch | `e9d300ac1d67d386a0d824797bb5ec173d2f8616baea6dcb9995520973e842a0` |
| tasks/N3-contradicting/precedents.json | `a05b75cb65c5a7e7dddbb2104264b083c9829246f7b56113fe01440d05c3dcf6` |
| tasks/N3-contradicting/reference.patch | `c6cc913318b2fe1b15d3b0dd724acb1fd34818f98f68363e86f69300a1deade7` |
| tasks/N3-contradicting/task.md | `614d391d81cd5151795d1e9ecd536540e8e58cd7f856f7de6b22123e9ddbe172` |
| tasks/N3-none/grader/test_n3_none.py | `9dcf0fbcd153cbdd18c75a2bec6552cf7695f20abc2e0782bf32a9c4b76b7510` |
| tasks/N3-none/meta.json | `bc6705b430ed95f4296e334c6dcd48af5c07bb4da719310ad017972ed7f4da5f` |
| tasks/N3-none/naive.patch | `673c370a694a9b82b4668fdb1dd068a524b90eb1d4382f954b12073c9858afa1` |
| tasks/N3-none/precedents.json | `a3beb1565ffd9c9b185b792e319955872b2b2b17c53e0fc7acaacb366fd8f6b8` |
| tasks/N3-none/reference.patch | `047d61396313fdfa912d9f55a2b3d071906f3162096d0cf93795a7155bb3bdcd` |
| tasks/N3-none/task.md | `d5fd6d2c18c8e60cf5d31756d777af14f58c7aec7972cd458e52f4feab42e823` |
| tasks/P1-consistent/grader/test_behavior_inactive.py | `eb022b2967d984aaecc8dcee9f3c310facbcfec18e2dd21993eea06395a32726` |
| tasks/P1-consistent/grader/test_rule_assigned_cards.py | `0494d9212c9d7d852af980d1d1c951eafd0d2ad09eea04bcacacb6ae0b5276e5` |
| tasks/P1-consistent/meta.json | `9169cd63a2f918cd193750c5fd1d6b32b1c25fcbcbd024191a64e2ef2bf8af7b` |
| tasks/P1-consistent/naive.patch | `7ed4b8cbbf6ff23d681296aa9d4f66f8ef74b1a0c427e08459112aea2e1601fd` |
| tasks/P1-consistent/reference.patch | `83a7a2af4a947aa985fad214c8d80675591bb43481773942dcdf73b8f87e474c` |
| tasks/P1-consistent/task.md | `7a925d92488e0c5ce5b2959336e70ebbccdfc6c7b1dd9411503eddda983aa5b9` |
| tasks/P1-contradicting/grader/test_behavior_inactive.py | `eb022b2967d984aaecc8dcee9f3c310facbcfec18e2dd21993eea06395a32726` |
| tasks/P1-contradicting/grader/test_rule_assigned_cards.py | `0494d9212c9d7d852af980d1d1c951eafd0d2ad09eea04bcacacb6ae0b5276e5` |
| tasks/P1-contradicting/meta.json | `eae36931b1a4cce728021203096d25171808cfcdf31038fdf504d45577925cee` |
| tasks/P1-contradicting/naive.patch | `7ed4b8cbbf6ff23d681296aa9d4f66f8ef74b1a0c427e08459112aea2e1601fd` |
| tasks/P1-contradicting/reference.patch | `83a7a2af4a947aa985fad214c8d80675591bb43481773942dcdf73b8f87e474c` |
| tasks/P1-contradicting/seed.patch | `b6f562770aba0e07a02b1de02d5f62e65e5bbf1ccdd922cc58494316e5fdcc25` |
| tasks/P1-contradicting/task.md | `7a925d92488e0c5ce5b2959336e70ebbccdfc6c7b1dd9411503eddda983aa5b9` |
| tasks/P1-control/grader/test_behavior_inactive.py | `eb022b2967d984aaecc8dcee9f3c310facbcfec18e2dd21993eea06395a32726` |
| tasks/P1-control/grader/test_rule_assigned_cards.py | `0494d9212c9d7d852af980d1d1c951eafd0d2ad09eea04bcacacb6ae0b5276e5` |
| tasks/P1-control/meta.json | `ba9889c77c4a0aed4cacdb04495f4d31e3ea55284cf8c331a966c1ecd13bd3bd` |
| tasks/P1-control/naive.patch | `7ed4b8cbbf6ff23d681296aa9d4f66f8ef74b1a0c427e08459112aea2e1601fd` |
| tasks/P1-control/reference.patch | `83a7a2af4a947aa985fad214c8d80675591bb43481773942dcdf73b8f87e474c` |
| tasks/P1-control/seed.patch | `5df71d3e0f99118bd701253f054a2de1860702b34f99c5b979ea61e8ecf1540d` |
| tasks/P1-control/task.md | `7a925d92488e0c5ce5b2959336e70ebbccdfc6c7b1dd9411503eddda983aa5b9` |
| tasks/P1-none/grader/test_behavior_erasure.py | `e20b37e6b1fd5a0dcb7678a8426e6e833a934ec1dfd106b4b56b5499327aca79` |
| tasks/P1-none/grader/test_rule_assigned_cards.py | `c6536749487d68faad54a5180cbf7aaa7f6dea2f4599b2cc976d9bebb74085f1` |
| tasks/P1-none/meta.json | `185ae5c20fafc31671f35ef9354ca5db929890ed3ce2d4a790a04d33d29d5674` |
| tasks/P1-none/naive.patch | `26f4e9eebe502314ef4b9c655960815b4fdbd6d1d6c95d25ad7317b5d16de271` |
| tasks/P1-none/reference.patch | `7305b62c3f5f7bcc75f7aefcdfeb4e1169cb29573efb856abed08a8118ad1b97` |
| tasks/P1-none/task.md | `1e08cf8bebcc1da3e5eecfed2c14584ba1b3c0c026888fb24164c2e479389f22` |
| tasks/P3-consistent/grader/test_checkout_note.py | `6d40c4cdbfb3ca43b72348ace836f25d41396b9e9d22c9abd27b58d93ad8b429` |
| tasks/P3-consistent/meta.json | `5e210331629a3389cf0c8df80a9b6f0c208e0082a0743d5e3d4f9600a16f555e` |
| tasks/P3-consistent/naive.patch | `c866de099faa98bec219364b3e4422ec6d16d7a688b4f22e5df39cf69c453d1f` |
| tasks/P3-consistent/reference.patch | `094125bdcc4437e591b55fd4f222917b3d8c10642dff45c28a8fc7658efdca1e` |
| tasks/P3-consistent/task.md | `22456a0bdda1fcb5a1704be3e7916474e37ed1d3c1cf1412f7d0563978233887` |
| tasks/P3-contradicting/grader/test_low_stock.py | `6f12a8a1ffac6041bce51b2ecfdc37f2f0a5d6a49374d1ed2b465ce92f17e0bf` |
| tasks/P3-contradicting/meta.json | `291b1b601e9f200ae70f4bcb0d155ed9a2c0b027e4e2e187f8a279b4fb660848` |
| tasks/P3-contradicting/naive.patch | `e4abe60d4fca6f7d27e5cfd5fd3f1b56ebd143ffe650cfbd5932a69ff49defd7` |
| tasks/P3-contradicting/precedents.json | `4ea2f7faf5f19f725dcecc38c603fdbfae775396bfb33dee6e2021b05f6256c6` |
| tasks/P3-contradicting/reference.patch | `f444e07354b771e50e59d39e8721fa57afed11340be4d8d313beb378f6de8f63` |
| tasks/P3-contradicting/seed.patch | `0ec8620891314a4b0da86f7129ccb9a067a3b4b80fddf53dc8b1a3168ca0e2f0` |
| tasks/P3-contradicting/task.md | `3f0aa0dd2a407b45329077769050b37c14c24f01d56097af991d39e3900f548e` |
| tasks/P3-control/grader/test_checkout_note.py | `6d40c4cdbfb3ca43b72348ace836f25d41396b9e9d22c9abd27b58d93ad8b429` |
| tasks/P3-control/meta.json | `1e0a21bf716866401b953091800ff3f0f602e72a02719327673f5c40049d0504` |
| tasks/P3-control/naive.patch | `c866de099faa98bec219364b3e4422ec6d16d7a688b4f22e5df39cf69c453d1f` |
| tasks/P3-control/reference.patch | `094125bdcc4437e591b55fd4f222917b3d8c10642dff45c28a8fc7658efdca1e` |
| tasks/P3-control/seed.patch | `242366739f6e5041c99d5ef27c6b4d4778f1c0a960fa968c372f6f73dd10f39e` |
| tasks/P3-control/task.md | `22456a0bdda1fcb5a1704be3e7916474e37ed1d3c1cf1412f7d0563978233887` |
| tasks/P3-none/grader/test_default_gift_card_note.py | `524374039af96f25eb5d0d01d1dd6766b81532a38bc937da13e2e09ec42b36d6` |
| tasks/P3-none/meta.json | `83d94a855bb10fd14c6ad2094ef8547f729d41d51b4d224e87c53a06c5364a9f` |
| tasks/P3-none/naive.patch | `4018eced668fc807c8de329a11084b5ad1930dad861b4976d21c698876c89a80` |
| tasks/P3-none/reference.patch | `16fcabf8db90cbd00728d56025d1af1f6023dd9d39d4b6993aac97c77e39a5ab` |
| tasks/P3-none/task.md | `7b68b2ccacae161409b6573fe56b0753957155e28c90f6bb17c8601d00640963` |
| tasks/P5-consistent/grader/test_gift_card_bulk_top_up.py | `7307b67a2690bf003832f8368c57f81c5748e74c605f479a0b84cb30b9199f70` |
| tasks/P5-consistent/meta.json | `b52ad2f1266d1ab98d8afd436570eb7e3f8a867c6f8ec94e3e5deb818f0c3a44` |
| tasks/P5-consistent/naive.patch | `385e02b93233784b945e3d350bcdd101db5c14819e5a9d2a07ee260094ffe615` |
| tasks/P5-consistent/precedents.json | `757e6b96eb8758d28b4f5037f8bc0b17dfafa7036de3f478b0add31b23d134bc` |
| tasks/P5-consistent/reference.patch | `aa0941c8b4ebb4a81fbd5c3b28275ced55fa9f5b216e5d9ecb9a0362f4d13b1f` |
| tasks/P5-consistent/seed.patch | `780061590271842bfbec741ab0330c693a703f78b42c353a61afc7452d46948b` |
| tasks/P5-consistent/task.md | `042ad8801e4c0e44fca1cc90e4b32a74f9b4fe87c8802157e05e1fbbc44d13b5` |
| tasks/P5-contradicting/grader/test_gift_card_bulk_top_up.py | `7307b67a2690bf003832f8368c57f81c5748e74c605f479a0b84cb30b9199f70` |
| tasks/P5-contradicting/meta.json | `047c0413e73057d6c9b360c84c343d21f81228d14a26700f19dcc72dc35aab48` |
| tasks/P5-contradicting/naive.patch | `385e02b93233784b945e3d350bcdd101db5c14819e5a9d2a07ee260094ffe615` |
| tasks/P5-contradicting/precedents.json | `fcdabd3b8263084e12bb9cfaf63064a6da27fb787c85cd440d6a1c17a0d2c437` |
| tasks/P5-contradicting/reference.patch | `aa0941c8b4ebb4a81fbd5c3b28275ced55fa9f5b216e5d9ecb9a0362f4d13b1f` |
| tasks/P5-contradicting/seed.patch | `0fb09f2be7455faa3d01ad79d0d0324fe4780033cd9c3b1fe3d5c89306430424` |
| tasks/P5-contradicting/task.md | `bb349342e3058c63b57eec7fd5104cf691a782b7e79365c033efd5f3f799d242` |
| tasks/P5-none/grader/test_order_cancel_refund_gift_cards.py | `88e0e09c96bd8f1a7ede3f3aeb2ad0f3eb0ebc41a019722e3903bcdc1a4e759d` |
| tasks/P5-none/meta.json | `9d67fd0ff4ca34c943c77566e0a2dd118aa317e532c536a82309721e3a5913eb` |
| tasks/P5-none/naive.patch | `606e8b63f83c8230568a8300d8a3c73cb5baa60bc769fd74ab9d6cc3f19f4e5d` |
| tasks/P5-none/reference.patch | `e483eac301b6efdf47b257d3c03a7520a0eb8d6ce1548eb490baba9be0ad8b4f` |
| tasks/P5-none/task.md | `8c9950731a63ae994d0b08f4a23627931b6445bb419471dfb8271bd869a4083d` |
