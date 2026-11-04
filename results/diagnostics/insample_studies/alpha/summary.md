# Selected widths alpha* against fixed widths

Not part of the paper. `experiments/diagnostics/insample_studies.py alpha`: 6 options of results/two_per_day, 504 dates a year, 300k main paths, in-sample rule, 30 labels each: the default (the selector chooses alpha_S and alpha_σ on the pilot, label by label) and fixed widths at 0.5, 0.75, 1, 1.5 and 2 × the median selected alpha* of the option (no pilot). Reference: the American PDE. Root mean square error of one label = √(bias² + noise²); of the mean of 100 labels = √(bias² + noise² / 100). Median over the options, % of |PDE|.

Error of the one label:

| Greek | selector | 0.5× | 0.75× | 1× | 1.5× | 2× |
|---|---|---|---|---|---|---|
| price | 0.295 | 0.26 | 0.27 | **0.25** | 0.279 | 0.309 |
| delta | 0.979 | 1.09 | 0.979 | **0.806** | 0.871 | 0.982 |
| gamma | 7.22 | 13.7 | 7.68 | 6.99 | 6.4 | **6.26** |
| theta | 0.635 | 0.648 | 0.671 | 0.713 | 0.61 | **0.574** |
| vega | 2.65 | 5.02 | 3.44 | 2.67 | 1.93 | **1.61** |
| volga | 440 | 1.38e+03 | 662 | 392 | 193 | **115** |
| vanna | 83.8 | 168 | 99.7 | 71.8 | 55.8 | **49.9** |
| rho | **0.849** | 0.976 | 0.925 | 0.901 | 0.953 | 1.12 |
| phi | **0.799** | 0.947 | 0.893 | 0.868 | 0.899 | 1.05 |

Error of the mean of 100 labels:

| Greek | selector | 0.5× | 0.75× | 1× | 1.5× | 2× |
|---|---|---|---|---|---|---|
| price | 0.0747 | 0.0553 | 0.049 | 0.0485 | 0.0441 | **0.0417** |
| delta | **0.146** | 0.178 | 0.2 | 0.154 | 0.174 | 0.242 |
| gamma | 1.44 | 1.4 | 1.24 | 0.949 | 0.799 | **0.775** |
| theta | **0.173** | 0.212 | 0.23 | 0.245 | 0.255 | 0.208 |
| vega | 0.352 | 0.966 | 0.512 | 0.279 | 0.258 | **0.217** |
| volga | 133 | 447 | 234 | 149 | 53.9 | **27.8** |
| vanna | 14.6 | 43.6 | 15.1 | 7.18 | 7.02 | **5.46** |
| rho | 0.258 | **0.148** | 0.149 | 0.194 | 0.326 | 0.721 |
| phi | 0.216 | **0.119** | 0.138 | 0.169 | 0.297 | 0.665 |

Median |bias| and noise of one label by width:

| Greek | selector bias / noise | 0.5× bias / noise | 0.75× bias / noise | 1× bias / noise | 1.5× bias / noise | 2× bias / noise |
|---|---|---|---|---|---|---|
| price | 0.0676 / 0.29 | 0.0453 / 0.252 | 0.034 / 0.264 | 0.0378 / 0.247 | 0.0302 / 0.277 | 0.0304 / 0.305 |
| delta | 0.109 / 0.973 | 0.144 / 1.09 | 0.164 / 0.954 | 0.128 / 0.796 | 0.143 / 0.842 | 0.216 / 0.954 |
| gamma | 1.15 / 6.95 | 0.5 / 13.6 | 0.73 / 7.66 | 0.529 / 6.92 | 0.31 / 6.39 | 0.356 / 6.24 |
| theta | 0.154 / 0.618 | 0.198 / 0.566 | 0.22 / 0.615 | 0.236 / 0.654 | 0.246 / 0.579 | 0.196 / 0.57 |
| vega | 0.134 / 2.62 | 0.803 / 4.8 | 0.361 / 3.27 | 0.0916 / 2.62 | 0.185 / 1.92 | 0.142 / 1.58 |
| volga | 120 / 412 | 442 / 1.34e+03 | 226 / 622 | 143 / 365 | 52.8 / 181 | 27.2 / 108 |
| vanna | 12.1 / 82.9 | 40.5 / 163 | 11.4 / 99 | 3.67 / 71.8 | 4.28 / 55.6 | 3.96 / 49.9 |
| rho | 0.24 / 0.793 | 0.14 / 0.975 | 0.136 / 0.921 | 0.188 / 0.893 | 0.313 / 0.892 | 0.715 / 0.855 |
| phi | 0.198 / 0.752 | 0.0846 / 0.945 | 0.112 / 0.889 | 0.159 / 0.847 | 0.284 / 0.84 | 0.659 / 0.806 |

Bold: the width with the smallest error. The selector targets Γ (alpha_S) and Volga (alpha_σ).

