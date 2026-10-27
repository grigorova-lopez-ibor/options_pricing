# Pilot width of S scaled to the option (c0_S_rule="sd") against the fixed width

Not part of the paper. `experiments/diagnostics/pilot_width_check.py`, 6 paired labels per option (same seed for both). fixed = MultiConfig(); sd = MultiConfig(c0_S_rule="sd"): alpha0_S = min(0.25, 1.25 sigma sqrt(T)) S0. Per part and sigma sqrt(T) bin: bias = mean over options of the signed relative error of the option's mean label (t), typical error = mean |relative error| of one label; options with |ref| < 1 % of the Greek's largest |ref| in the part, and labels in the exercise region, left out.

## grid, sigma sqrt(T) sd < 0.1: 4 options; mean alpha_S fixed 2.16, sd 1.41

| Greek | bias % fixed (t) | bias % sd (t) | typical % fixed | typical % sd |
|---|---|---|---|---|
| price | +0.09 (+0.6) | -0.02 (-0.4) | 0.4 | 0.4 |
| delta | +0.07 (+0.2) | +0.29 (+0.7) | 1.6 | 1.5 |
| gamma | -0.83 (-0.7) | -0.31 (-0.9) | 7.3 | 8.8 |
| theta | +3.78 (+1.0) | +1.47 (+1.0) | 19.5 | 25.3 |
| vega | -1.74 (-1.7) | -1.47 (-2.0) | 2.9 | 2.8 |
| volga | -48.95 (-1.3) | -27.43 (-1.5) | 60.9 | 56.2 |
| vanna | -48.48 (-1.7) | -23.13 (-1.5) | 82.4 | 74.6 |
| rho | -0.41 (-1.2) | -0.22 (-1.1) | 1.1 | 0.8 |
| phi | +0.37 (+1.1) | +0.19 (+1.0) | 1.0 | 0.8 |

## grid, sigma sqrt(T) 0.1-0.2: 14 options; mean alpha_S fixed 2.05, sd 2.04

| Greek | bias % fixed (t) | bias % sd (t) | typical % fixed | typical % sd |
|---|---|---|---|---|
| price | -0.09 (-1.6) | -0.10 (-1.4) | 0.2 | 0.2 |
| delta | -0.02 (-0.2) | +0.03 (+0.3) | 0.9 | 0.8 |
| gamma | +0.76 (+0.7) | +1.18 (+1.2) | 6.1 | 6.2 |
| theta | -0.14 (-0.0) | -1.53 (-0.7) | 21.0 | 21.1 |
| vega | -0.32 (-0.7) | -0.28 (-0.5) | 2.5 | 2.8 |
| volga | -18.98 (-2.0) | -11.57 (-1.0) | 79.3 | 89.9 |
| vanna | -40.71 (-1.7) | -42.51 (-1.7) | 73.0 | 70.6 |
| rho | -0.13 (-0.9) | -0.13 (-0.8) | 0.7 | 0.7 |
| phi | +0.10 (+0.7) | +0.10 (+0.6) | 0.6 | 0.6 |

## grid, sigma sqrt(T) >= 0.2: 12 options; mean alpha_S fixed 4.02, sd 4.02

| Greek | bias % fixed (t) | bias % sd (t) | typical % fixed | typical % sd |
|---|---|---|---|---|
| price | -0.04 (-1.1) | -0.04 (-1.1) | 0.2 | 0.2 |
| delta | -0.02 (-0.1) | -0.02 (-0.1) | 1.0 | 1.0 |
| gamma | -1.69 (-1.1) | -1.69 (-1.1) | 9.8 | 9.8 |
| theta | +8.26 (+1.1) | +8.26 (+1.1) | 26.5 | 26.5 |
| vega | +0.07 (+0.2) | +0.07 (+0.2) | 1.9 | 1.9 |
| volga | -39.88 (-1.4) | -39.88 (-1.4) | 153.2 | 153.2 |
| vanna | +40.20 (+1.0) | +40.20 (+1.0) | 183.9 | 183.9 |
| rho | -0.50 (-2.8) | -0.50 (-2.8) | 0.9 | 0.9 |
| phi | +0.37 (+2.3) | +0.37 (+2.3) | 0.8 | 0.8 |

## sample, sigma sqrt(T) sd < 0.1: 4 options; mean alpha_S fixed 3.72, sd 2.40

| Greek | bias % fixed (t) | bias % sd (t) | typical % fixed | typical % sd |
|---|---|---|---|---|
| price | +0.00 (+nan) | -0.03 (+nan) | 0.2 | 0.2 |
| delta | +0.06 (+0.4) | -0.15 (-0.5) | 0.5 | 0.6 |
| gamma | -0.81 (-1.1) | -2.05 (-1.6) | 2.5 | 3.3 |
| theta | +1.00 (+0.8) | +0.90 (+1.1) | 3.2 | 2.9 |
| vega | +0.01 (+0.0) | -0.17 (-0.4) | 1.2 | 1.5 |
| volga | +287.90 (+1.0) | +27.10 (+1.0) | 1111.4 | 333.0 |
| vanna | -37.37 (-1.0) | -2.68 (-0.8) | 57.8 | 40.0 |
| rho | -0.38 (-2.0) | -0.34 (-2.9) | 0.8 | 1.0 |
| phi | +0.33 (+1.5) | +0.29 (+2.1) | 0.7 | 0.9 |

## sample, sigma sqrt(T) 0.1-0.2: 3 options; mean alpha_S fixed 8.12, sd 7.49

| Greek | bias % fixed (t) | bias % sd (t) | typical % fixed | typical % sd |
|---|---|---|---|---|
| price | +0.04 (+0.9) | +0.03 (+0.7) | 0.1 | 0.1 |
| delta | +1.36 (+1.1) | +1.22 (+1.1) | 0.7 | 0.7 |
| gamma | -0.49 (-0.9) | -1.77 (-1.8) | 2.2 | 2.1 |
| theta | +0.50 (+0.9) | +1.72 (+1.8) | 2.1 | 2.1 |
| vega | +0.17 (+3.1) | +0.21 (+1.0) | 0.6 | 0.8 |
| volga | -4.10 (+nan) | -6.12 (+nan) | 8.6 | 7.0 |
| vanna | -9.74 (-0.7) | -6.74 (-0.8) | 29.2 | 34.0 |
| rho | -0.30 (-0.4) | -0.57 (-0.9) | 0.9 | 1.0 |
| phi | +0.21 (+0.3) | +0.44 (+0.8) | 0.8 | 0.8 |

## sample, sigma sqrt(T) >= 0.2: 16 options; mean alpha_S fixed 8.70, sd 8.70

| Greek | bias % fixed (t) | bias % sd (t) | typical % fixed | typical % sd |
|---|---|---|---|---|
| price | -0.02 (-0.9) | -0.02 (-0.9) | 0.1 | 0.1 |
| delta | +0.08 (+1.2) | +0.08 (+1.2) | 0.6 | 0.6 |
| gamma | -1.53 (-1.6) | -1.53 (-1.6) | 6.6 | 6.6 |
| theta | +1.94 (+1.5) | +1.94 (+1.5) | 7.9 | 7.9 |
| vega | -0.10 (-0.5) | -0.10 (-0.5) | 1.2 | 1.2 |
| volga | +13.70 (+0.5) | +13.70 (+0.5) | 133.4 | 133.4 |
| vanna | +0.89 (+0.2) | +0.89 (+0.2) | 24.9 | 24.9 |
| rho | -0.08 (-0.6) | -0.08 (-0.6) | 0.8 | 0.8 |
| phi | +0.05 (+0.5) | +0.05 (+0.5) | 0.6 | 0.6 |

Mean seconds per label (one core, 4 processes at once): fixed 11.6, sd 11.5.
