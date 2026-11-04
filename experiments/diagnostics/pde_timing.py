"""Time of the PDE reference values (the "ground truth" the labels are compared
with) against one label. Not part of the paper. One core.

    python experiments/diagnostics/pde_timing.py   # writes results/diagnostics/pde_timing/summary.md

* generator reference: experiments/generate_labels.exact, the Bermudan PDE on
  the label's exercise dates with central bumps (what --exact adds to a label);
* American reference: reference.label_reference(style="american"), exercise at
  every PDE step, Richardson over 20 and 40 steps per date, plus forward bumps
  (what the SCC checks compare with).
"""
import os
import sys
import time
from pathlib import Path

for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(v, "1")
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "experiments")]

from generate_labels import exact  # noqa: E402
from simgreeks.core import PutSpec  # noqa: E402
from simgreeks.reference import label_reference  # noqa: E402


def clock(fn):
    t = time.time(); fn(); return time.time() - t


rows = []
for T in (0.5, 1.0, 2.0):
    for spy in (50, 252, 504):
        s = PutSpec(S0=40, K=40, sigma=0.2, r=0.03, d=0.01, T=T, steps_per_year=spy)
        g = clock(lambda: exact(s))
        a = clock(lambda: label_reference(s, style="american", vera=False)) if spy == 504 else float("nan")
        rows.append((T, spy, g, a))
        print(T, spy, round(g, 1), round(a, 1), flush=True)
low = PutSpec(S0=40, K=40, sigma=0.01, r=0.03, d=0.01, T=1 / 6, steps_per_year=504)
g_low = clock(lambda: exact(low))
lines = ["# Time of the PDE reference values", "",
         "Not part of the paper. `experiments/diagnostics/pde_timing.py`, one core, K = S0 = 40, σ = 20 %, "
         "r = 3 %, d = 1 %. Generator = `generate_labels.exact` (Bermudan on the label's dates, central "
         "bumps: what `--exact` adds); American = `label_reference(style=\"american\")` (what the SCC checks "
         "use). For comparison, one in-sample label at 504 dates a year takes about 50 s at T = 1 "
         "(results/diagnostics/insample_studies).", "",
         "| T | dates a year | generator reference (s) | American reference (s) |", "|---|---|---|---|"]
lines += [f"| {T} | {spy} | {g:.1f} | {'' if a != a else f'{a:.1f}'} |" for T, spy, g, a in rows]
lines += ["", f"σ = 1 %, T = 2 months (refined grid, 8001 nodes): {g_low:.1f} s.", ""]
out = ROOT / "results" / "diagnostics" / "pde_timing"
out.mkdir(parents=True, exist_ok=True)
(out / "summary.md").write_text("\n".join(lines))
print("\n".join(lines))
