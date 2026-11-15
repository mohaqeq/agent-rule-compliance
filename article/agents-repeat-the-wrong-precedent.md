# Coding agents repeat the wrong precedent

*Draft, 2026-11-15. A short report on Study A of the agent-rule-compliance project.*

A project has rules that its tests do not always examine. An architecture decision says "send webhooks through this
function". A security rule says "this record stays restricted after the customer is deleted". When does an AI coding
agent break such a rule?

I tested one possible cause: the code near the change. The result is clear. **If the near code breaks the rule, the
agent breaks it again, in almost every run.**

## The experiment

- **Codebase:** saleor, a large open-source shop system with written architecture decisions.
- **Rules:** six rules from those decisions.
- **Tasks:** 21 tickets. Each rule has a ticket at three types of site:
  - *consistent:* the near code follows the rule;
  - *none:* the near code has no example of the rule;
  - *contradicting:* the near code breaks the rule.
- **Agents:** Claude Haiku and Claude Sonnet, with no project documentation. They could read all the code.
- **Runs:** 210 (5 for each ticket and model).
- **Grading:** hidden tests. Each grader was proven before the runs: it fails on the base, it passes on a correct
  solution, and it finds a solution that does the task but breaks the rule.

The hypotheses, the tasks and the analysis were published before the first run.

## The result

| Code near the change | Runs that broke the rule, Haiku | Runs that broke the rule, Sonnet |
|---|---|---|
| Follows the rule | 17% | 17% |
| No example | 23% | 13% |
| Breaks the rule | 87% | 97% |

Three things are important.

1. **A wrong precedent is copied.** The difference between "breaks the rule" and "follows the rule" is 70 points for
   Haiku and 80 points for Sonnet. The 95% interval does not include zero for either model.
2. **A stronger model does not help.** Sonnet did the tasks with fewer steps, but it copied the wrong precedent at
   least as often as Haiku.
3. **A missing precedent is not the problem.** Where the near code had no example, the agents did not break rules
   more often than at consistent sites.

One more number shows how sharp the effect is. I looked only at runs that did the task correctly. At sites without
a wrong precedent, 0 of 117 of those runs broke a rule. At sites with a wrong precedent, 37 of 42 broke it.

## What this means in practice

- An agent treats the near code as the specification. This is good when the code is correct. It is bad when the
  code contains old violations.
- Each violation that stays in the code is thus an instruction to the next agent to do the same.
- A project does not need to document each rule for the agent. It needs to know where the code disagrees with its
  rules, because those places are where the agent fails.

## Limits

- One codebase, one language and six rules. The interval is over rules, and six is a small number.
- The two models are from one supplier.
- The agents did not run tests. Tests that examine a rule can change the result for that rule.
- Two of the six rules had difficult tasks with low success. Their cells are weak evidence. The effect stays large
  when I remove either of them.

## Next

The next study asks the practical question: what is the cheapest thing that prevents the violation at such a site?
The candidates are a short text about the rule, the tests that the project already has, and one test written for the rule.

The data, the graders, the analysis and the tool-call logs of all runs are public:
[github.com/mohaqeq/agent-rule-compliance](https://github.com/mohaqeq/agent-rule-compliance).
The full report is in
[research/docs/12-study-a-results.md](https://github.com/mohaqeq/agent-rule-compliance/blob/main/research/docs/12-study-a-results.md).
