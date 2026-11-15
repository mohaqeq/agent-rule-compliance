Study A: 105 runs analysed, 0 skipped (no rule test left)

| Site condition | Violation rate | Runs |
|---|---|---|
| consistent | 16.7% | 30 |
| contradicting | 86.7% | 30 |
| control | 13.3% | 15 |
| none | 23.3% | 30 |

By agent_model:

| agent_model | consistent | contradicting | control | none |
|---|---|---|---|---|
| haiku | 16.7% (n=30) | 86.7% (n=30) | 13.3% (n=15) | 23.3% (n=30) |

By half:

| half | consistent | contradicting | control | none |
|---|---|---|---|---|
| new | 26.7% (n=15) | 93.3% (n=15) | 40.0% (n=5) | 33.3% (n=15) |
| phase1 | 6.7% (n=15) | 80.0% (n=15) | 0.0% (n=10) | 13.3% (n=15) |

By seeded:

| seeded | consistent | contradicting | control | none |
|---|---|---|---|---|
| False | 16.0% (n=25) | 100.0% (n=10) | n/a (n=0) | 23.3% (n=30) |
| True | 20.0% (n=5) | 80.0% (n=20) | 13.3% (n=15) | n/a (n=0) |

| Difference | Estimate | 95% cluster-bootstrap interval | Permutation p | Rules |
|---|---|---|---|---|
| contradicting - consistent | +70.0 pp | [+36.7, +100.0] pp | 0.0001 | 6 |
| none - consistent | +6.7 pp | [+0.0, +13.3] pp | 0.6615 | 6 |
| control - consistent | -3.3 pp | [-16.0, +16.7] pp | 1.0000 | 6 |

Leave one rule out (difference in percentage points):

| Rule left out | contradicting - consistent | none - consistent |
|---|---|---|
| N1 | +64.0 pp | +8.0 pp |
| N2 | +84.0 pp | +8.0 pp |
| N3 | +64.0 pp | +4.0 pp |
| P1 | +64.0 pp | +8.0 pp |
| P3 | +64.0 pp | +8.0 pp |
| P5 | +80.0 pp | +4.0 pp |

Mixed-effects logistic regression, violation ~ site + (1 | rule):

| Term | Odds ratio | 95% interval |
|---|---|---|
| contradicting | 35.16 | [13.01, 95.03] |
| none | 1.12 | [0.45, 2.79] |

Decision: H1 for 'contradicting': SUPPORTED; H1 for 'none': REFUTED
