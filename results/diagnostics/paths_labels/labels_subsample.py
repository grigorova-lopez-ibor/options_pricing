"""Error of the mean of n labels against the American PDE, by subsampling the
100 labels per option of results/two_per_day (default label, 504 dates a year):
total = RMS error of the mean of n labels; noise = sd / sqrt(n); bias = the
option's noise-corrected |bias|. Medians over the options (relative to |PDE|)."""
import sys
sys.path.insert(0, ".")
import numpy as np, pandas as pd
import experiments.two_per_day_report as T
G = ["price", "delta", "gamma", "theta", "vega", "volga", "vanna", "rho", "phi"]
NS = [1, 2, 5, 10, 25, 50, 100]
rng = np.random.default_rng(0)
frames = []
for s in ("check", "random"):
    lab = pd.read_parquet(f"results/two_per_day/raw/{s}_labels.parquet")
    ref = pd.read_parquet(f"results/two_per_day/raw/{s}_reference.parquet")
    frames.append((lab, T.ref_frame(ref, "")))
print("| Greek | " + " | ".join(f"n={n}: total / noise / bias" for n in NS) + " |")
print("|---|" + "---|" * len(NS))
for q in G:
    tot, noi, bia = {n: [] for n in NS}, {n: [] for n in NS}, []
    for lab, R in frames:
        mx = R[q].abs().max()
        for i, g in lab.groupby("id"):
            x, r = g[q].dropna().values, R.loc[i, q]
            if len(x) < 100 or abs(r) < 0.01 * mx or x.std() <= 1e-9 * max(1, abs(r)):
                continue
            sd, b = x.std(ddof=1), x.mean() - r
            bia.append(np.sqrt(max(0.0, b * b - sd * sd / len(x))) / abs(r))
            for n in NS:
                e = (np.array([x.mean() - r]) if n == len(x)
                     else np.array([rng.choice(x, n, replace=False).mean() - r for _ in range(200)]))
                tot[n].append(np.sqrt((e ** 2).mean()) / abs(r))
                noi[n].append(sd / np.sqrt(n) / abs(r))
    print(f"| {q} | " + " | ".join(f"{100 * np.median(tot[n]):.3g} / {100 * np.median(noi[n]):.3g} / "
                                   f"{100 * np.median(bia):.3g}" for n in NS) + " |")
