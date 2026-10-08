"""Generic feasibility-audit runner.  Stage 1 (always): column dump, construct inventory, id/time/weight checks.
Stage 2 (only if a COMPLETE map is supplied): N, eligible N, AI-user N, weighted prevalence (+BRR SE if rho given),
missing-code tabulations, analytic N for AI x outcome.  No models are estimated.

python audit/src/run_audit.py --dataset htops --map audit/config/htops_map.yaml
python audit/src/run_audit.py --dataset shed  --file path/to/file.dta        (stage 1 only)
"""
import argparse, sys, re
from pathlib import Path
import numpy as np, pandas as pd, yaml
sys.path.insert(0, str(Path(__file__).parent))
from common import *

ap = argparse.ArgumentParser()
ap.add_argument("--dataset", required=True)
ap.add_argument("--file"); ap.add_argument("--map")
a = ap.parse_args()
ROOT = Path(__file__).resolve().parents[1]
cons = yaml.safe_load((ROOT / "config/constructs.yaml").read_text())
m = yaml.safe_load(Path(a.map).read_text()) if a.map else {}
path = a.file or m.get("data_file")
if not path: sys.exit("no data file given (--file or map.data_file)")
df, labels, vlabels = read_any(Path(path))
if m.get("repweight_file"):
    rw, _, _ = read_any(Path(m["repweight_file"]))
    keys = m["merge_keys"]; assert keys, "merge_keys required with repweight_file"
    n0 = len(df); df = df.merge(rw, on=keys, how="left", validate="1:1", indicator="_rw_merge")
    print("replicate merge:", df["_rw_merge"].value_counts().to_dict(), "rows", n0, "->", len(df))
ds = a.dataset
log = dict(dataset=ds, file=str(path), sha256=sha256(Path(path)), n_rows=len(df), n_cols=df.shape[1])

# ---------- Stage 1 ----------
pd.DataFrame(dict(variable=df.columns, label=[labels.get(c, "") for c in df.columns],
                  dtype=[str(t) for t in df.dtypes], n_nonmissing=df.notna().sum().values)
             ).to_csv(OUT / f"{ds}_columns.csv", index=False)
inv = inventory(df, labels, vlabels, cons, ds); inv.to_csv(OUT / f"{ds}_inventory.csv", index=False)
log["id_checks"] = id_checks(df, [c for c in m.get("id_cols", []) if c in df])
log["time_tabs"] = {c: tab(df[c]).to_dict()["n"] for c in m.get("time_cols", []) if c in df}
log["inventory_counts"] = inv.groupby("construct").size().to_dict() if len(inv) else {}

# ---------- Stage 2 ----------
need = [m.get(k) for k in ("weight",)] + [m.get("eligible", {}).get("var"), m.get("ai_user", {}).get("var")]
if not m or any(x is None for x in need):
    log["stage2"] = "SKIPPED: map incomplete (weight / eligible.var / ai_user.var)"
else:
    miss = m.get("missing_codes", [])
    D = df.copy()
    num = D.select_dtypes("number").columns
    D[num] = D[num].replace(miss, np.nan)               # recode special codes to NaN (raw tabs below use df, not D)
    w = D[m["weight"]]
    el = D[m["eligible"]["var"]].isin(m["eligible"]["codes"])
    ai = D[m["ai_user"]["var"]].isin(m["ai_user"]["codes"])
    ai_valid = D[m["ai_user"]["var"]].notna()
    log["raw_tab_eligible_var"] = tab(df[m["eligible"]["var"]]).to_dict()["n"]
    log["raw_tab_ai_var"] = tab(df[m["ai_user"]["var"]]).to_dict()["n"]
    # any-task AI use as alternative AI definition
    if m.get("ai_task_vars"):
        t = D[m["ai_task_vars"]].isin(m["ai_task_yes_codes"])
        anyt = t.any(axis=1); allmiss = D[m["ai_task_vars"]].isna().all(axis=1)
        log["ai_any_task_N_among_eligible"] = int((anyt & el).sum())
        log["ai_task_all_missing_among_eligible"] = int((allmiss & el).sum())
        log["ai_task_item_yes_N"] = {v: int((D[v].isin(m["ai_task_yes_codes"]) & el).sum()) for v in m["ai_task_vars"]}
    log.update(N_total=len(D), N_eligible=int(el.sum()), N_eligible_ai_valid=int((el & ai_valid).sum()),
               N_ai_user=int((el & ai).sum()), N_ai_nonuser=int((el & ai_valid & ~ai).sum()),
               prevalence_unweighted=float((el & ai).sum() / (el & ai_valid).sum()),
               prevalence_weighted=wshare(ai, el & ai_valid, w),
               weight_missing_among_eligible=int(w[el].isna().sum()), weight_zero_among_eligible=int((w[el] == 0).sum()))
    reps = [c for c in D.columns if m.get("rep_prefix") and re.fullmatch(m["rep_prefix"], str(c))]
    log["n_rep_weights_found"] = len(reps)
    if reps and m.get("fay_rho") is not None:
        sub = D[el & ai_valid].copy(); sub["_ai"] = ai[el & ai_valid].astype(float)
        stat = lambda d, wc: float((d["_ai"] * d[wc]).sum() / d[wc].sum())
        log["prevalence_weighted_BRR_se"] = brr_se(sub, stat, m["weight"], reps, m["fay_rho"])
    elif reps: log["prevalence_weighted_BRR_se"] = "NOT COMPUTED: fay_rho not set (take from official variance doc)"
    rows = []
    for name, o in m.get("outcomes", {}).items():
        v = o["var"]; ov = D[v].notna()
        uni = el if o.get("universe", "all_eligible") == "all_eligible" else (el & ai)
        rows.append(dict(outcome=name, var=v, universe=o.get("universe", "all_eligible"),
                         N_universe=int(uni.sum()), N_valid=int((uni & ov).sum()),
                         N_valid_ai_user=int((uni & ov & ai).sum()), N_valid_ai_nonuser=int((uni & ov & ai_valid & ~ai).sum()),
                         raw_tab=str(tab(df.loc[uni.values, v]).to_dict()["n"])))
    pd.DataFrame(rows).to_csv(OUT / f"{ds}_analytic_n.csv", index=False)
dump(f"{ds}_audit_log.json", log)
print(pd.Series({k: v for k, v in log.items() if not isinstance(v, dict)}).to_string())
