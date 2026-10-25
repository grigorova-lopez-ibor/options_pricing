# Default label (pathwise r and d) against design D2

Not part of the paper. `experiments/diagnostics/pathwise_label_check.py`. new = MultiConfig() (one (S, sigma) run, 300k main + 100k pilot, pathwise r and d Greeks); D2 = the label before the carlos branch ((S, sigma), (S, r), (S, d), 100k + 100k each). Per part: bias = mean over options of the signed relative error of the option's mean label (± se over options), typical error = mean |relative error| of one label, median error = its median; options with |ref| < 1 % of the Greek's largest |ref| left out; options in the exercise region (exact labels) left out.

## grid: 12 options, 10 labels each

| Greek | bias % new (t) | bias % D2 (t) | typical % new | typical % D2 | median % new | median % D2 |
|---|---|---|---|---|---|---|
| price | -0.02 (-1.1) | +0.05 (+2.3) | 0.1 | 0.1 | 0.1 | 0.1 |
| delta | +0.09 (+1.1) | -0.06 (-1.1) | 0.6 | 0.5 | 0.4 | 0.4 |
| gamma | -0.37 (-0.4) | +0.55 (+0.6) | 6.2 | 6.2 | 5.3 | 4.8 |
| theta | +0.29 (+0.3) | -0.58 (-0.6) | 6.6 | 6.7 | 5.6 | 4.8 |
| vega | +0.30 (+0.9) | +0.06 (+0.2) | 1.9 | 3.0 | 1.3 | 2.5 |
| volga | -144.83 (-1.0) | -223.27 (-0.9) | 711.0 | 1170.8 | 76.4 | 123.3 |
| vanna | +6.57 (+0.7) | +4.81 (+0.3) | 46.4 | 93.1 | 25.1 | 36.7 |
| rho | -0.45 (-1.5) | -0.72 (-0.4) | 1.3 | 12.7 | 0.9 | 9.1 |
| phi | +0.37 (+1.4) | +2.89 (+2.5) | 1.1 | 8.0 | 0.8 | 5.5 |
| delta_r | -8.41 (-1.2) | +46.99 (+1.2) | 15.8 | 237.7 | 4.5 | 114.2 |
| delta_d | +16.91 (+1.2) | -50.86 (-1.6) | 24.4 | 142.0 | 4.9 | 57.9 |

## sample: 23 options, 4 labels each

| Greek | bias % new (t) | bias % D2 (t) | typical % new | typical % D2 | median % new | median % D2 |
|---|---|---|---|---|---|---|
| price | -0.04 (-1.4) | -0.00 (-0.1) | 0.1 | 0.1 | 0.1 | 0.1 |
| delta | +0.17 (+1.1) | +0.10 (+0.9) | 0.6 | 0.6 | 0.4 | 0.3 |
| gamma | -0.43 (-0.5) | -1.64 (-1.4) | 7.0 | 7.4 | 4.3 | 4.4 |
| theta | +0.38 (+0.4) | +2.11 (+1.2) | 8.6 | 9.3 | 4.6 | 4.3 |
| vega | -0.16 (-0.7) | +0.53 (+2.0) | 1.4 | 2.2 | 1.0 | 1.3 |
| volga | -14.35 (-0.5) | +46.87 (+0.6) | 236.5 | 439.0 | 45.1 | 84.0 |
| vanna | +1.12 (+0.2) | -22.27 (-1.4) | 30.1 | 53.0 | 13.4 | 16.7 |
| rho | -0.19 (-0.9) | +1.09 (+1.2) | 0.9 | 7.4 | 0.5 | 3.9 |
| phi | +0.14 (+0.8) | -0.47 (-0.2) | 0.7 | 11.5 | 0.4 | 5.5 |
| delta_r | +4.68 (+1.0) | -60.65 (-1.3) | 17.9 | 155.8 | 5.3 | 54.3 |
| delta_d | -17.09 (-1.1) | +50.35 (+0.5) | 28.9 | 307.4 | 4.8 | 59.5 |

Mean seconds per label (one core, 4 processes at once): new 12.2, D2 14.8.
