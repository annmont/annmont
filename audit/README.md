# Dataset feasibility audit: HTOPS Mar-2026, SHED 2025, EWCS 2024

**Status (2026-10-08): documentation-level audit only. No microdata file was opened.**
The cloud sandbox that produced this repo denies egress to census.gov, www2.census.gov, federalreserve.gov and
eurofound.europa.eu (HTTP 403 on CONNECT, organization policy), so no file could be downloaded. Every N cell in
`AUDIT_REPORT.md` is therefore "NOT COMPUTED". The code here is the reproducible procedure that fills those cells.

## Run order (on a machine with open egress)
```
pip install pandas numpy pyyaml requests pyreadstat openpyxl
python audit/src/00_fetch.py htops shed ewcs          # edit config/sources.yaml with true file names first
# EWCS microdata: register at UK Data Service, download manually into audit/data/raw/ewcs/
python audit/src/run_audit.py --dataset htops --file <puf.csv>            # stage 1: columns + construct inventory
#   read outputs/htops_inventory.csv against the official data dictionary, then fill config/htops_map.yaml
python audit/src/run_audit.py --dataset htops --map audit/config/htops_map.yaml   # stage 2: N, prevalence, analytic N
bash audit/tests/run_tests.sh                          # logic test on synthetic data only
```
Same for `shed` and `ewcs`. Stage 2 refuses to run unless weight / eligibility / AI variables are explicitly mapped:
the scripts never infer what a variable means. Missing codes, Fay rho and the number of replicates come from the
official documentation and are inputs, not defaults. No models are estimated anywhere.

Hosts needed: www.census.gov, www2.census.gov, www.federalreserve.gov, eurofound.europa.eu,
ukdataservice.ac.uk (+ doc./beta. subdomains).
