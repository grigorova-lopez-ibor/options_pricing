"""Report of the two-exercise-dates-per-day check (experiments/tournament.py,
parts tpd_check, tpd_check_ref, tpd_random, tpd_random_ref): puts with 504
exercise dates a year, the default label (one (S, sigma) run, pathwise r, d,
Theta and Charm, hybrid of the out-of-sample and in-sample labels) with the
value-function label at 1/50 year, 100 labels per option. Not part of the paper.

    python experiments/two_per_day_report.py --out OUT

Writes results/two_per_day/report.md and raw/ (Parquet). Bias is against the
continuous American PDE (the target) and the Bermudan PDE on the labels' 504
dates a year; their difference is the remaining discreteness gap.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from experiments.tournament import TPD_RANDOM_N, TPD_SEED, load  # noqa: E402

DEST = ROOT / "results" / "two_per_day"
GREEKS = ["price", "delta", "gamma", "theta", "charm", "vega", "volga", "vanna", "rho", "phi",
          "delta_r", "delta_d", "theta_pde"]
REF_OF = {"theta_pde": "theta"}             # theta_pde is compared with the reference Theta
MODES = ("oos", "ins", "avg")
REF_TOL = 1e-4                              # relative accuracy allowed for the PDE reference in t
REFS = {"American": "", "Bermudan 504/yr": "berm_"}
SETS = {"check": "35 put check options", "random": f"{TPD_RANDOM_N} options from the input ranges"}


def ref_frame(ref: pd.DataFrame, prefix: str) -> pd.DataFrame:
    r = ref.drop_duplicates("id").set_index("id")
    out = pd.DataFrame({q: r[prefix + REF_OF.get(q, q)] for q in GREEKS})
    out["ex_region"] = r[prefix + "ex_region"].astype(bool)
    return out


def per_option(lab: pd.DataFrame, ref: pd.DataFrame, col_of=lambda q: q) -> pd.DataFrame:
    rows = []
    for i, g in lab.groupby("id"):
        for q in GREEKS:
            x = g[col_of(q)].dropna() if col_of(q) in g else pd.Series(dtype=float)
            if len(x) < 2:
                continue
            r = float(ref.loc[i, q])
            m, sd = x.mean(), x.std(ddof=1)
            tol = 1e-9 * max(1.0, abs(r))
            if sd <= tol:                     # exact label
                sd = 0.0
            se = sd / np.sqrt(len(x))
            b = m - r
            # the PDE reference is accurate to about REF_TOL relative: with labels
            # that are (nearly) deterministic (no early exercise in practice) a
            # difference of that size is not a bias
            se_t = np.hypot(se, REF_TOL * abs(r))
            t = b / se_t if se_t > 0 else (0.0 if abs(b) <= tol else np.sign(b) * np.inf)
            rows.append(dict(id=i, greek=q, n=len(x), ref=r, mean=m, bias=b, se=se, t=t, sd=sd))
    df = pd.DataFrame(rows)
    big = df.groupby("greek").ref.transform(lambda s: s.abs().max())
    df["use_rel"] = (df.ref.abs() > 0.01 * big) & (df.sd > 0)
    df["rel_bias"] = np.where(df.use_rel, df.bias / df.ref.abs(), np.nan)
    df["rel_se"] = np.where(df.use_rel, df.se / df.ref.abs(), np.nan)
    df["rel_noise"] = np.where(df.use_rel, df.sd / df.ref.abs(), np.nan)
    return df


def cells(po: pd.DataFrame, q: str) -> str:
    """t > 3 / t < -3 · median signed rel. bias · mean t · scaled bias (t) · MAE of bias
    (noise-corrected RMS bias) · median noise."""
    d = po[po.greek == q]
    if d.empty:
        return "–"
    fin = d[np.isfinite(d.t) & (d.sd > 0)]
    scaled = d.bias.sum() / d.ref.abs().sum()
    sse = np.sqrt((d.se ** 2).sum()) / d.ref.abs().sum()
    rb, rs = d.rel_bias.dropna(), d.rel_se.dropna()
    mae = 100 * rb.abs().mean()
    rms = 100 * np.sqrt(max(0.0, (rb ** 2 - rs ** 2).mean())) if len(rb) else np.nan
    return (f"{int((d.t > 3).sum())}/{int((d.t < -3).sum())} · {100 * rb.median():+.2f}% · "
            f"{fin.t.mean():+.2f} · {100 * scaled:+.2f}% ({scaled / sse if sse > 0 else 0:+.1f}) · "
            f"{mae:.2f}% ({rms:.2f}%) · {100 * d.rel_noise.median():.1f}%")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    (DEST / "raw").mkdir(parents=True, exist_ok=True)
    data = {}
    for s in SETS:
        lab, ref = load(f"tpd_{s}", a.out), load(f"tpd_{s}_ref", a.out)
        lab.to_parquet(DEST / "raw" / f"{s}_labels.parquet", index=False)
        ref.to_parquet(DEST / "raw" / f"{s}_reference.parquet", index=False)
        data[s] = (lab, ref, {rn: ref_frame(ref, p) for rn, p in REFS.items()})

    L = []
    w = L.append
    w("# Puts with two exercise dates per day: default label check\n")
    w("Not part of the paper. `experiments/tournament.py --part tpd_check / tpd_check_ref / tpd_random / "
      "tpd_random_ref`, `experiments/two_per_day_report.py`.\n")
    w("**Label.** `MultiConfig(vf_time=0.02)`: the default label of the `carlos` branch (one (S, σ) run of "
      "300,000 main + 100,000 pilot paths; Rho, Phi, ∂Δ/∂r, ∂Δ/∂d, Theta and Charm pathwise on its paths; "
      "pilot width of S min(0.25, 1.25 σ√T) S0; averaged out-of-sample and in-sample labels, Volga, Vanna, "
      "∂Δ/∂r, ∂Δ/∂d out of sample) with **504 exercise dates a year** (two per business day, J = round(504 T)) "
      "and the value-function label at the date nearest 1/50 year (as validated at daily dates in "
      "`results/american_daily/`). Theta and Charm are pathwise with the number of dates fixed; the reference's "
      "are calendar ones (the gap halves each time the dates double). `theta_pde` is the PDE-identity Theta.\n")
    w(f"**Options.** {SETS['check']} (the production check's: T 0.5/1/2 × σ 10/20/40 % × K 36/40/44 at r = 6 %, "
      f"d = 0, plus r = d = 0, r = d = 6 %, r = d = 1 %) and {SETS['random']} drawn by "
      f"`generate_labels.sample_options(n={TPD_RANDOM_N}, S0=40, seed={TPD_SEED})` over the `carlos` ranges "
      "(S0/K 0.8–1.2, σ plateau 5–50 % with tails to 1 % and 60 %, r and d 0–5 %, T 2 months–2 years); "
      "100 labels each, seeds `job_seed(8020 / 8021, {id}, rep)`.\n")
    w("**References.** Crank–Nicolson PDE: *American* = exercise at every time step, Richardson-extrapolated "
      "in the step (continuous exercise, the target); *Bermudan 504/yr* = exercise on the labels' dates.\n")

    w("## Time and memory\n")
    w("| set | T | labels | seconds per label (mean) | p95 | peak RSS MB |")
    w("|---|---|---|---|---|---|")
    for s, (lab, ref, _) in data.items():
        bins = pd.cut(lab["T"], [0, 0.5, 1.0, 1.5, 2.01], right=True)
        for b, g in lab.groupby(bins, observed=True):
            w(f"| {s} | {b} | {len(g)} | {g.seconds.mean():.0f} | {g.seconds.quantile(.95):.0f} | "
              f"{g.rss_mb.max():.0f} |")
        w(f"| {s} | references | {len(ref)} | {ref.seconds.mean():.0f} | {ref.seconds.quantile(.95):.0f} | "
          f"{ref.rss_mb.max():.0f} |")
    w("")

    w("## Summary per Greek (default label)\n")
    w("Per option: bias = mean of 100 labels − reference, t = bias / √(se² + (10⁻⁴ ref)²) (the second term "
      "allows for the PDE's own error where a label is nearly deterministic). Cells: options with t > 3 / t < −3 · "
      "median signed relative bias · mean t · scaled bias Σ bias / Σ |ref| (t) · MAE of the relative bias "
      "(noise-corrected RMS bias, √mean(b² − se²)) · median noise of one label. Relative measures over the "
      "options with |ref| ≥ 1 % of the largest and a non-exact label.\n")
    POS = {}
    for s, (lab, ref, R) in data.items():
        w(f"### {SETS[s]}\n")
        w("| Greek | " + " | ".join(f"vs {rn}" for rn in REFS) + " |")
        w("|---|" + "---|" * len(REFS))
        for rn in REFS:
            POS[(s, rn)] = per_option(lab, R[rn])
        for q in GREEKS:
            w(f"| {q} | " + " | ".join(cells(POS[(s, rn)], q) for rn in REFS) + " |")
        w("")

    w("## Out-of-sample, in-sample and averaged labels (vs American)\n")
    for s, (lab, ref, R) in data.items():
        w(f"### {SETS[s]}\n")
        w("| Greek | default | oos | ins | avg |")
        w("|---|---|---|---|---|")
        pm = {m: per_option(lab, R["American"], lambda q, m=m: f"{q}_{m}") for m in MODES}
        for q in GREEKS:
            w(f"| {q} | " + " | ".join([cells(POS[(s, "American")], q)] + [cells(pm[m], q) for m in MODES]) + " |")
        w("")

    w("## Bermudan (504/yr) vs American gap per option\n")
    w("Gap = American − Bermudan 504/yr (PDE), relative to |American| in brackets; 'price gap in se' = gap / se "
      "of the mean of 100 labels.\n")
    for s, (lab, ref, R) in data.items():
        A, B = R["American"], R["Bermudan 504/yr"]
        po = POS[(s, "American")].set_index(["id", "greek"])
        opts = ref.drop_duplicates("id").set_index("id")
        w(f"### {SETS[s]}\n")
        w("| id | T | σ | r | d | K | price | Δ | Γ | Θ | Charm | Rho | Phi | price gap in se |")
        w("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for i, o in opts.iterrows():
            cs = []
            for q in ("price", "delta", "gamma", "theta", "charm", "rho", "phi"):
                gap = A.loc[i, q] - B.loc[i, q]
                rel = f" [{100 * gap / abs(A.loc[i, q]):+.3f}%]" if abs(A.loc[i, q]) > 1e-12 else ""
                cs.append(f"{gap:+.1e}{rel}")
            se = po.loc[(i, "price"), "se"] if (i, "price") in po.index else 0
            ins = f"{(A.loc[i, 'price'] - B.loc[i, 'price']) / se:+.1f}" if se > 0 else "exact"
            w(f"| {i} | {o['T']:g} | {o.sigma:.2%} | {o.r:.2%} | {o.d:.2%} | {o.K:g} | " + " | ".join(cs)
              + f" | {ins} |")
        w("")

    w("## Every option and Greek (default label, vs American)\n")
    w("Cells: reference · bias ± se (t) [relative bias %, relative noise %].\n")
    for s, (lab, ref, R) in data.items():
        po = POS[(s, "American")].set_index(["id", "greek"])
        opts = ref.drop_duplicates("id").set_index("id")
        w(f"### {SETS[s]}\n")
        w("| id | T | σ | r | d | K | Greek | American | Bermudan 504 | label: bias ± se (t) [rel %, noise %] |")
        w("|---|---|---|---|---|---|---|---|---|---|")
        for i, o in opts.iterrows():
            for q in GREEKS:
                if (i, q) not in po.index:
                    continue
                r = po.loc[(i, q)]
                rb = f"{100 * r.rel_bias:+.2f}" if np.isfinite(r.rel_bias) else "–"
                rn = f"{100 * r.rel_noise:.1f}" if np.isfinite(r.rel_noise) else "–"
                w(f"| {i} | {o['T']:g} | {o.sigma:.2%} | {o.r:.2%} | {o.d:.2%} | {o.K:g} | {q} | "
                  f"{R['American'].loc[i, q]:+.4f} | {R['Bermudan 504/yr'].loc[i, q]:+.4f} | "
                  f"{r.bias:+.4f} ± {r.se:.4f} ({r.t:+.1f}) [{rb}, {rn}] |")
        w("")
    (DEST / "report.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[: L.index("## Bermudan (504/yr) vs American gap per option\n")]))


if __name__ == "__main__":
    main()
