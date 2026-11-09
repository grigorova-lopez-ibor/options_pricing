# 252 exercise dates a year with 600k paths on the 35 check and 40 range options

The combination chosen from `results/diagnostics/bias_vs_dates_paths` (same cost as
504/yr with 300k paths), in-sample label, run on the options of `results/two_per_day`
with 100 labels each (7,500 labels, 125 CPU hours on the BU SCC). Tables with the
MAE of the bias and its 95 % CI, the mean signed bias and its 95 % CI, the SD over the
options, the noise floor and the 504/300k comparison: `report.md`; histograms of the
per-option bias: `hist_check.png`, `hist_random.png`.

**Time per label** 59 s (check options) and 61 s (range options) on one core;
**peak memory** 3.0 GB.

## MAE of the bias (%), this run [95 % CI] vs the 504/yr, 300k in-sample label

| Greek | check: 252/600k | check: 504/300k | range: 252/600k | range: 504/300k |
|---|---|---|---|---|
| Price | 0.045 [0.033, 0.058] | 0.043 [0.031, 0.056] | **0.025** [0.017, 0.035] | 0.051 [0.037, 0.066] |
| Delta | **0.095** [0.072, 0.119] | 0.183 [0.128, 0.239] | 0.081 [0.045, 0.133] | 0.132 [0.086, 0.188] |
| Gamma | **0.76** [0.56, 0.97] | 1.34 [0.99, 1.73] | 1.6 [0.6, 3.3] | 7.5 [1.0, 20] |
| Theta | 0.43 [0.30, 0.58] | 0.34 [0.24, 0.46] | 0.094 [0.058, 0.136] | 0.157 [0.098, 0.222] |
| Charm | 2.8 [1.9, 3.9] | 4.2 [2.8, 5.7] | 0.92 [0.55, 1.37] | 1.5 [0.7, 2.5] |
| Vega | 0.24 [0.18, 0.32] | 0.30 [0.23, 0.38] | 0.16 [0.11, 0.22] | 0.27 [0.20, 0.36] |
| Volga | 18.8 [10.6, 29] | 37 [23, 53] | **24.5** [14.8, 36] | 45 [28, 66] |
| Vanna | 5.8 [3.0, 9.0] | 13.7 [5.9, 25.6] | 2.9 [1.8, 4.2] | 3.8 [2.5, 5.3] |
| Rho | 0.64 [0.39, 0.93] | 0.47 [0.27, 0.72] | 0.38 [0.23, 0.57] | 0.55 [0.38, 0.75] |
| Phi | 0.58 [0.34, 0.87] | 0.44 [0.26, 0.66] | 0.31 [0.19, 0.46] | 0.46 [0.30, 0.63] |
| dDelta/dr | 6.9 [2.7, 12.6] | 7.1 [3.2, 12.3] | 4.5 [2.5, 6.9] | 8.3 [3.9, 13.7] |
| dDelta/dd | 9.1 [2.6, 19.9] | 9.8 [2.6, 22] | 6.3 [2.7, 10.7] | 12.6 [4.0, 24.7] |

Bold: the two 95 % intervals do not overlap.

## Findings

* 252/yr with 600k paths is as good as or better than 504/yr with 300k for almost
  every Greek at about the same cost: clearly better for Delta and Gamma (check
  options), Price (range options) and Volga (both sets); lower but within the
  intervals for Vega, Charm, Vanna and the cross terms; the noise of one label is
  lower by about 1/√2.
* Check options (mostly r = 6 %, strong early exercise): the price bias is now mostly
  the Bermudan approximation (|Bermudan(252) − American| = 0.043 % against an MAE of
  0.045 %; mean bias −0.02 %). Theta (0.43 vs 0.34 %), Rho (0.64 vs 0.47 %) and Phi
  (0.58 vs 0.44 %) are slightly worse than at 504/yr, within the intervals; the
  Bermudan approximation of Rho and Phi is about 0.15 %.
* Range options: everything is equal or better, Rho and Phi included.
* Volga stays the least accurate output (MAE about 20-25 %, mean bias +14 to +23 %),
  half of the 504/300k value.
