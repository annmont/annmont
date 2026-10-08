"""SHED 2025 extra checks: (1) reproduce published D52 shares, (2) shedid overlap with the 2024 public file (is wave linkage possible?),
(3) D50 x D52 cross-tab, (4) universe of autonomy items. Descriptive only.
python audit/src/shed_checks.py"""
import sys, glob, json
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).parent))
from common import dump
R = Path(__file__).resolve().parents[1]
d25 = pd.read_stata(R/"data/x/shed_dta/public2025.dta", convert_categoricals=False)
w = d25[d25.D1A == 1]; out = {}
sh = lambda m, d, x: float(x[m & d].sum() / x[d].sum())
for v in ["D52_a","D52_b","D52_c","D52_d","D52_e","D52_f"]:
    agree = w[v] == 1
    out[v] = dict(all_workers_wt=sh(agree, w[v].notna(), w.weight_pop) if False else float(w.weight_pop[agree].sum()/w.weight_pop[w[v].notna()].sum()),
                  users_wt=float(w.weight_pop[agree & (w.D50==1)].sum()/w.weight_pop[w[v].notna() & (w.D50==1)].sum()),
                  nonusers_wt=float(w.weight_pop[agree & (w.D50==0)].sum()/w.weight_pop[w[v].notna() & (w.D50==0)].sum()))
out["D50_given_D1A"] = pd.crosstab(d25.D1A, d25.D50.fillna(-9)).to_dict()
out["D51_given_D50"] = pd.crosstab(d25.D50.fillna(-9), d25.D51.fillna(-9)).to_dict()
out["autonomy_universe_D28_a_nonmissing_by_D3A"] = pd.crosstab(d25.D3A.fillna(-9), d25.D28_a.notna()).to_dict()
out["n_with_panel_weight"] = int(d25.panel_weight.notna().sum())
f24 = glob.glob(str(R/"data/x/shed2024/*.dta"))
if f24:
    d24 = pd.read_stata(f24[0], convert_categoricals=False)
    a, b = set(d25.shedid.astype(str)), set(d24.shedid.astype(str))
    out["shedid_2024_n"] = len(b); out["shedid_overlap_2025_2024"] = len(a & b)
    out["overlap_among_panel_weight_nonmissing"] = len(set(d25.loc[d25.panel_weight.notna(), "shedid"].astype(str)) & b)
    out["2024_has_genai_items"] = [c for c in d24.columns if c.upper() in ("D50","D51") or c.upper().startswith("D52")]
dump("shed_extra_checks.json", out)
print(json.dumps(out, indent=1, default=str)[:3500])

# ---- (5) is the ID match the same person? how big is the linkable analytic sample? ----
if f24:
    m = d25.merge(d24, on="shedid", suffixes=("", "_24"), how="inner", validate="1:1")
    L = {"n_linked": len(m)}
    for v in ["ppgender", "ppeducat", "ppethm", "ppstaten"]:
        if v in m and v + "_24" in m: L[f"{v}_same_share"] = float((m[v] == m[v + "_24"]).mean())
    if "ppage" in m: L["age_diff_counts"] = (m.ppage - m.ppage_24).value_counts().head(5).to_dict()
    L["linked_workers_2025"] = int((m.D1A == 1).sum())
    L["linked_genai_users_2025"] = int(((m.D1A == 1) & (m.D50 == 1)).sum())
    L["linked_D51_nonmissing"] = int(m.D51.notna().sum())
    for v in ["D1A", "D3A", "D28_a", "D28_b", "ppcm0160", "ind1", "ppinc7", "D34A", "D44_b"]:
        L[f"2024_has_{v}"] = (v in d24.columns)
    if "D1A_24" in m:
        L["linked_workers_in_BOTH_2024_and_2025"] = int(((m.D1A == 1) & (m.D1A_24 == 1)).sum())
        L["linked_users_who_were_workers_2024"] = int(((m.D1A == 1) & (m.D50 == 1) & (m.D1A_24 == 1)).sum())
    if "D28_a_24" in m: L["linked_2025workers_with_2024_autonomy"] = int(((m.D1A == 1) & m.D28_a_24.notna()).sum())
    out["linkage_2024_2025"] = L
    dump("shed_extra_checks.json", out); print(json.dumps(L, indent=1, default=str))

# ---- (6) analytic N for the linked design: 2024 autonomy -> 2025 GenAI use; wording equality of D28 across waves ----
if f24:
    import pyreadstat
    _, m25 = pyreadstat.read_dta(str(R/"data/x/shed_dta/public2025.dta"), metadataonly=True)
    _, m24 = pyreadstat.read_dta(f24[0], metadataonly=True)
    lab25, lab24 = dict(zip(m25.column_names, m25.column_labels)), dict(zip(m24.column_names, m24.column_labels))
    A = {"label_equal_D28_a": lab25["D28_a"] == lab24.get("D28_a"), "label_equal_D28_b": lab25["D28_b"] == lab24.get("D28_b"),
         "valuelabels_equal_D28_a": m25.variable_value_labels.get("D28_a") == m24.variable_value_labels.get("D28_a"),
         "label_equal_ppcm0160": lab25["ppcm0160"] == lab24.get("ppcm0160")}
    ok = (m.D3A == 0) & (m.D1A == 1) & m.D28_a_24.notna() & m.D50.notna()
    A["linked_2025_employees_with_2024_D28_and_2025_D50"] = int(ok.sum())
    A["... of which GenAI users"] = int((ok & (m.D50 == 1)).sum())
    A["... with panel_weight_pop"] = int((ok & m.panel_weight_pop.notna()).sum())
    A["... D51 valid"] = int((ok & m.D51.notna()).sum())
    A["2024_D28_values_in_linked_sample"] = m.loc[ok, "D28_a_24"].value_counts().sort_index().to_dict()
    A["2024_fieldwork_has_D3A"] = bool("D3A" in d24.columns)
    out["linked_design_N"] = A; dump("shed_extra_checks.json", out); print(json.dumps(A, indent=1, default=str))
