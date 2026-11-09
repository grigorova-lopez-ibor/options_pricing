"""The 35 put check options and the 40 options from the input ranges of
results/two_per_day, re-run with the best combination of results/diagnostics/
bias_vs_dates_paths: in-sample label, SPY exercise dates a year, N_MAIN main paths
(pilot 100k), REPS labels per option. References: American PDE and the Bermudan
PDE at SPY dates a year.

    python experiments/diagnostics/best_config.py run --task 0 --ntasks 100 --out OUT
    python experiments/diagnostics/best_config.py ref --task 0 --ntasks 25 --out OUT
    python experiments/diagnostics/best_config.py count --out OUT
    python experiments/diagnostics/best_config.py plan --ntasks 100

Labels go to OUT/best_config/labels/task_XXXX/chunk_*.parquet (10 a chunk, finished
labels skipped on a restart), references to OUT/best_config/ref. The tables and
histograms: best_config_report.py."""
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

from experiments.tournament import tpd_options  # noqa: E402
from simgreeks.core import PutSpec  # noqa: E402
from simgreeks.multi import MultiConfig, label  # noqa: E402
from simgreeks.reference import FORWARD_GREEKS, LABEL_GREEKS, label_reference  # noqa: E402
from simgreeks.runner import job_seed  # noqa: E402

SPY = 252
N_MAIN = 600_000
N_PILOT = 100_000
REPS = 100
SETS = {"check": 9300, "random": 9301}          # option set -> base seed
Q = ["price", "delta", "gamma", "theta", "theta_pde", "charm", "vega", "volga", "vanna",
     "rho", "phi", "delta_r", "delta_d"]


def options(s: str) -> pd.DataFrame:
    """The options of results/two_per_day (tpd_check / tpd_random), with SPY dates a year."""
    o = tpd_options(f"tpd_{s}").copy()
    o["spy"] = SPY
    return o


def spec(row) -> PutSpec:
    return PutSpec(S0=float(row["S0"]), K=float(row["K"]), sigma=float(row["sigma"]),
                   r=float(row["r"]), d=float(row["d"]), T=float(row["T"]), kind="put",
                   steps_per_year=SPY)


def config() -> MultiConfig:
    # as freq_paths_grid.config: in-sample rule on the main paths, exercise_bound=False
    return MultiConfig(N=N_MAIN // 3, N_pilot=N_PILOT, vf_time=0.02, exercise_bound=False,
                       exercise_rule="insample", label_source="oos")


def est_seconds(T) -> float:
    """~55 s at T = 1 (252 a year, 600k paths, in-sample, SCC)."""
    return 3.0 + 52.0 * T


def jobs():
    return [(s, int(i), rep) for s in SETS for i in options(s).id for rep in range(REPS)]


def split(js, ntasks: int):
    """Longest jobs first, each to the least-loaded task (deterministic)."""
    mat = {s: options(s).set_index("id")["T"] for s in SETS}
    cost = {j: est_seconds(mat[j[0]][j[1]]) for j in js}
    load, tasks = np.zeros(ntasks), [[] for _ in range(ntasks)]
    for j in sorted(js, key=lambda j: (-cost[j], j)):
        k = int(np.argmin(load))
        tasks[k].append(j)
        load[k] += cost[j]
    return tasks, load


def _done(d: Path) -> set:
    done = set()
    for f in sorted(d.glob("chunk_*.parquet")):
        df = pd.read_parquet(f, columns=["set", "id", "rep"])
        done.update(zip(df["set"], df["id"].astype(int), df["rep"].astype(int)))
    return done


def one_label(opts: dict, job) -> dict:
    s, i, rep = job
    row = opts[s].loc[opts[s].id == i].iloc[0]
    out = dict(set=s, id=i, rep=rep, spy=SPY, N_main=N_MAIN,
               **{c: float(row[c]) for c in ("S0", "K", "sigma", "r", "d", "T")})
    t = time.perf_counter()
    res = label(spec(row), config(), job_seed(SETS[s], {"id": i}, rep))
    out.update({q: float(res.get(q, np.nan)) for q in Q})
    out["ex_region"] = bool(res.get("ex_region", False))
    out["seconds"] = time.perf_counter() - t
    out["rss_mb"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    return out


def run(task: int, ntasks: int, out: str, chunk: int = 10):
    mine = split(jobs(), ntasks)[0][task]
    d = Path(out) / "best_config" / "labels" / f"task_{task:04d}"
    d.mkdir(parents=True, exist_ok=True)
    done = _done(d)
    todo = [j for j in mine if j not in done]
    k = len(list(d.glob("chunk_*.parquet")))
    print(f"task {task}/{ntasks}: {len(mine)} labels, {len(done)} done, {len(todo)} to do", flush=True)
    opts, rows = {s: options(s) for s in SETS}, []
    for m, j in enumerate(todo, 1):
        rows.append(one_label(opts, j))
        if len(rows) >= chunk or m == len(todo):
            pd.DataFrame(rows).to_parquet(d / f"chunk_{k:05d}.parquet", index=False)
            k, rows = k + 1, []
            print(f"  {m}/{len(todo)} written", flush=True)


def ref(task: int, ntasks: int, out: str):
    """American PDE and the Bermudan PDE at SPY dates a year, per option."""
    d = Path(out) / "best_config" / "ref"
    d.mkdir(parents=True, exist_ok=True)
    qs = [q for q in LABEL_GREEKS if q != "vera"] + ["charm"] + [f"{q}_fwd" for q in FORWARD_GREEKS]
    allopts = [(s, int(i)) for s in SETS for i in options(s).id]
    for s, i in allopts[task::ntasks]:
        f = d / f"ref_{s}_{i:03d}.parquet"
        if f.exists():
            continue
        o = options(s)
        row = o.loc[o.id == i].iloc[0]
        rows = []
        for style in ("american", "bermudan"):
            t = time.perf_counter()
            r = label_reference(spec(row), style=style, vera=False)
            rows.append(dict(set=s, id=i, style=style, **{q: float(r[q]) for q in qs},
                             ex_region=bool(r["ex_region"]), seconds=time.perf_counter() - t))
            print(f"  {s} {i} {style}: {rows[-1]['seconds']:.0f} s", flush=True)
        pd.DataFrame(rows).to_parquet(f, index=False)


def load(out: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Labels and references: OUT/raw/{labels,reference}.parquet if present (the committed
    copy), else the task chunks in OUT/best_config."""
    raw = Path(out) / "raw"
    if (raw / "labels.parquet").exists():
        return pd.read_parquet(raw / "labels.parquet"), pd.read_parquet(raw / "reference.parquet")
    base = Path(out) / "best_config"
    lab = [pd.read_parquet(f) for f in sorted((base / "labels").glob("task_*/chunk_*.parquet"))]
    refs = [pd.read_parquet(f) for f in sorted((base / "ref").glob("ref_*.parquet"))]
    return (pd.concat(lab, ignore_index=True) if lab else pd.DataFrame(),
            pd.concat(refs, ignore_index=True) if refs else pd.DataFrame())


def main():
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["run", "ref", "count", "plan"])
    p.add_argument("--task", type=int, default=0)
    p.add_argument("--ntasks", type=int, default=1)
    p.add_argument("--out", default="best_config_out")
    a = p.parse_args()
    if a.cmd == "run":
        run(a.task, a.ntasks, a.out)
    elif a.cmd == "ref":
        ref(a.task, a.ntasks, a.out)
    elif a.cmd == "plan":
        _, load_ = split(jobs(), a.ntasks)
        print(f"{len(jobs())} labels, {sum(load_) / 3600:.0f} CPU hours (est.), longest task "
              f"{load_.max() / 3600:.1f} h with {a.ntasks} tasks, peak about 3 GB")
    else:
        lab, refs = load(a.out)
        n_ref = len(refs[["set", "id"]].drop_duplicates()) if len(refs) else 0
        print(f"labels: {len(lab)} of {len(jobs())}; reference options: {n_ref} of "
              f"{sum(len(options(s)) for s in SETS)}")


if __name__ == "__main__":
    main()
