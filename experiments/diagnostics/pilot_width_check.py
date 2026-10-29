"""The pilot width of S scaled to the option, c0_S_rule="sd", against the fixed
pilot width, outside the low-volatility corner. Not part of the paper.

    python experiments/diagnostics/pilot_width_check.py [reps]   (6 reps: ~45 min on 4 cores)

c0_S_rule="sd" sets alpha0_S = min(0.25, 1.25 sigma sqrt(T)) S0 instead of
0.25 S0, i.e. it narrows the pilot wherever sigma sqrt(T) < 0.2. This checks
that nothing gets worse there: the 33 options of the American check
(multi_check.american_grid, S0 = 40) and the 23 options from the new ranges of
rd_pathwise_stress.py. Both labels of a replication use the same seed (paired).
Reference: reference.put_fd_greeks with central bumps (sigma: min(0.005, sigma/10),
r: min(0.002, r/2)) on a refined grid where sigma sqrt(T) < 0.1; the closed form
where no early exercise is optimal; the exercise values in the exercise region.
Writes results/diagnostics/pilot_width/summary.md and raw.csv.
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
sys.path.insert(0, str(ROOT / "experiments"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from multi_check import american_grid, spec_of  # noqa: E402
from rd_pathwise_stress import sample  # noqa: E402
from simgreeks.multi import MultiConfig, label  # noqa: E402
from simgreeks.reference import FDGrid, bs_option, put_fd_greeks  # noqa: E402

G = ["price", "delta", "gamma", "theta", "vega", "volga", "vanna", "rho", "phi"]
CONFIGS = {"fixed": MultiConfig(c0_S_rule="fixed", exercise_rule="pilot"),
           "sd": MultiConfig(c0_S_rule="sd", exercise_rule="pilot")}
OUT = ROOT / "results" / "diagnostics" / "pilot_width"


def reference(job):
    part, i, spec = job
    sd = spec.sigma * np.sqrt(spec.T)
    if spec.no_early_exercise:
        eu = bs_option(spec)
        ref = {g: float(eu[g]) for g in G}
    else:
        grid = (FDGrid(n_x=8001, half_width=abs(np.log(spec.S0 / spec.K)) + 12 * sd + 0.02)
                if sd < 0.1 else None)
        bumps = {"sigma": min(0.005, spec.sigma / 10),
                 "r": min(0.002, spec.r / 2) if spec.r > 0 else 0.002, "d": 0.002}
        f = put_fd_greeks(spec, "bermudan", grid, bumps, vera=False)
        ref = {g: float(f[g]) for g in G}
        if f["ex_region"]:
            ref = {g: 0.0 for g in G}
            ref["price"], ref["delta"] = spec.intrinsic, spec.sign
    return dict(part=part, option=i, sd=sd, **{f"ref_{g}": v for g, v in ref.items()})


def one(job):
    part, i, spec, rep = job
    rows = []
    for name, cfg in CONFIGS.items():
        t0 = time.time()
        lab = label(spec, cfg, np.random.SeedSequence([4246, part == "grid", i, rep]))
        rows.append(dict(part=part, option=i, rep=rep, method=name, seconds=time.time() - t0,
                         ex_region=bool(lab["ex_region"]), alpha_S=lab.get("alpha_S", np.nan),
                         **{g: lab[g] for g in G}))
    return rows


def summarise(df, ref, reps):
    df = df.merge(ref, on=["part", "option"])
    df = df[~df.ex_region]
    lines = ["# Pilot width of S scaled to the option (c0_S_rule=\"sd\") against the fixed width", "",
             "Not part of the paper. `experiments/diagnostics/pilot_width_check.py`, "
             f"{reps} paired labels per option (same seed for both). fixed = MultiConfig(c0_S_rule=\"fixed\"); "
             "sd = MultiConfig(c0_S_rule=\"sd\"): alpha0_S = min(0.25, 1.25 sigma sqrt(T)) S0. "
             "Per part and sigma sqrt(T) bin: bias = mean over options of the signed relative "
             "error of the option's mean label (t), typical error = mean |relative error| of "
             "one label; options with |ref| < 1 % of the Greek's largest |ref| in the part, and "
             "labels in the exercise region, left out.", ""]
    df["bin"] = pd.cut(df.sd, [0, 0.1, 0.2, np.inf], labels=["sd < 0.1", "0.1-0.2", ">= 0.2"])
    for (part, b), d0 in df.groupby(["part", "bin"], sort=True, observed=True):
        n = d0.option.nunique()
        a = d0.groupby("method").alpha_S.mean()
        lines += [f"## {part}, sigma sqrt(T) {b}: {n} options; mean alpha_S fixed {a['fixed']:.2f}, "
                  f"sd {a['sd']:.2f}", "",
                  "| Greek | bias % fixed (t) | bias % sd (t) | typical % fixed | typical % sd |",
                  "|---|---|---|---|---|"]
        for g in G:
            big = d0[f"ref_{g}"].abs() >= 0.01 * df[df.part == part][f"ref_{g}"].abs().max()
            cells = []
            for meth in CONFIGS:
                d = d0[big & (d0.method == meth)]
                if d.empty:
                    cells.append(("–", "–"))
                    continue
                e = 100 * (d[g] - d[f"ref_{g}"]) / d[f"ref_{g}"].abs()
                per = e.groupby(d.option).mean()
                b_, se = per.mean(), per.std() / np.sqrt(len(per)) if len(per) > 1 else np.nan
                cells.append((f"{b_:+.2f} ({b_ / se:+.1f})", f"{e.abs().mean():.1f}"))
            lines.append(f"| {g} | {cells[0][0]} | {cells[1][0]} | {cells[0][1]} | {cells[1][1]} |")
        lines.append("")
    t = df.groupby("method").seconds.mean()
    lines.append(f"Mean seconds per label (one core, 4 processes at once): fixed {t['fixed']:.1f}, "
                 f"sd {t['sd']:.1f}.")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    reps = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    specs = [("grid", i, spec_of(c)) for i, c in enumerate(american_grid())]
    specs += [("sample", i, s) for i, s in enumerate(sample(24))]
    jobs = [(p, i, s, k) for p, i, s in specs for k in range(reps)]
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with ProcessPoolExecutor(4) as ex:
        ref = pd.DataFrame(list(ex.map(reference, specs)))
        print(f"references done, {time.time() - t0:.0f} s", flush=True)
        rows = []
        for k, rs in enumerate(ex.map(one, jobs, chunksize=1)):
            rows += rs
            if (k + 1) % max(1, len(jobs) // 10) == 0:
                print(f"{k + 1}/{len(jobs)} options, {time.time() - t0:.0f} s", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "raw.csv", index=False)
    ref.to_csv(OUT / "reference.csv", index=False)
    text = summarise(df, ref, reps)
    (OUT / "summary.md").write_text(text)
    print(text)
