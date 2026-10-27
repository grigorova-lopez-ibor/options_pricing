# In-sample label: noise and bias against the number of labels and of paths

Default label of the `carlos` branch (one (S, sigma) run, pathwise r, d, Theta),
**in-sample** version (exercise rule fitted on the main paths), puts with 504
exercise dates a year, value-function label at 1/50 year; against the American
PDE; % of |PDE|. Not part of the paper. Data: `results/two_per_day/raw/` (labels)
and `paths_raw.csv` (paths); see `summary.md` for the default and out-of-sample
labels.

## 1. More labels

300k main paths; 75 options x 100 labels (`results/two_per_day`), the mean of n
labels per option; medians over the options. Cells: total error of the mean of
n labels / pure noise sd/sqrt(n).

| Greek | n = 1 | n = 5 | n = 25 | n = 100 | pure bias (unchanged by n) |
|---|---|---|---|---|---|
| price | 0.19 / 0.18 | 0.10 / 0.08 | 0.057 / 0.037 | 0.043 / 0.018 | 0.03 |
| Delta | 0.96 / 0.96 | 0.44 / 0.43 | 0.22 / 0.19 | 0.089 / 0.096 | 0.05 |
| Gamma | 9.7 / 9.8 | 4.2 / 4.4 | 1.9 / 2.0 | 1.06 / 0.98 | 0.56 |
| Theta | 0.48 / 0.44 | 0.26 / 0.20 | 0.17 / 0.089 | 0.155 / 0.044 | 0.15 |
| Vega | 2.4 / 2.5 | 1.15 / 1.11 | 0.52 / 0.50 | 0.23 / 0.25 | 0.06 |
| Volga | 126 / 116 | 58 / 52 | 32 / 23 | 24 / 12 | 19 |
| Vanna | 38 / 36 | 16 / 16 | 8.1 / 7.2 | 2.7 / 3.6 | 0 |
| Rho | 1.21 / 1.11 | 0.63 / 0.50 | 0.44 / 0.22 | 0.31 / 0.11 | 0.29 |
| Phi | 1.03 / 1.00 | 0.58 / 0.45 | 0.36 / 0.20 | 0.26 / 0.10 | 0.25 |

## 2. More main paths

5 check options (T 0.5 and 1, sigma 20-40 %, K 36/40/44) x 30 labels, pilot fixed
at 100k, the same seeds at every path count. Cells: noise of one label (median
over the options) / signed bias ± se (mean over the 5 options). Noise exponent:
slope of log noise on log paths (-0.5 = 1/sqrt(N)).

| Greek | 75k | 150k | 300k | 600k | noise exponent |
|---|---|---|---|---|---|
| price | 0.44 / +0.15 ± 0.05 | 0.38 / +0.08 ± 0.04 | 0.24 / +0.02 ± 0.02 | 0.19 / +0.02 ± 0.02 | -0.44 |
| Delta | 2.1 / -0.36 ± 0.17 | 1.5 / -0.10 ± 0.12 | 0.95 / -0.02 ± 0.08 | 0.67 / +0.01 ± 0.06 | -0.55 |
| Gamma | 13.6 / +1.4 ± 1.4 | 10.4 / -1.4 ± 1.0 | 8.2 / -0.4 ± 0.7 | 5.4 / -0.6 ± 0.5 | -0.43 |
| Theta | 1.24 / -0.34 ± 0.15 | 1.04 / -0.32 ± 0.11 | 0.69 / -0.31 ± 0.08 | 0.50 / -0.23 ± 0.06 | -0.45 |
| Vega | 7.1 / +0.5 ± 1.0 | 5.3 / -0.2 ± 0.7 | 3.7 / -0.7 ± 0.5 | 2.4 / -0.4 ± 0.4 | -0.53 |
| Volga | 503 / +173 ± 65 | 441 / +72 ± 56 | 256 / +63 ± 38 | 157 / +19 ± 22 | -0.58 |
| Vanna | 159 / +58 ± 82 | 110 / +25 ± 52 | 79 / +27 ± 33 | 65 / +2 ± 23 | -0.44 |
| Rho | 2.1 / -0.47 ± 0.20 | 1.5 / -0.81 ± 0.16 | 0.97 / -0.85 ± 0.13 | 0.74 / -0.99 ± 0.10 | -0.52 |
| Phi | 2.0 / +0.44 ± 0.19 | 1.4 / +0.77 ± 0.15 | 0.92 / +0.79 ± 0.13 | 0.69 / +0.91 ± 0.09 | -0.53 |

## Notes

- Labels: noise falls like 1/sqrt(n) and the bias stays fixed. The in-sample
  bias is small (price 0.03 %, Delta 0.05 %, Vega 0.06 %), so price and Delta keep
  improving up to about 25-100 labels (the default label levels off at about
  0.08 % and 0.11 %).
- Paths: noise falls like 1/sqrt(paths) (exponent -0.43 to -0.58). The foresight
  bias shrinks with paths: price +0.15 % -> +0.02 %, Delta -0.36 % -> 0, Volga
  +173 % -> +19 %. The Rho/Phi bias does not shrink: it comes mostly from one
  in-the-money option (K = 44, T = 0.5), about -3.5 % on Rho at every path count.
- Volga in-sample keeps a large per-option bias (19 %) at 300k paths, so Volga
  should stay out-of-sample.
