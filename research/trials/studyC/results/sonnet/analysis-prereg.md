Study C: 53 runs analysed, 1 skipped

## Model: sonnet (53 runs)

### Main analysis

| Arm | Violations | Rate | Task success |
|---|---|---|---|
| none | 17 / 18 | 94.4% | 61.1% |
| mark | 3 / 17 | 17.6% | 88.2% |
| warn | 6 / 18 | 33.3% | 55.6% |

| Difference | Estimate | 95% cluster-bootstrap interval | Permutation p | Decision |
|---|---|---|---|---|
| mark - none | -76.8 pp | [-100.0 pp, -36.7 pp] | 0.0001 | EFFECTIVE |
| warn - none | -61.1 pp | [-94.4 pp, -16.7 pp] | 0.0008 | EFFECTIVE |
| mark - warn | -15.7 pp | [-38.2 pp, +0.0 pp] | 0.3074 | NO DIFFERENCE SHOWN |

### For each rule (violations / runs, and runs with task success)

| Rule | none | mark | warn |
|---|---|---|---|
| N1 | 3/3 (3) | 0/3 (3) | 0/3 (3) |
| N2 | 3/3 (0) | 0/3 (3) | 0/3 (3) |
| N3 | 3/3 (3) | 0/3 (3) | 0/3 (3) |
| P1 | 3/3 (1) | 1/3 (3) | 1/3 (0) |
| P3 | 3/3 (3) | 0/3 (3) | 2/3 (1) |
| P5 | 2/3 (1) | 2/2 (0) | 3/3 (0) |

### Leave one rule out

| Rule left out | mark - none | warn - none | mark - warn |
|---|---|---|---|
| N1 | -71.9 pp | -53.3 pp | -18.6 pp |
| N2 | -71.9 pp | -53.3 pp | -18.6 pp |
| N3 | -71.9 pp | -53.3 pp | -18.6 pp |
| P1 | -79.0 pp | -60.0 pp | -19.0 pp |
| P3 | -71.9 pp | -66.7 pp | -5.2 pp |
| P5 | -93.3 pp | -80.0 pp | -13.3 pp |

### Sensitivity 1: only runs with task success

| Arm | Violations | Rate | Task success |
|---|---|---|---|
| none | 10 / 11 | 90.9% | 100.0% |
| mark | 1 / 15 | 6.7% | 100.0% |
| warn | 0 / 10 | 0.0% | 100.0% |

| Difference | Estimate | 95% cluster-bootstrap interval | Permutation p | Decision |
|---|---|---|---|---|
| mark - none | -84.2 pp | [-100.0 pp, -46.0 pp] | 0.0001 | EFFECTIVE |
| warn - none | -90.9 pp | [-100.0 pp, -60.0 pp] | 0.0007 | EFFECTIVE |
| mark - warn | +6.7 pp | [+0.0 pp, +20.0 pp] | 1.0000 | INCONCLUSIVE (ceiling or floor) |

### Sensitivity 2: without the rules with places given by hand (P1, P5)

| Arm | Violations | Rate | Task success |
|---|---|---|---|
| none | 12 / 12 | 100.0% | 75.0% |
| mark | 0 / 12 | 0.0% | 100.0% |
| warn | 2 / 12 | 16.7% | 83.3% |

| Difference | Estimate | 95% cluster-bootstrap interval | Permutation p | Decision |
|---|---|---|---|---|
| mark - none | -100.0 pp | [-100.0 pp, -100.0 pp] | 0.0001 | EFFECTIVE |
| warn - none | -83.3 pp | [-100.0 pp, -50.0 pp] | 0.0001 | EFFECTIVE |
| mark - warn | -16.7 pp | [-50.0 pp, +0.0 pp] | 0.3973 | NO DIFFERENCE SHOWN |

### Cost (medians)

| Arm | Tokens | Tool calls |
|---|---|---|
| none | 58475.5 | 13.5 |
| mark | 62311 | 16 |
| warn | 54222.0 | 18.0 |

