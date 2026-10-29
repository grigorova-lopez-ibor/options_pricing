"""Can the r and d Greeks reuse the (S, sigma) run's paths? Not part of the paper.

    python experiments/diagnostics/rd_pathwise_check.py [reps]   (40 reps: ~10 min on 4 cores)

Writes results/diagnostics/rd_pathwise/raw.csv and summary.md. Exercise rule out
of sample (label_source="oos") in all three; reference: reference.put_fd_greeks.

Per replication of one option, on the default label's runs:
  A  default: (S, sigma) 200k+100k, (S, r) and (S, d) 50k+50k, independent shocks
  B  shared shocks: the (S, r), (S, d) runs reuse the first rows of the (S, sigma) run's W
  C  pathwise: Rho, Phi, dDelta/dr, dDelta/dd from the (S, sigma) run alone, no r, d runs:
     per path Y_rho = -tau K e^{-r tau} 1{ex}, Y_phi = tau S_tau e^{-r tau} 1{ex}
     (exercise time tau of the out-of-sample rule held fixed; envelope theorem),
     minus the same for the European payoff (control variate, closed form added back),
     regressed on the (S, sigma) Taylor basis: intercept = Greek at z0, S-slope = cross term.
"""
import os
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[v] = "1"
import sys
import time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import simgreeks.multi as m  # noqa: E402
from simgreeks.core import PutSpec  # noqa: E402
from simgreeks.reference import bs_option, put_fd_greeks  # noqa: E402

OPTIONS = [PutSpec(S0=40, K=40, sigma=0.20, r=0.04, d=0.01, T=0.5),
           PutSpec(S0=40, K=44, sigma=0.30, r=0.03, d=0.02, T=1.0),
           PutSpec(S0=40, K=36, sigma=0.15, r=0.05, d=0.00, T=1.0)]
G = ["price", "delta", "gamma", "rho", "phi", "delta_r", "delta_d"]


def exercise_paths(spec, cfg, z, W, scale, rules, euro_bound=False):
    """tau (years), S_tau and the in-the-money indicator at exercise for the stored rule.
    euro_bound: exercise only where the payoff is at least the European value
    (the American continuation value is never below it)."""
    J, N = spec.J, len(z["S"])
    params, P, Pk = m._params(spec, z, scale)
    mono, index = m.monomials(P, m.basis_terms(cfg.M_tau, len(params), cfg.weight,
                                               cfg.param_degree, None), Pk)
    jt = np.full(N, J)
    St = m.stock_at(spec, z, W, J)
    alive = np.ones(N, dtype=bool)
    for j in range(1, J):              # forward: first date the rule exercises
        Sj = m.stock_at(spec, z, W, j)
        ex = spec.payoff(Sj)
        itm = (ex > 0) & alive
        fit = rules.get(j)
        if fit is None or not itm.any():
            continue
        e = np.zeros(N, dtype=bool)
        e[itm] = ex[itm] >= m._predict(fit, Sj[itm], mono[itm], index, cfg.M_tau)
        if euro_bound:
            e[itm] &= ex[itm] >= m.european_value(spec, Sj[itm], spec.T - j * spec.dt,
                                                  z["sigma"][itm], z["r"][itm], z["d"][itm])
        jt[e], St[e] = j, Sj[e]
        alive &= ~e
    return jt * spec.dt, St, St < spec.K, m.stock_at(spec, z, W, J)


def pathwise(spec, cfg, z, W, scale, rules, euro_bound=False):
    tau, St, itm, ST = exercise_paths(spec, cfg, z, W, scale, rules, euro_bound)
    r, K, T = spec.r, spec.K, spec.T
    eu_itm = ST < K
    y_rho = -tau * K * np.exp(-r * tau) * itm + T * K * np.exp(-r * T) * eu_itm
    y_phi = tau * St * np.exp(-r * tau) * itm - T * ST * np.exp(-r * T) * eu_itm
    bs = bs_option(spec)
    out = {}
    dims = ("S", "sigma")
    for name, y, eu in (("rho", y_rho, "rho"), ("phi", y_phi, "phi")):
        g = m.greeks_from(m.taylor_fit(spec, cfg, z, y, dims))
        out[name] = g["price"] + bs[eu]
        out[f"delta_{name[0] if name == 'rho' else 'd'}"] = g["delta"]
    # cross terms: European parts from a bump of the closed form
    h = 1e-3 * spec.S0
    for name, eu in (("delta_r", "rho"), ("delta_d", "phi")):
        up = bs_option(PutSpec(**{**spec.__dict__, "S0": spec.S0 + h}))[eu]
        dn = bs_option(PutSpec(**{**spec.__dict__, "S0": spec.S0 - h}))[eu]
        out[name] = out.pop(name, 0.0) + (up - dn) / (2 * h)
    return out


class Shared:
    """Patch for multi.brownian: return the first N rows of stored pilot/main shocks."""
    def __init__(self, Wp, W):
        self.arrays, self.k = [Wp, W], 0

    def __call__(self, spec, N, rng):
        a = self.arrays[self.k % 2][:N]
        self.k += 1
        return a


def one(job):
    i, rep = job
    spec, cfg = OPTIONS[i], m.MultiConfig(label_source="oos", exercise_rule="pilot")
    ss = np.random.SeedSequence([9001, i, rep])
    seeds = ss.spawn(3)
    t0 = time.time()
    # (S, sigma) run, by hand so its paths and rule are kept
    sc = m.run_config(cfg, ("S", "sigma"))
    rng = np.random.default_rng(seeds[0])
    alphas, scale, rules = m.pilot(spec, sc, ("S", "sigma"), rng)
    z = m.isd_multi(spec, sc, alphas, rng)
    W = m.brownian(spec, sc.N, rng)
    _, Y, _ = m.lsm_multi(spec, sc, z, W, scale, rules)
    run_s = m.greeks_multi(spec, sc, ("S", "sigma"), z, Y, bs_option(spec))
    run_s["N"] = sc.N
    t_sigma = time.time() - t0
    # Wp of the sigma run: regenerate from the same stream (pilot draws first)
    rng2 = np.random.default_rng(seeds[0])
    m.isd_multi(spec, sc, m.pilot_widths(spec, sc, ("S", "sigma")), rng2, sc.N_pilot)
    Wp = m.brownian(spec, sc.N_pilot, rng2)
    t1 = time.time()
    pw = pathwise(spec, sc, z, W, scale, rules)
    t_pw = time.time() - t1
    rows = []
    t2 = time.time()
    indep = [m.run_group(spec, cfg, g, s) for g, s in zip(cfg.groups[1:], seeds[1:])]
    t_rd = time.time() - t2
    orig = m.brownian
    m.brownian = Shared(Wp, W)
    try:
        shared = [m.run_group(spec, cfg, g, s) for g, s in zip(cfg.groups[1:], seeds[1:])]
    finally:
        m.brownian = orig
    for name, runs in (("A_independent", [run_s] + indep), ("B_shared", [run_s] + shared)):
        lab = m._assemble(spec, cfg, runs)
        rows.append(dict(option=i, rep=rep, method=name, **{g: lab[g] for g in G}))
    lab_c = {g: run_s[g] for g in ("price", "delta", "gamma")}
    lab_c.update(pw)
    rows.append(dict(option=i, rep=rep, method="C_pathwise", **lab_c))
    for r in rows:
        r.update(t_sigma=t_sigma, t_rd=t_rd, t_pw=t_pw)
    return rows


if __name__ == "__main__":
    reps = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    out_dir = ROOT / "results" / "diagnostics" / "rd_pathwise"
    out_dir.mkdir(parents=True, exist_ok=True)
    jobs = [(i, k) for i in range(len(OPTIONS)) for k in range(reps)]
    with ProcessPoolExecutor(4) as ex:
        rows = [r for rs in ex.map(one, jobs) for r in rs]
    df = pd.DataFrame(rows)
    df.to_csv(out_dir / "raw.csv", index=False)
    ref = [put_fd_greeks(s) for s in OPTIONS]
    lines = []
    for i, s in enumerate(OPTIONS):
        lines.append(f"\noption {i}: K={s.K} sigma={s.sigma} r={s.r} d={s.d} T={s.T}")
        lines.append("bias % (t) / sd of one label %, both relative to |reference|")
        lines.append(f"{'':14s}" + "".join(f"{g:>21s}" for g in G))
        lines.append(f"{'reference':14s}" + "".join(f"{ref[i][g]:21.4f}" for g in G))
        for meth, d in df[df.option == i].groupby("method"):
            cells = []
            for g in G:
                a = abs(ref[i][g])
                b, sd = d[g].mean() - ref[i][g], d[g].std()
                t = b / (sd / np.sqrt(len(d)))
                cells.append(f"{100 * b / a:+6.2f} ({t:+5.1f}) / {100 * sd / a:5.1f}".rjust(21))
            lines.append(f"{meth:14s}" + "".join(cells))
        d = df[df.option == i]
        lines.append(f"seconds: sigma run {d.t_sigma.mean():.1f}, r+d runs {d.t_rd.mean():.1f}, "
                     f"pathwise {d.t_pw.mean():.2f}")
    text = "\n".join(lines)
    (out_dir / "summary.md").write_text(f"# r and d Greeks from the (S, sigma) paths, {reps} reps\n\n```{text}\n```\n")
    print(text)
