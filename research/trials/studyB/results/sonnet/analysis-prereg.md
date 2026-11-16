Study B: 54 runs analysed, 0 skipped (no rule, no arm in the list, or no violations value)

## Model: sonnet (54 runs)

### Violation rate and task success for each arm

| Arm | Violation rate | Task success | Runs |
|---|---|---|---|
| prose | 22.2% | 83.3% | 18 |
| gen | 83.3% | 83.3% | 18 |
| rule | 0.0% | 100.0% | 18 |

### For each rule and arm (violation rate, task success, runs)

| Rule | prose | gen | rule |
|---|---|---|---|
| N1 | 0.0% / 100.0% / n=3 | 100.0% / 100.0% / n=3 | 0.0% / 100.0% / n=3 |
| N2 | 0.0% / 100.0% / n=3 | 100.0% / 0.0% / n=3 | 0.0% / 100.0% / n=3 |
| N3 | 0.0% / 100.0% / n=3 | 100.0% / 100.0% / n=3 | 0.0% / 100.0% / n=3 |
| P1 | 100.0% / 33.3% / n=3 | 100.0% / 100.0% / n=3 | 0.0% / 100.0% / n=3 |
| P3 | 0.0% / 100.0% / n=3 | 100.0% / 100.0% / n=3 | 0.0% / 100.0% / n=3 |
| P5 | 33.3% / 66.7% / n=3 | 0.0% / 100.0% / n=3 | 0.0% / 100.0% / n=3 |

### Pre-registered differences

| Difference | Rate a | Rate b | Estimate | 95% cluster-bootstrap interval | Permutation p |
|---|---|---|---|---|---|
| gen - prose | 83.3% | 22.2% | +61.1 pp | [+16.7, +100.0] pp | 0.0004 |
| prose - none | 22.2% | n/a | not available | not available | not available |
| gen - none | 83.3% | n/a | not available | not available | not available |
| rule - none | 0.0% | n/a | not available | not available | not available |
| prule - none | n/a | n/a | not available | not available | not available |
| urule - none | n/a | n/a | not available | not available | not available |
| urule - prule | n/a | n/a | not available | not available | not available |

### Decisions

- H2 (gen - prose): SUPPORTED
- H2b, prose against none: not available
- H2b, gen against none: not available
- H2b, rule against none: not available
- H2b, prule against none: not available
- H2b, urule against none: not available
- H3 (prule against rule): not available
- UCN (urule - prule, no decision): violations n/a, median tokens n/a, median failed check runs n/a

### Leave one rule out, H2 difference (gen - prose)

| Rule left out | gen - prose |
|---|---|
| N1 | +53.3 pp |
| N2 | +53.3 pp |
| N3 | +53.3 pp |
| P1 | +73.3 pp |
| P3 | +53.3 pp |
| P5 | +80.0 pp |

### Mixed-effects logistic regression, violation ~ arm + (1 | rule), reference arm none (descriptive)

Not run: no none arm

### Sensitivity 1: only runs with task success

| Arm | Violation rate | Task success | Runs |
|---|---|---|---|
| prose | 6.7% | 100.0% | 15 |
| gen | 80.0% | 100.0% | 15 |
| rule | 0.0% | 100.0% | 18 |

| Difference | Rate a | Rate b | Estimate | 95% cluster-bootstrap interval | Permutation p |
|---|---|---|---|---|---|
| gen - prose | 80.0% | 6.7% | +73.3 pp | [+33.3, +100.0] pp | 0.0004 |
| prose - none | 6.7% | n/a | not available | not available | not available |
| gen - none | 80.0% | n/a | not available | not available | not available |
| rule - none | 0.0% | n/a | not available | not available | not available |
| prule - none | n/a | n/a | not available | not available | not available |
| urule - none | n/a | n/a | not available | not available | not available |
| urule - prule | n/a | n/a | not available | not available | not available |

H2: SUPPORTED; H2b: prose not available; gen not available; rule not available; prule not available; urule not available

### Sensitivity 2: without rules N2 and P1

| Arm | Violation rate | Task success | Runs |
|---|---|---|---|
| prose | 8.3% | 91.7% | 12 |
| gen | 75.0% | 100.0% | 12 |
| rule | 0.0% | 100.0% | 12 |

| Difference | Rate a | Rate b | Estimate | 95% cluster-bootstrap interval | Permutation p |
|---|---|---|---|---|---|
| gen - prose | 75.0% | 8.3% | +66.7 pp | [+0.0, +100.0] pp | 0.0044 |
| prose - none | 8.3% | n/a | not available | not available | not available |
| gen - none | 75.0% | n/a | not available | not available | not available |
| rule - none | 0.0% | n/a | not available | not available | not available |
| prule - none | n/a | n/a | not available | not available | not available |
| urule - none | n/a | n/a | not available | not available | not available |
| urule - prule | n/a | n/a | not available | not available | not available |

H2: INCONCLUSIVE; H2b: prose not available; gen not available; rule not available; prule not available; urule not available

### Sensitivity 3: a changed rule test counts as a violation

| Arm | Violation rate | Task success | Runs |
|---|---|---|---|
| prose | 22.2% | 83.3% | 18 |
| gen | 83.3% | 83.3% | 18 |
| rule | 0.0% | 100.0% | 18 |

| Difference | Rate a | Rate b | Estimate | 95% cluster-bootstrap interval | Permutation p |
|---|---|---|---|---|---|
| gen - prose | 83.3% | 22.2% | +61.1 pp | [+16.7, +100.0] pp | 0.0004 |
| prose - none | 22.2% | n/a | not available | not available | not available |
| gen - none | 83.3% | n/a | not available | not available | not available |
| rule - none | 0.0% | n/a | not available | not available | not available |
| prule - none | n/a | n/a | not available | not available | not available |
| urule - none | n/a | n/a | not available | not available | not available |
| urule - prule | n/a | n/a | not available | not available | not available |

H2: SUPPORTED; H2b: prose not available; gen not available; rule not available; prule not available; urule not available

### Check arms: runs that ended with a passing visible rule test

| Arm | Runs | Ended with passing rule test | Share | Never ran it | Violation rate, passing | Violation rate, other |
|---|---|---|---|---|---|---|
| rule | 18 | 18 | 100.0% | 0 | 0.0% | n/a |

### Cost for each arm (medians)

| Arm | Tokens | Tool calls | Check invocations | Runs |
|---|---|---|---|---|
| prose | 59498.5 | 17 | n/a | 18 |
| gen | 58241 | 18.5 | 1 | 18 |
| rule | 57812 | 15 | 2 | 18 |

