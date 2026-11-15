Study A: 79 runs analysed, 0 skipped (no rule test left)

| Site condition | Violation rate | Runs |
|---|---|---|
| consistent | 0.0% | 25 |
| contradicting | 81.8% | 22 |
| control | 0.0% | 12 |
| none | 0.0% | 20 |

By agent_model:

| agent_model | consistent | contradicting | control | none |
|---|---|---|---|---|
| haiku | 0.0% (n=25) | 81.8% (n=22) | 0.0% (n=12) | 0.0% (n=20) |

By half:

| half | consistent | contradicting | control | none |
|---|---|---|---|---|
| new | 0.0% (n=11) | 90.9% (n=11) | 0.0% (n=3) | 0.0% (n=7) |
| phase1 | 0.0% (n=14) | 72.7% (n=11) | 0.0% (n=9) | 0.0% (n=13) |

By seeded:

| seeded | consistent | contradicting | control | none |
|---|---|---|---|---|
| False | 0.0% (n=21) | 100.0% (n=10) | n/a (n=0) | 0.0% (n=20) |
| True | 0.0% (n=4) | 66.7% (n=12) | 0.0% (n=12) | n/a (n=0) |

| Difference | Estimate | 95% cluster-bootstrap interval | Permutation p | Rules |
|---|---|---|---|---|
| contradicting - consistent | +81.8 pp | [+44.4, +100.0] pp | 0.0001 | 6 |
| none - consistent | +0.0 pp | [+0.0, +0.0] pp | 1.0000 | 6 |
| control - consistent | +0.0 pp | [+0.0, +0.0] pp | 1.0000 | 6 |

Leave one rule out (difference in percentage points):

| Rule left out | contradicting - consistent | none - consistent |
|---|---|---|
| N1 | +76.5 pp | +0.0 pp |
| N2 | +85.7 pp | +0.0 pp |
| N3 | +76.5 pp | +0.0 pp |
| P1 | +78.9 pp | +0.0 pp |
| P3 | +76.5 pp | +0.0 pp |
| P5 | +94.7 pp | +0.0 pp |

Mixed-effects logistic regression, violation ~ site + (1 | rule):

Not run: no stats image given

Decision: H1 for 'contradicting': SUPPORTED; H1 for 'none': INCONCLUSIVE (ceiling or floor)
