"""252 against 504 exercise dates a year: how close the Bermudan put is to the
American one, and what the label costs. Not part of the paper.

    python experiments/diagnostics/exercise_frequency_check.py   (~30 min on 4 cores)

Options: the 75 of results/two_per_day (35 check options, 40 from the input
ranges), whose American and 504/yr Bermudan references are in
results/two_per_day/raw/*_reference.parquet. For each option this computes the
252/yr Bermudan reference (reference.label_reference, as for 504/yr) and, at
both frequencies, the Theta and Charm the labels compute: pathwise with the
number of exercise dates J = round(spy T) fixed while T moves,
    theta_J = -(P(T + h) - P(T - h)) / 2h,  charm_J = -(Delta(T + h) - Delta(T - h)) / 2h,
with the dates at spacing (T +- h) / J (reference.put_fd).

Gap = Bermudan - American, % of |American|, over the options with |American| >= 1 %
of the largest in the set and outside the exercise region. It is compared with
the noise of one label and of the mean of 100 labels (median sd over the options,
results/two_per_day/raw/*_labels.parquet, 504/yr): a gap well below the noise of
the mean of 100 labels is invisible in any label set we would make.
Time per label: MultiConfig(vf_time=0.02) at T = 0.5, 1, 2 (S0 = K = 40, sigma =
20 %, r = 4 %, d = 1 %), 2 labels each, 4 processes at once on this machine.
Writes results/diagnostics/exercise_frequency/summary.md and raw.csv.
"""
import os
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[v] = "1"
import sys  # noqa: E402
import time  # noqa: E402
from concurrent.futures import ProcessPoolExecutor  # noqa: E402
from dataclasses import replace  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from simgreeks.core import PutSpec  # noqa: E402
from simgreeks.multi import MultiConfig, label  # noqa: E402
from simgreeks.reference import label_reference, put_fd  # noqa: E402

RAW = ROOT / "results" / "two_per_day" / "raw"
OUT = ROOT / "results" / "diagnostics" / "exercise_frequency"
G = ["price", "delta", "gamma", "theta", "charm", "vega", "rho", "phi"]
SPYS = (252, 504)


def spec_of(row, spy):
    return PutSpec(S0=row["S0"], K=row["K"], sigma=row["sigma"], r=row["r"], d=row["d"],
                   T=row["T"], steps_per_year=spy)


def theta_charm_jfixed(spec):
    """Theta and Charm with the number of exercise dates fixed (the labels' definition)."""
    J, h = spec.J, 1e-3 * spec.T
    up = put_fd(replace(spec, T=spec.T + h, steps_per_year=J / (spec.T + h)))
    dn = put_fd(replace(spec, T=spec.T - h, steps_per_year=J / (spec.T - h)))
    return -(up["price"] - dn["price"]) / (2 * h), -(up["delta"] - dn["delta"]) / (2 * h)


def one_option(job):
    part, row = job
    out = dict(part=part, id=int(row["id"]))
    t0 = time.time()
    b = label_reference(spec_of(row, 252), style="bermudan", vera=False)
    out.update({f"b252_{g}": b[g] for g in G})
    out["b252_ex_region"] = bool(b["ex_region"])
    for spy in SPYS:
        th, ch = theta_charm_jfixed(spec_of(row, spy))
        out[f"j{spy}_theta"], out[f"j{spy}_charm"] = th, ch
    out["seconds"] = time.time() - t0
    return out


def one_timing(job):
    spy, T, k = job
    spec = PutSpec(S0=40, K=40, sigma=0.2, r=0.04, d=0.01, T=T, steps_per_year=spy)
    t0 = time.time()
    label(spec, MultiConfig(vf_time=0.02, exercise_rule="pilot"), k)
    return dict(spy=spy, T=T, seconds=time.time() - t0)


def gaps(df, col_of, noise, part):
    """Rows of |gap| statistics per Greek for one part."""
    rows = []
    d = df[(df.part == part) & ~df.ex_region]
    for g in G:
        am = d[g]
        big = am.abs() >= 0.01 * df[df.part == part][g].abs().max()
        rows.append((g, {name: (100 * (d[c] - am)[big] / am[big].abs()).abs() for name, c in col_of(g)},
                     noise.get((part, g), np.nan)))
    return rows


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    refs = []
    for part in ("check", "random"):
        r = pd.read_parquet(RAW / f"{part}_reference.parquet")
        r["part"] = part
        refs.append(r)
    ref = pd.concat(refs, ignore_index=True)
    noise = {}
    for part in ("check", "random"):
        L = pd.read_parquet(RAW / f"{part}_labels.parquet")
        R = ref[ref.part == part].set_index("id")
        for g in G:
            sd = L.groupby("id")[g].std()
            rel = 100 * sd / R[g].abs().reindex(sd.index)
            big = R[g].abs().reindex(sd.index) >= 0.01 * R[g].abs().max()
            noise[(part, g)] = float(rel[big & ~R.ex_region.reindex(sd.index).astype(bool)].median())
    jobs = [(row["part"], row) for _, row in ref.iterrows()]
    t0 = time.time()
    with ProcessPoolExecutor(4) as ex:
        res = pd.DataFrame(list(ex.map(one_option, jobs, chunksize=1)))
        print(f"references done, {time.time() - t0:.0f} s", flush=True)
        timing = pd.DataFrame(list(ex.map(one_timing, [(spy, T, k) for spy in SPYS
                                                      for T in (0.5, 1.0, 2.0) for k in range(2)])))
    df = ref.merge(res, on=["part", "id"])
    df.to_csv(OUT / "raw.csv", index=False)
    timing.to_csv(OUT / "timing.csv", index=False)

    lines = ["# 252 against 504 exercise dates a year", "",
             "Not part of the paper. `experiments/diagnostics/exercise_frequency_check.py`. "
             "Gap to the American put, % of |American| (options with |American| >= 1 % of the "
             "largest in the set, outside the exercise region): median / 95th percentile / max. "
             "Bermudan = the PDE with exercise on the labels' dates; J-fixed Theta and Charm = "
             "what the pathwise labels compute (number of dates fixed while T moves). Noise = "
             "median noise of one label at 504/yr (`results/two_per_day`); a gap below the noise "
             "of the mean of 100 labels (noise / 10) cannot be seen in any label set.", ""]

    def fmt(x):
        return f"{x.median():.3f} / {x.quantile(0.95):.3f} / {x.max():.3f}"

    for part, title in (("check", "35 check options"), ("random", "40 options from the input ranges")):
        lines += [f"## {title}", "",
                  "| Greek | Bermudan 252/yr | Bermudan 504/yr | noise of one label | noise of the mean of 100 |",
                  "|---|---|---|---|---|"]
        for g, gs, nz in gaps(df, lambda g: [("252", f"b252_{g}"), ("504", f"berm_{g}")], noise, part):
            lines.append(f"| {g} | {fmt(gs['252'])} | {fmt(gs['504'])} | {nz:.2f} | {nz / 10:.3f} |")
        lines += ["", "Theta and Charm as the labels compute them (number of dates fixed):", "",
                  "| Greek | J-fixed 252/yr | J-fixed 504/yr | noise of one label | noise of the mean of 100 |",
                  "|---|---|---|---|---|"]
        for g in ("theta", "charm"):
            d = df[(df.part == part) & ~df.ex_region]
            big = d[g].abs() >= 0.01 * df[df.part == part][g].abs().max()
            cells = [fmt((100 * (d[f"j{spy}_{g}"] - d[g])[big] / d[g][big].abs()).abs()) for spy in SPYS]
            nz = noise[(part, g)]
            lines.append(f"| {g} | {cells[0]} | {cells[1]} | {nz:.2f} | {nz / 10:.3f} |")
        ex_diff = int((df[df.part == part].b252_ex_region != df[df.part == part].ex_region).sum())
        lines += ["", f"Exercise region at 252/yr different from the American one: {ex_diff} options.", ""]
    t = timing.groupby(["T", "spy"]).seconds.mean().unstack()
    lines += ["## Time per label (MultiConfig(vf_time=0.02), 4 processes at once on this machine)", "",
              "| T | 252/yr (s) | 504/yr (s) | ratio |", "|---|---|---|---|"]
    for T, row in t.iterrows():
        lines.append(f"| {T:g} | {row[252]:.0f} | {row[504]:.0f} | {row[504] / row[252]:.2f} |")
    text = "\n".join(lines) + "\n"
    (OUT / "summary.md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
