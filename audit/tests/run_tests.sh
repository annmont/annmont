#!/usr/bin/env bash
# Pipeline logic test on SYNTHETIC data (not real). Run from repo root: bash audit/tests/run_tests.sh
set -euo pipefail
python3 -I audit/tests/make_synthetic.py
python3 -I audit/src/run_audit.py --dataset synthetic --map audit/tests/fixtures/synthetic_map.yaml >/dev/null
python3 -I - <<'PY'
import json; l=json.load(open("audit/outputs/synthetic_audit_log.json"))
assert l["N_total"]==2000 and l["n_rep_weights_found"]==80 and 0<l["prevalence_weighted"]<1, l
print("pipeline test OK")
PY
rm -f audit/outputs/synthetic_*
