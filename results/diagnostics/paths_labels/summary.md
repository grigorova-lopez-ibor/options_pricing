# Noise and bias against the number of paths and the number of labels

Default label of the `carlos` branch (one (S, sigma) run, pathwise r, d, Theta),
puts with 504 exercise dates a year, value-function label at 1/50 year; against
the American PDE. Not part of the paper.

* **Labels** (`labels_subsample.py`, `labels_tables.md`): the 100 labels per option
  of `results/two_per_day` (75 options) subsampled to n labels; medians over the
  options of the error of the mean of n labels (total), its noise sd/sqrt(n), and
  the option's noise-corrected bias.
* **Paths** (`paths_run.py`, `paths_analyse.py`, `paths_tables.md`, `paths_raw.csv`):
  5 check options (T 0.5 and 1, sigma 20-40 %, K 36/40/44), 30 labels each at
  75k, 150k, 300k and 600k main paths (pilot fixed at 100k), the same seeds at every
  path count. Noise = median sd of one label; noise exponent = slope of log noise on
  log paths (-0.5 = 1/sqrt(N)); bias = mean over the 5 options of the signed
  relative bias (± se).

## More labels (measured)

| Greek | noise of the mean of n labels | per-option bias | total error, n = 1 / 5 / 25 / 100 |
|---|---|---|---|
| price | 0.18 % / sqrt(n) | 0.08 % (unchanged) | 0.20 / 0.11 / 0.088 / 0.081 % |
| Delta | 0.92 % / sqrt(n) | 0.11 % | 0.96 / 0.45 / 0.25 / 0.17 % |
| Gamma | 9.2 % / sqrt(n) | 0.7 % | 9.4 / 4.3 / 2.1 / 1.1 % |
| Theta | 0.39 % / sqrt(n) | 0.18 % | 0.49 / 0.30 / 0.22 / 0.19 % |
| Vega | 2.4 % / sqrt(n) | 0 | 2.5 / 1.1 / 0.53 / 0.22 % |
| Rho | 1.1 % / sqrt(n) | 0.31 % | 1.16 / 0.61 / 0.42 / 0.33 % |
| Phi | 0.96 % / sqrt(n) | 0.26 % | 1.01 / 0.56 / 0.37 / 0.27 % |
| Volga | 120 % / sqrt(n) | 0.4 % | 118 / 56 / 23 / 9 % |
| Vanna | 37 % / sqrt(n) | 0 | 39 / 18 / 8.6 / 2.9 % |

Noise falls exactly like 1/sqrt(n); the bias does not change; the total levels
off at the bias (price after ~5-10 labels, Theta, Rho, Phi after ~5-25, Delta
~25-50, Gamma ~100; Vega, Vanna, Volga still noise-limited at 100).

## More main paths (experiment)

Time per label: 17 / 26 / 46 / 95 s at 75k / 150k / 300k / 600k (4 processes on
one machine), proportional to the paths plus a fixed pilot cost.

Noise of one label (default label, %) and noise exponent (default / in-sample /
out-of-sample):

| Greek | 75k | 150k | 300k | 600k | exponent |
|---|---|---|---|---|---|
| price | 0.44 | 0.36 | 0.24 | 0.18 | -0.44 / -0.44 / -0.45 |
| Delta | 1.9 | 1.5 | 0.97 | 0.70 | -0.51 / -0.55 / -0.50 |
| Gamma | 12.7 | 9.8 | 7.9 | 5.4 | -0.41 / -0.43 / -0.43 |
| Theta | 1.18 | 0.85 | 0.63 | 0.56 | -0.37 / -0.45 / -0.19 |
| Vega | 6.8 | 4.4 | 3.5 | 2.3 | -0.49 / -0.53 / -0.49 |
| Rho | 1.6 | 1.2 | 0.99 | 0.88 | -0.29 / -0.52 / -0.09 |
| Phi | 1.4 | 1.1 | 0.90 | 0.82 | -0.27 / -0.53 / -0.09 |
| Volga | 523 | 418 | 244 | 155 | -0.60 / -0.58 / -0.60 |
| Vanna | 165 | 99 | 78 | 54 | -0.52 / -0.44 / -0.52 |

Signed bias (mean over the 5 options, %, ± se):

| | 75k | 150k | 300k | 600k |
|---|---|---|---|---|
| price oos | -0.24 ± 0.05 | -0.20 ± 0.04 | -0.23 ± 0.03 | -0.20 ± 0.02 |
| price ins | +0.15 ± 0.05 | +0.08 ± 0.04 | +0.02 ± 0.02 | +0.02 ± 0.02 |
| price default | -0.04 ± 0.05 | -0.06 ± 0.04 | -0.10 ± 0.02 | -0.09 ± 0.02 |
| Delta oos | +0.28 ± 0.15 | +0.42 ± 0.12 | +0.40 ± 0.08 | +0.40 ± 0.06 |
| Delta ins | -0.36 ± 0.17 | -0.10 ± 0.12 | -0.02 ± 0.08 | +0.01 ± 0.06 |
| Rho oos | -0.36 ± 0.25 | -0.42 ± 0.25 | -0.42 ± 0.24 | -0.43 ± 0.24 |
| Rho ins | -0.47 ± 0.20 | -0.81 ± 0.16 | -0.85 ± 0.13 | -0.99 ± 0.10 |
| Phi ins | +0.44 ± 0.19 | +0.77 ± 0.15 | +0.79 ± 0.13 | +0.91 ± 0.09 |

Findings: noise falls like 1/sqrt(paths) for price, Delta, Gamma, Vega, Volga,
Vanna and for the in-sample Theta, Rho, Phi; the out-of-sample Theta, Rho, Phi
hardly improve (exponent -0.1 to -0.2): their noise comes from the exercise rule
fitted on the fixed 100k pilot. The out-of-sample price/Delta bias (-0.2 % /
+0.4 %) does not shrink with main paths (same pilot rule); the in-sample one
vanishes by 300k (foresight bias ~ 1/N), so the average becomes more biased with
more paths. On these 5 options the Rho/Phi bias (-0.4 to -1 % / +0.4 to +0.9 %)
does not shrink with paths, and the in-sample one grows.
