# In-sample label against the number of main paths

Not part of the paper. `experiments/diagnostics/insample_studies.py paths`: the default in-sample label (exercise bound on) at 150k, 300k, 450k and 600k main paths (pilot 100k), 504 dates a year, 40 labels per option and path count with the same seeds, on the 14 options of the 600k Volga check (picked as the worst in-sample Volga in results/two_per_day, so the biases here are larger than typical). Reference: the American PDE. Options whose label is exact (r < d: no path exercises early) are left out per Greek.

Mean time per label measured (4 processes on this machine): 150k 24.6 s, 300k 22.3 s, 450k 67.2 s, 600k 44.5 s. The 150k and 450k labels ran while other jobs used the machine, so their times are inflated; the budget below uses t(N) = 0.0742 s per 1,000 main paths, fitted to the 300k and 600k runs (made under the same conditions): 150k 11.1 s, 300k 22.3 s, 450k 33.4 s, 600k 44.5 s.

Median over the options of |bias| and of the noise of one label, % of |PDE|:

| Greek | options | |bias| 150k | |bias| 300k | |bias| 450k | |bias| 600k | noise 150k | noise 300k | noise 450k | noise 600k |
|---|---|---|---|---|---|---|---|---|---|
| price | 8 | 0.131 | 0.0321 | 0.0231 | 0.015 | 0.139 | 0.104 | 0.0765 | 0.0714 |
| delta | 9 | 0.273 | 0.0967 | 0.0574 | 0.0582 | 0.698 | 0.549 | 0.445 | 0.35 |
| gamma | 10 | 0.488 | 0.371 | 0.306 | 0.337 | 7.19 | 3.87 | 3.12 | 2.39 |
| theta | 9 | 0.123 | 0.122 | 0.0634 | 0.0536 | 0.349 | 0.238 | 0.202 | 0.219 |
| vega | 9 | 0.243 | 0.17 | 0.14 | 0.0752 | 1.76 | 1.41 | 1.19 | 1.1 |
| volga | 10 | 8 | 5 | 2.99 | 2.57 | 28.6 | 21.1 | 14.9 | 13.9 |
| vanna | 10 | 1.14 | 0.635 | 0.711 | 0.343 | 8.94 | 8.51 | 6.32 | 5.77 |
| rho | 9 | 0.1 | 0.152 | 0.186 | 0.218 | 1.41 | 1.11 | 0.979 | 0.859 |
| phi | 9 | 0.185 | 0.14 | 0.225 | 0.184 | 1.27 | 1.07 | 0.939 | 0.858 |

In-sample Volga bias per option, % ± se:

| option | 150k | 300k | 450k | 600k |
|---|---|---|---|---|
| check 0 | +7.9 ± 1.3 | +4.9 ± 1.1 | +3.0 ± 0.8 | +2.6 ± 0.9 |
| check 3 | +8.0 ± 4.5 | +5.0 ± 3.3 | +2.9 ± 2.4 | +2.6 ± 2.2 |
| check 9 | +7.7 ± 1.8 | +3.9 ± 1.1 | +2.3 ± 1.0 | +2.0 ± 0.9 |
| check 30 | +27.5 ± 10.8 | +29.8 ± 6.5 | +22.3 ± 5.8 | +18.3 ± 5.3 |
| random 6 | +0.0 ± 0.0 | +0.0 ± 0.0 | +0.0 ± 0.0 | +0.0 ± 0.0 |
| random 9 | +88.1 ± 16.0 | +63.9 ± 12.1 | +47.4 ± 8.6 | +40.1 ± 10.9 |
| random 11 | +36.9 ± 6.0 | +22.1 ± 4.3 | +14.9 ± 3.7 | +14.9 ± 2.9 |
| random 23 | +51.2 ± 21.0 | +68.4 ± 14.3 | +51.0 ± 11.5 | +40.2 ± 12.0 |
| random 26 | +24.5 ± 6.8 | +16.4 ± 4.5 | +12.9 ± 2.5 | +11.5 ± 2.8 |
| random 31 | +0.0 ± 0.0 | +0.0 ± 0.0 | +0.0 ± 0.0 | +0.0 ± 0.0 |
| random 39 | +1.2 ± 0.3 | +1.0 ± 0.2 | +0.8 ± 0.1 | +0.6 ± 0.1 |

## Fixed budget

Expected error of the mean of the labels one option gets for C CPU seconds: √(b² + s² · t(N) / C), b = median bias with its sampling noise removed, s = median noise, t(N) the time per label. C stands for the budget per neighbourhood of the network's inputs, since a network fitted to noisy labels averages nearby ones the same way.

| Greek | C = 100 s | 1,000 s | 10,000 s | 100,000 s |
|---|---|---|---|---|
| price | 600k (0.049 %) | 600k (0.018 %) | 600k (0.012 %) | 600k (0.011 %) |
| delta | 600k (0.23 %) | 600k (0.076 %) | 450k (0.026 %) | 450k (0.0081 %) |
| gamma | 600k (1.6 %) | 600k (0.5 %) | 600k (0.16 %) | 600k (0.05 %) |
| theta | 450k (0.13 %) | 600k (0.059 %) | 600k (0.04 %) | 600k (0.038 %) |
| vega | 150k (0.59 %) | 150k (0.19 %) | 150k (0.059 %) | 150k (0.019 %) |
| volga | 450k (8.8 %) | 600k (3.2 %) | 600k (1.6 %) | 600k (1.4 %) |
| vanna | 150k (3 %) | 150k (0.94 %) | 150k (0.3 %) | 150k (0.094 %) |
| rho | 150k (0.47 %) | 150k (0.15 %) | 150k (0.047 %) | 150k (0.015 %) |
| phi | 150k (0.42 %) | 150k (0.13 %) | 150k (0.042 %) | 150k (0.013 %) |

Each cell: the path count with the smallest expected error, and that error.

