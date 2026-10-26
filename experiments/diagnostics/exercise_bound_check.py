"""The European bound on the label's own exercise decisions
(MultiConfig(exercise_bound=True)) against the default, paired. Not part of the
paper.

    python experiments/diagnostics/exercise_bound_check.py [n_options]   (400: ~25 min on 4 cores)

(Run before exercise_bound became the default; the stored labels were made with
exercise_bound=False.)

The 1000-label check (results/labels_1000_new) found the price -0.03 % (t -6)
and Delta +0.09 % (t +3) off, mostly where r < d: there early exercise is worth
(almost) nothing, but the fitted rule exercises some paths below the European
value, which the American continuation value never is. The pathwise Greeks
already ignore those exercises (pathwise_bound); exercise_bound applies the
same to the price's exercise decisions (pilot, main and in-sample).

The first n options of results/labels_1000_new/labels.csv are relabelled with
exercise_bound=True and the same seeds as the stored labels (paired: the stored
labels are reproduced exactly with the default config). Reference: the stored
exact_<greek>. Writes results/diagnostics/exercise_bound/summary.md and raw.csv.
"""
import os
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[v] = "1"
import sys  # noqa: E402
import time  # noqa: E402
from concurrent.futures import ProcessPoolExecutor  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "experiments")]
from generate_labels import spec_of  # noqa: E402
from simgreeks.multi import MultiConfig, label  # noqa: E402
from simgreeks.runner import job_seed  # noqa: E402

LABELS = ROOT / "results" / "labels_1000_new" / "labels.csv"
OUT = ROOT / "results" / "diagnostics" / "exercise_bound"
G = ["price", "delta", "gamma", "theta", "charm", "vega", "volga", "vanna", "rho", "phi",
     "delta_r", "delta_d"]
SEED = 3                                  # the 1000-label run's --seed


def one(row):
    t0 = time.time()
    lab = label(spec_of(row), MultiConfig(exercise_bound=True), job_seed(SEED, {"id": int(row["id"])}, 0))
    return dict(id=int(row["id"]), seconds=time.time() - t0, new_ex_region=bool(lab["ex_region"]),
                **{f"new_{g}": lab[g] for g in G})


def summarise(df):
    ref_ex = np.isclose(df.exact_price, df.K - df.S0, rtol=1e-5, atol=1e-6) & (df.exact_delta == -1.0)
    keep = ~(df.ex_region | df.new_ex_region | ref_ex)
    d0 = df[keep]
    lines = ["# European bound on the label's exercise decisions (paired)", "",
             f"Not part of the paper. `experiments/diagnostics/exercise_bound_check.py`: {len(df)} options "
             "of the 1000-label check relabelled with MultiConfig(exercise_bound=True), same seeds. "
             f"{int((~keep).sum())} options in the exercise region (either label or reference) left out. "
             "Errors in % of |reference|; options with |reference| < 1 % of the largest left out per "
             "Greek. paired = mean of (new - default) / |reference| ± se: the effect of the bound "
             "itself, without the labels' noise. † = |t| > 2.576.", ""]
    for name, mask in (("all", d0.r >= -1), ("r < d", d0.r < d0.d), ("r >= d", d0.r >= d0.d)):
        d = d0[mask]
        lines += [f"## {name}: {len(d)} options", "",
                  "| Greek | bias default (t) | bias with bound (t) | paired change ± se (t) | typical default | typical with bound |",
                  "|---|---|---|---|---|---|"]
        for g in G:
            ref = d[f"exact_{g}"]
            big = ref.abs() >= 0.01 * d0[f"exact_{g}"].abs().max()
            if big.sum() < 5:
                continue
            a = 100 * (d[g] - ref)[big] / ref[big].abs()
            b = 100 * (d[f"new_{g}"] - ref)[big] / ref[big].abs()
            p = b - a
            cells = []
            for e in (a, b, p):
                m, se = e.mean(), e.std() / np.sqrt(len(e))
                t = m / se if se > 0 else 0.0
                cells.append(f"{m:+.3f} ± {se:.3f} ({t:+.1f}){'†' if abs(t) > 2.576 else ''}")
            lines.append(f"| {g} | {cells[0]} | {cells[1]} | {cells[2]} | {a.abs().mean():.2f} | "
                         f"{b.abs().mean():.2f} |")
        lines.append("")
    lines.append(f"Mean seconds per label with the bound (one core, 4 processes at once): "
                 f"{df.seconds.mean():.1f}.")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    base = pd.read_csv(LABELS).sort_values("id").head(n)
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    rows = []
    with ProcessPoolExecutor(4) as ex:
        for k, r in enumerate(ex.map(one, base.to_dict("records"), chunksize=1)):
            rows.append(r)
            if (k + 1) % max(1, n // 10) == 0:
                print(f"{k + 1}/{n} labels, {time.time() - t0:.0f} s", flush=True)
    df = base.merge(pd.DataFrame(rows), on="id")
    df.to_csv(OUT / "raw.csv", index=False)
    text = summarise(df)
    (OUT / "summary.md").write_text(text)
    print(text)
