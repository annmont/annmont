# Dataset feasibility audit: HTOPS Mar-2026, SHED 2025, EWCS 2024

**Status (2026-10-08):** HTOPS Mar-2026 and SHED 2025 microdata + official documentation were downloaded and audited
(see `AUDIT_REPORT.md`, `outputs/`). EWCS 2024 microdata are NOT included: they need a UK Data Service login (SN 9511) and
eurofound.europa.eu blocks scripted access, so EWCS is documentation-only. Raw data live in `data/` (git-ignored).

## Run order (on a machine with open egress)
```
pip install pandas numpy pyyaml requests pyreadstat openpyxl
python audit/src/00_fetch.py htops shed ewcs          # edit config/sources.yaml with true file names first
# EWCS microdata: register at UK Data Service, download manually into audit/data/raw/ewcs/
python audit/src/run_audit.py --dataset htops --file <puf.csv>            # stage 1: columns + construct inventory
#   read outputs/htops_inventory.csv against the official data dictionary, then fill config/htops_map.yaml
python audit/src/run_audit.py --dataset htops --map audit/config/htops_map.yaml   # stage 2: N, prevalence, analytic N
python audit/src/htops_checks.py     # reproduces Census-published figures with SDR SEs
python audit/src/shed_checks.py      # reproduces Fed D52 shares; tests 2024-2025 shedid linkage
bash audit/tests/run_tests.sh                          # logic test on synthetic data only
```
Same for `shed` (use `config/shed_map.yaml`, `.dta` file) and `ewcs` (fill `config/ewcs_map.template.yaml`). Stage 2 refuses to run unless weight / eligibility / AI variables are explicitly mapped:
the scripts never infer what a variable means. Missing codes, Fay rho and the number of replicates come from the
official documentation and are inputs, not defaults. No models are estimated anywhere.

Hosts needed: www.census.gov, www2.census.gov, www.federalreserve.gov, eurofound.europa.eu,
ukdataservice.ac.uk (+ doc./beta. subdomains).
