#!/bin/bash
# Runs the in-sample studies one after another (resumable: rerun to continue).
cd "$(dirname "$0")/../../.."
for s in paths alpha dates crn; do
  echo "=== $s $(date -u +%FT%TZ)"
  python experiments/diagnostics/insample_studies.py $s || echo "FAILED $s"
done
echo "=== all done $(date -u +%FT%TZ)"
