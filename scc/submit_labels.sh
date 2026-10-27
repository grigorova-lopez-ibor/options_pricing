#!/bin/bash
# Submit a training set (experiments/generate_labels.py) as an SGE job array.
#   SCC_PROJECT=<project> OUT=<dir>/labels.csv bash scc/submit_labels.sh <n> <ntasks> [h_rt]
# Optional environment: SEED (default 1), SPY (exercise dates a year, default 504),
# EXACT_EVERY (reference values for ids divisible by it; 0 = none, default 10),
# VENV (default ~/venvs/simgreeks).
# When every task has finished (qstat -u $USER is empty), merge:
#   python experiments/generate_labels.py --n <n> --ntasks <ntasks> --merge --out $OUT
set -euo pipefail
N=$1; NTASKS=$2; HRT=${3:-12:00:00}
: "${SCC_PROJECT:?set SCC_PROJECT to your SCC project name}"
: "${OUT:?set OUT to the output CSV, e.g. /projectnb/<project>/$USER/labels/labels.csv}"
mkdir -p logs "$(dirname "$OUT")"
qsub -P "$SCC_PROJECT" -N labels -t 1-"$NTASKS" -l h_rt="$HRT" \
     -v N="$N",NTASKS="$NTASKS",OUT="$OUT",SEED="${SEED:-1}",SPY="${SPY:-504}",EXACT_EVERY="${EXACT_EVERY:-10}",VENV="${VENV:-$HOME/venvs/simgreeks}" \
     scc/labels.qsub
