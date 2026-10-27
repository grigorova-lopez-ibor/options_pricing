"""Generate labels (price and Greeks) for a sample of Bermudan puts. Not part of
the paper.

Options are drawn on scrambled Sobol points (seeded) over moneyness,
volatility, rate, dividend yield and maturity at a fixed S0, then rounded:

    S0/K   uniform on [0.8, 1.2]; K = S0 / (S0/K) rounded to 0.01
    sigma  plateau on [5 %, 50 %] with tails to 1 % and 60 %
           (simgreeks.sampling.plateau_ppf; --sigma-tail sets their shape), step 0.01 %
    r, d   uniform on [0, 5 %], step 0.25 % (so the shrinking windows min(0.03, r0)
           are >= 0.25 %; r0 = 0 is exact)
    T      uniform on [2 months, 2 years], step 0.001

Each label is one call of simgreeks.multi.label with the default MultiConfig
(one (S, sigma) run of 300,000 main + 100,000 pilot paths; Rho, Phi, dDelta/dr,
dDelta/dd, Theta and Charm pathwise on its paths); labels scale exactly with
(S0, K), so S0 only sets the units.

Exercise dates. --steps-per-year (default 504, two a business day): the puts are
Bermudan with J = round(steps_per_year T) dates. At 504 a year they are within
0.015 % (median, max 0.07 %) of the American price, 0.03-0.06 % (max 0.4 %) in
Rho and Phi (results/diagnostics/exercise_frequency); 50 a year is the earlier
setting. Above 50 dates a year the value-function label is taken at the date
nearest 1/50 year (MultiConfig.vf_time = 0.02, --vf-time), as validated at daily
dates (results/american_daily) and at 504 (results/two_per_day). A label at 504
takes about 35 / 76 / 150 s at T = 0.5 / 1 / 2 on one core and up to 2.8 GB.

    python experiments/generate_labels.py [--n 100] [--S0 100] [--workers N]
                                          [--seed 1] [--sigma-tail concave]
                                          [--steps-per-year 504] [--vf-time 0.02]
                                          [--exact] [--exact-every 1] [--out PATH]
                                          [--task i --ntasks n | --merge --ntasks n]

On the SCC (scc/labels.qsub, scc/submit_labels.sh): --task i --ntasks n labels
the options with id % n == i into <out stem>.task<i>of<n>.csv (resumable, one
process: --workers 1); when all tasks are done, the same command with --merge
instead of --task checks that every option is there and writes the final CSV.
The options and each label's seed depend only on --n, --seed and the option's
id, so the result does not depend on the number of tasks.

Writes one CSV row per option: the inputs, the label (price, delta, gamma,
theta, charm, vega, volga, vanna, rho, phi, delta_r, delta_d, theta_pde,
ex_region, alpha_S, alpha_sigma), each Greek's three versions <greek>_oos (the
exercise rule fitted on the pilot paths), <greek>_ins (refitted on the main
paths) and <greek>_avg (their average), with default_source naming which one
the plain column is (multi.HYBRID_OOS), so the version to train on can be
chosen per Greek after the run, and, with --exact, the reference values as exact_<greek>
(reference.put_fd_greeks; where exercising at t_0 is optimal, the exercise
values K - S0, -1 and 0, as in the labels; --exact-every k: only for the
options with id % k == 0, e.g. 10 for a 10 % check subset). theta and charm are pathwise (the
Theta of a Bermudan option with the number of exercise dates fixed), theta_pde
the PDE-identity Theta; the reference's Theta and Charm are calendar ones
(exercise dates fixed in calendar time), which differ from theta and charm by
0.3-2.7 % and up to ~6 % at 50 dates a year. The reference values are for
checking the labels (experiments/analyze_labels.py) and add about 25 % to the
time.

Small positive rates. Near r = 0 the early-exercise premium has a kink (it is 0
for r <= 0, d >= 0), and Rho changes fast just above it. Shrinking windows,
MultiConfig(alpha_r_shrink=True, alpha_d_shrink="r0"): alpha_r = alpha_d =
min(0.03, r0), remove most of the Rho and Phi bias there (200-replication check
at r0 = 0.5 % and 1 %, sigma = 20 %, T = 1), but the noise of one label grows
like 1 / r0: Rho 11-19 % at r0 = 1 % and 16-29 % at 0.5 %, Phi 13-23 % and
19-38 %, against 3-6 % with the 0.03 window. When building a training set,
oversample r0 in (0, 0.03) so that a network sees enough labels there to
average the extra noise out; r0 = 0 itself is exact with
MultiConfig(european_region=True). Open: at r0 = d0 = 1 % (K = 40, 44) Rho and
Phi stay 3-4 % off with any window.

Progress is printed at every 1 %. Each finished option is appended to
<out>.partial.csv, so an interrupted run resumes where it stopped when the same
command is run again; the partial files are removed once the CSV is written.
Each process uses one thread (OMP/MKL/OpenBLAS/Accelerate), so --workers should
be the number of physical cores.
"""
from __future__ import annotations

import os

for _var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
             "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_var, "1")          # before numpy; inherited by the workers

import argparse  # noqa: E402
import csv  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
import warnings  # noqa: E402
from dataclasses import replace  # noqa: E402
from concurrent.futures import ProcessPoolExecutor, as_completed  # noqa: E402
from pathlib import Path  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.stats import qmc  # noqa: E402

from simgreeks.core import PutSpec  # noqa: E402
from simgreeks.multi import MultiConfig, label  # noqa: E402
from simgreeks.reference import bs_option, grid_for, put_fd_greeks  # noqa: E402
from simgreeks.runner import job_seed  # noqa: E402
from simgreeks.sampling import SIGMA_BOUNDS, TAILS, plateau_ppf  # noqa: E402

GREEKS = ["price", "delta", "gamma", "theta", "charm", "vega", "volga", "vanna", "rho", "phi",
          "delta_r", "delta_d", "theta_pde"]
INPUTS = ["id", "S0", "K", "sigma", "r", "d", "T", "steps_per_year"]
EXTRA = ["ex_region", "alpha_S", "alpha_sigma", "seconds"]
VERSIONS = [f"{g}_{v}" for g in GREEKS for v in ("oos", "ins", "avg")] + ["default_source"]
# (low, high, rounding step) of each input drawn uniformly; "moneyness" is S0/K.
# sigma: SIGMA_BOUNDS (plateau and tails), rounded to SIGMA_STEP
RANGES = {"moneyness": (0.8, 1.2, None), "r": (0.0, 0.05, 0.0025),
          "d": (0.0, 0.05, 0.0025), "T": (1 / 6, 2.0, 0.001)}
SIGMA_STEP = 0.0001


def sample_options(n: int, S0: float, seed: int, sigma_tail: str = "concave") -> pd.DataFrame:
    with warnings.catch_warnings():           # n need not be a power of 2 here
        warnings.simplefilter("ignore", UserWarning)
        U = qmc.Sobol(d=len(RANGES) + 1, scramble=True, seed=seed).random(n)
    cols = {}
    for j, (k, (lo, hi, step)) in enumerate(RANGES.items()):
        x = lo + (hi - lo) * U[:, j]
        cols[k] = x if step is None else np.round(x / step) * step
    cols["sigma"] = np.round(plateau_ppf(U[:, -1], SIGMA_BOUNDS, sigma_tail) / SIGMA_STEP) * SIGMA_STEP
    df = pd.DataFrame(cols)
    df.insert(0, "K", np.round(S0 / df.pop("moneyness"), 2))
    df.insert(0, "S0", S0)
    df.insert(0, "id", np.arange(n))
    return df.round(6)


def spec_of(row) -> PutSpec:
    return PutSpec(S0=row["S0"], K=row["K"], sigma=row["sigma"], r=row["r"], d=row["d"],
                   T=row["T"], steps_per_year=int(row.get("steps_per_year", 50)))


def exact(spec: PutSpec) -> dict:
    """Reference values. No early exercise optimal (r <= 0 <= d): the closed form,
    as the labels. Otherwise the Bermudan PDE with central bumps sigma/10 (at
    most 0.005) and r/2 (at most 0.002, so r stays > 0), on a refined grid where
    sigma sqrt(T) < 0.1: the default grid and the fixed sigma bump 0.005 are off
    by up to 1.5 % in price and 1 % in Vega at sigma = 1 %, T = 2 months
    (experiments/diagnostics/low_vol_corner_check.py)."""
    if spec.no_early_exercise:
        f = dict(bs_option(spec))
    else:
        sd = spec.sigma * np.sqrt(spec.T)
        grid = (replace(grid_for(spec), n_x=8001,
                        half_width=abs(np.log(spec.S0 / spec.K)) + 12 * sd + 0.02)
                if sd < 0.1 else None)
        bumps = {"sigma": min(0.005, spec.sigma / 10),
                 "r": min(0.002, spec.r / 2) if spec.r > 0 else 0.002, "d": 0.002}
        f = dict(put_fd_greeks(spec, "bermudan", grid, bumps, vera=False))
    f["theta_pde"] = f["theta"]          # the reference has one (calendar) Theta
    out = {g: f[g] for g in GREEKS}
    if f.get("ex_region", False):       # exercise at t_0, as the labels do
        out = {g: 0.0 for g in GREEKS}
        out["price"], out["delta"] = spec.K - spec.S0, -1.0
    return {f"exact_{g}": v for g, v in out.items()}


def one_option(job) -> dict:
    """Label (and reference values) of one option; runs in a worker."""
    row, base_seed, with_exact, vf_time = job
    spec = spec_of(row)
    out = dict(row)
    t0 = time.time()
    lab = label(spec, MultiConfig(vf_time=vf_time), job_seed(base_seed, {"id": int(row["id"])}, 0))
    out["seconds"] = round(time.time() - t0, 1)
    out.update({k: lab[k] for k in GREEKS + EXTRA if k != "seconds"})
    out.update({k: lab.get(k, np.nan) for k in VERSIONS})
    if with_exact:
        out.update(exact(spec))
    return out


def task_path(out: Path, task: int, ntasks: int) -> Path:
    return out.with_name(f"{out.stem}.task{task:04d}of{ntasks:04d}.csv")


def finish(rows: pd.DataFrame, path: Path) -> pd.DataFrame:
    df = rows.sort_values("id").reset_index(drop=True)
    df.insert(df.columns.get_loc("K") + 1, "moneyness", (df.S0 / df.K).round(4))
    df.to_csv(path, index=False, float_format="%.6g")
    return df


def merge(args) -> None:
    """Combine the task files of an SCC run into the final CSV."""
    parts = [task_path(args.out, i, args.ntasks) for i in range(args.ntasks)]
    missing = [p.name for p in parts if not p.exists()]
    if missing:
        sys.exit(f"{len(missing)} of {args.ntasks} task files missing, e.g. {missing[0]} "
                 "(resubmit the tasks; a running or killed task leaves only its .partial.csv)")
    df = pd.concat([pd.read_csv(p) for p in parts], ignore_index=True).drop(columns="moneyness")
    lost = sorted(set(range(args.n)) - set(df["id"]))
    if lost or len(df) != args.n:
        sys.exit(f"{len(df)} rows for {args.n} options; missing ids {lost[:10]}")
    finish(df, args.out)
    print(f"wrote {args.out} ({len(df)} options from {args.ntasks} task files)")


def _clock(s: float) -> str:
    s = int(round(s))
    return f"{s // 3600}h{s % 3600 // 60:02d}m" if s >= 3600 else f"{s // 60}m{s % 60:02d}s"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--S0", type=float, default=100.0)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--sigma-tail", choices=sorted(TAILS), default="concave",
                    help="shape of the sigma tails (1-5 %% and 50-60 %%; simgreeks.sampling)")
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--steps-per-year", type=int, default=504,
                    help="exercise dates a year (504: two a business day; 50: the earlier setting)")
    ap.add_argument("--vf-time", type=float, default=None,
                    help="value-function label date in years (default: 0.02 above 50 dates a "
                         "year, else the first exercise date)")
    ap.add_argument("--exact", action="store_true",
                    help="add the reference PDE values (for checking the labels)")
    ap.add_argument("--exact-every", type=int, default=1,
                    help="with --exact: reference values only for ids divisible by this")
    ap.add_argument("--task", type=int, default=None, help="SCC: this task's index, 0-based")
    ap.add_argument("--ntasks", type=int, default=1, help="SCC: number of tasks")
    ap.add_argument("--merge", action="store_true", help="SCC: combine the task files")
    ap.add_argument("--no-exact", action="store_true", help=argparse.SUPPRESS)  # old default
    ap.add_argument("--out", type=Path, default=ROOT / "results" / "labels_sample.csv")
    args = ap.parse_args()
    if args.merge:
        return merge(args)
    if args.task is not None and not 0 <= args.task < args.ntasks:
        ap.error("--task must be in 0 .. ntasks - 1")
    if args.task is None and args.ntasks > 1:
        ap.error("--ntasks > 1 needs --task (or --merge)")
    vf_time = args.vf_time if args.vf_time is not None else (0.02 if args.steps_per_year > 50 else None)
    out = args.out if args.task is None else task_path(args.out, args.task, args.ntasks)

    columns = (INPUTS + GREEKS + EXTRA + VERSIONS
               + ([f"exact_{g}" for g in GREEKS] if args.exact else []))
    settings = json.dumps(dict(n=args.n, S0=args.S0, seed=args.seed, exact=args.exact, versions=True,
                               ranges=RANGES, sigma=SIGMA_BOUNDS, sigma_tail=args.sigma_tail,
                               steps_per_year=args.steps_per_year, vf_time=vf_time,
                               exact_every=args.exact_every, task=args.task, ntasks=args.ntasks),
                          sort_keys=True)
    partial = out.with_name(out.stem + ".partial.csv")
    meta = out.with_name(out.stem + ".partial.json")
    out.parent.mkdir(parents=True, exist_ok=True)

    opts = sample_options(args.n, args.S0, args.seed, args.sigma_tail)
    opts["steps_per_year"] = args.steps_per_year
    if args.task is not None:
        opts = opts[opts["id"] % args.ntasks == args.task]
    n_mine = len(opts)
    done = set()
    if partial.exists():
        if not meta.exists() or meta.read_text() != settings:
            sys.exit(f"{partial} was made with other settings; delete it (and {meta.name}) "
                     "or use another --out")
        done = set(pd.read_csv(partial, usecols=["id"])["id"])
        print(f"resuming: {len(done)} of {n_mine} options already done", flush=True)
    else:
        meta.write_text(settings)
    todo = [dict(r) for r in opts.to_dict("records") if r["id"] not in done]

    workers = args.workers or os.cpu_count()
    print(f"{len(todo)} options to label on {workers} processes, {args.steps_per_year} exercise "
          f"dates a year{', with reference values' if args.exact else ''}", flush=True)
    t0, n_new, last_pct = time.time(), 0, int(100 * len(done) / max(n_mine, 1))
    with open(partial, "a", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        if fh.tell() == 0:
            writer.writeheader()
        ex = ProcessPoolExecutor(max_workers=workers)
        futures = [ex.submit(one_option, (r, args.seed,
                                          args.exact and r["id"] % args.exact_every == 0, vf_time))
                   for r in todo]
        try:
            for fut in as_completed(futures):
                writer.writerow(fut.result())
                fh.flush()
                n_new += 1
                n_done = len(done) + n_new
                pct = int(100 * n_done / n_mine)
                if pct > last_pct or n_done == n_mine:
                    last_pct = pct
                    elapsed = time.time() - t0
                    left = elapsed / n_new * (n_mine - n_done)
                    print(f"{pct:3d}% ({n_done}/{n_mine}) · {_clock(elapsed)} elapsed · "
                          f"~{_clock(left)} left", flush=True)
        except KeyboardInterrupt:
            ex.shutdown(wait=False, cancel_futures=True)
            sys.exit(f"\nstopped after {len(done) + n_new} of {n_mine} options; "
                     "run the same command again to resume")
        ex.shutdown()

    df = finish(pd.read_csv(partial), out)
    partial.unlink()
    meta.unlink()
    print(f"wrote {out} ({len(df)} options, {_clock(time.time() - t0)})")


if __name__ == "__main__":
    main()
