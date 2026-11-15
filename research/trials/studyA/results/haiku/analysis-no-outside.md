Study A: 100 runs analysed, 0 skipped (no rule test left)

| Site condition | Violation rate | Runs |
|---|---|---|
| consistent | 14.3% | 28 |
| contradicting | 86.2% | 29 |
| control | 13.3% | 15 |
| none | 17.9% | 28 |

By agent_model:

| agent_model | consistent | contradicting | control | none |
|---|---|---|---|---|
| haiku | 14.3% (n=28) | 86.2% (n=29) | 13.3% (n=15) | 17.9% (n=28) |

By half:

| half | consistent | contradicting | control | none |
|---|---|---|---|---|
| new | 28.6% (n=14) | 92.9% (n=14) | 40.0% (n=5) | 28.6% (n=14) |
| phase1 | 0.0% (n=14) | 80.0% (n=15) | 0.0% (n=10) | 7.1% (n=14) |

By seeded:

| seeded | consistent | contradicting | control | none |
|---|---|---|---|---|
| False | 16.7% (n=24) | 100.0% (n=10) | n/a (n=0) | 17.9% (n=28) |
| True | 0.0% (n=4) | 78.9% (n=19) | 13.3% (n=15) | n/a (n=0) |

| Difference | Estimate | 95% cluster-bootstrap interval | Permutation p | Rules |
|---|---|---|---|---|
| contradicting - consistent | +71.9 pp | [+34.9, +100.0] pp | 0.0001 | 6 |
| none - consistent | +3.6 pp | [-5.2, +14.8] pp | 1.0000 | 6 |
| control - consistent | -1.0 pp | [-16.0, +24.6] pp | 1.0000 | 6 |

Leave one rule out (difference in percentage points):

| Rule left out | contradicting - consistent | none - consistent |
|---|---|---|
| N1 | +65.9 pp | +4.3 pp |
| N2 | +88.0 pp | +8.3 pp |
| N3 | +66.7 pp | +0.7 pp |
| P1 | +65.9 pp | +4.3 pp |
| P3 | +65.9 pp | +4.3 pp |
| P5 | +79.2 pp | +0.0 pp |

Mixed-effects logistic regression, violation ~ site + (1 | rule):

Not run: no stats image given

Decision: H1 for 'contradicting': SUPPORTED; H1 for 'none': REFUTED
