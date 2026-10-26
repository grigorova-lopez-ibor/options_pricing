"""Bias, noise and significance of a label CSV with reference values
(experiments/generate_labels.py --exact), overall and by region. Not part of
the paper.

    python experiments/diagnostics/label_run_report.py LABELS.csv [--out REPORT.md]

One label per option, so per Greek: bias = mean over options of the signed
relative error (label - reference) / |reference| (± se over options, t);
scaled bias = mean (label - reference) / mean |reference| (for Greeks that cross
zero); typical / median error = mean / median |relative error|, mostly the noise
of one label. Options where both label and reference are in the exercise region
(exact values) are left out and counted; for each Greek, options with
|reference| < 1 % of its largest |reference| are left out of the relative errors.
Regions: sigma (tails < 5 %, > 50 %), T, S0/K, r < d, small r.

Theta and Charm are pathwise with the number of exercise dates fixed; the
reference's are calendar ones (dates fixed in calendar time), which differ by
0.3-2.7 % and up to ~6 % at 50 dates a year (results/diagnostics/theta_pathwise);
theta_pde is the PDE-identity Theta.
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

GREEKS = ["price", "delta", "gamma", "theta", "charm", "vega", "volga", "vanna", "rho", "phi",
          "delta_r", "delta_d", "theta_pde"]
KEY = ["price", "delta", "gamma", "theta", "charm", "vega", "rho", "phi"]


def regions(df):
    return {
        "sigma < 5 % (lower tail)": df.sigma < 0.05,
        "sigma 5-50 %": (df.sigma >= 0.05) & (df.sigma <= 0.5),
        "sigma > 50 % (upper tail)": df.sigma > 0.5,
        "T < 0.5": df["T"] < 0.5,
        "T 0.5-1": (df["T"] >= 0.5) & (df["T"] < 1),
        "T >= 1": df["T"] >= 1,
        "S0/K < 0.9 (in the money)": df.moneyness < 0.9,
        "S0/K 0.9-1.1": (df.moneyness >= 0.9) & (df.moneyness <= 1.1),
        "S0/K > 1.1 (out of the money)": df.moneyness > 1.1,
        "r < d": df.r < df.d,
        "r >= d": df.r >= df.d,
        "0 < r < 1 %": (df.r > 0) & (df.r < 0.01),
    }


def stats(d, g, floor):
    ref, lab = d[f"exact_{g}"], d[g]
    big = ref.abs() >= floor
    e = 100 * (lab[big] - ref[big]) / ref[big].abs()
    if len(e) < 3:
        return None
    b, se = e.mean(), e.std() / np.sqrt(len(e))
    scaled = 100 * (lab - ref).mean() / ref.abs().mean() if ref.abs().mean() > 0 else np.nan
    scaled_se = 100 * (lab - ref).std() / np.sqrt(len(d)) / ref.abs().mean() if ref.abs().mean() > 0 else np.nan
    return dict(n=len(e), bias=b, se=se, t=b / se if se > 0 else np.nan, scaled=scaled,
                scaled_t=scaled / scaled_se if scaled_se > 0 else np.nan,
                typical=e.abs().mean(), median=e.abs().median())


def fmt(s):
    flag = "†" if abs(s["t"]) > 2.576 else ""
    return f"{s['bias']:+.2f} ± {s['se']:.2f} ({s['t']:+.1f}){flag}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    df = pd.read_csv(args.csv)
    ref_ex = (df.exact_price == df.K - df.S0) & (df.exact_delta == -1.0)
    both = df.ex_region & ref_ex
    lines = [f"# Label check: {args.csv}", "",
             f"{len(df)} options; {int(both.sum())} in the exercise region for both label and reference "
             f"(exact, left out); exercise-region disagreements: label only {int((df.ex_region & ~ref_ex).sum())}, "
             f"reference only {int((~df.ex_region & ref_ex).sum())}.", "",
             "Inputs: S0/K {:.2f}-{:.2f}, sigma {:.4f}-{:.4f} ({:.1%} below 5 %, {:.1%} above 50 %), "
             "r {:.4f}-{:.4f}, d {:.4f}-{:.4f}, T {:.3f}-{:.3f}.".format(
                 df.moneyness.min(), df.moneyness.max(), df.sigma.min(), df.sigma.max(),
                 (df.sigma < 0.05).mean(), (df.sigma > 0.5).mean(), df.r.min(), df.r.max(),
                 df.d.min(), df.d.max(), df["T"].min(), df["T"].max()), "",
             __doc__.split("\n\n")[2].replace("\n", " "), "",
             "† = |t| > 2.576.", "",
             "## All options", "",
             "| Greek | n | bias % ± se (t) | scaled bias % (t) | typical error % | median error % |",
             "|---|---|---|---|---|---|"]
    d0 = df[~both]
    floors = {g: 0.01 * d0[f"exact_{g}"].abs().max() for g in GREEKS}
    for g in GREEKS:
        s = stats(d0, g, floors[g])
        if s:
            lines.append(f"| {g} | {s['n']} | {fmt(s)} | {s['scaled']:+.2f} ({s['scaled_t']:+.1f}) | "
                         f"{s['typical']:.2f} | {s['median']:.2f} |")
    lines += ["", "## By region: bias % ± se (t) / median error %", "",
              "| region | n | " + " | ".join(KEY) + " |", "|---|---|" + "---|" * len(KEY)]
    for name, mask in regions(d0).items():
        d = d0[mask]
        cells = []
        for g in KEY:
            s = stats(d, g, floors[g])
            cells.append("–" if s is None else f"{fmt(s)} / {s['median']:.1f}")
        lines.append(f"| {name} | {len(d)} | " + " | ".join(cells) + " |")
    lines += ["", "## Largest relative errors (price, Delta, Gamma, Theta, Rho)", "",
              "| Greek | S0/K | sigma | r | d | T | label | reference | error % |", "|---|---|---|---|---|---|---|---|---|"]
    for g in ["price", "delta", "gamma", "theta", "rho"]:
        d = d0[d0[f"exact_{g}"].abs() >= floors[g]].copy()
        d["err"] = 100 * (d[g] - d[f"exact_{g}"]) / d[f"exact_{g}"].abs()
        for _, row in d.reindex(d.err.abs().sort_values(ascending=False).index).head(3).iterrows():
            lines.append(f"| {g} | {row.moneyness:.3f} | {row.sigma:.4f} | {row.r:.4f} | {row.d:.4f} | "
                         f"{row['T']:.3f} | {row[g]:.4g} | {row[f'exact_{g}']:.4g} | {row.err:+.1f} |")
    if "seconds" in df:
        lines.append(f"\nMean seconds per option: {df.seconds.mean():.1f}.")
    text = "\n".join(lines) + "\n"
    if args.out:
        args.out.write_text(text)
    print(text)


if __name__ == "__main__":
    main()
