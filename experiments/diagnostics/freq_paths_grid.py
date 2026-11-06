"""Bias and noise of the in-sample label against the number of exercise dates a
year (SPY) and of main paths (N_MAIN): 15 put options spanning the input ranges,
REPS labels each at every (SPY, N_MAIN), pilot fixed at 100,000 paths, seeds
job_seed(BASE_SEED, {id}, rep) (the same at every setting). References: the
American PDE and the Bermudan PDE at each SPY, so a label's bias splits into
the exercise-date gap (Bermudan - American, exact) and the simulation bias
(label - Bermudan).

    python experiments/diagnostics/freq_paths_grid.py run --task 0 --ntasks 50 --size small --out OUT
    python experiments/diagnostics/freq_paths_grid.py ref --task 0 --ntasks 15 --out OUT
    python experiments/diagnostics/freq_paths_grid.py count --out OUT
    python experiments/diagnostics/freq_paths_grid.py plan --ntasks 50          # jobs, hours, memory

Labels are written as Parquet chunks of 10 to OUT/freq_paths/<size>/task_XXXX and
finished labels are skipped on a restart. --size small: the jobs whose estimated
peak memory is below SMALL_GB (run with mem_per_core=4G); --size big: the rest
(run with 16 GB). The analysis is freq_paths_report.py."""
import argparse
import os
import resource
import sys
import time
from pathlib import Path

for v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(v, "1")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from simgreeks.core import PutSpec  # noqa: E402
from simgreeks.multi import MultiConfig, label  # noqa: E402
from simgreeks.reference import FORWARD_GREEKS, LABEL_GREEKS, label_reference  # noqa: E402
from simgreeks.runner import job_seed  # noqa: E402

S0 = 40.0
SPYS = [126, 252, 504, 1008]
N_MAIN = [75_000, 150_000, 300_000, 600_000]
N_PILOT = 100_000
REPS = 30
BASE_SEED = 9200
SMALL_GB = 3.3
# (T, sigma, r, d, K): short and long maturities, out of / at / in the money,
# low and high volatility, r > d, r = d and r < d, all inside generate_labels' ranges
OPTIONS = [
    (0.5, 0.20, 0.05, 0.00, 40), (0.5, 0.20, 0.05, 0.00, 44), (0.5, 0.20, 0.05, 0.00, 36),
    (1 / 6, 0.20, 0.05, 0.00, 40), (1 / 6, 0.40, 0.03, 0.00, 46), (2.0, 0.20, 0.05, 0.00, 40),
    (2.0, 0.10, 0.03, 0.00, 44), (2.0, 0.40, 0.02, 0.01, 34), (1.0, 0.05, 0.03, 0.00, 40.5),
    (1.0, 0.50, 0.04, 0.02, 40), (1.0, 0.20, 0.01, 0.04, 40), (1.0, 0.20, 0.05, 0.05, 44),
    (1.0, 0.20, 0.005, 0.00, 40), (0.5, 0.30, 0.03, 0.01, 50), (1.5, 0.15, 0.05, 0.02, 38),
]
Q = ["price", "delta", "gamma", "theta", "theta_pde", "charm", "vega", "volga", "vanna",
     "rho", "phi", "delta_r", "delta_d"]


def options() -> pd.DataFrame:
    return pd.DataFrame([dict(id=i, S0=S0, K=float(K), sigma=s, r=r, d=d, T=round(T, 6))
                         for i, (T, s, r, d, K) in enumerate(OPTIONS)])


def spec(row, spy: int) -> PutSpec:
    return PutSpec(S0=S0, K=float(row["K"]), sigma=float(row["sigma"]), r=float(row["r"]),
                   d=float(row["d"]), T=float(row["T"]), kind="put", steps_per_year=int(spy))


def config(n_main: int) -> MultiConfig:
    # the in-sample label of results/two_per_day: one (S, sigma) run with
    # 3 N main paths, the pilot chooses the widths, the exercise rule is fitted
    # on the main paths (exercise_bound=False as in results/two_per_day)
    return MultiConfig(N=n_main // 3, N_pilot=N_PILOT, vf_time=0.02, exercise_bound=False,
                       exercise_rule="insample", label_source="oos")


def est_seconds(T, spy, n_main) -> float:
    """~55 s per label at T = 1, 504 dates a year, 300k main paths (in-sample, SCC)."""
    return 3.0 + 52.0 * T * (spy / 504) * (n_main / 300_000)


def est_gb(T, spy, n_main) -> float:
    """~2.9 GB at T = 2, 504 a year, 300k main paths; grows with paths x dates."""
    return 0.3 + 1.3 * T * (spy / 504) * (n_main / 300_000)


def jobs(size: str | None = None):
    o = options()
    out = []
    for row in o.itertuples():
        for spy in SPYS:
            for n in N_MAIN:
                big = est_gb(row.T, spy, n) >= SMALL_GB
                if size is None or (size == "big") == big:
                    out += [(int(row.id), spy, n, rep) for rep in range(REPS)]
    return out


def split(js, ntasks: int):
    """Longest jobs first, each to the least-loaded task (deterministic)."""
    mat = options().set_index("id")["T"]
    cost = {j: est_seconds(mat[j[0]], j[1], j[2]) for j in js}
    load, tasks = np.zeros(ntasks), [[] for _ in range(ntasks)]
    for j in sorted(js, key=lambda j: (-cost[j], j)):
        k = int(np.argmin(load))
        tasks[k].append(j)
        load[k] += cost[j]
    return tasks, load


def _done(d: Path, cols) -> set:
    done = set()
    for f in sorted(d.glob("chunk_*.parquet")):
        df = pd.read_parquet(f, columns=cols)
        done.update(map(tuple, df[cols].astype(int).values))
    return done


def one_label(o: pd.DataFrame, job) -> dict:
    i, spy, n, rep = job
    row = o.loc[o.id == i].iloc[0]
    out = dict(id=i, spy=spy, N_main=n, rep=rep, **{c: float(row[c]) for c in ("K", "sigma", "r", "d", "T")})
    t = time.perf_counter()
    res = label(spec(row, spy), config(n), job_seed(BASE_SEED, {"id": i}, rep))
    out.update({q: float(res.get(q, np.nan)) for q in Q})
    out["ex_region"] = bool(res.get("ex_region", False))
    out["seconds"] = time.perf_counter() - t
    out["rss_mb"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    return out


def run(task: int, ntasks: int, size: str, out: str, chunk: int = 10):
    mine = split(jobs(size), ntasks)[0][task]
    d = Path(out) / "freq_paths" / size / f"task_{task:04d}"
    d.mkdir(parents=True, exist_ok=True)
    done = _done(d, ["id", "spy", "N_main", "rep"])
    todo = [j for j in mine if j not in done]
    k = len(list(d.glob("chunk_*.parquet")))
    print(f"{size} task {task}/{ntasks}: {len(mine)} labels, {len(done)} done, {len(todo)} to do", flush=True)
    o, rows = options(), []
    for m, j in enumerate(todo, 1):
        rows.append(one_label(o, j))
        if len(rows) >= chunk or m == len(todo):
            pd.DataFrame(rows).to_parquet(d / f"chunk_{k:05d}.parquet", index=False)
            k, rows = k + 1, []
            print(f"  {m}/{len(todo)} written", flush=True)


def ref(task: int, ntasks: int, out: str):
    """American PDE once and the Bermudan PDE at every SPY, per option."""
    o = options()
    d = Path(out) / "freq_paths" / "ref"
    d.mkdir(parents=True, exist_ok=True)
    qs = [q for q in LABEL_GREEKS if q != "vera"] + ["charm"] + [f"{q}_fwd" for q in FORWARD_GREEKS]
    for i in o.id[task::ntasks]:
        f = d / f"ref_{i:03d}.parquet"
        if f.exists():
            continue
        row = o.loc[o.id == i].iloc[0]
        rows = []
        for style, spy in [("american", 504)] + [("bermudan", s) for s in SPYS]:
            t = time.perf_counter()
            r = label_reference(spec(row, spy), style=style, vera=False)
            rows.append(dict(id=int(i), style=style, spy=spy if style == "bermudan" else 0,
                             **{q: float(r[q]) for q in qs}, ex_region=bool(r["ex_region"]),
                             seconds=time.perf_counter() - t))
            print(f"  option {i} {style} {spy}: {rows[-1]['seconds']:.0f} s", flush=True)
        pd.DataFrame(rows).to_parquet(f, index=False)


def load(out: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    base = Path(out) / "freq_paths"
    lab = [pd.read_parquet(f) for s in ("small", "big") for f in sorted((base / s).glob("task_*/chunk_*.parquet"))]
    refs = [pd.read_parquet(f) for f in sorted((base / "ref").glob("ref_*.parquet"))]
    return (pd.concat(lab, ignore_index=True) if lab else pd.DataFrame(),
            pd.concat(refs, ignore_index=True) if refs else pd.DataFrame())


def plan(ntasks: int):
    o = options().set_index("id")
    for size in ("small", "big"):
        js = jobs(size)
        if not js:
            continue
        _, load_ = split(js, ntasks)
        gb = max(est_gb(o.loc[j[0], "T"], j[1], j[2]) for j in js)
        print(f"{size}: {len(js)} labels, {sum(load_) / 3600:.0f} CPU hours (est.), "
              f"longest task {load_.max() / 3600:.1f} h with {ntasks} tasks, peak {gb:.1f} GB")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["run", "ref", "count", "plan"])
    p.add_argument("--task", type=int, default=0)
    p.add_argument("--ntasks", type=int, default=1)
    p.add_argument("--size", choices=["small", "big"], default="small")
    p.add_argument("--out", default="freq_paths_out")
    a = p.parse_args()
    if a.cmd == "run":
        run(a.task, a.ntasks, a.size, a.out)
    elif a.cmd == "ref":
        ref(a.task, a.ntasks, a.out)
    elif a.cmd == "plan":
        plan(a.ntasks)
    else:
        lab, refs = load(a.out)
        print(f"labels: {len(lab)} of {len(jobs())}; reference options: "
              f"{refs.id.nunique() if len(refs) else 0} of {len(OPTIONS)}")


if __name__ == "__main__":
    main()
