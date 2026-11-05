"""Studies of the in-sample default label (exercise_rule="insample"). Not part
of the paper. Each study is resumable and writes one row per label to
results/diagnostics/insample_studies/<study>/raw.csv (and ref.csv for the PDE
reference values); insample_studies_report.py summarises them.

    python experiments/diagnostics/insample_studies.py <study> [--reps n] [--workers 4]

Studies:
  paths  in-sample labels at 150k, 300k, 450k, 600k main paths (pilot 100k),
         504 dates a year, on the 14 options of the 600k Volga check (the
         options whose in-sample Volga was most biased at 300k in
         results/two_per_day); the same seeds at every path count.
  dates  the default label at 50, 252 and 504 exercise dates a year on 20
         options of results/two_per_day with T <= 1, and the Bermudan PDE at
         each frequency plus the American PDE.
  crn    common random numbers: 2,000 options from the training-set ranges at
         50 dates a year, labelled once with a fresh seed each (independent)
         and once with one seed for all (common random numbers), plus the PDE.
  widthrule  the width rule fitted to the selector's alpha* (RULE_S, RULE_SIGMA) at 0.5,
         1, 1.5, 2 x, against the selector, out of sample: 25 options from the
         training ranges with r > d, 20 labels each, 252 dates a year, PDE.
  alpha  alpha*: on 6 options, 30 labels with the selector (alpha* as chosen),
         then 30 labels at fixed widths 0.5, 0.75, 1, 1.5, 2 x the median alpha*
         of S and sigma, 504 dates a year.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(v, "1")
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "experiments")]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from simgreeks.core import PutSpec  # noqa: E402
from simgreeks.multi import MultiConfig, label  # noqa: E402
from simgreeks.reference import label_reference  # noqa: E402
from simgreeks.runner import job_seed  # noqa: E402

OUT = ROOT / "results" / "diagnostics" / "insample_studies"
TPD = ROOT / "results" / "two_per_day" / "raw"
Q = ["price", "delta", "gamma", "theta", "charm", "vega", "volga", "vanna", "rho", "phi",
     "delta_r", "delta_d"]
PATHS_PICK = ([("random", i) for i in (6, 1, 26, 21, 37, 11, 9, 31, 23, 39)]
              + [("check", i) for i in (0, 9, 30, 3)])
PART_CODE = {"random": 1, "check": 2}


def tpd_spec(part: str, i: int, spy: int = 504) -> PutSpec:
    R = pd.read_parquet(TPD / f"{part}_reference.parquet").set_index("id").loc[i]
    return PutSpec(S0=float(R.S0), K=float(R.K), sigma=float(R.sigma), r=float(R.r), d=float(R.d),
                   T=float(R["T"]), steps_per_year=spy)


def vf_time(spy: int):
    return 0.02 if spy > 50 else None


# ------------------------------------------------------------------ jobs
def run_label(job: dict) -> dict:
    spec = PutSpec(**job["spec"])
    cfg = MultiConfig(**job["cfg"])
    seed = np.random.SeedSequence(job["seed"])
    t = time.time()
    lab = label(spec, cfg, seed)
    row = {k: v for k, v in job.items() if k not in ("spec", "cfg", "seed")}
    row["seconds"] = time.time() - t
    row.update({q: lab.get(q, np.nan) for q in Q})
    row.update({k: lab.get(k, np.nan) for k in ("alpha_S", "alpha_sigma", "ex_region", "european_region")})
    return row


def run_ref(job: dict) -> dict:
    spec = PutSpec(**job["spec"])
    t = time.time()
    ref = label_reference(spec, style=job["style"], vera=False)
    row = {k: v for k, v in job.items() if k != "spec"}
    row["seconds"] = time.time() - t
    row.update({q: ref.get(q, np.nan) for q in Q})
    row["ex_region"] = ref.get("ex_region", False)
    return row


def spec_dict(s: PutSpec) -> dict:
    return dict(S0=s.S0, K=s.K, sigma=s.sigma, r=s.r, d=s.d, T=s.T, steps_per_year=s.steps_per_year)


def execute(fn, jobs: list, path: Path, keys: list, workers: int) -> pd.DataFrame:
    """Run the jobs not yet in ``path`` (matched on ``keys``), saving as they finish."""
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = pd.read_csv(path).to_dict("records") if path.exists() else []
    done = {tuple(r[k] for k in keys) for r in rows}
    todo = [j for j in jobs if tuple(j[k] for k in keys) not in done]
    print(f"{path.parent.name}/{path.name}: {len(done)} done, {len(todo)} to do", flush=True)
    t0 = time.time()
    with ProcessPoolExecutor(workers) as ex:
        for k, row in enumerate(ex.map(fn, todo, chunksize=1), 1):
            rows.append(row)
            if k % 8 == 0 or k == len(todo):
                pd.DataFrame(rows).to_csv(path, index=False)
                left = (time.time() - t0) / k * (len(todo) - k)
                print(f"  {k} of {len(todo)} ({left / 60:.0f} min left)", flush=True)
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ studies
def study_paths(reps: int, workers: int) -> None:
    jobs = []
    for main in (150_000, 300_000, 450_000, 600_000):
        for rep in range(reps):
            for part, i in PATHS_PICK:
                jobs.append(dict(part=part, id=i, N_main=main, rep=rep,
                                 spec=spec_dict(tpd_spec(part, i)),
                                 cfg=dict(vf_time=0.02, N=main // 3, N_pilot=100_000),
                                 seed=[9600, PART_CODE[part], i, rep]))
    jobs.sort(key=lambda j: (j["rep"], -j["N_main"]))
    execute(run_label, jobs, OUT / "paths" / "raw.csv", ["part", "id", "N_main", "rep"], workers)


def dates_options() -> list:
    """20 options of results/two_per_day with T <= 1, outside the exercise and
    no-early-exercise regions: all such check options with K = 36, 40 and the
    random ones, in id order."""
    out = []
    for part in ("check", "random"):
        R = pd.read_parquet(TPD / f"{part}_reference.parquet")
        R = R[(R["T"] <= 1.0) & ~R.ex_region & ~(R.r <= 0)]
        if part == "check":
            R = R[R.K.isin([36.0, 40.0]) & (R.sigma > 0.1)]
        out += [(part, int(i)) for i in R.id]
    return out[:20]


def study_dates(reps: int, workers: int) -> None:
    opts = dates_options()
    refs = []
    for part, i in opts:
        for spy in (50, 252, 504):
            refs.append(dict(part=part, id=i, spy=spy, style="bermudan", spec=spec_dict(tpd_spec(part, i, spy))))
        refs.append(dict(part=part, id=i, spy=0, style="american", spec=spec_dict(tpd_spec(part, i, 504))))
    execute(run_ref, refs, OUT / "dates" / "ref.csv", ["part", "id", "spy", "style"], workers)
    jobs = []
    for rep in range(reps):
        for spy in (504, 252, 50):
            for part, i in opts:
                jobs.append(dict(part=part, id=i, spy=spy, rep=rep, spec=spec_dict(tpd_spec(part, i, spy)),
                                 cfg=dict(vf_time=vf_time(spy)),
                                 seed=[9700, PART_CODE[part], i, rep]))
    execute(run_label, jobs, OUT / "dates" / "raw.csv", ["part", "id", "spy", "rep"], workers)


def crn_options(n: int = 2000) -> pd.DataFrame:
    from generate_labels import sample_options
    return sample_options(n, 40.0, seed=97)


def study_crn(reps: int, workers: int) -> None:
    opts = crn_options()
    specs = {int(r.id): PutSpec(S0=float(r.S0), K=float(r.K), sigma=float(r.sigma), r=float(r.r),
                                d=float(r.d), T=float(r.T), steps_per_year=50)
             for r in opts.itertuples()}
    refs = [dict(id=i, style="bermudan", spec=spec_dict(s)) for i, s in specs.items()]
    execute(run_ref, refs, OUT / "crn" / "ref.csv", ["id", "style"], workers)
    jobs = []
    for i, s in specs.items():
        jobs.append(dict(id=i, mode="independent", spec=spec_dict(s), cfg={}, seed=[9800, i]))
        jobs.append(dict(id=i, mode="common", spec=spec_dict(s), cfg={}, seed=[9800, 0]))
    execute(run_label, jobs, OUT / "crn" / "raw.csv", ["id", "mode"], workers)


ALPHA_PICK = [("check", 4), ("check", 13), ("check", 3), ("random", 5), ("random", 29), ("random", 18)]
ALPHA_MULTS = (0.5, 0.75, 1.0, 1.5, 2.0)


def study_alpha(reps: int, workers: int) -> None:
    path = OUT / "alpha" / "raw.csv"
    sel = []
    for rep in range(reps):
        for part, i in ALPHA_PICK:
            sel.append(dict(part=part, id=i, mult=0.0, rep=rep, spec=spec_dict(tpd_spec(part, i)),
                            cfg=dict(vf_time=0.02), seed=[9900, PART_CODE[part], i, rep]))
    df = execute(run_label, sel, path, ["part", "id", "mult", "rep"], workers)
    med = df[df.mult == 0].groupby(["part", "id"])[["alpha_S", "alpha_sigma"]].median()
    jobs = []
    for rep in range(reps):
        for part, i in ALPHA_PICK:
            s = tpd_spec(part, i)
            aS, aV = med.loc[(part, i)]
            for m in ALPHA_MULTS:
                c_S = m * aS / (s.S0 * s.sigma * np.sqrt(s.T))
                c_sigma = min(m * aV / s.sigma, 0.75)          # sigma must stay positive
                jobs.append(dict(part=part, id=i, mult=m, rep=rep, spec=spec_dict(s),
                                 cfg=dict(vf_time=0.02, widths="fixed", c_S=float(c_S),
                                          c_sigma=float(c_sigma), pilot_widen=1.0),
                                 seed=[9900, PART_CODE[part], i, rep]))
    execute(run_label, jobs, path, ["part", "id", "mult", "rep"], workers)


# Width rule fitted to the selector's median alpha* over the 67 options of results/two_per_day
# (bias_distribution.py; log alpha_S / (S0 sigma sqrt T) on log sigma sqrt T and log T: R^2 0.87)
RULE_S = (0.154, 0.658, -0.194)        # alpha_S = a S0 (sigma sqrt T)^b T^c
RULE_SIGMA = 0.222                     # alpha_sigma = RULE_SIGMA sigma
RULE_MULTS = (0.5, 1.0, 1.5, 2.0)


def rule_widths(s: PutSpec, mult: float) -> tuple:
    """(c_S, c_sigma) of MultiConfig for the width rule times ``mult``, capped like the selector."""
    a, b, c = RULE_S
    sd = s.sigma * np.sqrt(s.T)
    aS = mult * a * s.S0 * sd ** b * s.T ** c
    aS = min(aS, min(0.25, 1.25 * sd) * s.S0)                   # the selector's cap: the pilot width
    return float(aS / (s.S0 * sd)), float(min(mult * RULE_SIGMA, 0.75))


def widthrule_options(n: int = 25) -> pd.DataFrame:
    """n options from the training-set ranges (a Sobol draw not used to fit the rule)
    with early exercise possible and informative (r > d)."""
    from generate_labels import sample_options
    o = sample_options(400, 40.0, seed=2026)
    return o[o.r > o.d].head(n).reset_index(drop=True)


def study_widthrule(reps: int, workers: int) -> None:
    spy = 252
    opts = widthrule_options()
    specs = {int(r.id): PutSpec(S0=float(r.S0), K=float(r.K), sigma=float(r.sigma), r=float(r.r),
                                d=float(r.d), T=float(r.T), steps_per_year=spy) for r in opts.itertuples()}
    refs = []
    for i, s in specs.items():
        refs.append(dict(id=i, style="bermudan", spec=spec_dict(s)))
        refs.append(dict(id=i, style="american", spec=spec_dict(s)))
    execute(run_ref, refs, OUT / "widthrule" / "ref.csv", ["id", "style"], workers)
    jobs = []
    for rep in range(reps):
        for i, s in specs.items():
            jobs.append(dict(id=i, mult=0.0, rep=rep, spec=spec_dict(s), cfg=dict(vf_time=0.02),
                             seed=[9950, i, rep]))
            for m in RULE_MULTS:
                c_S, c_sigma = rule_widths(s, m)
                jobs.append(dict(id=i, mult=m, rep=rep, spec=spec_dict(s),
                                 cfg=dict(vf_time=0.02, widths="fixed", c_S=c_S, c_sigma=c_sigma,
                                          pilot_widen=1.0),
                                 seed=[9950, i, rep]))
    execute(run_label, jobs, OUT / "widthrule" / "raw.csv", ["id", "mult", "rep"], workers)


STUDIES = {"paths": study_paths, "dates": study_dates, "crn": study_crn, "alpha": study_alpha,
           "widthrule": study_widthrule}
DEFAULT_REPS = {"paths": 40, "dates": 30, "crn": 1, "alpha": 30, "widthrule": 20}

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("study", choices=sorted(STUDIES))
    ap.add_argument("--reps", type=int, default=None)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    STUDIES[a.study](a.reps or DEFAULT_REPS[a.study], a.workers)
    print("done", flush=True)
