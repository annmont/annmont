"""HTOPS Mar-2026 extra checks: reproduce Census-published AI-at-work figures with SDR standard errors (Var = 4/80 * sum),
test sensitivity of prevalence to the treatment of item non-response, and report AI x occupation cell sizes. Descriptive only.
python audit/src/htops_checks.py"""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).parent))
from common import dump
R = Path(__file__).resolve().parents[1]
P = pd.read_csv(R/"data/x/htops/HTOPS_HPS_2603_PUF.csv"); W = pd.read_csv(R/"data/x/htops/HTOPS_HPS_2603_REPWGT_PUF.csv")
D = P.merge(W, on="SCRAMID", validate="1:1").copy()
reps = [f"PWEIGHT{i}" for i in range(1, 81)]
TASKS = ["AIWRK_ADMIN","AIWRK_CODE","AIWRK_CUSTSUPP","AIWRK_DATAVIS","AIWRK_GENIDEA","AIWRK_INTERP","AIWRK_LOG","AIWRK_MED","AIWRK_SEARCH","AIWRK_TUTOR","AIWRK_COMM"]
def est(num, den):
    """weighted share num/den (boolean Series) with SDR SE"""
    f = lambda w: float(w[num & den].sum() / w[den].sum())
    th = f(D.PWEIGHT); se = float(np.sqrt(4/80 * sum((f(D[r]) - th) ** 2 for r in reps)))
    return dict(est=round(th*100, 2), se=round(se*100, 2), n_den=int(den.sum()), n_num=int((num & den).sum()))
wk = D.ANYWORK == 1
T = D[TASKS].where(D[TASKS] > 0)                       # -99/-88 -> NaN
yes = (T == 1).any(axis=1); allno = (T == 2).all(axis=1); anymiss = T.isna().any(axis=1)
out = {}
out["prev_any_AI_valid_denominator(main)"] = est(yes, wk & (yes | allno))
out["prev_ambiguous_as_nonuser(lower bound)"] = est(yes, wk & (yes | anymiss.eq(False) | anymiss))   # all workers incl. all-missing
out["prev_ambiguous_dropped_but_allmiss_as_nonuser"] = est(yes, wk)
out["prev_last_week_use(FREQ 1,2) / workers"] = est(D.AIWRK_FREQ.isin([1, 2]), wk)
out["prev_last_week_use / valid denominator"] = est(D.AIWRK_FREQ.isin([1, 2]), wk & (yes | allno))
base = wk & (yes | allno)
for t in TASKS: out["task_"+t] = est(D[t] == 1, base)
u = wk & yes & D.AIWRK_FREQ.isin([1, 2, 3])
for k, lab in {1:"every day",2:"some days",3:"used, not last week"}.items(): out[f"freq_{lab}(among users)"] = est(D.AIWRK_FREQ == k, u)
h = wk & D.AIWRK_FREQ.isin([1, 2]) & D.AIWRK_HOURS.isin(range(1, 9))
for k, lab in {1:"<1h",2:"1h",3:"2h",4:"3h",5:"4h",6:">4h",7:"no saving",8:"required more time"}.items(): out[f"hours_{lab}(among last-week users)"] = est(D.AIWRK_HOURS == k, h)
out["hours_1-2h"] = est(D.AIWRK_HOURS.isin([2, 3]), h)
out["AIWRK_HOURS_nonresponse_among_lastweek_users"] = dict(asked=int((wk & D.AIWRK_FREQ.isin([1,2])).sum()), valid=int(h.sum()), dk=int((wk & D.AIWRK_FREQ.isin([1,2]) & (D.AIWRK_HOURS == -99)).sum()))
occ = pd.crosstab(D.loc[wk & D.AI_OCC.gt(0), "AI_OCC"], np.where(yes[wk & D.AI_OCC.gt(0)], "user", np.where(allno[wk & D.AI_OCC.gt(0)], "nonuser", "ambig/missing")))
out["occupation_x_AI_counts"] = occ.to_dict()
out["age_min_max"] = [int(D.TAGE.min()), int(D.TAGE.max())]
out["weights_sum_PWEIGHT"] = float(D.PWEIGHT.sum())
out["n_workers_ANYWORK1"] = int(wk.sum()); out["n_workers_selfemployed_or_family(CLASS_WORKER 4,5)"] = int((wk & D.CLASS_WORKER.isin([4, 5])).sum())
dump("htops_extra_checks.json", out)
for k, v in out.items():
    if k != "occupation_x_AI_counts": print(k, v)
print(occ.to_string())
