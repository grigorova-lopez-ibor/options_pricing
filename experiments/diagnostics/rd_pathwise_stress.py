"""Pathwise r and d Greeks on the hard cases. Not part of the paper.

    python experiments/diagnostics/rd_pathwise_stress.py [grid_reps] [sample_reps] [n_sample]
    (defaults 40, 10, 24: about 1 h on 4 cores)

Compares, on the same (S, sigma) run, the default label's Rho, Phi, dDelta/dr and
dDelta/dd (separate (S, r) and (S, d) runs, hybrid label) with pathwise
derivatives on the (S, sigma) paths alone (rd_pathwise_check.pathwise), using
the out-of-sample rule (pw_oos), the rule refitted in sample on the main paths
(pw_ins) and their average (pw_avg), as the default label averages oos and ins.

Part 1 (grid): the small-r grid of results/diagnostics/r_d_windows/
small_r_shrink_200reps.md, where the window method is biased: S0 = 40,
sigma = 20 %, T = 1, r0 in {0.5 %, 1 %}, d0 in {0, 1 %}, K in {36, 40, 44}.
Part 2 (sample): options from experiments/generate_labels.sample_options (the
new ranges), without the exact European ones (r0 = 0).
Reference: reference.label_reference (central bumps, r bump <= r0 / 2).
Writes results/diagnostics/rd_pathwise/stress.md and stress_raw.csv.
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
import simgreeks.multi as m  # noqa: E402
from simgreeks.core import PutSpec  # noqa: E402
from simgreeks.reference import bs_option, label_reference  # noqa: E402
from generate_labels import sample_options  # noqa: E402
from rd_pathwise_check import pathwise  # noqa: E402

G = ["rho", "phi", "delta_r", "delta_d"]
METHODS = ["default", "pw_oos", "pw_ins", "pw_avg"]
OUT = Path(os.environ["RD_OUT"]) if "RD_OUT" in os.environ else ROOT / "results" / "diagnostics" / "rd_pathwise"


def grid():
    return [PutSpec(S0=40, K=K, sigma=0.2, r=r, d=d, T=1.0)
            for r in (0.005, 0.01) for d in (0.0, 0.01) for K in (36, 40, 44)]


def sample(n):
    df = sample_options(4 * n, 100.0, 7, "cosine")    # the tail shape the results were made with
    df = df[df.r > 0].head(n)
    return [PutSpec(S0=row.S0, K=row.K, sigma=row.sigma, r=row.r, d=row.d, T=row.T)
            for row in df.itertuples()]


def one(job):
    part, i, spec, rep = job
    cfg = m.MultiConfig(exercise_rule="pilot")
    seeds = np.random.SeedSequence([4242, part == "grid", i, rep]).spawn(3)
    t0 = time.time()
    sc = m.run_config(cfg, ("S", "sigma"))
    rng = np.random.default_rng(seeds[0])
    alphas, scale, rules = m.pilot(spec, sc, ("S", "sigma"), rng)
    z = m.isd_multi(spec, sc, alphas, rng)
    W = m.brownian(spec, sc.N, rng)
    add = bs_option(spec)
    _, Y, _ = m.lsm_multi(spec, sc, z, W, scale, rules)
    _, Y_ins, fits_ins = m.lsm_multi(spec, sc, z, W, alphas, None)
    run_s = m.greeks_multi(spec, sc, ("S", "sigma"), z, Y, add)
    run_s["ins"] = m.greeks_multi(spec, sc, ("S", "sigma"), z, Y_ins, add)
    run_s["N"] = run_s["ins"]["N"] = sc.N
    t_sigma = time.time() - t0
    t1 = time.time()
    pw_oos = pathwise(spec, sc, z, W, scale, rules)
    pw_ins = pathwise(spec, sc, z, W, alphas, fits_ins)
    t_pw = time.time() - t1
    t2 = time.time()
    runs = [run_s] + [m.run_group(spec, cfg, g, s) for g, s in zip(cfg.groups[1:], seeds[1:])]
    t_rd = time.time() - t2
    lab = m._assemble(spec, cfg, runs)
    m._add_ins_avg(lab, m._assemble(spec, cfg, [r["ins"] for r in runs]))
    m._set_default(lab, cfg)
    ex = bool(lab["ex_region"])
    vals = {"default": {g: lab[g] for g in G}, "pw_oos": pw_oos, "pw_ins": pw_ins,
            "pw_avg": {g: 0.5 * (pw_oos[g] + pw_ins[g]) for g in G}}
    rows = []
    for meth, v in vals.items():
        rows.append(dict(part=part, option=i, rep=rep, method=meth, ex_region=ex,
                         K=spec.K, S0=spec.S0, sigma=spec.sigma, r=spec.r, d=spec.d, T=spec.T,
                         t_sigma=t_sigma, t_pw=t_pw, t_rd=t_rd,
                         **{g: (0.0 if ex else v[g]) for g in G}))
    return rows


def reference(job):
    part, i, spec = job
    ref = label_reference(spec, vera=False)
    return dict(part=part, option=i, **{f"ref_{g}": ref[g] for g in G})


def fmt(b, se, sd):
    flag = "†" if abs(b) > 2.576 * se else ""
    return f"{b:+.2f} ± {se:.2f}{flag} ({sd:.1f})"


def summarise(df, ref):
    df = df.merge(ref, on=["part", "option"])
    df = df[~df.ex_region]
    lines = ["# Pathwise r and d Greeks on the hard cases", "",
             "Not part of the paper. `experiments/diagnostics/rd_pathwise_stress.py`. "
             "default = the default label (separate (S, r), (S, d) runs of 50k + 50k paths, hybrid "
             "label: Rho, Phi averaged oos/ins, cross terms oos); pw_* = pathwise derivatives on "
             "the (S, sigma) run's 200k main paths alone, with the out-of-sample rule (oos), the "
             "rule refitted on the main paths (ins), and their average (avg). Same (S, sigma) run "
             "in all. Cells: bias ± se, % of |reference| († = |bias| > 2.576 se), "
             "(noise of one label, %). Reference: reference.label_reference.", ""]
    grid_df = df[df.part == "grid"]
    if len(grid_df):
        lines += ["## Part 1: small r0 and d0 (S0 = 40, sigma = 20 %, T = 1)", ""]
        for g in G:
            lines += [f"### {g}", "", "| r0 | d0 | K | ref | " + " | ".join(METHODS) + " |",
                      "|---|---|---|---|" + "---|" * len(METHODS)]
            for i, d in grid_df.groupby("option"):
                rf = d[f"ref_{g}"].iloc[0]
                a = abs(rf)
                cells = []
                for meth in METHODS:
                    x = d[d.method == meth][g]
                    e = 100 * (x - rf) / a
                    cells.append(fmt(e.mean(), e.std() / np.sqrt(len(e)), e.std()))
                r0 = d.r.iloc[0]
                lines.append(f"| {100 * r0:g}% | {100 * d.d.iloc[0]:g}% | {d.K.iloc[0]:g} | "
                             f"{rf:+.3f} | " + " | ".join(cells) + " |")
            lines.append("")
    s_df = df[df.part == "sample"]
    if len(s_df):
        n_opt = s_df.option.nunique()
        lines += [f"## Part 2: {n_opt} options from the new ranges", "",
                  "Per option the mean label over the reps; bias = mean over options of the "
                  "signed relative error of that mean (± se over options), typical error = mean "
                  "|relative error| of one label, median error = its median; options with "
                  "|ref| < 1 % of the Greek's largest |ref| left out.", "",
                  "| Greek | method | bias % (t) | typical error % | median error % |",
                  "|---|---|---|---|---|"]
        for g in G:
            big = s_df[f"ref_{g}"].abs() >= 0.01 * s_df[f"ref_{g}"].abs().max()
            for meth in METHODS:
                d = s_df[big & (s_df.method == meth)]
                e = 100 * (d[g] - d[f"ref_{g}"]) / d[f"ref_{g}"].abs()
                per_opt = e.groupby(d.option).mean()
                b, se = per_opt.mean(), per_opt.std() / np.sqrt(len(per_opt))
                lines.append(f"| {g} | {meth} | {b:+.2f} ({b / se:+.1f}) | {e.abs().mean():.1f} | "
                             f"{e.abs().median():.1f} |")
        lines += ["", "Options (no exercise at t0):", "",
                  "| option | S0/K | sigma | r | d | T | worst pw_avg Rho error % | worst default Rho error % |",
                  "|---|---|---|---|---|---|---|---|"]
        for i, d in s_df.groupby("option"):
            rf = d["ref_rho"].iloc[0]
            w = {meth: (100 * (d[d.method == meth].rho - rf) / abs(rf)).abs().max()
                 for meth in ("pw_avg", "default")}
            lines.append(f"| {i} | {d.S0.iloc[0] / d.K.iloc[0]:.3f} | {d.sigma.iloc[0]:.4f} | "
                         f"{d.r.iloc[0]:.4f} | {d.d.iloc[0]:.4f} | {d["T"].iloc[0]:.3f} | "
                         f"{w['pw_avg']:.1f} | {w['default']:.1f} |")
    t = df.groupby("method")[["t_sigma", "t_rd", "t_pw"]].mean().iloc[0]
    lines += ["", f"Mean seconds per label (one core): (S, sigma) run with its in-sample refit "
              f"{t.t_sigma:.1f}, (S, r) + (S, d) runs {t.t_rd:.1f}, both pathwise passes "
              f"{t.t_pw:.1f} (a separate forward pass here; not yet folded into the LSM loop)."]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    grid_reps = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    sample_reps = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    n_sample = int(sys.argv[3]) if len(sys.argv) > 3 else 24
    specs = [("grid", i, s) for i, s in enumerate(grid())]
    specs += [("sample", i, s) for i, s in enumerate(sample(n_sample))]
    jobs = [(p, i, s, k) for p, i, s in specs
            for k in range(grid_reps if p == "grid" else sample_reps)]
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with ProcessPoolExecutor(4) as ex:
        ref = pd.DataFrame(list(ex.map(reference, specs)))
        rows = []
        for k, rs in enumerate(ex.map(one, jobs, chunksize=1)):
            rows += rs
            if (k + 1) % max(1, len(jobs) // 20) == 0:
                print(f"{k + 1}/{len(jobs)} labels, {time.time() - t0:.0f} s", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "stress_raw.csv", index=False)
    ref.to_csv(OUT / "stress_reference.csv", index=False)
    text = summarise(df, ref)
    (OUT / "stress.md").write_text(text)
    print(text)
