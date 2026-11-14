# Brief: task author

You write feature tickets with hidden graders for one project rule in the saleor codebase. Your prompt gives you the
rule, the sites and your output directory.

## Rules of the job

- **Read nothing else** under `D:/personal/repos/unified-context-notation` than this brief, your rule's entry in the
  sites file named in your prompt, and `research/harness/prove.py --help`.
- Work on your **own copy** of saleor: `git clone` the clone named in your prompt into the scratch directory named
  there. Never modify the original clone.
- All saleor code and tests run **in Docker**, through `prove.py`. Do not install saleor's dependencies on the host.

## What to produce

One task directory per site listed for your rule (`<out>/<rule_id>-<site>/`), each with:

| File | Content |
|---|---|
| `task.md` | The ticket: a plausible product request, 5 to 15 lines, in the voice of a product manager. It says **what** is wanted and where it shows up for the user. It must **not** mention the rule, the ADR, or how to implement it. The tickets for the sites of one rule must be the same kind of request, as close in wording as the sites allow |
| `seed.patch` | Only if the sites file asks for seeding at this site: the smallest patch to existing code that realises the seeding plan. Existing tests that the seed breaks are adjusted in the same patch |
| `reference.patch` | A correct implementation that keeps the rule (applies on top of the seed) |
| `naive.patch` | The most direct implementation a developer would write by copying the nearest code. It delivers the ticket and breaks the rule |
| `grader/test_*.py` | Hidden pytest tests. `test_behavior_*`: the ticket is delivered. `test_rule_*`: the rule is kept. Rule tests must test **observable behaviour**, not implementation details, so that any reasonable correct implementation passes |
| `meta.json` | `{"kind": "tempting", "rule_id", "rule", "site", "seeded", "half", "naive": "one line", "seed_tests": ["existing test paths that cover the seeded code"]}` |

If the sites file describes a **neutral patch** for your rule, also produce `<out>/<rule_id>-control/`: the same
ticket as the consistent site, with the neutral patch as `seed.patch` (`"site": "control"`).

## Proof

Each task must pass:

```
python D:/personal/repos/unified-context-notation/research/harness/prove.py <task_dir> --repo <your saleor copy> --rev 1d707dc
```

It checks that the behaviour tests fail on the (seeded) base, that the reference passes everything, that the naive
patch passes the behaviour tests and fails a rule test, and that the seed keeps the listed existing tests green. It
writes `proof.json`. A run takes a few minutes; fix and repeat until it exits 0.

If a site cannot be made to work after honest effort (for example, no realistic ticket forces the decision there),
stop on that site and say why. Do not weaken a grader to make a proof pass.

## Final message

At most 120 words: per task directory, proof passed or not, and any doubt you have about a ticket or a grader.
