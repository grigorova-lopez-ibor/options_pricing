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
3–4. **Decided Nov 2026: 252 exercise dates a year with 600k main paths** (now the default of
   `experiments/generate_labels.py`, about 60 s a label, ≤ 3 GB). See "Exercise dates against main
   paths" below.
5. Widths: the selector's label-by-label choice gains nothing over a smoothed rule (`widthrule/`), and a wider spread (about 2× the selected alpha*) significantly helps Γ and the σ-Greeks. Keeping the paper's selector and scaling its choice is the option closest to the paper; replacing it with the rule also drops the pilot (−20 % time). **Decided 6 Nov 2026: keep the paper's selector** (Appendix A.2, on the pilot paths): the rule is only the selector's average over 67 options, too little data to replace it. The pilot paths therefore stay.
6. Reference values: the Bermudan PDE costs about 10 % of a label (4.5 s at T = 1, 504 a year), so a reference for every label is affordable.

## Exercise dates against main paths (Nov 2026)

Evidence: Alika's SCC grid on `main` (`results/diagnostics/bias_vs_dates_paths`: 126 / 252 / 504 /
1008 dates a year × 75k / 150k / 300k / 600k main paths, 15 options × 30 labels, American and
Bermudan PDE) and its confirmation run (`results/diagnostics/best_config`: 252/yr, 600k, the 75
options of results/two_per_day × 100 labels, MAE with bootstrap 95 % intervals), plus `paths/` and
`dates/` here.

* **Time per label is linear in paths × dates**, so 252/yr with 600k and 504/yr with 300k cost the
  same (about 55–60 s).
* **At that cost 252/600k is as good or better for every Greek.** In the grid (paired by option,
  error of the mean of 100 labels): better on 10 of 15 options for the price, Δ and Vega and
  12 of 15 for Γ (sign test p = 0.04), median error ratio 0.47–0.90; Volga, Rho and Phi equal. In
  the confirmation run, the three cells whose intervals do not overlap all favour 252/600k
  (Δ 0.095 against 0.18 % and Γ 0.76 against 1.34 % on the check options, price 0.025 against
  0.051 % on the range options); on the range options it is lower for all 12 outputs. Only Θ, Rho
  and Phi on the check options (strong early exercise) lean the other way, within the intervals.
* **504/600k (twice the cost) is not better than 252/600k** for price, Δ, Γ, Θ, Rho or Phi (total
  bias, mean over the 15 options: price 0.047 against 0.043 %, Γ 1.69 against 1.03 %, Rho 1.12
  against 1.02 %). More dates halve the Bermudan gap (price 0.033 → 0.017 %, Rho 0.32 → 0.15 %)
  but raise the simulation bias by more (price 0.030 → 0.047 %, Rho 0.84 → 1.09 %): the in-sample
  rule is refitted at every date, so its foresight grows with the number of dates. Vega, Volga and
  Vanna look better at 504 only in the mean, at the noise floor, driven by one or two options.
* **Paths matter more than dates** once at 252/yr: foresight bias falls about like 1/paths and
  noise like 1/√paths, while the 252/yr gap to the American value is small (price 0.03 %,
  Rho/Phi 0.15–0.3 %). Below 252 the gap shows (126/yr: Rho about 0.6 %).
* **What neither fixes:** the Θ, Rho, Phi bias on options with strong early exercise (0.4–0.6 %)
  and the Volga bias (about +20 %) are method biases; they do not fall with more dates and only
  Volga's falls with paths.
