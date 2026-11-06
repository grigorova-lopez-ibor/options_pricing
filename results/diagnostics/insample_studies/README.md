# Studies of the in-sample default label (4-5 Nov 2026)

Not part of the paper. Runner: `experiments/diagnostics/insample_studies.py`;
summaries: `experiments/diagnostics/insample_studies_report.py`. Each folder has
`raw.csv` (one row per label), `ref.csv` where the study computes its own PDE
values, and `summary.md`. Run on one 4-core machine; the production set is for
the SCC. See also `../bias_distribution/` (per-option bias of the out-of-sample,
in-sample and averaged labels, from results/two_per_day) and `../pde_timing/`.

| Study | Question | Finding |
|---|---|---|
| `paths/` | 150k–600k main paths | Foresight bias falls like 1/N (price \|bias\| 0.13 → 0.03 → 0.023 → 0.015 %, Volga 8 → 5 → 3 → 2.6 %); Rho, Phi do not change. For a fixed CPU budget price, Δ, Γ, Θ, Volga are best at 450–600k, Vega, Vanna, Rho, Phi at 150k (no bias to remove). |
| `alpha/` | the selector's alpha* against fixed widths | alpha* varies ~30 % between labels of an option (pilot noise); a fixed width at the option's median alpha* is as good or better for price, Δ, Γ, Vega, Vanna and needs no pilot (44 s against 62 s). Wider (1.5–2×) lowers the noise of Γ and the σ-Greeks; Rho and Phi prefer narrower: their bias grows from 0.14 % at 0.5× to 0.7 % at 2×. 6 options only. |
| `dates/` | 50, 252, 504 exercise dates a year | The method's own bias and the noise hardly change; the Bermudan–American gap does (price −0.107 / −0.023 / −0.011 %, Rho −0.69 / −0.14 / −0.07 %). Against the American PDE every median bias is ≤ 0.12 % at 252 and ≤ 0.09 % at 504; time 18 against 36 s (T ≤ 1). |
| `widthrule/` | the selector against a width rule fitted to its alpha*, out of sample (25 options, 20 labels, 252/yr) | Rule 1× ≈ selector for every Greek (paired sign tests p ≥ 0.19): choosing alpha* label by label gains nothing measurable, and costs the pilot (43.9 s against 35.2 s). Twice the width is significantly better for Γ, Vega, Volga and Vanna (17–18 of 22 options, p ≈ 0.02; Volga bias +24 → +8 %); half the width is significantly worse for them. Rho and Phi lean narrower but not significantly (14/22, p = 0.29), so the 6-option hint is not confirmed. |
| `crn/` | one shared seed for all options against a fresh seed each | Same median error, errors of neighbouring options barely correlated (\|r\| ≤ 0.14), same error after smoothing, same time. No gain at 2,000 options; with denser sets neighbours would share more of their error. |

## Recommendations for the SCC production set

1. In-sample rule only (done, `MultiConfig()` default since 29 Oct).
2. Independent seeds per option, no common random numbers.
3. Main paths: 300k as the balance; 450k if price, Γ and Volga matter most (1.5× the time).
4. Exercise dates: 252 a year is within 0.12 % of the American values at half the time of 504; 504 if the time is not a concern.
5. Widths: the selector's label-by-label choice gains nothing over a smoothed rule (`widthrule/`), and a wider spread (about 2× the selected alpha*) significantly helps Γ and the σ-Greeks. Keeping the paper's selector and scaling its choice is the option closest to the paper; replacing it with the rule also drops the pilot (−20 % time). **Decided 6 Nov 2026: keep the paper's selector** (Appendix A.2, on the pilot paths): the rule is only the selector's average over 67 options, too little data to replace it. The pilot paths therefore stay.
6. Reference values: the Bermudan PDE costs about 10 % of a label (4.5 s at T = 1, 504 a year), so a reference for every label is affordable.
