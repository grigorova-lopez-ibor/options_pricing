"""Skipping exercise dates where no path can be exercised (MultiConfig.skip_dead_dates):
same label, less time? Not part of the paper. 24 options from the training-set
ranges (generate_labels.sample_options, seed 77), the production label (252 dates
a year, 600k main + 100k pilot paths, in sample), each labelled with and without
the skip from the same seed, one after the other in the same process (comparable
times). Writes results/diagnostics/dead_dates/{raw.csv, summary.md}.

    python experiments/diagnostics/dead_dates_check.py [--n 24] [--workers 4] [--seed 77] [--tag NAME]

With --tag the results go to results/diagnostics/dead_dates/NAME/; finished options are appended to
raw_partial.csv as they come, and a rerun skips them (resumable).
"""
import argparse
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import replace
from pathlib import Path

for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(v, "1")
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "experiments")]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from generate_labels import label_config, sample_options  # noqa: E402
from simgreeks.core import PutSpec  # noqa: E402
from simgreeks.multi import label  # noqa: E402

OUT = ROOT / "results" / "diagnostics" / "dead_dates"
Q = ["price", "delta", "gamma", "theta", "charm", "vega", "volga", "vanna", "rho", "phi", "delta_r", "delta_d"]


def one(row: dict) -> dict:
    seed = row.pop("_seed")
    spec = PutSpec(S0=row["S0"], K=row["K"], sigma=row["sigma"], r=row["r"], d=row["d"], T=row["T"],
                   steps_per_year=252)
    cfg = label_config(0.02, 600_000, 100_000)
    t = time.time(); a = label(spec, cfg, seed + row["id"]); ta = time.time() - t
    t = time.time(); b = label(spec, replace(cfg, skip_dead_dates=True), seed + row["id"]); tb = time.time() - t
    diff = max(abs(a[q] - b[q]) for q in Q if q in a)
    return dict(row, t_off=ta, t_on=tb, max_abs_diff=diff, ex_region=a.get("ex_region"),
                european_region=a.get("european_region"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=24)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--seed", type=int, default=77)
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    out = OUT / a.tag if a.tag else OUT
    out.mkdir(parents=True, exist_ok=True)
    opts = sample_options(a.n, 40.0, seed=a.seed).to_dict("records")
    part = out / "raw_partial.csv"
    done = set(pd.read_csv(part).id) if part.exists() else set()
    todo = [dict(o, _seed=a.seed) for o in opts if o["id"] not in done]
    with ProcessPoolExecutor(a.workers) as ex:
        for f in as_completed([ex.submit(one, o) for o in todo]):
            r = pd.DataFrame([f.result()])
            r.to_csv(part, mode="a", header=not part.exists(), index=False)
            print(f"done {len(done) + 1}/{len(opts)}", flush=True); done.add(int(r.id[0]))
    d = pd.read_csv(part).sort_values("id").reset_index(drop=True)
    d.to_csv(out / "raw.csv", index=False)
    OUT_ = out
    sim = d[~d.european_region.astype(bool)]
    d["r_lt_d"] = d.r < d.d
    sim = d[~d.european_region.astype(bool)]
    lines = ["# Skipping exercise dates where no path can be exercised", "",
             "Not part of the paper. `experiments/diagnostics/dead_dates_check.py`: "
             f"{len(d)} options from the training-set ranges (seed {a.seed}), the production label (252 dates a "
             "year, 600k main + 100k pilot paths, in sample, exercise bound on), each labelled from the same "
             "seed without and with `MultiConfig(skip_dead_dates=True)`, in the same process one after the "
             "other. A date is skipped when no in-the-money path can pass the exercise bound (payoff ≥ "
             "European value), checked with one European value at (min S, min σ, max r, min d) of the "
             "in-the-money paths; its regression would be thrown away, so the label must be identical.", "",
             f"**Identical labels:** {int((d.max_abs_diff == 0).sum())} of {len(d)} options "
             f"(largest absolute difference over all outputs: {d.max_abs_diff.max():.3g}).", "",
             f"{len(d) - len(sim)} options are in the no-early-exercise region (exact label, no simulation) "
             "and are left out of the times.", "",
             "| options | n | time without (s) | time with (s) | saving |", "|---|---|---|---|---|"]
    for name, x in (("all simulated", sim), ("r < d", sim[sim.r_lt_d]), ("r ≥ d", sim[~sim.r_lt_d])):
        if len(x):
            lines.append(f"| {name} | {len(x)} | {x.t_off.sum():.0f} | {x.t_on.sum():.0f} | "
                         f"{100 * (1 - x.t_on.sum() / x.t_off.sum()):.0f} % |")
    lines += ["", "Per option (saving = 1 − time with / time without):", "",
              "| id | S0/K | σ | r | d | T | without (s) | with (s) | saving |", "|---|---|---|---|---|---|---|---|---|"]
    for r in sim.sort_values("t_off").itertuples():
        lines.append(f"| {r.id} | {r.S0 / r.K:.2f} | {100 * r.sigma:.1f} % | {100 * r.r:.2f} % | {100 * r.d:.2f} % | "
                     f"{r.T:.2f} | {r.t_off:.1f} | {r.t_on:.1f} | {100 * (1 - r.t_on / r.t_off):.0f} % |")
    (OUT_ / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
