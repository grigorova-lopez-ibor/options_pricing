# Width rule against the selector, out of sample

Not part of the paper. `experiments/diagnostics/insample_studies.py widthrule`. The rule was fitted to the selector's median alpha* over the 67 options of results/two_per_day (bias_distribution.py): alpha_S = 0.154 S0 (σ√T)^0.658 T^-0.194 (capped at the pilot width min(0.25, 1.25 σ√T) S0, as the selector is), alpha_σ = 0.222 σ. It is tested here on 25 other options from the training-set ranges (Sobol draw, r > d so that early exercise matters), 20 in-sample labels per option and configuration, 252 dates a year, 300k main paths: the selector (the default: pilot of 100k paths, alpha* label by label) and the rule at 0.5, 1, 1.5 and 2 × (no pilot). Bias against the Bermudan PDE at the same dates (the method's own error); the bias against the American PDE adds the 252/yr gap (≤ 0.12 %, results/diagnostics/insample_studies/dates). Error of one label = √(b² + noise²), of the mean of 100 labels = √(b² + noise²/100), b the bias with its sampling noise removed; % of |PDE|, median over the options. Options in the exercise region, Greeks below 1 % of their largest |PDE| and exact labels are left out.

Time per label: selector 43.9 s, rule 0.5× 34.9 s, rule 1× 35.2 s, rule 1.5× 35.5 s, rule 2× 35.6 s.

Error of the mean of 100 labels (the bias matters):

| Greek | options | selector | rule 0.5× | rule 1× | rule 1.5× | rule 2× |
|---|---|---|---|---|---|---|
| price | 21 | 0.0554 | **0.0285** | 0.0352 | 0.0321 | 0.0473 |
| delta | 22 | 0.142 | 0.196 | 0.174 | **0.128** | 0.132 |
| gamma | 22 | 1.18 | 2.1 | 1.17 | 0.946 | **0.923** |
| theta | 21 | 0.126 | 0.11 | 0.101 | 0.0668 | **0.0547** |
| vega | 22 | 0.229 | 0.523 | 0.242 | 0.236 | **0.168** |
| volga | 19 | 26.6 | 156 | 31 | 16.2 | **7.26** |
| vanna | 22 | 5.44 | 9.38 | 6.79 | 3.81 | **2.38** |
| rho | 22 | 0.397 | **0.304** | 0.446 | 0.46 | 0.592 |
| phi | 22 | 0.373 | **0.253** | 0.378 | 0.328 | 0.532 |

Error of one label (the noise matters):

| Greek | options | selector | rule 0.5× | rule 1× | rule 1.5× | rule 2× |
|---|---|---|---|---|---|---|
| price | 21 | 0.184 | **0.163** | 0.164 | 0.176 | 0.184 |
| delta | 22 | 1.11 | 1.02 | 1.01 | **0.982** | 1.09 |
| gamma | 22 | 10.6 | 14.4 | 9.85 | 8.04 | **7.99** |
| theta | 21 | 0.407 | 0.407 | 0.41 | 0.411 | **0.406** |
| vega | 22 | 2.16 | 3.91 | 2.04 | 1.41 | **1.18** |
| volga | 19 | 157 | 466 | 117 | 59 | **39.7** |
| vanna | 22 | 45.4 | 80.2 | 37.6 | 25.2 | **16.2** |
| rho | 22 | 1.42 | **1.41** | 1.48 | 1.55 | 1.53 |
| phi | 22 | **1.16** | 1.24 | 1.32 | 1.25 | 1.26 |

Paired by option: share of options where the rule's mean-of-100 error is below the selector's, and the two-sided sign-test p-value:

| Greek | rule 0.5× | rule 1× | rule 1.5× | rule 2× |
|---|---|---|---|---|
| price | 14/21 (p = 0.19) | 14/21 (p = 0.19) | 13/21 (p = 0.38) | 15/21 (p = 0.078) |
| delta | 9/22 (p = 0.52) | 9/22 (p = 0.52) | 8/22 (p = 0.29) | 9/22 (p = 0.52) |
| gamma | 2/22 (p = 0.00012) | 13/22 (p = 0.52) | 15/22 (p = 0.13) | 17/22 (p = 0.017) |
| theta | 10/21 (p = 1) | 11/21 (p = 1) | 11/21 (p = 1) | 8/21 (p = 0.38) |
| vega | 3/22 (p = 0.00086) | 11/22 (p = 1) | 15/22 (p = 0.13) | 17/22 (p = 0.017) |
| volga | 0/19 (p = 3.8e-06) | 9/19 (p = 1) | 14/19 (p = 0.064) | 15/19 (p = 0.019) |
| vanna | 4/22 (p = 0.0043) | 11/22 (p = 1) | 15/22 (p = 0.13) | 18/22 (p = 0.0043) |
| rho | 14/22 (p = 0.29) | 12/22 (p = 0.83) | 11/22 (p = 1) | 8/22 (p = 0.29) |
| phi | 13/22 (p = 0.52) | 13/22 (p = 0.52) | 13/22 (p = 0.52) | 7/22 (p = 0.13) |

Median bias against the American PDE (signed, %):

| Greek | selector | rule 0.5× | rule 1× | rule 1.5× | rule 2× |
|---|---|---|---|---|---|
| price | +0.0512 | +0.0299 | +0.0238 | +0.0149 | +0.016 |
| delta | -0.166 | -0.229 | -0.214 | -0.0882 | -0.0642 |
| gamma | +0.525 | +0.824 | +0.463 | +0.44 | +0.164 |
| theta | -0.0562 | -0.0598 | -0.0437 | -0.0389 | -0.0454 |
| vega | -0.00981 | +0.146 | +0.103 | +0.0792 | +0.116 |
| volga | +24 | +184 | +38.9 | +20.6 | +8.16 |
| vanna | -0.429 | +0.537 | +1.01 | +0.72 | +0.496 |
| rho | +0.0234 | +0.00347 | -0.149 | -0.143 | -0.135 |
| phi | +0.0122 | +0.00076 | +0.165 | +0.165 | +0.152 |

