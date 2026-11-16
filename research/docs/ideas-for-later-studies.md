# Ideas for later studies

This file collects inputs that are not evaluated yet. Nothing here is a decision.
Evaluate each item against the plan ([11-next-phase.md](11-next-phase.md)) when Study B is complete.

## 2026-11-16: two articles about "decoherence"

Status: read by an agent one time. The cited papers are not verified and not read.

### Sources

1. Jimmy Breck-McKye, "Software is breaking down at a systemic level", 15 November 2026.
   <https://www.breck-mckye.com/blog/2026/11/software-is-breaking-down-at-a-systemic-level/>
   - Opinion text, no data.
   - Thesis: the large failures of 2026 come from many small changes. Each change is reasonable, but the changes are
     not coherent together.
   - Possible use: motivation in the introduction of the post. It is not evidence.
2. Kristen Maevyn, "The Decoherence Trap", 14 October 2026. <https://maevyn.codes/decoherence>
   - Mostly argument, with a toy simulation. The author says that the weights of the simulation are arbitrary.
   - Definition: decoherence is "the accumulation of locally valid but mutually incompatible or redundant models
     within a system".
   - Key claim: "decoherence does not grow over time, but with change".
   - Possible use: a name and a frame for the Study A result (a wrong precedent near the change).

### Hypotheses that the articles suggest

1. The violation rate of a change increases with the number of violations already in the code.
2. When two conventions are near the change, the agent chooses one of them or makes a third.
3. A smaller turn or token budget causes more violations.
4. The cost of a change (files read, tokens) increases with the number of violations.
5. The repair of violations decreases the violation rate of later changes.

### First assessment

- Hypothesis 1 is the most valuable. Study A measured one change at one site. A chain of changes can show if one
  violation makes the next violation more probable.
- Study B gives the control for such a chain: the same chain with a rule test in the loop.
- Hypothesis 2 needs a new site type (two patterns near the change). Study A had sites with one pattern only.
- No article gives a reason to change Study B.

### Papers that the second article cites (possible related work)

| Paper | Claim as the article gives it | Link |
|---|---|---|
| Chen and Stratton | 718 companies: 30% more code, pull request reviews 49% longer | <https://fion.ac/jellyfish.pdf> |
| He et al., MSR '26 | Cursor adoption: the speed gain went away, the added complexity stayed | <https://arxiv.org/abs/2511.04427> |
| Liu et al. | More than 300,000 AI commits: about 1 in 11 added a quality problem | <https://arxiv.org/abs/2603.28592> |

Read each paper before a citation. The claims above come from the article, not from the papers.

### Open actions

- Compare hypothesis 1 with the Study C and Study D plan before a design decision.
- Read the three papers.
