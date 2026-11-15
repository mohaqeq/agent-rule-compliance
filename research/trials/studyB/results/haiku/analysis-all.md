Study B: 180 runs analysed, 0 skipped (no rule, no arm in the list, or no violations value)

## Model: haiku (180 runs)

### Violation rate and task success for each arm

| Arm | Violation rate | Task success | Runs |
|---|---|---|---|
| none | 86.7% | 80.0% | 30 |
| prose | 20.0% | 86.7% | 30 |
| gen | 83.3% | 90.0% | 30 |
| rule | 0.0% | 100.0% | 30 |
| prule | 0.0% | 100.0% | 30 |
| urule | 0.0% | 100.0% | 30 |

### For each rule and arm (violation rate, task success, runs)

| Rule | none | prose | gen | rule | prule | urule |
|---|---|---|---|---|---|---|
| N1 | 100.0% / 100.0% / n=5 | 0.0% / 100.0% / n=5 | 100.0% / 100.0% / n=5 | 0.0% / 100.0% / n=5 | 0.0% / 100.0% / n=5 | 0.0% / 100.0% / n=5 |
| N2 | 100.0% / 0.0% / n=5 | 20.0% / 80.0% / n=5 | 100.0% / 40.0% / n=5 | 0.0% / 100.0% / n=5 | 0.0% / 100.0% / n=5 | 0.0% / 100.0% / n=5 |
| N3 | 100.0% / 100.0% / n=5 | 0.0% / 100.0% / n=5 | 80.0% / 100.0% / n=5 | 0.0% / 100.0% / n=5 | 0.0% / 100.0% / n=5 | 0.0% / 100.0% / n=5 |
| P1 | 100.0% / 100.0% / n=5 | 60.0% / 80.0% / n=5 | 100.0% / 100.0% / n=5 | 0.0% / 100.0% / n=5 | 0.0% / 100.0% / n=5 | 0.0% / 100.0% / n=5 |
| P3 | 100.0% / 100.0% / n=5 | 0.0% / 100.0% / n=5 | 100.0% / 100.0% / n=5 | 0.0% / 100.0% / n=5 | 0.0% / 100.0% / n=5 | 0.0% / 100.0% / n=5 |
| P5 | 20.0% / 80.0% / n=5 | 40.0% / 60.0% / n=5 | 20.0% / 100.0% / n=5 | 0.0% / 100.0% / n=5 | 0.0% / 100.0% / n=5 | 0.0% / 100.0% / n=5 |

### Pre-registered differences

| Difference | Rate a | Rate b | Estimate | 95% cluster-bootstrap interval | Permutation p |
|---|---|---|---|---|---|
| gen - prose | 83.3% | 20.0% | +63.3 pp | [+26.7, +93.3] pp | 0.0002 |
| prose - none | 20.0% | 86.7% | -66.7 pp | [-96.7, -30.0] pp | 0.0001 |
| gen - none | 83.3% | 86.7% | -3.3 pp | [-10.0, +0.0] pp | 1.0000 |
| rule - none | 0.0% | 86.7% | -86.7 pp | [-100.0, -60.0] pp | 0.0001 |
| prule - none | 0.0% | 86.7% | -86.7 pp | [-100.0, -60.0] pp | 0.0001 |
| urule - none | 0.0% | 86.7% | -86.7 pp | [-100.0, -60.0] pp | 0.0001 |
| urule - prule | 0.0% | 0.0% | +0.0 pp | [+0.0, +0.0] pp | 1.0000 |

### Decisions

- H2 (gen - prose): SUPPORTED
- H2b, prose against none: EFFECTIVE
- H2b, gen against none: NOT EFFECTIVE
- H2b, rule against none: EFFECTIVE
- H2b, prule against none: EFFECTIVE
- H2b, urule against none: EFFECTIVE
- H3 (prule against rule): INCONCLUSIVE
  - median tokens: prule 77288, rule 76256
  - median failed check runs: prule 0, rule 0.5
- UCN (urule - prule, no decision): violations +0.0 pp, median tokens -3359.5, median failed check runs 0

### Leave one rule out, H2 difference (gen - prose)

| Rule left out | gen - prose |
|---|---|
| N1 | +56.0 pp |
| N2 | +60.0 pp |
| N3 | +60.0 pp |
| P1 | +68.0 pp |
| P3 | +56.0 pp |
| P5 | +80.0 pp |

### Mixed-effects logistic regression, violation ~ arm + (1 | rule), reference arm none (descriptive)

| Arm | Odds ratio | 95% interval |
|---|---|---|
| gen | 2.15 | [0.80, 5.73] |
| prose | 0.08 | [0.03, 0.19] |
| prule | 0.01 | [0.00, 0.04] |
| rule | 0.01 | [0.00, 0.04] |
| urule | 0.01 | [0.00, 0.04] |

### Sensitivity 1: only runs with task success

| Arm | Violation rate | Task success | Runs |
|---|---|---|---|
| none | 83.3% | 100.0% | 24 |
| prose | 7.7% | 100.0% | 26 |
| gen | 81.5% | 100.0% | 27 |
| rule | 0.0% | 100.0% | 30 |
| prule | 0.0% | 100.0% | 30 |
| urule | 0.0% | 100.0% | 30 |

| Difference | Rate a | Rate b | Estimate | 95% cluster-bootstrap interval | Permutation p |
|---|---|---|---|---|---|
| gen - prose | 81.5% | 7.7% | +73.8 pp | [+46.5, +96.3] pp | 0.0001 |
| prose - none | 7.7% | 83.3% | -75.6 pp | [-100.0, -37.4] pp | 0.0001 |
| gen - none | 81.5% | 83.3% | -1.9 pp | [-11.1, +11.1] pp | 1.0000 |
| rule - none | 0.0% | 83.3% | -83.3 pp | [-100.0, -45.5] pp | 0.0001 |
| prule - none | 0.0% | 83.3% | -83.3 pp | [-100.0, -45.5] pp | 0.0001 |
| urule - none | 0.0% | 83.3% | -83.3 pp | [-100.0, -45.5] pp | 0.0001 |
| urule - prule | 0.0% | 0.0% | +0.0 pp | [+0.0, +0.0] pp | 1.0000 |

H2: SUPPORTED; H2b: prose EFFECTIVE; gen NOT EFFECTIVE; rule EFFECTIVE; prule EFFECTIVE; urule EFFECTIVE

### Sensitivity 2: without rules N2 and P1

| Arm | Violation rate | Task success | Runs |
|---|---|---|---|
| none | 80.0% | 95.0% | 20 |
| prose | 10.0% | 90.0% | 20 |
| gen | 75.0% | 100.0% | 20 |
| rule | 0.0% | 100.0% | 20 |
| prule | 0.0% | 100.0% | 20 |
| urule | 0.0% | 100.0% | 20 |

| Difference | Rate a | Rate b | Estimate | 95% cluster-bootstrap interval | Permutation p |
|---|---|---|---|---|---|
| gen - prose | 75.0% | 10.0% | +65.0 pp | [+10.0, +100.0] pp | 0.0002 |
| prose - none | 10.0% | 80.0% | -70.0 pp | [-100.0, -10.0] pp | 0.0001 |
| gen - none | 75.0% | 80.0% | -5.0 pp | [-15.0, +0.0] pp | 1.0000 |
| rule - none | 0.0% | 80.0% | -80.0 pp | [-100.0, -40.0] pp | 0.0001 |
| prule - none | 0.0% | 80.0% | -80.0 pp | [-100.0, -40.0] pp | 0.0001 |
| urule - none | 0.0% | 80.0% | -80.0 pp | [-100.0, -40.0] pp | 0.0001 |
| urule - prule | 0.0% | 0.0% | +0.0 pp | [+0.0, +0.0] pp | 1.0000 |

H2: SUPPORTED; H2b: prose EFFECTIVE; gen NOT EFFECTIVE; rule EFFECTIVE; prule EFFECTIVE; urule EFFECTIVE

### Sensitivity 3: a changed rule test counts as a violation

| Arm | Violation rate | Task success | Runs |
|---|---|---|---|
| none | 86.7% | 80.0% | 30 |
| prose | 20.0% | 86.7% | 30 |
| gen | 83.3% | 90.0% | 30 |
| rule | 0.0% | 100.0% | 30 |
| prule | 0.0% | 100.0% | 30 |
| urule | 0.0% | 100.0% | 30 |

| Difference | Rate a | Rate b | Estimate | 95% cluster-bootstrap interval | Permutation p |
|---|---|---|---|---|---|
| gen - prose | 83.3% | 20.0% | +63.3 pp | [+26.7, +93.3] pp | 0.0002 |
| prose - none | 20.0% | 86.7% | -66.7 pp | [-96.7, -30.0] pp | 0.0001 |
| gen - none | 83.3% | 86.7% | -3.3 pp | [-10.0, +0.0] pp | 1.0000 |
| rule - none | 0.0% | 86.7% | -86.7 pp | [-100.0, -60.0] pp | 0.0001 |
| prule - none | 0.0% | 86.7% | -86.7 pp | [-100.0, -60.0] pp | 0.0001 |
| urule - none | 0.0% | 86.7% | -86.7 pp | [-100.0, -60.0] pp | 0.0001 |
| urule - prule | 0.0% | 0.0% | +0.0 pp | [+0.0, +0.0] pp | 1.0000 |

H2: SUPPORTED; H2b: prose EFFECTIVE; gen NOT EFFECTIVE; rule EFFECTIVE; prule EFFECTIVE; urule EFFECTIVE

### Check arms: runs that ended with a passing visible rule test

| Arm | Runs | Ended with passing rule test | Share | Never ran it | Violation rate, passing | Violation rate, other |
|---|---|---|---|---|---|---|
| rule | 30 | 29 | 96.7% | 1 | 0.0% | 0.0% |
| prule | 30 | 29 | 96.7% | 1 | 0.0% | 0.0% |
| urule | 30 | 29 | 96.7% | 1 | 0.0% | 0.0% |

### Cost for each arm (medians)

| Arm | Tokens | Tool calls | Check invocations | Runs |
|---|---|---|---|---|
| none | 82285 | 36.5 | n/a | 30 |
| prose | 84922.5 | 41.5 | n/a | 30 |
| gen | 77863.5 | 33.5 | 2 | 30 |
| rule | 76256 | 34 | 2 | 30 |
| prule | 77288 | 34.5 | 2 | 30 |
| urule | 73928.5 | 35 | 2 | 30 |

