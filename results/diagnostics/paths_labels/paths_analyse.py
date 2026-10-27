import sys
sys.path.insert(0, "/home/user/options_pricing")
import numpy as np, pandas as pd
import experiments.two_per_day_report as T
d = pd.read_csv(sys.argv[1])
ref = pd.read_parquet("/home/user/options_pricing/results/two_per_day/raw/check_reference.parquet")
G = ["price", "delta", "gamma", "theta", "vega", "volga", "vanna", "rho", "phi"]
T.GREEKS = G
R = T.ref_frame(ref, "")
Ns = sorted(d.N_main.unique())
print(f"{d.groupby('N_main').size().to_dict()} labels; options {sorted(d.id.unique())}")
print("time per label (s):", d.groupby("N_main").seconds.mean().round(1).to_dict())
for mode, col in (("default", lambda q: q), ("in-sample", lambda q: q + "_ins"), ("out-of-sample", lambda q: q + "_oos")):
    print(f"\n{mode}: cells = noise of one label % (median over options) / |bias| % noise-corrected (median) / signed bias % (mean, ± se)")
    print("| Greek | " + " | ".join(f"{n//1000}k main" for n in Ns) + " | noise exponent |")
    print("|---|" + "---|" * (len(Ns) + 1))
    for q in G:
        cells, noise = [], []
        for n in Ns:
            po = T.per_option(d[d.N_main == n], R, col)
            x = po[(po.greek == q) & po.rel_bias.notna()]
            corr = np.sqrt(np.maximum(0, x.rel_bias ** 2 - x.rel_se ** 2))
            sb, sse = x.rel_bias.mean(), np.sqrt((x.rel_se ** 2).sum()) / len(x)
            noise.append(x.rel_noise.median())
            cells.append(f"{100 * x.rel_noise.median():.3g} / {100 * corr.median():.3g} / {100 * sb:+.3g} ± {100 * sse:.2g}")
        k = np.polyfit(np.log(Ns), np.log(noise), 1)[0]
        print(f"| {q} | " + " | ".join(cells) + f" | {k:+.2f} |")
