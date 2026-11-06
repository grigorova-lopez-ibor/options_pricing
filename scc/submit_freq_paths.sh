#!/bin/bash
# Submit one part of the exercise-dates x main-paths grid as an SGE job array.
#   OUT=<dir> bash scc/submit_freq_paths.sh <ref|small|big> <ntasks> [h_rt]
# SCC_PROJECT=<project> is optional: without it the job goes to your default project.
# ref: PDE references (15 options); small: labels below 3.3 GB (1 core, 4 GB);
# big: labels up to ~11 GB (1008 dates a year with 600k paths, ...): 4 slots x 4 GB.
set -euo pipefail
PART=$1; NTASKS=$2; HRT=${3:-04:00:00}
: "${OUT:?set OUT to the output directory, e.g. ~/experiments/freq_paths_out}"
mkdir -p logs "$OUT"
case "$PART" in
  ref)   CMD=ref; SIZE=small; PE=1 ;;
  small) CMD=run; SIZE=small; PE=1 ;;
  big)   CMD=run; SIZE=big;   PE=4 ;;
  *) echo "part must be ref, small or big"; exit 1 ;;
esac
PROJ=(); [ -n "${SCC_PROJECT:-}" ] && PROJ=(-P "$SCC_PROJECT")
qsub "${PROJ[@]}" -N "fp_$PART" -t 1-"$NTASKS" -l h_rt="$HRT" -pe omp "$PE" -l mem_per_core=4G \
     -v CMD="$CMD",SIZE="$SIZE",NTASKS="$NTASKS",OUT="$OUT",VENV="${VENV:-$HOME/venvs/simgreeks}" \
     scc/freq_paths.qsub
