"""Pathwise Theta and Charm against the PDE identity. Not part of the paper.

    python experiments/diagnostics/theta_pathwise_check.py [reps]   (8 reps: ~40 min on 4 cores)

The label's Theta comes from the PDE identity Theta = r V - (r - d) S Delta
- 1/2 sigma^2 S^2 Gamma, so it carries the noise of Gamma. Charm = dDelta/dt =
dTheta/dS from the same identity needs Speed = dGamma/dS as well:
    Charm_pde = d Delta - (r - d) S Gamma - sigma^2 S Gamma - 1/2 sigma^2 S^2 Speed.

Pathwise. With W_tau = sqrt(tau) Z, a path's discounted payoff
Y = e^{-r tau} phi(S_tau), S_tau = S exp(mu tau + sigma W_tau), mu = r - d - sigma^2 / 2,
depends on the maturity T through tau = (j / J) T (exercise date index j held
fixed, envelope theorem), so
    dY/dT = (tau / T) e^{-r tau} [-r phi + s 1{in the money} S_tau (mu + sigma W_tau / (2 tau))]
and Theta = -dV/dT (time to maturity; with the number of exercise dates held
fixed, which differs from the calendar Theta of a Bermudan option by the
effect of the exercise spacing). The same for the European payoff (tau = T) is
subtracted and the closed-form European Theta added back (control variate);
the per-path values are regressed on the run's t = 0 Taylor basis: the
intercept is Theta, the S-slope Charm. Exercise as in the default label's
pathwise Rho (European bound).

Runs the default label's (S, sigma) run by hand; options: the 33 of the
American check (S0 = 40) and the 23 from the new ranges. Reference:
reference.put_fd_greeks (Theta and Charm by central differences in calendar
time, exercise dates fixed), refined grid where sigma sqrt(T) < 0.1.
Writes results/diagnostics/theta_pathwise/summary.md and raw.csv.
"""
import os
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[v] = "1"
import sys  # noqa: E402
import time  # noqa: E402
from concurrent.futures import ProcessPoolExecutor  # noqa: E402
from dataclasses import replace  # noqa: E402
from math import factorial  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiments"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import simgreeks.multi as m  # noqa: E402
from multi_check import american_grid, spec_of  # noqa: E402
from rd_pathwise_check import exercise_paths  # noqa: E402
from rd_pathwise_stress import sample  # noqa: E402
from simgreeks.core import theta_pde  # noqa: E402
from simgreeks.reference import FDGrid, bs_option, put_fd_greeks  # noqa: E402

OUT = ROOT / "results" / "diagnostics" / "theta_pathwise"
DIMS = ("S", "sigma")
METHODS = ["pde", "pw_oos", "pw_ins", "pw_avg", "cal_oos", "cal_ins", "cal_avg"]


def european_charm_speed(spec):
    hT, hS = 1e-4 * spec.T, 1e-4 * spec.S0
    charm = -(bs_option(replace(spec, T=spec.T + hT))["delta"]
              - bs_option(replace(spec, T=spec.T - hT))["delta"]) / (2 * hT)
    speed = (bs_option(replace(spec, S0=spec.S0 + hS))["gamma"]
             - bs_option(replace(spec, S0=spec.S0 - hS))["gamma"]) / (2 * hS)
    return charm, speed


def theta_paths(spec, cfg, z, W, scale, rules, calendar=False):
    """Per-path pathwise Theta, less the European one (control variate).
    calendar=False: maturity T stretched with the number of exercise dates fixed
    (all dates scale); True: today moved with the exercise dates fixed in calendar
    time, so only the first interval t_0 -> t_1 shrinks:
        dY/dt = e^{-r tau} [r phi - s 1{in the money} S_tau (mu + sigma W_{t_1} / (2 dt))]."""
    tau, S_tau, _, S_T = exercise_paths(spec, cfg, z, W, scale, rules, euro_bound=True)
    N, J = len(tau), spec.J
    j = np.rint(tau / spec.dt).astype(int)
    W_tau, W_T = W[np.arange(N), j - 1], W[:, J - 1]
    r, sig, s = z["r"], z["sigma"], spec.sign
    mu = r - z["d"] - 0.5 * sig ** 2

    if calendar:
        W_1 = W[:, 0]

        def dYdt(t, St):
            phi = spec.payoff(St)
            return np.exp(-r * t) * (r * phi - s * (phi > 0) * St * (mu + sig * W_1 / (2 * spec.dt)))
        return dYdt(tau, S_tau) - dYdt(np.full(N, spec.T), S_T)

    def dYdT(t, St, Wt):
        phi = spec.payoff(St)
        return (t / spec.T) * np.exp(-r * t) * (-r * phi + s * (phi > 0) * St * (mu + sig * Wt / (2 * t)))
    return -(dYdT(tau, S_tau, W_tau) - dYdT(np.full(N, spec.T), S_T, W_T))


def run_fits(spec, cfg, z, Y, y_theta, y_cal, eu, charm_eu, speed_eu):
    """PDE-identity and pathwise Theta and Charm (both variants) from one regression."""
    fit = m.taylor_fit(spec, cfg, z, np.column_stack([Y, y_theta, y_cal]), DIMS)
    g = m.greeks_from(replace(fit, coef=fit.coef[:, 0]), eu)
    k = fit.terms.index((3, (0,)))
    speed = fit.coef[k, 0] * factorial(3) / fit.h["S"] ** 3 + speed_eu
    S, r, d, sig = spec.S0, spec.r, spec.d, spec.sigma
    th_pde = theta_pde(spec, g["price"], g["delta"], g["gamma"])[0]
    ch_pde = d * g["delta"] - (r - d) * S * g["gamma"] - sig ** 2 * S * g["gamma"] - 0.5 * sig ** 2 * S ** 2 * speed
    p = m.greeks_from(replace(fit, coef=fit.coef[:, 1]))
    c = m.greeks_from(replace(fit, coef=fit.coef[:, 2]))
    return dict(price=g["price"], delta=g["delta"], gamma=g["gamma"], theta_pde=th_pde,
                charm_pde=ch_pde, theta_pw=p["price"] + eu["theta"], charm_pw=p["delta"] + charm_eu,
                theta_cal=c["price"] + eu["theta"], charm_cal=c["delta"] + charm_eu)


def one(job):
    part, i, spec, rep = job
    cfg = m.MultiConfig(exercise_rule="pilot")
    sc = m.run_config(cfg, DIMS)
    rng = np.random.default_rng(np.random.SeedSequence([4247, part == "grid", i, rep]))
    alphas, scale, rules = m.pilot(spec, sc, DIMS, rng)
    z = m.isd_multi(spec, sc, alphas, rng)
    W = m.brownian(spec, sc.N, rng)
    eu = bs_option(spec)
    charm_eu, speed_eu = european_charm_speed(spec)
    _, Y, _ = m.lsm_multi(spec, sc, z, W, scale, rules)
    _, Y_ins, fits_ins = m.lsm_multi(spec, sc, z, W, alphas, None)
    oos = run_fits(spec, sc, z, Y, theta_paths(spec, sc, z, W, scale, rules),
                   theta_paths(spec, sc, z, W, scale, rules, True), eu, charm_eu, speed_eu)
    ins = run_fits(spec, sc, z, Y_ins, theta_paths(spec, sc, z, W, alphas, fits_ins),
                   theta_paths(spec, sc, z, W, alphas, fits_ins, True), eu, charm_eu, speed_eu)
    avg = {k: 0.5 * (oos[k] + ins[k]) for k in oos}
    ex = theta_pde(spec, avg["price"], avg["delta"], avg["gamma"])[1]
    vals = {"pde": (avg["theta_pde"], avg["charm_pde"]), "pw_oos": (oos["theta_pw"], oos["charm_pw"]),
            "pw_ins": (ins["theta_pw"], ins["charm_pw"]), "pw_avg": (avg["theta_pw"], avg["charm_pw"]),
            "cal_oos": (oos["theta_cal"], oos["charm_cal"]), "cal_ins": (ins["theta_cal"], ins["charm_cal"]),
            "cal_avg": (avg["theta_cal"], avg["charm_cal"])}
    return [dict(part=part, option=i, rep=rep, method=k, ex_region=ex,
                 theta=0.0 if ex else v[0], charm=0.0 if ex else v[1]) for k, v in vals.items()]


def reference(job):
    part, i, spec = job
    sd = spec.sigma * np.sqrt(spec.T)
    if spec.no_early_exercise:
        return dict(part=part, option=i, sd=sd, ref_theta=bs_option(spec)["theta"],
                    ref_charm=european_charm_speed(spec)[0])
    grid = (FDGrid(n_x=8001, half_width=abs(np.log(spec.S0 / spec.K)) + 12 * sd + 0.02)
            if sd < 0.1 else None)
    f = put_fd_greeks(spec, "bermudan", grid, vera=False)
    if f["ex_region"]:
        return dict(part=part, option=i, sd=sd, ref_theta=0.0, ref_charm=0.0)
    return dict(part=part, option=i, sd=sd, ref_theta=f["theta"], ref_charm=f["charm"])


def summarise(df, ref, reps):
    df = df.merge(ref, on=["part", "option"])
    df = df[~df.ex_region]
    lines = ["# Pathwise Theta and Charm against the PDE identity", "",
             "Not part of the paper. `experiments/diagnostics/theta_pathwise_check.py`, "
             f"{reps} labels per option (the default label's (S, sigma) run, 300k main paths). "
             "pde = the label's Theta (PDE identity) and Charm from the identity with Speed; "
             "pw_* = pathwise, maturity stretched with the number of exercise dates fixed; "
             "cal_* = pathwise, exercise dates fixed in calendar time (only t_0 -> t_1 shrinks), "
             "as the reference; each with the out-of-sample rule, the in-sample rule and their "
             "average (the label averages them). Bias = mean over options of the signed relative error "
             "of the option's mean label (t); typical / median error = mean / median |relative "
             "error| of one label; options with |ref| < 1 % of the largest |ref| in the part, "
             "and the exercise region, left out.", ""]
    for part, d0 in df.groupby("part", sort=False):
        lines += [f"## {part}: {d0.option.nunique()} options", "",
                  "| Greek | method | bias % (t) | typical % | median % |", "|---|---|---|---|---|"]
        for g in ("theta", "charm"):
            big = d0[f"ref_{g}"].abs() >= 0.01 * d0[f"ref_{g}"].abs().max()
            for meth in METHODS:
                d = d0[big & (d0.method == meth)]
                e = 100 * (d[g] - d[f"ref_{g}"]) / d[f"ref_{g}"].abs()
                per = e.groupby(d.option).mean()
                b, se = per.mean(), per.std() / np.sqrt(len(per))
                lines.append(f"| {g} | {meth} | {b:+.2f} ({b / se:+.1f}) | {e.abs().mean():.1f} | "
                             f"{e.abs().median():.1f} |")
        lines += ["", "Per option (pde, pw_avg, cal_avg; bias % ± se, noise of one label %):", "",
                  "| option | sigma sqrt(T) | ref theta | theta pde | theta pw_avg | theta cal_avg "
                  "| ref charm | charm pde | charm pw_avg | charm cal_avg |",
                  "|---|---|---|---|---|---|---|---|---|---|"]
        for i, d in d0.groupby("option"):
            cells = []
            for g in ("theta", "charm"):
                rf = d[f"ref_{g}"].iloc[0]
                cells.append(f"{rf:+.4f}")
                for meth in ("pde", "pw_avg", "cal_avg"):
                    e = 100 * (d[d.method == meth][g] - rf) / abs(rf) if rf else d[d.method == meth][g] * np.nan
                    cells.append(f"{e.mean():+.1f} ± {e.std() / np.sqrt(len(e)):.1f} ({e.std():.1f})")
            lines.append(f"| {i} | {d.sd.iloc[0]:.3f} | " + " | ".join(cells) + " |")
        lines.append("")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    reps = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    specs = [("grid", i, spec_of(c)) for i, c in enumerate(american_grid())]
    specs += [("sample", i, s) for i, s in enumerate(sample(24))]
    jobs = [(p, i, s, k) for p, i, s in specs for k in range(reps)]
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with ProcessPoolExecutor(4) as ex:
        ref = pd.DataFrame(list(ex.map(reference, specs)))
        print(f"references done, {time.time() - t0:.0f} s", flush=True)
        rows = []
        for k, rs in enumerate(ex.map(one, jobs, chunksize=1)):
            rows += rs
            if (k + 1) % max(1, len(jobs) // 10) == 0:
                print(f"{k + 1}/{len(jobs)} labels, {time.time() - t0:.0f} s", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "raw.csv", index=False)
    ref.to_csv(OUT / "reference.csv", index=False)
    text = summarise(df, ref, reps)
    (OUT / "summary.md").write_text(text)
    print(text)
