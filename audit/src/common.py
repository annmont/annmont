"""Shared helpers for the dataset feasibility audit. No substantive models here: counts, tabulations, weighted shares, BRR variance only."""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path
import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parents[1] / "outputs"

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def read_any(path: Path):
    """Return (DataFrame, {col: label}, {col: {value: label}}). Labels empty for CSV."""
    p = Path(path); s = p.suffix.lower()
    if s in (".csv", ".txt"):
        return pd.read_csv(p, low_memory=False), {}, {}
    if s == ".tab":
        return pd.read_csv(p, sep="\t", low_memory=False), {}, {}
    if s in (".sav", ".zsav"):
        import pyreadstat
        df, meta = pyreadstat.read_sav(str(p), apply_value_formats=False)
        return df, dict(zip(meta.column_names, meta.column_labels)), meta.variable_value_labels
    if s == ".dta":
        import pyreadstat
        df, meta = pyreadstat.read_dta(str(p), apply_value_formats=False)
        return df, dict(zip(meta.column_names, meta.column_labels)), meta.variable_value_labels
    if s in (".parquet",):
        return pd.read_parquet(p), {}, {}
    raise ValueError(f"unsupported file type: {p}")

def find_cols(df: pd.DataFrame, pattern: str, labels: dict | None = None) -> list[str]:
    """Columns whose NAME or LABEL matches regex (case-insensitive)."""
    rx = re.compile(pattern, re.I)
    labels = labels or {}
    return [c for c in df.columns if rx.search(str(c)) or rx.search(str(labels.get(c) or ""))]

def tab(series: pd.Series, weights: pd.Series | None = None) -> pd.DataFrame:
    """Raw-code frequency table INCLUDING NaN, so every missing/special code is visible."""
    out = series.value_counts(dropna=False).rename("n").to_frame()
    out["pct"] = out["n"] / out["n"].sum() * 100
    if weights is not None:
        w = weights.groupby(series.fillna(-9999999)).sum()
        w.index = [np.nan if i == -9999999 else i for i in w.index]
        out["w_sum"] = w.reindex(out.index)
        out["w_pct"] = out["w_sum"] / out["w_sum"].sum() * 100
    return out.sort_index()

def wshare(mask_num: pd.Series, mask_den: pd.Series, w: pd.Series) -> float:
    d = w[mask_den].sum()
    return float(w[mask_den & mask_num].sum() / d) if d > 0 else float("nan")

def brr_se(df: pd.DataFrame, stat, w_main: str, rep_cols: list[str], fay_rho: float) -> float:
    """Fay-BRR SE: var = 1/(R(1-rho)^2) * sum_r (theta_r - theta)^2.  stat(df, wcol)->float.
    rho and R MUST come from the official documentation; there is no default."""
    R = len(rep_cols)
    th = stat(df, w_main)
    ss = sum((stat(df, c) - th) ** 2 for c in rep_cols)
    return float(np.sqrt(ss / (R * (1 - fay_rho) ** 2)))

def dump(name: str, obj) -> Path:
    OUT.mkdir(exist_ok=True)
    p = OUT / name
    if isinstance(obj, pd.DataFrame):
        obj.to_csv(p if p.suffix else p.with_suffix(".csv"))
    else:
        p.write_text(json.dumps(obj, indent=2, default=str))
    return p

def inventory(df: pd.DataFrame, labels: dict, vlabels: dict, constructs: dict[str, str], dataset: str) -> pd.DataFrame:
    """One row per (construct, matching variable): name, label, n_nonmissing, n_unique, value labels."""
    rows = []
    for cons, pat in constructs.items():
        for c in find_cols(df, pat, labels):
            s = df[c]
            rows.append(dict(dataset=dataset, construct=cons, variable=c, label=labels.get(c, ""),
                             dtype=str(s.dtype), n_nonmissing=int(s.notna().sum()),
                             n_unique=int(s.nunique(dropna=True)),
                             value_labels=json.dumps(vlabels.get(c, {}), default=str)[:400]))
    return pd.DataFrame(rows)

def id_checks(df: pd.DataFrame, id_cols: list[str]) -> dict:
    res = {}
    for c in id_cols:
        res[c] = dict(n_nonmissing=int(df[c].notna().sum()), n_unique=int(df[c].nunique()),
                      n_duplicated_values=int(df[c].dropna().duplicated().sum()))
    return res
