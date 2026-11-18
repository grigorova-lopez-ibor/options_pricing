# Where to put the exercise dates: Bermudan-American gap from the PDE

Not part of the paper. `experiments/diagnostics/exercise_placement.py`. Exercise dates t_j = T g(j/J), J = round(dates a year × T): uniform g(u) = u (the labels today); late p: g(u) = 1 − (1 − u)^p (denser towards maturity; p = 2 is uniform in √(time to maturity)); early p: g(u) = u^p (denser near the start); ends a: (1 − a) u + a (1 − cos πu)/2 (denser at both ends). Gap = (Bermudan − American) / |American| in %, both from the Crank–Nicolson PDE on the same x-grid (no Monte Carlo noise), on the options of results/two_per_day outside the exercise region and the no-early-exercise region; per Greek, options with |American| < 1 % of the largest are left out. The cost of a label is proportional to the number of dates, not to where they are.

## Mean |gap| (%)

| placement | dates/yr | price | delta | gamma | theta | charm | vega | rho | phi |
|---|---|---|---|---|---|---|---|---|---|
| uniform | 504 | 0.0117 | 0.0111 | 0.00758 | 0.00671 | 0.0324 | 0.00669 | 0.0637 | 0.0614 |
| uniform | 252 | 0.0235 | 0.0222 | 0.0152 | 0.0131 | 0.0612 | 0.0131 | 0.128 | 0.123 |
| late 1.5 | 252 | 0.0229 | 0.0264 | 0.0276 | 0.033 | 0.0341 | 0.0134 | 0.138 | 0.129 |
| late 2 | 252 | 0.026 | 0.0322 | 0.0385 | 0.0567 | 0.0889 | 0.0168 | 0.162 | 0.151 |
| late 3 | 252 | 0.0341 | 0.0446 | 0.0586 | 0.0971 | 0.227 | 0.0239 | 0.22 | 0.203 |
| early 2 | 252 | 0.0352 | 0.0275 | 0.0295 | 0.0947 | 0.433 | 0.0251 | 0.173 | 0.169 |
| ends 0.5 | 252 | 0.0238 | 0.0227 | 0.0184 | 0.0528 | 0.3 | 0.0118 | 0.13 | 0.122 |
| uniform | 126 | 0.0468 | 0.0444 | 0.0305 | 0.0249 | 0.115 | 0.0263 | 0.254 | 0.244 |
| late 1.5 | 126 | 0.0459 | 0.0528 | 0.0545 | 0.0643 | 0.0865 | 0.0267 | 0.275 | 0.257 |
| late 2 | 126 | 0.0521 | 0.0642 | 0.0749 | 0.107 | 0.212 | 0.0331 | 0.324 | 0.301 |
| late 3 | 126 | 0.068 | 0.0887 | 0.117 | 0.194 | 0.566 | 0.0467 | 0.435 | 0.401 |
| early 2 | 126 | 0.0699 | 0.0548 | 0.0586 | 0.188 | 0.866 | 0.0494 | 0.344 | 0.334 |
| ends 0.5 | 126 | 0.0475 | 0.0455 | 0.0368 | 0.105 | 0.6 | 0.0232 | 0.26 | 0.244 |
| Richardson 2·B(252) − B(126) | 252 | 0.000236 | 0.000297 | 0.000433 | 0.0017 | 0.0104 | 0.000843 | 0.004 | 0.00475 |

## 95th percentile of |gap| (%)

| placement | dates/yr | price | delta | gamma | theta | charm | vega | rho | phi |
|---|---|---|---|---|---|---|---|---|---|
| uniform | 504 | 0.0466 | 0.0495 | 0.0354 | 0.0387 | 0.143 | 0.0266 | 0.185 | 0.173 |
| uniform | 252 | 0.093 | 0.0988 | 0.0713 | 0.066 | 0.322 | 0.0526 | 0.37 | 0.351 |
| late 1.5 | 252 | 0.106 | 0.123 | 0.131 | 0.148 | 0.147 | 0.0687 | 0.4 | 0.383 |
| late 2 | 252 | 0.118 | 0.142 | 0.153 | 0.236 | 0.347 | 0.0874 | 0.509 | 0.488 |
| late 3 | 252 | 0.151 | 0.172 | 0.202 | 0.379 | 1.5 | 0.107 | 0.712 | 0.697 |
| early 2 | 252 | 0.141 | 0.115 | 0.128 | 0.583 | 1.59 | 0.104 | 0.499 | 0.484 |
| ends 0.5 | 252 | 0.095 | 0.108 | 0.0946 | 0.345 | 0.942 | 0.0488 | 0.389 | 0.359 |
| uniform | 126 | 0.185 | 0.197 | 0.146 | 0.0988 | 0.62 | 0.105 | 0.741 | 0.701 |
| late 1.5 | 126 | 0.211 | 0.246 | 0.264 | 0.295 | 0.389 | 0.138 | 0.792 | 0.759 |
| late 2 | 126 | 0.235 | 0.284 | 0.306 | 0.391 | 1.46 | 0.175 | 1 | 0.968 |
| late 3 | 126 | 0.3 | 0.342 | 0.405 | 0.832 | 3.73 | 0.214 | 1.39 | 1.36 |
| early 2 | 126 | 0.281 | 0.227 | 0.255 | 1.17 | 3.2 | 0.21 | 0.984 | 0.952 |
| ends 0.5 | 126 | 0.19 | 0.215 | 0.189 | 0.691 | 1.89 | 0.0974 | 0.779 | 0.716 |
| Richardson 2·B(252) − B(126) | 252 | 0.00109 | 0.000669 | 0.00109 | 0.00356 | 0.0118 | 0.00302 | 0.02 | 0.0192 |

Signed mean gap (%) (the Bermudan is below the American price):

| placement | dates/yr | price | delta | gamma | theta | charm | vega | rho | phi |
|---|---|---|---|---|---|---|---|---|---|
| uniform | 504 | -0.0117 | +0.0111 | -0.00643 | +2.32e-05 | +0.0287 | -0.00427 | -0.0635 | +0.0613 |
| uniform | 252 | -0.0235 | +0.0221 | -0.0129 | +0.000434 | +0.0538 | -0.0084 | -0.127 | +0.122 |
| late 1.5 | 252 | -0.0229 | +0.0263 | -0.0258 | +0.0322 | -0.0284 | -0.0018 | -0.138 | +0.128 |
| late 2 | 252 | -0.026 | +0.032 | -0.0364 | +0.0557 | -0.0863 | +0.00117 | -0.162 | +0.151 |
| late 3 | 252 | -0.0341 | +0.0444 | -0.0557 | +0.0956 | -0.174 | +0.00524 | -0.22 | +0.203 |
| early 2 | 252 | -0.0352 | +0.0263 | +0.00682 | -0.0809 | +0.426 | -0.0232 | -0.172 | +0.167 |
| ends 0.5 | 252 | -0.0238 | +0.0226 | -0.00715 | -0.0339 | +0.289 | -0.00911 | -0.13 | +0.122 |
| uniform | 126 | -0.0468 | +0.0442 | -0.026 | +0.00226 | +0.1 | -0.0166 | -0.253 | +0.243 |
| late 1.5 | 126 | -0.0459 | +0.0525 | -0.0509 | +0.0625 | -0.0219 | -0.0036 | -0.275 | +0.256 |
| late 2 | 126 | -0.0521 | +0.0639 | -0.0706 | +0.104 | -0.144 | +0.00157 | -0.324 | +0.301 |
| late 3 | 126 | -0.068 | +0.0883 | -0.111 | +0.191 | -0.509 | +0.00924 | -0.435 | +0.401 |
| early 2 | 126 | -0.0699 | +0.0524 | +0.0133 | -0.16 | +0.852 | -0.0454 | -0.342 | +0.332 |
| ends 0.5 | 126 | -0.0475 | +0.0453 | -0.0144 | -0.0673 | +0.578 | -0.0182 | -0.26 | +0.244 |
| Richardson 2·B(252) − B(126) | 252 | -0.000181 | +6.81e-05 | +0.000201 | -0.0014 | +0.00761 | -0.000151 | -0.00114 | +0.00194 |

## Findings

* **For a fixed number of dates, uniform spacing is as good as or better than every other placement
  tried.** Dates denser towards maturity (late 1.5, 2, 3) shrink the price gap at most marginally
  (late 1.5: 0.0229 against 0.0235 % at 252/yr) and enlarge it for Delta, Gamma, Theta, Rho and Phi;
  the more they are skewed, the worse (late 3 roughly doubles the Rho, Phi and Theta gaps). Dates
  denser near the start or at both ends are worse too. Per option, late 1.5 beats uniform on 36 of 66
  options for the price and 29 of 66 for Rho, with no pattern in maturity or moneyness: no option-
  dependent rule to exploit.
* **Why:** the gap builds up over the whole life of the option wherever early exercise is possible,
  not only near maturity, so thinning the dates anywhere loses about what thickening them elsewhere
  gains. Theta and Charm at t_0 also depend on the first and last intervals, which skewed placements
  stretch.
* **The number of dates is what matters:** uniform gaps scale like 1/J (126 → 252 → 504/yr: price
  0.047 → 0.024 → 0.012 %, Rho 0.25 → 0.13 → 0.064 %), so 126 placed dates cannot match 252 uniform.
* **Richardson in the number of dates removes about 99 % of the gap:** 2·B(252) − B(126) is within
  0.0002 % of the American price and 0.004 % in Rho (mean), better than uniform at 504/yr. For
  Monte Carlo labels it needs a second, coarser exercise rule on the same paths (every second date):
  about 1.5× the time of one label, and its noise grows unless both use the same paths.
