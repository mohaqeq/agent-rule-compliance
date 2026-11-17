Study C: 90 runs analysed, 0 skipped

## Model: haiku (90 runs)

### Main analysis

| Arm | Violations | Rate | Task success |
|---|---|---|---|
| none | 26 / 30 | 86.7% | 80.0% |
| mark | 6 / 30 | 20.0% | 93.3% |
| warn | 2 / 30 | 6.7% | 96.7% |

| Difference | Estimate | 95% cluster-bootstrap interval | Permutation p | Decision |
|---|---|---|---|---|
| mark - none | -66.7 pp | [-93.3 pp, -40.0 pp] | 0.0001 | EFFECTIVE |
| warn - none | -80.0 pp | [-100.0 pp, -46.7 pp] | 0.0001 | EFFECTIVE |
| mark - warn | +13.3 pp | [-13.3 pp, +43.3 pp] | 0.2257 | NO DIFFERENCE SHOWN |

### For each rule (violations / runs, and runs with task success)

| Rule | none | mark | warn |
|---|---|---|---|
| N1 | 5/5 (5) | 0/5 (5) | 0/5 (5) |
| N2 | 5/5 (1) | 0/5 (5) | 0/5 (5) |
| N3 | 5/5 (5) | 2/5 (5) | 0/5 (5) |
| P1 | 5/5 (5) | 0/5 (4) | 1/5 (5) |
| P3 | 5/5 (4) | 4/5 (4) | 0/5 (5) |
| P5 | 1/5 (4) | 0/5 (5) | 1/5 (4) |

### Leave one rule out

| Rule left out | mark - none | warn - none | mark - warn |
|---|---|---|---|
| N1 | -60.0 pp | -76.0 pp | +16.0 pp |
| N2 | -60.0 pp | -76.0 pp | +16.0 pp |
| N3 | -68.0 pp | -76.0 pp | +8.0 pp |
| P1 | -60.0 pp | -80.0 pp | +20.0 pp |
| P3 | -76.0 pp | -76.0 pp | +0.0 pp |
| P5 | -76.0 pp | -96.0 pp | +20.0 pp |

### Sensitivity 1: only runs with task success

| Arm | Violations | Rate | Task success |
|---|---|---|---|
| none | 20 / 24 | 83.3% | 100.0% |
| mark | 6 / 28 | 21.4% | 100.0% |
| warn | 1 / 29 | 3.4% | 100.0% |

| Difference | Estimate | 95% cluster-bootstrap interval | Permutation p | Decision |
|---|---|---|---|---|
| mark - none | -61.9 pp | [-93.1 pp, -25.4 pp] | 0.0001 | EFFECTIVE |
| warn - none | -79.9 pp | [-100.0 pp, -45.5 pp] | 0.0001 | EFFECTIVE |
| mark - warn | +18.0 pp | [-6.9 pp, +50.5 pp] | 0.0240 | NO DIFFERENCE SHOWN |

### Sensitivity 2: without the rules with places given by hand (P1, P5)

| Arm | Violations | Rate | Task success |
|---|---|---|---|
| none | 20 / 20 | 100.0% | 75.0% |
| mark | 6 / 20 | 30.0% | 95.0% |
| warn | 0 / 20 | 0.0% | 100.0% |

| Difference | Estimate | 95% cluster-bootstrap interval | Permutation p | Decision |
|---|---|---|---|---|
| mark - none | -70.0 pp | [-100.0 pp, -40.0 pp] | 0.0001 | EFFECTIVE |
| warn - none | -100.0 pp | [-100.0 pp, -100.0 pp] | 0.0001 | EFFECTIVE |
| mark - warn | +30.0 pp | [+0.0 pp, +60.0 pp] | 0.0102 | NO DIFFERENCE SHOWN |

### Cost (medians)

| Arm | Tokens | Tool calls |
|---|---|---|
| none | 89383.0 | 31.5 |
| mark | 92205.5 | 33.0 |
| warn | 90412.5 | 34.0 |

