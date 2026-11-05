# Common random numbers against independent paths

Not part of the paper. `experiments/diagnostics/insample_studies.py crn`: 2,000 options from the training-set ranges at 50 dates a year, labelled twice with the default in-sample label: with a fresh seed per option (independent) and with one seed for every option (common random numbers, the same random shocks for all), against the Bermudan PDE. The network is stood in for by two smoothers of the label errors over the inputs (S0/K, σ, r, d, T scaled to [0, 1]): the mean over each option's k nearest neighbours, and a cubic polynomial fitted to all 2,000. What a smoother leaves is the error a network trained on these labels would keep. Errors in % of |PDE|; options with |PDE| < 1 % of the largest and exact labels left out per Greek.

| Greek | mode | one label: median abs. / RMS | corr. with nearest neighbour | mean of 10 nearest | mean of 50 nearest | cubic fit |
|---|---|---|---|---|---|---|
| price | independent | 0.0454 / 0.15 | +0.05 | 0.0662 | 0.0496 | 0.0551 |
| price | common | 0.0425 / 0.147 | +0.14 | 0.061 | 0.0435 | 0.0542 |
| delta | independent | 0.247 / 0.851 | -0.05 | 0.26 | 0.13 | 0.138 |
| delta | common | 0.267 / 0.815 | +0.12 | 0.279 | 0.164 | 0.175 |
| gamma | independent | 2.6 / 12.2 | +0.14 | 3.65 | 1.69 | 2.39 |
| gamma | common | 2.59 / 12.1 | -0.07 | 3.68 | 1.57 | 2.58 |
| theta | independent | 0.0821 / 5.18 | +0.22 | 1.07 | 0.592 | 1.43 |
| theta | common | 0.0846 / 2.45 | +0.10 | 0.54 | 0.294 | 0.667 |
| vega | independent | 0.542 / 5.01 | +0.16 | 1.63 | 0.73 | 1.1 |
| vega | common | 0.609 / 15.8 | -0.13 | 4.22 | 1.64 | 3.43 |
| volga | independent | 6.56 / 161 | +0.15 | 63.3 | 30.5 | 35.2 |
| volga | common | 7.83 / 136 | +0.06 | 55.7 | 34.3 | 35.3 |
| vanna | independent | 7.56 / 40 | -0.05 | 14.7 | 6.89 | 8.86 |
| vanna | common | 7.93 / 43.1 | -0.09 | 15.6 | 8.37 | 9.67 |
| rho | independent | 0.514 / 3.03 | -0.04 | 0.932 | 0.498 | 0.622 |
| rho | common | 0.463 / 3.14 | -0.01 | 0.925 | 0.477 | 0.74 |
| phi | independent | 0.432 / 2.91 | -0.05 | 0.87 | 0.447 | 0.551 |
| phi | common | 0.395 / 3.01 | -0.03 | 0.865 | 0.426 | 0.682 |

RMS columns are sensitive to single options with near-zero reference values (e.g. one option at σ = 3.5 % has a Vega error of 620 % with common random numbers and 63 % without); the medians are the robust comparison.

Time per label: common 7.1 s, independent 7.0 s.

