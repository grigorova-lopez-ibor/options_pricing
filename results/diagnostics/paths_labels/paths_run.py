"""Noise and bias of the default label (2 dates/day, vf at 1/50 year) against main
paths: N_main = 3 N in {75k, 150k, 300k, 600k}, pilot 100k fixed; 5 check options,
REPS labels each, seeds job_seed(9100, {id}, rep) (the same for every N)."""
import os, sys, time
for v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"): os.environ[v] = "1"
sys.path.insert(0, "/home/user/options_pricing")
from concurrent.futures import ProcessPoolExecutor
import pandas as pd
from simgreeks.multi import MultiConfig, label
from simgreeks.runner import job_seed
from experiments.tournament import options, spec_of
IDS = [3, 4, 5, 7, 13]
NS = [25_000, 50_000, 100_000, 200_000]
Q = ["price", "delta", "gamma", "theta", "charm", "vega", "volga", "vanna", "rho", "phi", "delta_r", "delta_d"]
def one(job):
    i, N, rep = job
    o = options("tpd_check"); row = o[o.id == i].iloc[0]
    cfg = MultiConfig(vf_time=0.02, N=N, N_pilot=100_000)
    t = time.time(); l = label(spec_of(row), cfg, job_seed(9100, {"id": i}, rep))
    out = dict(id=i, N_main=3 * N, rep=rep, seconds=time.time() - t)
    for q in Q:
        out[q] = l[q]
        for m in ("oos", "ins", "avg"):
            out[f"{q}_{m}"] = l.get(f"{q}_{m}", l[q])
    return out
if __name__ == "__main__":
    reps, out = int(sys.argv[1]), sys.argv[2]
    rows = pd.read_csv(out).to_dict("records") if os.path.exists(out) else []
    done = {(int(x["id"]), int(x["N_main"]) // 3, int(x["rep"])) for x in rows}
    jobs = [(i, N, r) for r in range(reps) for N in NS[::-1] for i in IDS if (i, N, r) not in done]
    print(len(done), "done,", len(jobs), "to do", flush=True)
    with ProcessPoolExecutor(4) as ex:
        for k, res in enumerate(ex.map(one, jobs, chunksize=1)):
            rows.append(res)
            if k % 20 == 19:
                pd.DataFrame(rows).to_csv(out, index=False); print(k + 1, "of", len(jobs), flush=True)
    pd.DataFrame(rows).to_csv(out, index=False); print("done", len(rows), flush=True)
