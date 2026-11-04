"""Distribution of the per-option bias of the out-of-sample, in-sample and
averaged labels, confidence intervals, and the stability of the selected widths
alpha*. Not part of the paper. Reads results/two_per_day/raw (75 options x 100
labels, 504 dates a year, 300k main paths; made with exercise_rule="pilot",
which also stores the in-sample version on the same paths, and without the
exercise bound). Writes results/diagnostics/bias_distribution/.

    python experiments/diagnostics/bias_distribution.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from simgreeks.multi import ALPHA_CAP, MultiConfig  # noqa: E402

RAW = ROOT / "results" / "two_per_day" / "raw"
OUT = ROOT / "results" / "diagnostics" / "bias_distribution"
GREEKS = ["price", "delta", "gamma", "theta", "charm", "vega", "volga", "vanna", "rho", "phi",
          "delta_r", "delta_d"]
VERSIONS = {"oos": ("out of sample", "#eb6834"), "ins": ("in sample (now the default)", "#1baf7a"),
            "avg": ("averaged (the earlier default)", "#2a78d6")}
COL = {"oos": "{}_oos", "ins": "{}_ins", "avg": "{}_avg"}


def load():
    L = pd.concat([pd.read_parquet(RAW / f"{p}_labels.parquet") for p in ("check", "random")])
    R = pd.concat([pd.read_parquet(RAW / f"{p}_reference.parquet") for p in ("check", "random")])
    for df in (L, R):                       # "tpd_check" -> "check"
        df["part"] = df["part"].str.replace("tpd_", "", regex=False).str.replace("_ref", "", regex=False)
    return L, R.set_index(["part", "id"])


def per_option(L, R) -> pd.DataFrame:
    """One row per option, Greek and version: bias, se and noise in % of |American PDE|.
    Left out: options in the exercise region and, per Greek, |PDE| < 1 % of the
    largest in its part or a label with zero noise (exact: no path exercises)."""
    rows = []
    for (part, i), g in L.groupby(["part", "id"]):
        ref_row = R.loc[(part, i), :]
        if ref_row.ex_region or g.ex_region.mean() > 0.5:
            continue
        for q in GREEKS:
            ref = ref_row[q]
            big = R.loc[part][q].abs().max()
            if abs(ref) < 0.01 * big:
                continue
            for v in VERSIONS:
                x = g[COL[v].format(q)]
                sd = x.std(ddof=1)
                if not sd > 1e-12 * abs(ref):
                    continue
                rows.append(dict(part=part, id=i, greek=q, version=v, n=len(x), ref=ref,
                                 T=ref_row["T"], sigma=ref_row.sigma, r=ref_row.r, d=ref_row.d,
                                 bias=100 * (x.mean() - ref) / abs(ref),
                                 se=100 * sd / np.sqrt(len(x)) / abs(ref),
                                 noise=100 * sd / abs(ref)))
    return pd.DataFrame(rows)


def summary_table(d: pd.DataFrame) -> list:
    lines = ["| Greek | version | options | median bias | IQR of bias | sd of bias (true) | median se | "
             "CI excludes 0 | median noise | labels to resolve the median bias |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for q in GREEKS:
        for v in VERSIONS:
            x = d[(d.greek == q) & (d.version == v)]
            if x.empty:
                continue
            true_var = max(x.bias.var(ddof=1) - (x.se ** 2).mean(), 0.0)
            excl = (np.abs(x.bias) > 1.96 * x.se).mean()
            q1, q3 = x.bias.quantile([0.25, 0.75])
            mb = np.median(np.abs(x.bias))
            need = f"{(1.96 * x.noise.median() / mb) ** 2:,.0f}" if mb > 0 else "—"
            lines.append(f"| {q} | {v} | {len(x)} | {x.bias.median():+.3g} | {q1:+.3g} to {q3:+.3g} | "
                         f"{np.sqrt(true_var):.3g} | {x.se.median():.3g} | {100 * excl:.0f} % | "
                         f"{x.noise.median():.3g} | {need} |")
    return lines


def histograms(d: pd.DataFrame, path: Path) -> None:
    sel = ["price", "delta", "gamma", "theta", "vega", "volga", "rho", "phi"]
    fig, axs = plt.subplots(2, 4, figsize=(15, 6.4))
    for ax, q in zip(axs.ravel(), sel):
        x = d[d.greek == q]
        lo, hi = x.bias.quantile([0.02, 0.98])
        span = max(abs(lo), abs(hi))
        bins = np.linspace(-span, span, 31)
        for v, (name, c) in VERSIONS.items():
            ax.hist(np.clip(x[x.version == v].bias, -span, span), bins=bins, histtype="step", lw=1.8,
                    color=c, label=name)
        ax.axvline(0, color="k", lw=0.9)
        ax.set_title(q, loc="left", fontsize=10, fontweight="bold")
        ax.set_xlabel("bias of the option's mean label, % of |PDE|", fontsize=8)
    axs[0, 0].legend(fontsize=7.5, frameon=False, loc="upper left")
    fig.suptitle("Per-option bias, 75 options x 100 labels, 504 dates a year, 300k main paths "
                 "(values beyond the 2nd/98th percentile drawn at the edge)", fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def ci_plot(d: pd.DataFrame, path: Path) -> None:
    sel = ["price", "delta", "gamma", "volga"]
    fig, axs = plt.subplots(1, 4, figsize=(15, 4.2))
    for ax, q in zip(axs, sel):
        for k, (v, (name, c)) in enumerate(VERSIONS.items()):
            x = d[(d.greek == q) & (d.version == v)].sort_values("bias").reset_index(drop=True)
            y = np.arange(len(x)) + (k - 1) * 0.25
            ax.errorbar(x.bias, y, xerr=1.96 * x.se, fmt="o", ms=2.2, lw=0.7, color=c, label=name)
        ax.axvline(0, color="k", lw=0.9)
        lo, hi = d[d.greek == q].bias.quantile([0.03, 0.97])
        pad = 0.15 * (hi - lo)
        ax.set_xlim(lo - pad, hi + pad)          # a few outlying options fall outside
        ax.set_title(q, loc="left", fontsize=10, fontweight="bold")
        ax.set_yticks([]); ax.set_xlabel("bias ± 95 % CI, % of |PDE| (options sorted per version)", fontsize=8)
    fig.legend(*axs[0].get_legend_handles_labels(), loc="lower center", ncol=3, fontsize=8, frameon=False)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(path, dpi=130)
    plt.close(fig)


def alpha_section(L) -> list:
    """alpha* of every label: where it sits between its bounds and how much it varies."""
    cfg = MultiConfig()
    L = L[(L.alpha_S > 0) & ~L.ex_region.astype(bool)].copy()
    sqT = np.sqrt(L["T"])
    a0S = np.minimum(cfg.c0_S, cfg.c0_S_sd * L.sigma * sqT) * L.S0
    capS = np.minimum(a0S, ALPHA_CAP * L.S0)
    capV = cfg.c0_sigma * L.sigma / cfg.pilot_widen
    L["rS"] = L.alpha_S / (L.S0 * L.sigma * sqT)          # alpha_S in units of S0 sigma sqrt(T)
    L["rV"] = L.alpha_sigma / L.sigma                      # alpha_sigma in units of sigma
    L["capS"] = np.isclose(L.alpha_S, capS, rtol=1e-6)
    L["capV"] = np.isclose(L.alpha_sigma, capV, rtol=1e-6)
    g = L.groupby(["part", "id"])
    per = pd.DataFrame({"T": g["T"].first(), "sigma": g.sigma.first(), "rS": g.rS.median(),
                        "cvS": g.alpha_S.std() / g.alpha_S.mean(), "rV": g.rV.median(),
                        "cvV": g.alpha_sigma.std() / g.alpha_sigma.mean(),
                        "capS": g.capS.mean(), "capV": g.capV.mean()})
    # selection bias check: within an option, does a smaller alpha_S go with a larger Gamma?
    cors = []
    for _, x in L.groupby(["part", "id"]):
        if x.alpha_S.std() > 0 and x.gamma_ins.std() > 0:
            cors.append(np.corrcoef(x.alpha_S, x.gamma_ins)[0, 1])
    lines = ["## Selected widths alpha*", "",
             f"{len(L)} labels of {len(per)} options (labels in the exercise region or exact left out). "
             "alpha_S is in units of S0·σ√T, alpha_σ in units of σ; spread = coefficient of variation "
             "of alpha* over the 100 labels of an option; at the cap = share of labels whose alpha* is "
             f"the upper bound (alpha_S: the pilot width min(0.25, 1.25 σ√T)·S0; alpha_σ: "
             f"{cfg.c0_sigma}σ / {cfg.pilot_widen}).", "",
             "| | median over options | 5–95 % of options |", "|---|---|---|"]
    for col, name in (("rS", "alpha_S / (S0 σ√T)"), ("cvS", "spread of alpha_S within an option"),
                      ("capS", "alpha_S at the cap"), ("rV", "alpha_σ / σ"),
                      ("cvV", "spread of alpha_σ within an option"), ("capV", "alpha_σ at the cap")):
        q5, q50, q95 = per[col].quantile([0.05, 0.5, 0.95])
        fmt = (lambda v: f"{100 * v:.0f} %") if col.startswith(("cv", "cap")) else (lambda v: f"{v:.3g}")
        lines.append(f"| {name} | {fmt(q50)} | {fmt(q5)} – {fmt(q95)} |")
    lines += ["", f"Correlation, within an option, between alpha_S and the in-sample Gamma: median "
              f"{np.median(cors):+.2f} over {len(cors)} options (5–95 %: {np.percentile(cors, 5):+.2f} to "
              f"{np.percentile(cors, 95):+.2f}). The pilot paths are independent of the main paths, so "
              "alpha* should not track the label's own noise; a clearly negative value would mean a "
              "selection bias (small alpha where the data look curved).", ""]
    worst = per.sort_values("capS", ascending=False).head(5)
    lines += ["Options with the most labels at the alpha_S cap:", "",
              "| option | T | σ | alpha_S / (S0 σ√T) | at the cap |", "|---|---|---|---|---|"]
    for (p, i), r in worst.iterrows():
        lines.append(f"| {p} {i} | {r['T']:.2f} | {100 * r.sigma:.1f} % | {r.rS:.3g} | {100 * r.capS:.0f} % |")
    return lines


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    L, R = load()
    d = per_option(L, R)
    d.to_csv(OUT / "per_option.csv", index=False)
    histograms(d, OUT / "histograms.png")
    ci_plot(d, OUT / "confidence_intervals.png")
    lines = ["# Distribution of the bias, confidence intervals, alpha*", "",
             "Not part of the paper. `experiments/diagnostics/bias_distribution.py`. Data: "
             "`results/two_per_day/raw` (75 options x 100 labels, 504 dates a year, 300k main paths, "
             "made with the pilot's rule (`exercise_rule=\"pilot\"`) and without the exercise bound; "
             "its in-sample version is the current default label except for the bound, which only "
             "changes options with r < d). Reference: the American PDE.", "",
             "Per option and Greek: bias = (mean of its labels − PDE) / |PDE|, se = sd / √n / |PDE| "
             "(n = 100), noise = sd / |PDE|, all in %. 95 % confidence interval of an option's bias: "
             "bias ± 1.96 se. Its half-width is 1.96 · noise / √n, so it depends on the noise: to pin "
             "a bias down to ±0.1 × one label's noise takes (1.96 / 0.1)² ≈ 384 labels of the option; "
             "labels to resolve the median bias = (1.96 · median noise / median |bias|)², the labels of one "
             "option needed for a typical bias to be significant. "
             "sd of bias (true) = the spread of the bias across options with the labels' own noise "
             "removed, √(var(bias) − mean(se²)). Left out: options in the exercise region and, per "
             "Greek, |PDE| < 1 % of its largest value or labels with zero noise (exact).", "",
             "![histograms](histograms.png)", "", "![confidence intervals](confidence_intervals.png)", ""]
    lines += summary_table(d) + [""]
    lines += alpha_section(L)
    (OUT / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
