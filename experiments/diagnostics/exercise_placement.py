"""Where to put the exercise dates: the Bermudan-American gap for different
placements of the same number of dates, from the PDE alone (exact, no Monte
Carlo noise). Not part of the paper.

    python experiments/diagnostics/exercise_placement.py [--workers 4]

A placement is a map g from u = j/J (j = 1..J) to the date t_j = T g(u), with
g(0) = 0 and g(1) = 1:

    uniform        g(u) = u                              (the labels today)
    late p         g(u) = 1 - (1 - u)^p                   dates denser towards maturity
                                                          (p = 2: uniform in sqrt(time to maturity))
    early p        g(u) = u^p                             denser near the start (contrast)
    ends a         g(u) = (1 - a) u + a (1 - cos(pi u))/2 denser at both ends

Each placement is run with J = round(D T) dates for D = 252 and 126 a year (and
uniform at 504 for scale); plus Richardson in the number of uniform dates,
2 B(252) - B(126), since the gap is about proportional to 1/J. Gap = (Bermudan -
American) / |American| in %, for price, Delta, Gamma, Theta, Charm, Vega, Rho
and Phi, on the 75 options of results/two_per_day against their American PDE
values (the same x-grid). The Bermudan solver is put_fd with the exercise dates
as a list (steps_per_dt time steps in every interval, Rannacher after the
payoff and every exercise date); with uniform dates it reproduces put_fd.
Writes results/diagnostics/exercise_placement/{raw.csv, summary.md}.
"""
from __future__ import annotations

import argparse
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path

for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(v, "1")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from simgreeks.core import PutSpec  # noqa: E402
from simgreeks.reference import BUMPS, _half_width, _operator, _Stepper, grid_for  # noqa: E402

OUT = ROOT / "results" / "diagnostics" / "exercise_placement"
TPD = ROOT / "results" / "two_per_day" / "raw"
GREEKS = ["price", "delta", "gamma", "theta", "charm", "vega", "rho", "phi"]

PLACEMENTS = {
    "uniform": lambda u: u,
    "late 1.5": lambda u: 1 - (1 - u) ** 1.5,
    "late 2": lambda u: 1 - (1 - u) ** 2,
    "late 3": lambda u: 1 - (1 - u) ** 3,
    "early 2": lambda u: u ** 2,
    "ends 0.5": lambda u: 0.5 * u + 0.25 * (1 - np.cos(np.pi * u)),
}
COUNTS = (252, 126)


def dates(T: float, per_year: int, placement: str) -> np.ndarray:
    """Exercise dates t_1 < ... < t_J = T."""
    J = max(1, int(round(per_year * T)))
    t = T * PLACEMENTS[placement](np.arange(1, J + 1) / J)
    t[-1] = T
    return t


def put_fd_dates(spec: PutSpec, t: np.ndarray, grid) -> dict:
    """put_fd(style="bermudan") with exercise at the dates t (t[-1] = T is the
    payoff; no exercise at t_0), grid.steps_per_dt steps in each interval."""
    n = grid.n_x | 1
    ic = n // 2
    L = grid.half_width
    h = 2 * L / (n - 1)
    S = spec.S0 * np.exp((np.arange(n) - ic) * h)
    m = grid.steps_per_dt
    coefs = _operator(spec, h)
    payoff = spec.payoff(S)
    call = spec.kind == "call"
    never = spec.no_early_exercise
    cache = {}

    def stepper(k, th):
        key = (round(k, 15), th)
        if key not in cache:
            cache[key] = _Stepper(coefs, n, k, th)
        return cache[key]

    def bounds(s, tau):
        s = tau if never else s
        edge = S[-1] if call else S[0]
        v = spec.sign * (edge * np.exp(-spec.d * s) - spec.K * np.exp(-spec.r * s))
        return (0.0, v) if call else (v, 0.0)

    # interval lengths from maturity backwards: t_J - t_{J-1}, ..., t_1 - 0
    knots = np.concatenate([[0.0], t])
    lengths = np.diff(knots)[::-1]
    V = payoff.copy()
    tau, since, steps_since = 0.0, 0.0, 0
    rec = {}
    total = len(lengths) * m
    done = 0
    for i, Lk in enumerate(lengths):
        k = Lk / m
        for _ in range(m):
            done += 1
            if steps_since < 2:
                V = stepper(k / 2, 1.0)(V, *bounds(since + k / 2, tau + k / 2))
                V = stepper(k / 2, 1.0)(V, *bounds(since + k, tau + k))
            else:
                V = stepper(k, 0.5)(V, *bounds(since + k, tau + k))
            since += k
            tau += k
            steps_since += 1
            if done - total in (-1, 0):
                rec[done - total] = V[ic - 1:ic + 2].copy()
        if i < len(lengths) - 1:                       # exercise date (not t_0)
            V = np.maximum(V, payoff)
            since, steps_since = 0.0, 0
    # one step past t_0 with the first interval's step, for Theta and Charm
    k = lengths[-1] / m
    V = stepper(k, 0.5)(V, *bounds(since + k, tau + k)) if steps_since >= 2 else \
        stepper(k / 2, 1.0)(stepper(k / 2, 1.0)(V, *bounds(since + k / 2, tau + k / 2)), *bounds(since + k, tau + k))
    rec[1] = V[ic - 1:ic + 2].copy()
    v_m, v_0, v_p = rec[0]
    Vx = (v_p - v_m) / (2 * h)
    Vxx = (v_p - 2 * v_0 + v_m) / h ** 2
    theta = float((rec[-1][1] - rec[1][1]) / (2 * k))
    charm = float((rec[-1][2] - rec[-1][0] - rec[1][2] + rec[1][0]) / (2 * h) / spec.S0 / (2 * k))
    price = float(v_0)
    return dict(price=price, delta=float(Vx / spec.S0), gamma=float((Vxx - Vx) / spec.S0 ** 2),
                theta=theta, charm=charm, ex_region=bool(spec.intrinsic >= price))


def greeks_dates(spec: PutSpec, t: np.ndarray) -> dict:
    """put_fd_dates plus Vega, Rho, Phi by central bumps with Richardson over h and
    h/2, as reference.put_fd_greeks / label_reference (r bump at most r / 2)."""
    grid = grid_for(spec)
    grid = replace(grid, half_width=grid.half_width or _half_width(spec, grid))
    out = put_fd_dates(spec, t, grid)
    bumps = dict(BUMPS)
    if spec.r > 0:
        bumps["r"] = min(BUMPS["r"], spec.r / 2)
    names = {"sigma": "vega", "r": "rho", "d": "phi"}
    for p, h in bumps.items():
        D = []
        for hh in (h, h / 2):
            up = put_fd_dates(replace(spec, **{p: getattr(spec, p) + hh}), t, grid)["price"]
            dn = put_fd_dates(replace(spec, **{p: getattr(spec, p) - hh}), t, grid)["price"]
            D.append((up - dn) / (2 * hh))
        out[names[p]] = (4 * D[1] - D[0]) / 3
    return out


def configs():
    out = [("uniform", 504)]
    for c in COUNTS:
        out += [(p, c) for p in PLACEMENTS]
    return out


def one(job) -> dict:
    row, placement, per_year = job
    spec = PutSpec(S0=row["S0"], K=row["K"], sigma=row["sigma"], r=row["r"], d=row["d"], T=row["T"],
                   steps_per_year=max(per_year, 200))   # grid_for: 10 steps per date interval
    t = dates(spec.T, per_year, placement)
    g = greeks_dates(spec, t)
    return dict(part=row["part"], id=int(row["id"]), placement=placement, per_year=per_year, J=len(t),
                first_date_days=365 * t[0], last_gap_days=365 * (t[-1] - t[-2]) if len(t) > 1 else 365 * t[0],
                **{q: g[q] for q in GREEKS})


def load_options() -> pd.DataFrame:
    R = pd.concat([pd.read_parquet(TPD / f"{p}_reference.parquet") for p in ("check", "random")])
    R["part"] = R["part"].str.replace("tpd_", "", regex=False).str.replace("_ref", "", regex=False)
    spec_ok = [not PutSpec(S0=r.S0, K=r.K, sigma=r.sigma, r=r.r, d=r.d, T=r.T).no_early_exercise
               for r in R.itertuples()]
    return R[~R.ex_region & np.array(spec_ok)].reset_index(drop=True)


def summarise(raw: pd.DataFrame, R: pd.DataFrame) -> list:
    am = R.set_index(["part", "id"])
    rows = []
    for _, x in raw.iterrows():
        a = am.loc[(x.part, x.id)]
        for q in GREEKS:
            ref = a[q]
            big = R[R.part == x.part][q].abs().max()
            if abs(ref) < 0.01 * big:
                continue
            rows.append(dict(part=x.part, id=x.id, placement=x.placement, per_year=x.per_year, greek=q,
                             gap=100 * (x[q] - ref) / abs(ref)))
    g = pd.DataFrame(rows)
    # Richardson in the number of uniform dates
    u = g[g.placement == "uniform"].pivot_table(index=["part", "id", "greek"], columns="per_year", values="gap")
    rich = (2 * u[252] - u[126]).rename("gap").reset_index()
    rich["placement"], rich["per_year"] = "Richardson 2·B(252) − B(126)", 252
    g = pd.concat([g, rich], ignore_index=True)
    order = [("uniform", 504)] + [(p, c) for c in COUNTS for p in PLACEMENTS] + \
            [("Richardson 2·B(252) − B(126)", 252)]
    lines = ["# Where to put the exercise dates: Bermudan-American gap from the PDE", "",
             "Not part of the paper. `experiments/diagnostics/exercise_placement.py`. Exercise dates "
             "t_j = T g(j/J), J = round(dates a year × T): uniform g(u) = u (the labels today); "
             "late p: g(u) = 1 − (1 − u)^p (denser towards maturity; p = 2 is uniform in √(time to "
             "maturity)); early p: g(u) = u^p (denser near the start); ends a: (1 − a) u + a (1 − cos πu)/2 "
             "(denser at both ends). Gap = (Bermudan − American) / |American| in %, both from the "
             "Crank–Nicolson PDE on the same x-grid (no Monte Carlo noise), on the options of "
             "results/two_per_day outside the exercise region and the no-early-exercise region; "
             "per Greek, options with |American| < 1 % of the largest are left out. The cost of a "
             "label is proportional to the number of dates, not to where they are.", ""]
    for stat, f in (("Mean |gap| (%)", lambda s: s.abs().mean()),
                    ("95th percentile of |gap| (%)", lambda s: s.abs().quantile(0.95))):
        lines += [f"## {stat}", "", "| placement | dates/yr | " + " | ".join(GREEKS) + " |",
                  "|---|---|" + "---|" * len(GREEKS)]
        for p, c in order:
            y = g[(g.placement == p) & (g.per_year == c)]
            if y.empty:
                continue
            lines.append(f"| {p} | {c} | " + " | ".join(f"{f(y[y.greek == q].gap):.3g}" for q in GREEKS) + " |")
        lines.append("")
    lines += ["Signed mean gap (%) (the Bermudan is below the American price):", "",
              "| placement | dates/yr | " + " | ".join(GREEKS) + " |", "|---|---|" + "---|" * len(GREEKS)]
    for p, c in order:
        y = g[(g.placement == p) & (g.per_year == c)]
        if y.empty:
            continue
        lines.append(f"| {p} | {c} | " + " | ".join(f"{y[y.greek == q].gap.mean():+.3g}" for q in GREEKS) + " |")
    lines.append("")
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    R = load_options()
    jobs = [(r, p, c) for r in R.to_dict("records") for p, c in configs()]
    print(len(R), "options,", len(jobs), "PDE runs", flush=True)
    with ProcessPoolExecutor(a.workers) as ex:
        raw = pd.DataFrame(list(ex.map(one, jobs, chunksize=4)))
    raw.to_csv(OUT / "raw.csv", index=False)
    lines = summarise(raw, R)
    (OUT / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
