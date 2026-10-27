"""Pathwise r and d Greeks with the European bound on the exercise rule. Not
part of the paper.

    python experiments/diagnostics/rd_pathwise_bound.py [reps]   (16 reps: ~20 min on 4 cores)

rd_pathwise_stress.py found pathwise Rho and Phi biased where r0 < d0: early
exercise is then almost never optimal, but the fitted rule exercises some paths
(nearly free in price, a shorter tau in Rho and Phi). The American continuation
value is never below the European value, so exercising where the payoff is
below the European value is always wrong. Here the same (S, sigma) runs give
the pathwise Greeks with and without that bound, on the stress test's r0 < d0
options and some r0 >= d0 controls (references from stress_reference.csv).
Writes results/diagnostics/rd_pathwise/bound.md and bound_raw.csv.
"""
import os
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[v] = "1"
import sys  # noqa: E402
from concurrent.futures import ProcessPoolExecutor  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import simgreeks.multi as m  # noqa: E402
from rd_pathwise_check import pathwise  # noqa: E402
from rd_pathwise_stress import G, OUT, grid, sample  # noqa: E402
from simgreeks.reference import bs_option  # noqa: E402

GRID = [1, 3, 4, 5, 11]                  # (r0, d0) = (0.5, 0), (0.5, 1) x 3 K, (1, 1) K = 44
SAMPLE = [0, 1, 5, 14, 15, 21, 2, 8]     # r0 < d0, then two r0 > d0
METHODS = [f"pw_{rule}{tag}" for tag in ("", "_bound") for rule in ("oos", "ins", "avg")]


def one(job):
    part, i, spec, rep = job
    sc = m.run_config(m.MultiConfig(), ("S", "sigma"))
    rng = np.random.default_rng(np.random.SeedSequence([4243, part == "grid", i, rep]))
    alphas, scale, rules = m.pilot(spec, sc, ("S", "sigma"), rng)
    z = m.isd_multi(spec, sc, alphas, rng)
    W = m.brownian(spec, sc.N, rng)
    _, Y, _ = m.lsm_multi(spec, sc, z, W, scale, rules)
    _, _, fits_ins = m.lsm_multi(spec, sc, z, W, alphas, None)
    g = m.greeks_multi(spec, sc, ("S", "sigma"), z, Y, bs_option(spec))
    ex = m.theta_pde(spec, g["price"], g["delta"], g["gamma"])[1]
    rows = []
    for tag, bound in (("", False), ("_bound", True)):
        oos = pathwise(spec, sc, z, W, scale, rules, bound)
        ins = pathwise(spec, sc, z, W, alphas, fits_ins, bound)
        for rule, v in (("oos", oos), ("ins", ins),
                        ("avg", {k: 0.5 * (oos[k] + ins[k]) for k in G})):
            rows.append(dict(part=part, option=i, rep=rep, method=f"pw_{rule}{tag}",
                             ex_region=ex, r=spec.r, d=spec.d, K=spec.K, S0=spec.S0,
                             **{k: 0.0 if ex else v[k] for k in G}))
    return rows


if __name__ == "__main__":
    reps = int(sys.argv[1]) if len(sys.argv) > 1 else 16
    g, s = grid(), sample(24)
    specs = [("grid", i, g[i]) for i in GRID] + [("sample", i, s[i]) for i in SAMPLE]
    jobs = [(p, i, sp, k) for p, i, sp in specs for k in range(reps)]
    with ProcessPoolExecutor(4) as ex:
        df = pd.DataFrame([r for rs in ex.map(one, jobs, chunksize=1) for r in rs])
    df.to_csv(OUT / "bound_raw.csv", index=False)
    ref = pd.read_csv(OUT / "stress_reference.csv")
    df = df.merge(ref, on=["part", "option"])
    df = df[~df.ex_region]
    lines = ["# Pathwise r and d Greeks with the European exercise bound", "",
             "Not part of the paper. `experiments/diagnostics/rd_pathwise_bound.py`, "
             f"{reps} reps per option, same (S, sigma) run for all methods. _bound: exercise "
             "only where the payoff >= the European value. Cells: bias ± se, % of |reference| "
             "(† = |bias| > 2.576 se), (noise of one label, %).", ""]
    for k in G:
        lines += [f"## {k}", "", "| part | option | S0/K | r0 | d0 | ref | " + " | ".join(METHODS) + " |",
                  "|---|---|---|---|---|---|" + "---|" * len(METHODS)]
        for (part, i), d in df.groupby(["part", "option"], sort=False):
            rf = d[f"ref_{k}"].iloc[0]
            cells = []
            for meth in METHODS:
                e = 100 * (d[d.method == meth][k] - rf) / abs(rf)
                se = e.std() / np.sqrt(len(e))
                flag = "†" if abs(e.mean()) > 2.576 * se else ""
                cells.append(f"{e.mean():+.2f} ± {se:.2f}{flag} ({e.std():.1f})")
            lines.append(f"| {part} | {i} | {d.S0.iloc[0] / d.K.iloc[0]:.3f} | "
                         f"{100 * d.r.iloc[0]:.2f}% | {100 * d.d.iloc[0]:.2f}% | {rf:+.3f} | "
                         + " | ".join(cells) + " |")
        lines.append("")
    text = "\n".join(lines)
    (OUT / "bound.md").write_text(text)
    print(text)
