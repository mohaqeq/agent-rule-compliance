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

## 2026-11-17: proposals for the next study

Status: proposal. Nothing is decided, and no run is started.

Measured cost until now, for planning:

- One Haiku run without a test command: about 0.4% of a 5-hour window.
- One Sonnet run: about 1.3% of a 5-hour window.
- Study C (90 Haiku and 54 Sonnet runs) used about 14% of the weekly limit.

### Option E1: the accumulation chain (hypothesis 1 above)

Question: does one violation make the next violation more probable through a chain of changes? Do the measures of
Studies B and C stop that?

- **Design.** A chain is four tickets in one package. Each ticket starts from the code that the previous run left.
  The chain starts from a clean site (the consistent site of Study A). The first violation then comes from the
  agent itself, not from a seed.
- **Rules.** N1, N3 and P3. For these rules the Study D checks find the violations, so each step can be measured
  without a new grader for each ticket. One hidden grader for each rule examines all four tickets.
- **Arms.** `none`, and `scan`: after each step, the tool runs the check and puts the `warn` text of Study C into
  the next ticket when it finds an old violation.
- **Measures.** The violation rate at step k, against the number of violations already in the package. The share
  of chains that stay clean.
- **Runs.** 3 rules, 2 arms, 5 chains, 4 steps: 120 Haiku runs. The steps of one chain run one after the other.
- **Cost.** About 50% of one 5-hour window and 12% of the week. It also needs 12 new tickets and 3 graders with
  proofs (one author agent, about 15% of a window).
- **Risk.** If the agents seldom start a violation at a clean site (Study A: 17%), most chains stay clean, and the
  result has little information. A pilot of one chain for each rule shows this before the full run.

### Option E2: the `repair` arm of Study C

Question: does a repaired precedent prevent the violation as well as a test does?

- **Design.** The six contradicting tasks, with the old violation repaired in the base before the agent starts.
- **Runs.** 30 Haiku and 18 Sonnet runs. The `none` arms of Study C are the comparison.
- **Cost.** About 37% of one window. It needs new reference solutions and new grader proofs for five tasks.
- **Value.** Medium. The consistent sites of Study A (17%) already give similar evidence, and Study C showed that
  agents repair the precedent when the ticket asks for it.

### Option E3: a model of a different supplier

Question: do the main results hold outside one model family? This is a limit of all four studies.

- **Design.** Repeat the key cells with one non-Claude model: Study A contradicting and consistent, Study B `none`,
  `prose` and `rule`, Study C `mark` and `warn`. 3 runs for each task and cell: about 126 runs.
- **Cost.** Almost no Claude usage for the runs. The runs cost money through OpenRouter (the key is on this machine).
  It needs an agent loop for that model with the same tools (read, edit, shell, the test command), which is new
  harness work.
- **Value.** High for the credibility of the post and of the reports.
- **Risk.** A different agent loop is a second change at the same time as the model. The result then shows the
  effect of the model and of the loop together.

### Recommendation

1. **E1 first**, with a pilot of three chains. It asks the new question, it connects to the decoherence argument,
   and its cost is moderate.
2. **E3 second.** It answers the largest limit of all results before a wide publication.
3. **E2 only if** E1 shows that repair is the key measure.
