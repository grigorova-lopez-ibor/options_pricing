# Skipping exercise dates where no path can be exercised

Not part of the paper. `experiments/diagnostics/dead_dates_check.py`: 24 options from the training-set ranges (seed 77), the production label (252 dates a year, 600k main + 100k pilot paths, in sample, exercise bound on), each labelled from the same seed without and with `MultiConfig(skip_dead_dates=True)`, in the same process one after the other. A date is skipped when no in-the-money path can pass the exercise bound (payoff ≥ European value), checked with one European value at (min S, min σ, max r, min d) of the in-the-money paths; its regression would be thrown away, so the label must be identical.

**Identical labels:** 24 of 24 options (largest absolute difference over all outputs: 0).

1 options are in the no-early-exercise region (exact label, no simulation) and are left out of the times.

| options | n | time without (s) | time with (s) | saving |
|---|---|---|---|---|
| all simulated | 23 | 1403 | 1270 | 9 % |
| r < d | 10 | 741 | 598 | 19 % |
| r ≥ d | 13 | 662 | 672 | -1 % |

Per option (saving = 1 − time with / time without):

| id | S0/K | σ | r | d | T | without (s) | with (s) | saving |
|---|---|---|---|---|---|---|---|---|
| 4 | 1.05 | 32.4 % | 0.50 % | 3.75 % | 0.18 | 8.2 | 3.3 | 59 % |
| 18 | 0.94 | 21.2 % | 2.25 % | 2.25 % | 0.27 | 19.9 | 19.8 | 0 % |
| 11 | 1.09 | 15.2 % | 3.00 % | 2.50 % | 0.85 | 22.0 | 22.0 | 0 % |
| 9 | 0.86 | 46.8 % | 5.00 % | 0.75 % | 0.28 | 23.4 | 24.1 | -3 % |
| 23 | 1.18 | 30.0 % | 4.75 % | 1.50 % | 1.03 | 28.5 | 29.4 | -3 % |
| 3 | 1.03 | 37.6 % | 4.50 % | 4.25 % | 0.59 | 29.0 | 29.9 | -3 % |
| 8 | 1.20 | 16.8 % | 1.00 % | 4.75 % | 1.49 | 31.8 | 14.0 | 56 % |
| 14 | 0.83 | 52.1 % | 0.25 % | 1.25 % | 0.47 | 32.6 | 20.1 | 38 % |
| 21 | 0.97 | 26.4 % | 3.00 % | 0.50 % | 0.57 | 35.1 | 35.6 | -2 % |
| 15 | 1.12 | 25.6 % | 3.75 % | 3.00 % | 1.09 | 37.1 | 37.6 | -1 % |
| 12 | 1.01 | 6.5 % | 2.00 % | 0.50 % | 0.91 | 39.2 | 41.0 | -5 % |
| 6 | 0.89 | 28.8 % | 2.25 % | 4.50 % | 0.72 | 47.6 | 41.1 | 14 % |
| 20 | 1.08 | 57.1 % | 1.50 % | 3.75 % | 1.30 | 63.1 | 62.5 | 1 % |
| 19 | 1.01 | 47.7 % | 3.25 % | 3.25 % | 1.36 | 74.5 | 75.8 | -2 % |
| 0 | 1.14 | 49.8 % | 1.25 % | 1.75 % | 1.74 | 80.9 | 80.8 | 0 % |
| 5 | 0.99 | 2.1 % | 4.25 % | 2.00 % | 1.39 | 81.7 | 83.0 | -2 % |
| 1 | 0.82 | 20.0 % | 2.75 % | 2.50 % | 1.00 | 86.8 | 87.9 | -1 % |
| 7 | 1.15 | 55.3 % | 3.50 % | 1.00 % | 1.81 | 89.0 | 88.8 | 0 % |
| 2 | 0.92 | 11.1 % | 0.75 % | 0.25 % | 1.22 | 95.8 | 96.9 | -1 % |
| 13 | 0.93 | 36.2 % | 3.50 % | 4.00 % | 1.64 | 104.3 | 104.3 | -0 % |
| 10 | 0.96 | 41.4 % | 1.75 % | 3.25 % | 1.94 | 112.9 | 112.7 | 0 % |
| 22 | 0.87 | 3.8 % | 1.25 % | 3.00 % | 1.66 | 113.6 | 14.3 | 87 % |
| 17 | 0.85 | 9.1 % | 4.00 % | 5.00 % | 1.84 | 146.1 | 145.1 | 1 % |
