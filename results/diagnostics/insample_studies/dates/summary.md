# Noise and bias against the number of exercise dates

Not part of the paper. `experiments/diagnostics/insample_studies.py dates`: the default in-sample label (300k main paths, value function at 1/50 year above 50 dates a year) at 50, 252 and 504 exercise dates a year, 30 labels per option and frequency, on 20 options of results/two_per_day with T ≤ 1. Bias against the Bermudan PDE at the same dates (the method's own bias) and against the American PDE (what the network should learn); gap = Bermudan − American. Median over the options, % of |PDE|.

Time per label: 50/yr 4.3 s, 252/yr 18.3 s, 504/yr 36.4 s; Bermudan reference: 50/yr 3.1 s, 252/yr 4.7 s, 504/yr 9.3 s.

| Greek | 50/yr bias vs Berm. / vs Amer. / gap / noise | 252/yr bias vs Berm. / vs Amer. / gap / noise | 504/yr bias vs Berm. / vs Amer. / gap / noise |
|---|---|---|---|
| price | +0.0316 / -0.0825 / -0.107 / 0.204 | +0.0393 / +0.0128 / -0.0227 / 0.235 | +0.0534 / +0.036 / -0.0113 / 0.219 |
| delta | +0.00642 / +0.0594 / +0.0788 / 0.749 | -0.0927 / -0.0783 / +0.0159 / 0.902 | -0.0829 / -0.0718 / +0.00792 / 0.9 |
| gamma | +0.16 / +0.123 / -0.0373 / 6.9 | +0.00467 / -0.0138 / -0.0054 / 6.75 | +0.00316 / +0.0169 / -0.00268 / 6.57 |
| theta | +0.282 / +0.305 / +0.0074 / 0.388 | +0.0513 / +0.0479 / -0.000465 / 0.408 | -0.022 / -0.023 / -0.000236 / 0.387 |
| vega | +0.041 / -0.0071 / -0.0339 / 2 | +0.133 / +0.123 / -0.00698 / 2.07 | -0.00521 / -0.00626 / -0.00395 / 2.43 |
| volga | +29.7 / +29.6 / +0.0426 / 140 | +41 / +42.2 / +0.328 / 116 | +18.6 / +18.9 / +0.0063 / 135 |
| vanna | +1.8 / +0.673 / -0.0646 / 38.4 | +0.058 / +0.0594 / -0.0221 / 33 | -2.03 / -2.04 / -0.0107 / 39 |
| rho | -0.193 / -1.07 / -0.689 / 0.808 | +0.0441 / -0.118 / -0.139 / 0.908 | +0.152 / +0.085 / -0.0689 / 0.995 |
| phi | +0.167 / +0.949 / +0.658 / 0.737 | -0.0432 / +0.0933 / +0.134 / 0.841 | -0.151 / -0.0773 / +0.0669 / 0.963 |

