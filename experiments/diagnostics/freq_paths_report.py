"""Report of freq_paths_grid.py: bias and noise of the in-sample label against the
number of exercise dates a year (SPY) and of main paths.

    python experiments/diagnostics/freq_paths_report.py --out OUT     # writes OUT/freq_paths/report.md

Per option and setting: rel. errors in % of |American PDE|; options with
|American| < 1 % of the largest and exact labels (exercise at t_0, no early
exercise) are left out. Cells are means over the options:
* gap      = |Bermudan(SPY) - American|, the exercise-date bias (exact, PDE);
* sim bias = |mean of the labels - Bermudan(SPY)|, the simulation bias;
* bias     = |mean of the labels - American|, the label's total bias;
* floor    = sqrt(2/pi) se, the part of the two MAEs above explained by noise alone;
* noise    = median sd of one label;
* seconds and peak memory per label."""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import freq_paths_grid as G  # noqa: E402

GREEKS = ["price", "delta", "gamma", "theta", "vega", "rho", "phi", "charm", "volga", "vanna",
          "delta_r", "delta_d"]


def per_option(lab: pd.DataFrame, refs: pd.DataFrame) -> pd.DataFrame:
    am = refs[refs["style"] == "american"].set_index("id")
    be = refs[refs["style"] == "bermudan"].set_index(["id", "spy"])
    rows = []
    for (i, spy, n), g in lab.groupby(["id", "spy", "N_main"]):
        if (i not in am.index) or ((i, spy) not in be.index):
            continue
        for q in GREEKS:
            x = g[q].dropna()
            if len(x) < 2:
                continue
            a, b = float(am.loc[i, q]), float(be.loc[(i, spy), q])
            sd = x.std(ddof=1)
            rows.append(dict(id=i, spy=spy, N_main=n, greek=q, n=len(x), am=a, berm=b,
                             mean=x.mean(), sd=sd, se=sd / np.sqrt(len(x)),
                             exact=sd <= 1e-9 * max(1.0, abs(a)) or bool(g.ex_region.any())))
    df = pd.DataFrame(rows)
    big = df.groupby("greek").am.transform(lambda s: s.abs().max())
    df = df[(df.am.abs() > 0.01 * big) & ~df.exact].copy()
    s = 100 / df.am.abs()
    df["gap"] = (df.berm - df.am).abs() * s
    df["sim"] = (df["mean"] - df.berm).abs() * s
    df["bias"] = (df["mean"] - df.am).abs() * s
    df["floor"] = np.sqrt(2 / np.pi) * df.se * s
    df["noise"] = df.sd * s
    return df


def table(po: pd.DataFrame, q: str, col: str, fmt="{:.3g}") -> list[str]:
    d = po[po.greek == q]
    agg = d.groupby(["spy", "N_main"])[col].median() if col == "noise" else d.groupby(["spy", "N_main"])[col].mean()
    out = ["| SPY \\ main paths | " + " | ".join(f"{n // 1000}k" for n in G.N_MAIN) + " |",
           "|---|" + "---|" * len(G.N_MAIN)]
    for spy in G.SPYS:
        out.append(f"| {spy} | " + " | ".join(fmt.format(agg.get((spy, n), np.nan)) for n in G.N_MAIN) + " |")
    return out


def report(out: str) -> str:
    lab, refs = G.load(out)
    po = per_option(lab, refs)
    w = [f"# In-sample label against exercise dates a year and main paths\n",
         f"{len(lab)} labels of {len(G.jobs())}; {po.id.nunique()} options used "
         f"(of {len(G.OPTIONS)}); pilot {G.N_PILOT:,} paths. % of |American PDE|; means over the "
         "options except noise (median). See the module docstring for the columns.\n"]
    t = lab.groupby(["spy", "N_main"]).agg(seconds=("seconds", "mean"), gb=("rss_mb", "max"))
    w.append("## Time per label (s, mean over options) / peak memory (GB)\n")
    w.append("| SPY \\ main paths | " + " | ".join(f"{n // 1000}k" for n in G.N_MAIN) + " |")
    w.append("|---|" + "---|" * len(G.N_MAIN))
    for spy in G.SPYS:
        w.append(f"| {spy} | " + " | ".join(
            f"{t.seconds.get((spy, n), np.nan):.0f} / {t.gb.get((spy, n), np.nan) / 1024:.1f}"
            for n in G.N_MAIN) + " |")
    w.append("")
    for q in GREEKS:
        w.append(f"## {q}\n")
        d = po[po.greek == q]
        gap = d.groupby("spy").gap.mean()
        w.append("Exercise-date gap |Bermudan − American| (PDE, mean over options): "
                 + ", ".join(f"{spy}/yr {gap.get(spy, np.nan):.3g}" for spy in G.SPYS) + "\n")
        for col, name in [("bias", "Total bias |labels − American| (MAE)"),
                          ("sim", "Simulation bias |labels − Bermudan| (MAE)"),
                          ("floor", "Noise floor of the two MAEs above"),
                          ("noise", "Noise of one label (median sd)")]:
            w.append(f"**{name}**\n")
            w += table(po, q, col)
            w.append("")
    text = "\n".join(w)
    path = Path(out) / "freq_paths" / "report.md"
    path.write_text(text)
    po.to_csv(Path(out) / "freq_paths" / "per_option.csv", index=False)
    return text


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="freq_paths_out")
    print(report(p.parse_args().out))
