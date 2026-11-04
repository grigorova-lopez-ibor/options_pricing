# Time of the PDE reference values

Not part of the paper. `experiments/diagnostics/pde_timing.py`, one core, K = S0 = 40, σ = 20 %, r = 3 %, d = 1 %. Generator = `generate_labels.exact` (Bermudan on the label's dates, central bumps: what `--exact` adds); American = `label_reference(style="american")` (what the SCC checks use). For comparison, one in-sample label at 504 dates a year takes about 50 s at T = 1 (results/diagnostics/insample_studies).

| T | dates a year | generator reference (s) | American reference (s) |
|---|---|---|---|
| 0.5 | 50 | 1.9 |  |
| 0.5 | 252 | 2.6 |  |
| 0.5 | 504 | 5.2 | 38.4 |
| 1.0 | 50 | 3.8 |  |
| 1.0 | 252 | 5.0 |  |
| 1.0 | 504 | 10.5 | 81.2 |
| 2.0 | 50 | 7.2 |  |
| 2.0 | 252 | 10.1 |  |
| 2.0 | 504 | 21.8 | 155.1 |

Measured on 4 Nov 2026 while four study processes used the other cores, so about 2× an idle core (29 Oct, idle: 2.3 / 4.5 / 9.2 s for the generator reference at T = 0.5 / 1 / 2, 504 dates a year).

σ = 1 %, T = 2 months (refined grid, 8001 nodes): 4.3 s.
