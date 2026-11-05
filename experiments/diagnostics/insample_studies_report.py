"""Summaries of the in-sample studies (insample_studies.py). Not part of the
paper. Writes results/diagnostics/insample_studies/<study>/summary.md for each
study whose raw.csv exists.

    python experiments/diagnostics/insample_studies_report.py [study ...]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "experiments" / "diagnostics")]
from insample_studies import ALPHA_MULTS, OUT, TPD, Q  # noqa: E402

SHOW = ["price", "delta", "gamma", "theta", "vega", "volga", "vanna", "rho", "phi"]


def tpd_refs() -> pd.DataFrame:
    R = pd.concat([pd.read_parquet(TPD / f"{p}_reference.parquet") for p in ("check", "random")])
    R["part"] = R["part"].str.replace("tpd_", "", regex=False).str.replace("_ref", "", regex=False)
    return R.set_index(["part", "id"])


def stats(g: pd.DataFrame, ref: float, q: str) -> dict:
    a = abs(ref)
    x = g[q].astype(float)
    sd = x.std(ddof=1)
    return dict(bias=100 * (x.mean() - ref) / a, se=100 * sd / np.sqrt(len(x)) / a, noise=100 * sd / a,
                n=len(x))


def big_enough(R: pd.DataFrame, part: str, q: str, ref: float) -> bool:
    return abs(ref) >= 0.01 * R.loc[part][q].abs().max()


def fmt(v, d=3):
    return "—" if v != v else f"{v:+.{d}g}"


# ------------------------------------------------------------------ paths
def report_paths() -> list:
    raw = pd.read_csv(OUT / "paths" / "raw.csv")
    R = tpd_refs()
    rows = []
    for (part, i, N), g in raw.groupby(["part", "id", "N_main"]):
        r = R.loc[(part, i), :]
        for q in Q:
            if not big_enough(R, part, q, r[q]):
                continue
            s = stats(g, r[q], q)
            if s["noise"] < 1e-9:                   # exact label (r < d, no early exercise)
                continue
            rows.append(dict(part=part, id=i, N=N, greek=q, **s))
    d = pd.DataFrame(rows)
    Ns = sorted(d.N.unique())
    measured = raw.groupby("N_main").seconds.mean()
    # 300k and 600k ran on an otherwise idle machine; 150k and 450k shared it with other
    # jobs, so their times are inflated. Time per label ~ k N from the two clean runs.
    k = (measured[300_000] * 300_000 + measured[600_000] * 600_000) / (300_000 ** 2 + 600_000 ** 2)
    t = pd.Series({n: k * n for n in Ns})
    lines = ["# In-sample label against the number of main paths", "",
             "Not part of the paper. `experiments/diagnostics/insample_studies.py paths`: the default "
             "in-sample label (exercise bound on) at 150k, 300k, 450k and 600k main paths (pilot 100k), 504 "
             "dates a year, 40 labels per option and path count with the same seeds, on the 14 options of "
             "the 600k Volga check (picked as the worst in-sample Volga in results/two_per_day, so the "
             "biases here are larger than typical). Reference: the American PDE. Options whose label is "
             "exact (r < d: no path exercises early) are left out per Greek.", "",
             "Mean time per label measured (4 processes on this machine): "
             + ", ".join(f"{int(n / 1000)}k {measured[n]:.1f} s" for n in Ns) + ". The 150k and 450k "
             "labels ran while other jobs used the machine, so their times are inflated; the budget below "
             f"uses t(N) = {1000 * k:.4f} s per 1,000 main paths, fitted to the 300k and 600k runs (made "
             "under the same conditions): " + ", ".join(f"{int(n / 1000)}k {t[n]:.1f} s" for n in Ns) + ".", "",
             "Median over the options of |bias| and of the noise of one label, % of |PDE|:", "",
             "| Greek | options | " + " | ".join(f"|bias| {int(n / 1000)}k" for n in Ns) + " | "
             + " | ".join(f"noise {int(n / 1000)}k" for n in Ns) + " |",
             "|---|---|" + "---|" * (2 * len(Ns))]
    for q in SHOW:
        x = d[d.greek == q]
        if x.empty:
            continue
        b = [x[x.N == n].bias.abs().median() for n in Ns]
        s = [x[x.N == n].noise.median() for n in Ns]
        lines.append(f"| {q} | {x.id.nunique()} | " + " | ".join(f"{v:.3g}" for v in b) + " | "
                     + " | ".join(f"{v:.3g}" for v in s) + " |")
    # Volga per option
    v = d[d.greek == "volga"].pivot_table(index=["part", "id"], columns="N", values=["bias", "se"])
    lines += ["", "In-sample Volga bias per option, % ± se:", "",
              "| option | " + " | ".join(f"{int(n / 1000)}k" for n in Ns) + " |", "|---|" + "---|" * len(Ns)]
    for (p, i), r in v.iterrows():
        lines.append(f"| {p} {i} | " + " | ".join(f"{r[('bias', n)]:+.1f} ± {r[('se', n)]:.1f}" for n in Ns) + " |")
    # budget: error of the mean label for a fixed CPU time per option
    lines += ["", "## Fixed budget", "",
              "Expected error of the mean of the labels one option gets for C CPU seconds: "
              "√(b² + s² · t(N) / C), b = median bias with its sampling noise removed, s = median noise, "
              "t(N) the time per label. C stands for the budget per neighbourhood of the network's inputs, "
              "since a network fitted to noisy labels averages nearby ones the same way.", "",
              "| Greek | C = 100 s | 1,000 s | 10,000 s | 100,000 s |", "|---|---|---|---|---|"]
    for q in SHOW:
        x = d[d.greek == q]
        if x.empty:
            continue
        cells = []
        for C in (1e2, 1e3, 1e4, 1e5):
            best = None
            for n in Ns:
                y = x[x.N == n]
                b = np.sqrt(max(np.median(y.bias ** 2) - np.median(y.se ** 2), 0.0))
                e = np.sqrt(b ** 2 + y.noise.median() ** 2 * t[n] / C)
                if best is None or e < best[1]:
                    best = (n, e)
            cells.append(f"{int(best[0] / 1000)}k ({best[1]:.2g} %)")
        lines.append(f"| {q} | " + " | ".join(cells) + " |")
    lines += ["", "Each cell: the path count with the smallest expected error, and that error.", ""]
    return lines


# ------------------------------------------------------------------ alpha
def report_alpha() -> list:
    raw = pd.read_csv(OUT / "alpha" / "raw.csv")
    R = tpd_refs()
    rows = []
    for (part, i, m), g in raw.groupby(["part", "id", "mult"]):
        r = R.loc[(part, i), :]
        for q in SHOW:
            if not big_enough(R, part, q, r[q]):
                continue
            s = stats(g, r[q], q)
            rows.append(dict(part=part, id=i, mult=m, greek=q, aS=g.alpha_S.median(),
                             aV=g.alpha_sigma.median(), **s))
    d = pd.DataFrame(rows)
    mults = [0.0] + list(ALPHA_MULTS)
    name = {0.0: "selector"} | {m: f"{m:g}×" for m in ALPHA_MULTS}
    lines = ["# Selected widths alpha* against fixed widths", "",
             "Not part of the paper. `experiments/diagnostics/insample_studies.py alpha`: 6 options of "
             "results/two_per_day, 504 dates a year, 300k main paths, in-sample rule, 30 labels each: the "
             "default (the selector chooses alpha_S and alpha_σ on the pilot, label by label) and fixed "
             "widths at 0.5, 0.75, 1, 1.5 and 2 × the median selected alpha* of the option (no pilot). "
             "Reference: the American PDE. Root mean square error of one label = √(bias² + noise²); of the "
             "mean of 100 labels = √(bias² + noise² / 100). Median over the options, % of |PDE|.", ""]
    for label, n in (("one label", 1), ("mean of 100 labels", 100)):
        lines += [f"Error of the {label}:", "", "| Greek | " + " | ".join(name[m] for m in mults) + " |",
                  "|---|" + "---|" * len(mults)]
        for q in SHOW:
            x = d[d.greek == q]
            if x.empty:
                continue
            e = [np.sqrt(x[x.mult == m].bias ** 2 + x[x.mult == m].noise ** 2 / n).median() for m in mults]
            k = int(np.nanargmin(e))
            lines.append(f"| {q} | " + " | ".join((f"**{v:.3g}**" if j == k else f"{v:.3g}")
                                                   for j, v in enumerate(e)) + " |")
        lines.append("")
    lines += ["Median |bias| and noise of one label by width:", "",
              "| Greek | " + " | ".join(f"{name[m]} bias / noise" for m in mults) + " |",
              "|---|" + "---|" * len(mults)]
    for q in SHOW:
        x = d[d.greek == q]
        if x.empty:
            continue
        lines.append(f"| {q} | " + " | ".join(f"{x[x.mult == m].bias.abs().median():.3g} / "
                                               f"{x[x.mult == m].noise.median():.3g}" for m in mults) + " |")
    lines += ["", "Bold: the width with the smallest error. The selector targets Γ (alpha_S) and Volga (alpha_σ).", ""]
    return lines


# ------------------------------------------------------------------ dates
def report_dates() -> list:
    raw = pd.read_csv(OUT / "dates" / "raw.csv")
    ref = pd.read_csv(OUT / "dates" / "ref.csv")
    am = ref[ref["style"] == "american"].set_index(["part", "id"])
    be = ref[ref["style"] == "bermudan"].set_index(["part", "id", "spy"])
    rows = []
    for (part, i, spy), g in raw.groupby(["part", "id", "spy"]):
        for q in SHOW:
            ra, rb = am.loc[(part, i), q], be.loc[(part, i, spy), q]
            if abs(ra) < 0.01 * am[q].abs().max():
                continue
            sa, sb = stats(g, ra, q), stats(g, rb, q)
            if sa["noise"] < 1e-9:
                continue
            gap = 100 * (rb - ra) / abs(ra)
            rows.append(dict(part=part, id=i, spy=spy, greek=q, bias_am=sa["bias"], bias_be=sb["bias"],
                             se=sa["se"], noise=sa["noise"], gap=gap))
    d = pd.DataFrame(rows)
    t = raw.groupby("spy").seconds.mean()
    tr = ref[ref["style"] == "bermudan"].groupby("spy").seconds.mean()
    spys = sorted(d.spy.unique())
    lines = ["# Noise and bias against the number of exercise dates", "",
             "Not part of the paper. `experiments/diagnostics/insample_studies.py dates`: the default "
             "in-sample label (300k main paths, value function at 1/50 year above 50 dates a year) at 50, 252 "
             "and 504 exercise dates a year, 30 labels per option and frequency, on 20 options of "
             "results/two_per_day with T ≤ 1. Bias against the Bermudan PDE at the same dates (the method's "
             "own bias) and against the American PDE (what the network should learn); gap = Bermudan − "
             "American. Median over the options, % of |PDE|.", "",
             "Time per label: " + ", ".join(f"{s}/yr {t[s]:.1f} s" for s in spys)
             + "; Bermudan reference: " + ", ".join(f"{s}/yr {tr[s]:.1f} s" for s in spys) + ".", "",
             "| Greek | " + " | ".join(f"{s}/yr bias vs Berm. / vs Amer. / gap / noise" for s in spys) + " |",
             "|---|" + "---|" * len(spys)]
    for q in SHOW:
        x = d[d.greek == q]
        if x.empty:
            continue
        cells = []
        for s in spys:
            y = x[x.spy == s]
            cells.append(f"{y.bias_be.median():+.3g} / {y.bias_am.median():+.3g} / {y.gap.median():+.3g} / "
                         f"{y.noise.median():.3g}")
        lines.append(f"| {q} | " + " | ".join(cells) + " |")
    lines.append("")
    return lines


# ------------------------------------------------------------------ crn
def report_crn() -> list:
    from scipy.spatial import cKDTree
    raw = pd.read_csv(OUT / "crn" / "raw.csv")
    ref = pd.read_csv(OUT / "crn" / "ref.csv").set_index("id")
    from insample_studies import crn_options
    X = crn_options().set_index("id")
    X["m"] = X.S0 / X.K
    cols = ["m", "sigma", "r", "d", "T"]
    Z = (X[cols] - X[cols].min()) / (X[cols].max() - X[cols].min())
    tree = cKDTree(Z.values)
    lines = ["# Common random numbers against independent paths", "",
             "Not part of the paper. `experiments/diagnostics/insample_studies.py crn`: 2,000 options from "
             "the training-set ranges at 50 dates a year, labelled twice with the default in-sample label: "
             "with a fresh seed per option (independent) and with one seed for every option (common random "
             "numbers, the same random shocks for all), against the Bermudan PDE. The network is stood in "
             "for by two smoothers of the label errors over the inputs (S0/K, σ, r, d, T scaled to [0, 1]): "
             "the mean over each option's k nearest neighbours, and a cubic polynomial fitted to all 2,000. "
             "What a smoother leaves is the error a network trained on these labels would keep. Errors in % "
             "of |PDE|; options with |PDE| < 1 % of the largest and exact labels left out per Greek.", "",
             "| Greek | mode | one label: median abs. / RMS | corr. with nearest neighbour | mean of 10 nearest | mean of 50 nearest | cubic fit |",
             "|---|---|---|---|---|---|---|"]
    from itertools import combinations_with_replacement
    P = np.column_stack([np.ones(len(Z))] + [np.prod(Z.values[:, list(c)], axis=1)
                                             for k in (1, 2, 3) for c in combinations_with_replacement(range(5), k)])
    _, nn = tree.query(Z.values, k=51)
    for q in SHOW:
        for mode in ("independent", "common"):
            lab = raw[raw["mode"] == mode].set_index("id")[q].reindex(X.index)
            r = ref[q].reindex(X.index)
            e = 100 * (lab - r) / r.abs()
            ok = (r.abs() >= 0.01 * r.abs().max()) & e.notna()
            e = e.where(ok)
            ev = e.values
            corr = pd.Series(ev).corr(pd.Series(ev[nn[:, 1]]))
            k10 = np.nanmean(ev[nn[:, 1:11]], axis=1)
            k50 = np.nanmean(ev[nn[:, 1:51]], axis=1)
            m = ok.values
            coef = np.linalg.lstsq(P[m], ev[m], rcond=None)[0]
            fit = P @ coef
            rms = lambda a: float(np.sqrt(np.nanmean(np.where(m, a, np.nan) ** 2)))
            lines.append(f"| {q} | {mode} | {np.nanmedian(np.abs(ev)):.3g} / {rms(ev):.3g} | {corr:+.2f} | {rms(k10):.3g} | {rms(k50):.3g} | "
                         f"{rms(fit):.3g} |")
    t = raw.groupby("mode").seconds.mean()
    lines += ["", "RMS columns are sensitive to single options with near-zero reference values (e.g. one "
              "option at σ = 3.5 % has a Vega error of 620 % with common random numbers and 63 % without); "
              "the medians are the robust comparison.", "", "Time per label: " + ", ".join(f"{k} {v:.1f} s" for k, v in t.items()) + ".", ""]
    return lines


# ------------------------------------------------------------------ width rule
def report_widthrule() -> list:
    from scipy.stats import binomtest
    from insample_studies import RULE_MULTS, RULE_S, RULE_SIGMA
    raw = pd.read_csv(OUT / "widthrule" / "raw.csv")
    ref = pd.read_csv(OUT / "widthrule" / "ref.csv")
    be = ref[ref["style"] == "bermudan"].set_index("id")
    am = ref[ref["style"] == "american"].set_index("id")
    configs = [0.0] + list(RULE_MULTS)
    name = {0.0: "selector"} | {m: f"rule {m:g}×" for m in RULE_MULTS}
    rows = []
    for (i, m), g in raw.groupby(["id", "mult"]):
        for q in SHOW:
            rb, ra = be.loc[i, q], am.loc[i, q]
            if abs(rb) < 0.01 * be[q].abs().max() or be.loc[i, "ex_region"]:
                continue
            sb, sa = stats(g, rb, q), stats(g, ra, q)
            if sb["noise"] < 1e-9:
                continue
            b2 = max(sb["bias"] ** 2 - sb["se"] ** 2, 0.0)          # bias with its own noise removed
            rows.append(dict(id=i, mult=m, greek=q, bias=sb["bias"], bias_am=sa["bias"], se=sb["se"],
                             noise=sb["noise"], e1=np.sqrt(b2 + sb["noise"] ** 2),
                             e100=np.sqrt(b2 + sb["noise"] ** 2 / 100)))
    d = pd.DataFrame(rows)
    t = raw.groupby("mult").seconds.mean()
    a, b, c = RULE_S
    lines = ["# Width rule against the selector, out of sample", "",
             "Not part of the paper. `experiments/diagnostics/insample_studies.py widthrule`. The rule was "
             "fitted to the selector's median alpha* over the 67 options of results/two_per_day "
             f"(bias_distribution.py): alpha_S = {a} S0 (σ√T)^{b} T^{c} (capped at the pilot width "
             f"min(0.25, 1.25 σ√T) S0, as the selector is), alpha_σ = {RULE_SIGMA} σ. It is tested here on 25 "
             "other options from the training-set ranges (Sobol draw, r > d so that early exercise matters), "
             "20 in-sample labels per option and configuration, 252 dates a year, 300k main paths: the "
             "selector (the default: pilot of 100k paths, alpha* label by label) and the rule at 0.5, 1, 1.5 "
             "and 2 × (no pilot). Bias against the Bermudan PDE at the same dates (the method's own error); "
             "the bias against the American PDE adds the 252/yr gap (≤ 0.12 %, results/diagnostics/"
             "insample_studies/dates). Error of one label = √(b² + noise²), of the mean of 100 labels = "
             "√(b² + noise²/100), b the bias with its sampling noise removed; % of |PDE|, median over the "
             "options. Options in the exercise region, Greeks below 1 % of their largest |PDE| and exact "
             "labels are left out.", "",
             "Time per label: " + ", ".join(f"{name[m]} {t[m]:.1f} s" for m in configs) + ".", ""]
    for col, title in (("e100", "Error of the mean of 100 labels (the bias matters)"),
                       ("e1", "Error of one label (the noise matters)")):
        lines += [f"{title}:", "", "| Greek | options | " + " | ".join(name[m] for m in configs) + " |",
                  "|---|---|" + "---|" * len(configs)]
        for q in SHOW:
            x = d[d.greek == q]
            if x.empty:
                continue
            v = [x[x.mult == m][col].median() for m in configs]
            k = int(np.nanargmin(v))
            lines.append(f"| {q} | {x.id.nunique()} | " + " | ".join(
                (f"**{u:.3g}**" if j == k else f"{u:.3g}") for j, u in enumerate(v)) + " |")
        lines.append("")
    lines += ["Paired by option: share of options where the rule's mean-of-100 error is below the "
              "selector's, and the two-sided sign-test p-value:", "",
              "| Greek | " + " | ".join(name[m] for m in RULE_MULTS) + " |", "|---|" + "---|" * len(RULE_MULTS)]
    for q in SHOW:
        x = d[d.greek == q].pivot_table(index="id", columns="mult", values="e100")
        if x.empty or 0.0 not in x:
            continue
        cells = []
        for m in RULE_MULTS:
            y = x[[0.0, m]].dropna()
            wins = int((y[m] < y[0.0]).sum())
            n = len(y)
            p = binomtest(wins, n).pvalue if n else float("nan")
            cells.append(f"{wins}/{n} (p = {p:.2g})")
        lines.append(f"| {q} | " + " | ".join(cells) + " |")
    lines += ["", "Median bias against the American PDE (signed, %):", "",
              "| Greek | " + " | ".join(name[m] for m in configs) + " |", "|---|" + "---|" * len(configs)]
    for q in SHOW:
        x = d[d.greek == q]
        if x.empty:
            continue
        lines.append(f"| {q} | " + " | ".join(f"{x[x.mult == m].bias_am.median():+.3g}" for m in configs) + " |")
    lines.append("")
    return lines


REPORTS = {"paths": report_paths, "alpha": report_alpha, "dates": report_dates, "crn": report_crn,
           "widthrule": report_widthrule}

if __name__ == "__main__":
    for s in (sys.argv[1:] or REPORTS):
        if not (OUT / s / "raw.csv").exists():
            print(f"{s}: no data yet")
            continue
        lines = REPORTS[s]()
        (OUT / s / "summary.md").write_text("\n".join(lines) + "\n")
        print("\n".join(lines))
