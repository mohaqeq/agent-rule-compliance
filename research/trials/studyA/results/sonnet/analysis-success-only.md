Study A: 80 runs analysed, 0 skipped (no rule test left)

| Site condition | Violation rate | Runs |
|---|---|---|
| consistent | 0.0% | 24 |
| contradicting | 95.0% | 20 |
| control | 0.0% | 10 |
| none | 0.0% | 26 |

By agent_model:

| agent_model | consistent | contradicting | control | none |
|---|---|---|---|---|
| sonnet | 0.0% (n=24) | 95.0% (n=20) | 0.0% (n=10) | 0.0% (n=26) |

By half:

| half | consistent | contradicting | control | none |
|---|---|---|---|---|
| new | 0.0% (n=13) | 91.7% (n=12) | 0.0% (n=2) | 0.0% (n=14) |
| phase1 | 0.0% (n=11) | 100.0% (n=8) | 0.0% (n=8) | 0.0% (n=12) |

By seeded:

| seeded | consistent | contradicting | control | none |
|---|---|---|---|---|
| False | 0.0% (n=22) | 100.0% (n=10) | n/a (n=0) | 0.0% (n=26) |
| True | 0.0% (n=2) | 90.0% (n=10) | 0.0% (n=10) | n/a (n=0) |

| Difference | Estimate | 95% cluster-bootstrap interval | Permutation p | Rules |
|---|---|---|---|---|
| contradicting - consistent | +95.0 pp | [+80.0, +100.0] pp | 0.0001 | 6 |
| none - consistent | +0.0 pp | [+0.0, +0.0] pp | 1.0000 | 6 |
| control - consistent | +0.0 pp | [+0.0, +0.0] pp | 1.0000 | 6 |

Leave one rule out (difference in percentage points):

| Rule left out | contradicting - consistent | none - consistent |
|---|---|---|
| N1 | +93.3 pp | +0.0 pp |
| N2 | +100.0 pp | +0.0 pp |
| N3 | +93.3 pp | +0.0 pp |
| P1 | +93.8 pp | +0.0 pp |
| P3 | +93.8 pp | +0.0 pp |
| P5 | +95.0 pp | +0.0 pp |

Mixed-effects logistic regression, violation ~ site + (1 | rule):

Not run: no stats image given

Decision: H1 for 'contradicting': SUPPORTED; H1 for 'none': INCONCLUSIVE (ceiling or floor)
