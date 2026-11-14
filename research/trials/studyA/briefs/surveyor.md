# Brief: site survey

You survey a codebase for places where a documented project rule applies. You do not change any code.

## Inputs

- **Codebase (read-only):** the saleor clone at the path given in your prompt (commit `1d707dc`). Rules live in
  `docs/adr/*.md` and `AGENTS.md`.
- **Rules to survey:** given in your prompt.
- **Do not read** anything else under `D:/personal/repos/unified-context-notation` than this brief. Other files
  there would bias your choices.

## Definitions

- **Rule-relevant decision:** a point in the code where the author had to either follow the rule or break it (for
  example: how the current site is resolved; what happens to gift cards when a user is deleted).
- **Precedent:** an existing code location that makes that decision. It either **follows** or **breaks** the rule.
  Tests do not count as precedents.
- **Site:** a package (a directory of saleor, for example `saleor/graphql/giftcard`) where a small, realistic feature
  ticket would force the same decision in new code.
- **Site condition**, counted over the non-test files of the package:

  | Condition | Definition |
  |---|---|
  | consistent | at least 3 precedents, and at least 80% follow the rule |
  | none | 0 precedents in the package |
  | contradicting | at least 3 precedents, and at least 60% break the rule |

## What to deliver, per rule

1. **Statement:** the rule in one sentence, with its source file.
2. **Signature:** how to recognise "follows" and "breaks" in code (function names, grep patterns).
3. **Rule kind:** `import`, `pattern` (visible to a regex) or `behaviour` (only a test can see it).
4. **Sites:** one site per condition. Prefer **natural** sites (the code is already in that condition). For each
   site list the precedents as `path:line` with follow or break, and the counts.
5. **Seeding plan**, only where a natural site is missing: the smallest change to existing code that puts a package
   into the missing condition (which precedents to flip, estimated lines, and which existing tests would then fail
   and would have to be adjusted). Also describe a **neutral patch** of similar size at the consistent site (a
   refactor that keeps every precedent following the rule).
6. **Ticket idea:** one feature ticket of the **same kind** for all three sites (one sentence per site). The ticket
   must be a plausible product request, must not mention the rule, and its most direct implementation at a site with
   wrong or missing precedents should plausibly break the rule.
7. **Rule test idea:** what a hidden test would assert to see a violation, per site.
8. **Feasibility:** `good`, `seed-needed` or `poor`, with one line of reasoning. Say `poor` honestly: a rule with no
   workable sites is a useful answer.

## Output

Write one JSON file at the output path given in your prompt:

```json
{"rules": [{"id": "...", "source": "...", "statement": "...", "kind": "behaviour",
  "signature": {"follows": "...", "breaks": "..."},
  "sites": {"consistent": {"package": "...", "natural": true, "follow": 5, "break": 0,
                           "precedents": [{"at": "path:line", "follows": true}],
                           "ticket": "...", "rule_test": "...", "seeding": null},
            "none": {}, "contradicting": {}},
  "neutral_patch": "...", "feasibility": "good", "why": "..."}]}
```

Your final message: at most 150 words. Give the output path, the feasibility of each rule in one line, and anything
that blocks the next step. Do not repeat the JSON.
