# Bias vs number of exercise dates a year and number of paths

Which combination of exercise dates a year (126, 252, 504, 1008) and main paths
(75k, 150k, 300k, 600k) gives the in-sample label the best accuracy for its cost?
Full tables for every Greek and combination, with the time per label: `report.md`.

## Set-up

* In-sample label (one (S, sigma) run, pathwise Rho, Phi, Theta; value-function label
  at 1/50 year; exercise_bound=False as in `results/two_per_day`), puts, S0 = 40.
* 15 options across the input ranges (table below) x 30 labels at each of the 16
  combinations = 7,200 labels; pilot 100k paths; the same seeds at every combination.
* References: American PDE, and the Bermudan PDE at each number of dates a year.
  Each label's bias splits into
  * **bias from Bermudan approximation** = Bermudan − American (exercise on the grid
    dates only; exact, no noise), and
  * **simulation bias** = mean of the labels − Bermudan (Monte Carlo / LSM: exercise
    rule fitted on the same paths, finite regression basis, dispersed-start
    regression, pathwise approximation).
* **Noise floor (false bias)** = √(2/π) × se, se = sd of one label / √30: the |bias|
  an unbiased label would show from the noise left in the mean of 30 labels (the
  half-normal analogue of the Rician noise floor). A bias near it is not detectable;
  more labels lower it like 1/√labels. The noise of a single label falls only with
  more paths.
* Run on the BU SCC (about 100 CPU hours): `experiments/diagnostics/freq_paths_grid.py`,
  `scc/freq_paths.qsub`, `scc/freq_paths_ref.qsub`, `scc/freq_paths_big.qsub`; report
  `experiments/diagnostics/freq_paths_report.py --out results/diagnostics/bias_vs_dates_paths
  --dest results/diagnostics/bias_vs_dates_paths`. Data: `raw/labels.parquet`,
  `raw/reference.parquet`; per option and combination: `per_option.csv`.

| id | T | sigma | r | d | K | S0/K |
|---|---|---|---|---|---|---|
| 0 | 0.5 | 20% | 5.0% | 0% | 40 | 1.00 |
| 1 | 0.5 | 20% | 5.0% | 0% | 44 | 0.91 |
| 2 | 0.5 | 20% | 5.0% | 0% | 36 | 1.11 |
| 3 | 1/6 | 20% | 5.0% | 0% | 40 | 1.00 |
| 4 | 1/6 | 40% | 3.0% | 0% | 46 | 0.87 |
| 5 | 2 | 20% | 5.0% | 0% | 40 | 1.00 |
| 6 | 2 | 10% | 3.0% | 0% | 44 | 0.91 |
| 7 | 2 | 40% | 2.0% | 1% | 34 | 1.18 |
| 8 | 1 | 5% | 3.0% | 0% | 40.5 | 0.99 |
| 9 | 1 | 50% | 4.0% | 2% | 40 | 1.00 |
| 10 | 1 | 20% | 1.0% | 4% | 40 | 1.00 |
| 11 | 1 | 20% | 5.0% | 5% | 44 | 0.91 |
| 12 | 1 | 20% | 0.5% | 0% | 40 | 1.00 |
| 13 | 0.5 | 30% | 3.0% | 1% | 50 | 0.80 |
| 14 | 1.5 | 15% | 5.0% | 2% | 38 | 1.05 |

## Time per label (s, one core)

| Dates/yr \ main paths | 75k | 150k | 300k | 600k |
|---|---|---|---|---|
| 126 | 6 | 8 | 15 | 29 |
| 252 | 11 | 16 | 28 | 55 |
| 504 | 21 | 31 | 54 | 106 |
| 1008 | 42 | 63 | 103 | 208 |

Linear in main paths x exercise dates plus a few seconds of fixed cost. Peak memory
about 3 GB up to 504/yr with 300k paths, about 10 GB at 504/yr with 600k and at
1008/yr with 300k-600k (T = 2).

## Bias from Bermudan approximation (mean |Bermudan − American|, %)

| Greek | 126/yr | 252/yr | 504/yr | 1008/yr |
|---|---|---|---|---|
| Price | 0.06 | 0.03 | 0.02 | 0.01 |
| Delta | 0.05 | 0.02 | 0.01 | 0.01 |
| Theta | 0.25 | 0.06 | 0.02 | 0.02 |
| Rho | 0.63 | 0.32 | 0.15 | 0.08 |
| Phi | 0.61 | 0.31 | 0.14 | 0.07 |
| Charm | 1.98 | 0.72 | 0.15 | 0.09 |
| Gamma, Vega, Vanna | ≤ 0.11 | ≤ 0.05 | ≤ 0.03 | ≤ 0.01 |
| Volga | 0.52 | 0.33 | 0.26 | 0.12 |

It halves each time the dates double. At 126 and 252 a year it is still visible for
Theta, Rho, Phi and Charm; at 504 it is below every other error.

## Findings

* **Price**: the simulation bias is positive (foresight of the in-sample rule) and
  about halves when the paths double: 0.20 → 0.13 → 0.09 → 0.05 % at 504/yr. The total
  bias is 0.04-0.08 % at about 55 s per label (252/yr with 600k or 504/yr with 300k)
  and 0.02-0.05 % at 1008/yr with 300k-600k (100-200 s); the noise of one price label
  is 0.18 % at 300k and 0.13 % at 600k paths at every frequency.
* **Delta**: simulation bias about 0.2 % (Delta slightly low), no longer falling beyond
  300k paths; the Bermudan approximation is ≤ 0.05 %.
* **Theta, Rho, Phi**: a simulation bias of 0.6-1.2 % that does not fall with paths
  (method bias of the pathwise derivatives), concentrated in a few options: option 6
  (T = 2, sigma = 10 %, K = 44) Rho about −4 to −7 % at every combination, and its
  Theta from −1.7 % (126/yr) to −6.8 % (1008/yr); option 1 (K = 44, T = 0.5) Rho
  about −2 %; option 13 (K = 50) Rho from +0.4 % to +2.8 % as the dates increase.
  Theta is worse at 1008/yr than at 504/yr.
* **Gamma, Vega, Vanna, Charm**: the simulation bias is at the noise floor in most
  combinations (not detectable with 30 labels).
* **Volga**: a large in-sample bias at 75k-150k paths (56-109 %) that falls with paths
  to the noise floor (15-20 %) at 300k-600k with 504 or 1008 dates a year; 9 options
  only.

**Choice.** 504 exercise dates a year: the bias from the Bermudan approximation is
then below every other error, and 1008 doubles the cost to remove what is no longer
visible. 300k main paths: 600k halves the price bias (about 0.09 → 0.05 %) and lowers
the noise by 1/√2 for twice the time, but does not improve Delta, Theta, Rho or Phi,
whose remaining bias is a method bias in a few options. Compute beyond 300k paths is
better spent on more labels. 15 options and 30 labels each: the exact Bermudan
approximation and the trends are solid; the per-option simulation biases rest on 3-4
hard options.
