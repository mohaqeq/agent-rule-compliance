# Coding agents repeat the wrong precedent, and only a test stops them

*Draft, 2026-11-17. A short report on Study A and Study B of the agent-rule-compliance project.*

A project has rules that its tests do not always examine. An architecture decision says "send webhooks through this
function". A security rule says "this record stays restricted after the customer is deleted". When does an AI coding
agent break such a rule, and what prevents it?

I did two experiments with 444 agent runs. The results are clear.

1. **If the code near the change breaks the rule, the agent breaks it again, in almost every run.**
2. **The tests that the project has do not prevent this. One test written for the rule prevents it each time.**

## Experiment 1: what causes the violation

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

The hypotheses, the tasks and the analysis were published before the first run of each experiment.

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

## Experiment 2: what prevents the violation

The second experiment used only the six tickets where the near code breaks the rule. Each agent got one of these:

- **Nothing:** the ticket only.
- **The project tests:** a command that runs the tests of the project. The agent could use it as often as necessary.
- **The rule text:** the paragraph of the project documentation that states the rule.
- **A rule test:** the project tests, and one more test that fails when the new code breaks the rule.

There were 234 runs: 180 with Haiku and 54 with Sonnet.

| What the agent gets | Runs that broke the rule, Haiku | Runs that broke the rule, Sonnet |
|---|---|---|
| Nothing | 87% | not tested |
| The project tests to run | 83% | 83% |
| The rule text | 20% | 22% |
| A rule test | 0% | 0% |

1. **The project tests prevent almost nothing.** The agents ran the tests, the tests passed, and the violation
   stayed. The existing tests do not examine the rule at the new place, so a pass says nothing about the rule.
   The agent accepts the pass as confirmation.
2. **The rule text prevents most violations, but not all.** It failed most for one security rule. There the near
   code was a strong example of the opposite, and the agents followed the code. Sonnet failed there in all three runs.
3. **A rule test prevented all violations.** This was true in 48 of 48 runs with the two models, and in 57 more
   Haiku runs that also got guidance text. The agents read the failure and corrected the code. No agent changed
   or deleted the test.
4. **The rule test was not more expensive.** The median number of tokens for a run was almost the same in all groups.
   An agent that can run a test reads less code to make sure of its change.
5. **More guidance added nothing to the rule test.** Plain text or a formal notation with the rule test gave the
   same result as the rule test only.

## What this means in practice

- An agent treats the near code as the specification. This is good when the code is correct. It is bad when the
  code contains old violations.
- Each violation that stays in the code is thus an instruction to the next agent to do the same.
- "The agent ran the tests and they passed" is not evidence that the change obeys the rules of the project.
- If a rule is important, make it executable first. Then document it. The text helps, but the test decides.
- Do not expect a stronger model to solve this. In these experiments it did not.

## Limits

- One codebase, one language and six rules. The intervals are over rules, and six is a small number.
- The two models are from one supplier.
- Each rule test was written with knowledge of the ticket. It examines the rule for the new feature, not for all
  code. A real project must write such a test before the change, or have a general check for the rule.
- The agent got the correct rule text each time. In a real project, the agent must find that text first.
- The Sonnet part of experiment 2 is small: 3 runs for each ticket and group, and no group without help.
- An error in my test tooling made the first 36 Sonnet runs with a test command not valid. I did them again.
  This is not in the published plan. The report describes it, and the first attempts are public.
- Two of the six rules had difficult tasks with low success in experiment 1. The effect stays large when I remove
  either of them.

## Next

The two experiments looked at one change at a time. The next question is about time: if one violation makes the
next violation more probable, do violations increase through a chain of changes? And does a rule test stop that?

The data, the graders, the analysis and the tool-call logs of all runs are public:
[github.com/mohaqeq/agent-rule-compliance](https://github.com/mohaqeq/agent-rule-compliance).
The full reports are
[Study A](https://github.com/mohaqeq/agent-rule-compliance/blob/main/research/docs/12-study-a-results.md) and
[Study B](https://github.com/mohaqeq/agent-rule-compliance/blob/main/research/docs/13-study-b-results.md).
