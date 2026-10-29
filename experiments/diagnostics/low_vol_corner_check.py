"""Labels at low volatility and short maturity (the sigma tail 1-5 % of the new
ranges, T from 2 months). Not part of the paper.

    python experiments/diagnostics/low_vol_corner_check.py [reps] [NAME=VALUE ...]
    (6 reps: ~30 min on 4 cores; NAME=VALUE: MultiConfig fields, output files
    get the suffix _NAME-VALUE...)

Options: sigma in {1, 2, 3, 5 %} x T in {2, 3, 6 months} x (r, d) in
{(3 %, 1 %), (1 %, 3 %)} x S0/K in {exp(-sd), 1, exp(sd)} (sd = sigma sqrt(T),
the scale of the curved part of the price) and the far points {0.9, 1.1}.
S0 = 100. Labels: the default MultiConfig().

Reference. The default PDE grid (half-width >= 0.5 in log S, 2001 nodes) and the
fixed sigma bump 0.005 are too coarse here (European price -1.5 %, Vega -1 % at
sigma = 1 %, T = 2 months), so: a grid of 8001 nodes over |log(S0/K)| + 12 sd
+ 0.02, bumps sigma/10 in sigma and min(0.002, r/2) in r; checked per option
with the European PDE against the closed form (column ref_check, the largest
relative error of price, Delta, Gamma, Vega, Rho, Phi where they are not ~0).
Writes results/diagnostics/low_vol_corner/summary.md and raw.csv.
"""
import os
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[v] = "1"
import sys  # noqa: E402
import time  # noqa: E402
from concurrent.futures import ProcessPoolExecutor  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from simgreeks.core import PutSpec  # noqa: E402
from simgreeks.multi import config_from, label  # noqa: E402
from simgreeks.reference import FDGrid, bs_option, put_fd_greeks  # noqa: E402

G = ["price", "delta", "gamma", "theta", "vega", "rho", "phi"]
OUT = ROOT / "results" / "diagnostics" / "low_vol_corner"
CHECK = ["price", "delta", "gamma", "vega", "rho", "phi"]


def options():
    out = []
    for sigma in (0.01, 0.02, 0.03, 0.05):
        for T in (1 / 6, 0.25, 0.5):
            sd = sigma * np.sqrt(T)
            for r, d in ((0.03, 0.01), (0.01, 0.03)):
                for where, m in (("-1sd", np.exp(-sd)), ("atm", 1.0), ("+1sd", np.exp(sd)),
                                 ("0.9", 0.9), ("1.1", 1.1)):
                    out.append(dict(sigma=sigma, T=T, r=r, d=d, where=where,
                                    spec=PutSpec(S0=100.0, K=100.0 / m, sigma=sigma, r=r, d=d, T=T)))
    return out


def fine_grid(spec):
    sd = spec.sigma * np.sqrt(spec.T)
    return FDGrid(n_x=8001, half_width=abs(np.log(spec.S0 / spec.K)) + 12 * sd + 0.02)


def reference(i_opt):
    i, o = i_opt
    spec = o["spec"]
    grid = fine_grid(spec)
    bumps = {"sigma": spec.sigma / 10, "r": min(0.002, spec.r / 2), "d": 0.002}
    f = put_fd_greeks(spec, "bermudan", grid, bumps, vera=False)
    ref = {g: float(f[g]) for g in G}
    if f["ex_region"]:
        ref = {g: 0.0 for g in G}
        ref["price"], ref["delta"] = spec.intrinsic, spec.sign
    eu, ef = bs_option(spec), put_fd_greeks(spec, "european", grid, bumps, vera=False)
    check = max((abs(ef[g] - eu[g]) / abs(eu[g]) for g in CHECK
                 if abs(eu[g]) > 1e-6 * max(1.0, abs(eu["vega"]))), default=0.0)
    return dict(option=i, ref_ex_region=bool(f["ex_region"]), ref_check=100 * check,
                **{f"ref_{g}": v for g, v in ref.items()})


SETTINGS = tuple(sys.argv[2:])
PIN = ("exercise_rule=pilot",)   # the out-of-sample rule these results were made with


def one(job):
    i, spec, rep = job
    t0 = time.time()
    lab = label(spec, config_from(PIN + SETTINGS), np.random.SeedSequence([4245, i, rep]))
    return dict(option=i, rep=rep, seconds=time.time() - t0, ex_region=bool(lab["ex_region"]),
                european_region=bool(lab["european_region"]), **{g: lab[g] for g in G})


def summarise(df, opts, reps):
    lines = ["# Labels at low volatility and short maturity", "",
             "Not part of the paper. `experiments/diagnostics/low_vol_corner_check.py`, "
             f"MultiConfig({', '.join(SETTINGS)}), {reps} labels per option, S0 = 100. "
             "Reference: Bermudan PDE on a "
             "refined grid with bumps sigma/10 and min(0.002, r/2); ref check = largest relative "
             "error (%) of the European PDE against the closed form on the same grid. Cells: "
             "mean label error, % of |reference| (± se), and (noise of one label, %). "
             "ex = exercise region (label and reference exact: price K - S0, Delta -1, rest 0); "
             "rows where both are in it are left out. '–': |reference| below 1e-6 of the price "
             "scale (shown as the label's mean absolute value instead).", ""]
    meta = pd.DataFrame([{k: v for k, v in o.items() if k != "spec"} | {"option": i}
                         for i, o in enumerate(opts)])
    d = df.merge(meta, on="option")
    for (r, dd), part in d.groupby(["r", "d"], sort=False):
        lines += [f"## r = {100 * r:g} %, d = {100 * dd:g} %", "",
                  "| sigma | T | S0/K | ref check % | ex (label/ref) | " + " | ".join(G) + " |",
                  "|---|---|---|---|---|" + "---|" * len(G)]
        for i, x in part.groupby("option", sort=False):
            o = opts[i]
            exl, exr = x.ex_region.mean(), x.ref_ex_region.iloc[0]
            if exl == 1 and exr:
                continue
            cells = []
            for g in G:
                rf = x[f"ref_{g}"].iloc[0]
                if abs(rf) < 1e-6 * max(1.0, abs(x["ref_price"].iloc[0])):
                    cells.append(f"– (|label| {x[g].abs().mean():.2g})")
                    continue
                e = 100 * (x[g] - rf) / abs(rf)
                se = e.std() / np.sqrt(len(e))
                flag = "†" if abs(e.mean()) > 2.576 * se and abs(e.mean()) > 1 else ""
                cells.append(f"{e.mean():+.1f} ± {se:.1f}{flag} ({e.std():.1f})")
            lines.append(f"| {100 * o['sigma']:g}% | {12 * o['T']:.0f}m | {o['where']} "
                         f"({o['spec'].S0 / o['spec'].K:.4f}) | {x.ref_check.iloc[0]:.2f} | "
                         f"{exl:.0%}/{'yes' if exr else 'no'} | " + " | ".join(cells) + " |")
        lines.append("")
    lines.append(f"Mean seconds per label (one core, 4 processes at once): {df.seconds.mean():.1f}.")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    reps = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    opts = options()
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = [(i, o["spec"], k) for i, o in enumerate(opts) for k in range(reps)]
    t0 = time.time()
    with ProcessPoolExecutor(4) as ex:
        ref = pd.DataFrame(list(ex.map(reference, enumerate(opts))))
        print(f"references done, {time.time() - t0:.0f} s", flush=True)
        rows = []
        for k, r in enumerate(ex.map(one, jobs, chunksize=2)):
            rows.append(r)
            if (k + 1) % max(1, len(jobs) // 10) == 0:
                print(f"{k + 1}/{len(jobs)} labels, {time.time() - t0:.0f} s", flush=True)
    df = pd.DataFrame(rows).merge(ref, on="option")
    tag = "".join(f"_{x.replace('=', '-')}" for x in SETTINGS)
    df.to_csv(OUT / f"raw{tag}.csv", index=False)
    text = summarise(df, opts, reps)
    (OUT / f"summary{tag}.md").write_text(text)
    print(text)
