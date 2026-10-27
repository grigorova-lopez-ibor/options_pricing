# 252 against 504 exercise dates a year

Not part of the paper. `experiments/diagnostics/exercise_frequency_check.py`. Gap to the American put, % of |American| (options with |American| >= 1 % of the largest in the set, outside the exercise region): median / 95th percentile / max. Bermudan = the PDE with exercise on the labels' dates; J-fixed Theta and Charm = what the pathwise labels compute (number of dates fixed while T moves). Noise = median noise of one label at 504/yr (`results/two_per_day`); a gap below the noise of the mean of 100 labels (noise / 10) cannot be seen in any label set.

## 35 check options

| Greek | Bermudan 252/yr | Bermudan 504/yr | noise of one label | noise of the mean of 100 |
|---|---|---|---|---|
| price | 0.031 / 0.111 / 0.140 | 0.015 / 0.056 / 0.070 | 0.23 | 0.023 |
| delta | 0.024 / 0.120 / 0.201 | 0.012 / 0.060 / 0.101 | 1.14 | 0.114 |
| gamma | 0.009 / 0.100 / 0.175 | 0.004 / 0.050 / 0.088 | 9.87 | 0.987 |
| theta | 0.008 / 0.085 / 0.160 | 0.004 / 0.046 / 0.080 | 0.56 | 0.056 |
| charm | 0.041 / 0.428 / 0.552 | 0.022 / 0.210 / 0.425 | 16.61 | 1.661 |
| vega | 0.007 / 0.087 / 0.164 | 0.004 / 0.043 / 0.084 | 2.79 | 0.279 |
| rho | 0.119 / 0.305 / 0.565 | 0.059 / 0.154 / 0.285 | 1.04 | 0.104 |
| phi | 0.116 / 0.296 / 0.552 | 0.058 / 0.151 / 0.278 | 0.96 | 0.096 |

Theta and Charm as the labels compute them (number of dates fixed):

| Greek | J-fixed 252/yr | J-fixed 504/yr | noise of one label | noise of the mean of 100 |
|---|---|---|---|---|
| theta | 0.105 / 0.581 / 0.601 | 0.074 / 0.355 / 0.457 | 0.56 | 0.056 |
| charm | 0.102 / 1.022 / 1.616 | 0.076 / 0.495 / 1.088 | 16.61 | 1.661 |

Exercise region at 252/yr different from the American one: 0 options.

## 40 options from the input ranges

| Greek | Bermudan 252/yr | Bermudan 504/yr | noise of one label | noise of the mean of 100 |
|---|---|---|---|---|
| price | 0.004 / 0.032 / 0.045 | 0.002 / 0.016 / 0.022 | 0.13 | 0.013 |
| delta | 0.002 / 0.025 / 0.033 | 0.001 / 0.012 / 0.016 | 0.61 | 0.061 |
| gamma | 0.002 / 0.014 / 0.027 | 0.001 / 0.007 / 0.014 | 7.67 | 0.767 |
| theta | 0.001 / 0.015 / 0.020 | 0.001 / 0.007 / 0.010 | 0.13 | 0.013 |
| charm | 0.007 / 0.054 / 0.372 | 0.003 / 0.027 / 0.183 | 5.05 | 0.505 |
| vega | 0.002 / 0.015 / 0.047 | 0.001 / 0.008 / 0.024 | 1.50 | 0.150 |
| rho | 0.058 / 0.379 / 0.828 | 0.029 / 0.188 / 0.410 | 0.96 | 0.096 |
| phi | 0.052 / 0.360 / 0.810 | 0.026 / 0.177 / 0.401 | 0.78 | 0.078 |

Theta and Charm as the labels compute them (number of dates fixed):

| Greek | J-fixed 252/yr | J-fixed 504/yr | noise of one label | noise of the mean of 100 |
|---|---|---|---|---|
| theta | 0.037 / 0.129 / 0.338 | 0.033 / 0.139 / 0.268 | 0.13 | 0.013 |
| charm | 0.032 / 0.208 / 0.431 | 0.027 / 0.200 / 0.244 | 5.05 | 0.505 |

Exercise region at 252/yr different from the American one: 0 options.

## Time per label (MultiConfig(vf_time=0.02), 4 processes at once on this machine)

| T | 252/yr (s) | 504/yr (s) | ratio |
|---|---|---|---|
| 0.5 | 21 | 35 | 1.63 |
| 1 | 40 | 76 | 1.91 |
| 2 | 77 | 150 | 1.94 |
