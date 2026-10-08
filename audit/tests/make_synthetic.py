"""SYNTHETIC fixture to test the pipeline logic ONLY. These are not real data and carry no substantive information."""
import numpy as np, pandas as pd, yaml
from pathlib import Path
rng = np.random.default_rng(0); n = 2000
d = pd.DataFrame(dict(SCRAM=np.arange(n), WEEK=rng.choice([1, 2], n), EMPLOY=rng.choice([1, 2, -99], n, p=[.6, .35, .05]),
    AIWORK=rng.choice([1, 2, -99, -88], n, p=[.4, .5, .05, .05]), AITASK1=rng.choice([1, 2, -99], n), AITASK2=rng.choice([1, 2, -99], n),
    SAVEHRS=rng.choice([1, 2, 3, -99], n), PWEIGHT=rng.uniform(100, 900, n)))
for r in range(1, 81): d[f"PWEIGHT{r}"] = d.PWEIGHT * rng.uniform(.5, 1.5, n)
d.loc[d.EMPLOY != 1, ["AIWORK", "AITASK1", "AITASK2", "SAVEHRS"]] = np.nan
p = Path(__file__).parent / "fixtures"; p.mkdir(exist_ok=True); d.to_csv(p / "synthetic_puf.csv", index=False)
m = dict(data_file=str(p / "synthetic_puf.csv"), repweight_file=None, merge_keys=[], missing_codes=[-99, -88], weight="PWEIGHT",
    rep_prefix=r"PWEIGHT\d+", fay_rho=0.5, eligible=dict(var="EMPLOY", codes=[1]), ai_user=dict(var="AIWORK", codes=[1]),
    ai_task_vars=["AITASK1", "AITASK2"], ai_task_yes_codes=[1], outcomes=dict(hours=dict(var="SAVEHRS", universe="ai_users")),
    id_cols=["SCRAM"], time_cols=["WEEK"])
(p / "synthetic_map.yaml").write_text(yaml.safe_dump(m))
