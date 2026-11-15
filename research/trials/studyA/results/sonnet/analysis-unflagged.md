Study A: 105 runs analysed, 0 skipped (no rule test left)

| Site condition | Violation rate | Runs |
|---|---|---|
| consistent | 10.0% | 30 |
| contradicting | 80.0% | 30 |
| control | 0.0% | 15 |
| none | 0.0% | 30 |

By agent_model:

| agent_model | consistent | contradicting | control | none |
|---|---|---|---|---|
| sonnet | 10.0% (n=30) | 80.0% (n=30) | 0.0% (n=15) | 0.0% (n=30) |

By half:

| half | consistent | contradicting | control | none |
|---|---|---|---|---|
| new | 0.0% (n=15) | 66.7% (n=15) | 0.0% (n=5) | 0.0% (n=15) |
| phase1 | 20.0% (n=15) | 93.3% (n=15) | 0.0% (n=10) | 0.0% (n=15) |

By seeded:

| seeded | consistent | contradicting | control | none |
|---|---|---|---|---|
| False | 4.0% (n=25) | 100.0% (n=10) | n/a (n=0) | 0.0% (n=30) |
| True | 40.0% (n=5) | 70.0% (n=20) | 0.0% (n=15) | n/a (n=0) |

| Difference | Estimate | 95% cluster-bootstrap interval | Permutation p | Rules |
|---|---|---|---|---|
| contradicting - consistent | +70.0 pp | [+40.0, +93.3] pp | 0.0001 | 6 |
| none - consistent | -10.0 pp | [-23.3, +0.0] pp | 0.2283 | 6 |
| control - consistent | -10.0 pp | [-23.3, +0.0] pp | 0.5030 | 6 |

Leave one rule out (difference in percentage points):

| Rule left out | contradicting - consistent | none - consistent |
|---|---|---|
| N1 | +64.0 pp | -12.0 pp |
| N2 | +84.0 pp | -12.0 pp |
| N3 | +64.0 pp | -12.0 pp |
| P1 | +68.0 pp | -8.0 pp |
| P3 | +68.0 pp | -12.0 pp |
| P5 | +72.0 pp | -4.0 pp |

Mixed-effects logistic regression, violation ~ site + (1 | rule):

| Term | Odds ratio | 95% interval |
|---|---|---|
| contradicting | 85.21 | [29.25, 248.27] |
| none | 0.07 | [0.01, 0.61] |

Decision: H1 for 'contradicting': SUPPORTED; H1 for 'none': INCONCLUSIVE (ceiling or floor)
