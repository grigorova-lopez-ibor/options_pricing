"""The default label (one (S, sigma) run, pathwise r and d Greeks) against the
original design D2, all Greeks, against the PDE reference. Not part of the paper.

    python experiments/diagnostics/pathwise_label_check.py [grid_reps] [sample_reps]
    (defaults 10, 5: about 45 min on 4 cores)

Options: the small-r0/d0 grid and the 23 options from the new ranges of
rd_pathwise_stress.py. "new" = MultiConfig(); "D2" = MultiConfig(groups=GROUPS,
run_paths=(), rd_greeks="runs"), the label before the carlos branch. Labels are
independent between methods. Reference: reference.label_reference.
Writes results/diagnostics/rd_pathwise/label_check.md and label_check_raw.csv.
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

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rd_pathwise_stress import OUT, grid, sample  # noqa: E402
from simgreeks.multi import GROUPS, MultiConfig, label  # noqa: E402
from simgreeks.reference import label_reference  # noqa: E402

G = ["price", "delta", "gamma", "theta", "vega", "volga", "vanna", "rho", "phi",
     "delta_r", "delta_d"]
CONFIGS = {"new": MultiConfig(), "D2": MultiConfig(groups=GROUPS, run_paths=(), rd_greeks="runs")}


def one(job):
    part, i, spec, rep = job
    rows = []
    for k, (name, cfg) in enumerate(CONFIGS.items()):
        t0 = time.time()
        lab = label(spec, cfg, np.random.SeedSequence([4244, part == "grid", i, rep, k]))
        rows.append(dict(part=part, option=i, rep=rep, method=name, seconds=time.time() - t0,
                         ex_region=bool(lab["ex_region"]), **{g: lab[g] for g in G}))
    return rows


def reference(job):
    part, i, spec = job
    ref = label_reference(spec, vera=False)
    return dict(part=part, option=i, **{f"ref_{g}": ref[g] for g in G})


def summarise(df, ref):
    df = df.merge(ref, on=["part", "option"])
    df = df[~df.ex_region]
    lines = ["# Default label (pathwise r and d) against design D2", "",
             "Not part of the paper. `experiments/diagnostics/pathwise_label_check.py`. new = "
             "MultiConfig() (one (S, sigma) run, 400k main + 100k pilot, pathwise r and d "
             "Greeks); D2 = the label before the carlos branch ((S, sigma), (S, r), (S, d), "
             "100k + 100k each). Per part: bias = mean over options of the signed relative "
             "error of the option's mean label (± se over options), typical error = mean "
             "|relative error| of one label, median error = its median; options with |ref| < 1 % "
             "of the Greek's largest |ref| left out; options in the exercise region (exact "
             "labels) left out.", ""]
    for part, d0 in df.groupby("part", sort=False):
        lines += [f"## {part}: {d0.option.nunique()} options, "
                  f"{d0.groupby('option').rep.nunique().min()} labels each", "",
                  "| Greek | bias % new (t) | bias % D2 (t) | typical % new | typical % D2 "
                  "| median % new | median % D2 |", "|---|---|---|---|---|---|---|"]
        for g in G:
            big = d0[f"ref_{g}"].abs() >= 0.01 * d0[f"ref_{g}"].abs().max()
            cells = {}
            for meth in CONFIGS:
                d = d0[big & (d0.method == meth)]
                e = 100 * (d[g] - d[f"ref_{g}"]) / d[f"ref_{g}"].abs()
                per = e.groupby(d.option).mean()
                b, se = per.mean(), per.std() / np.sqrt(len(per))
                cells[meth] = (f"{b:+.2f} ({b / se:+.1f})", f"{e.abs().mean():.1f}",
                               f"{e.abs().median():.1f}")
            lines.append(f"| {g} | {cells['new'][0]} | {cells['D2'][0]} | {cells['new'][1]} | "
                         f"{cells['D2'][1]} | {cells['new'][2]} | {cells['D2'][2]} |")
        lines.append("")
    t = df.groupby("method").seconds.mean()
    lines.append(f"Mean seconds per label (one core, 4 processes at once): new {t['new']:.1f}, "
                 f"D2 {t['D2']:.1f}.")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    grid_reps = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    sample_reps = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    specs = [("grid", i, s) for i, s in enumerate(grid())]
    specs += [("sample", i, s) for i, s in enumerate(sample(24))]
    jobs = [(p, i, s, k) for p, i, s in specs
            for k in range(grid_reps if p == "grid" else sample_reps)]
    t0 = time.time()
    with ProcessPoolExecutor(4) as ex:
        ref = pd.DataFrame(list(ex.map(reference, specs)))
        rows = []
        for k, rs in enumerate(ex.map(one, jobs, chunksize=1)):
            rows += rs
            if (k + 1) % max(1, len(jobs) // 20) == 0:
                print(f"{k + 1}/{len(jobs)} options, {time.time() - t0:.0f} s", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "label_check_raw.csv", index=False)
    text = summarise(df, ref)
    (OUT / "label_check.md").write_text(text)
    print(text)
