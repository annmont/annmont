"""Download documentation + data listed in config/sources.yaml into data/raw/<dataset>/.
Records HTTP status, bytes, Last-Modified and SHA-256 in outputs/fetch_log.json.
Needs outbound access to census.gov, www2.census.gov, federalreserve.gov (and eurofound.europa.eu for docs).
EWCS microdata are NOT fetched: they require UK Data Service registration (see README).
Usage: python audit/src/00_fetch.py [htops shed ewcs]"""
import sys, json, time
from pathlib import Path
import requests, yaml
sys.path.insert(0, str(Path(__file__).parent))
from common import sha256, dump

ROOT = Path(__file__).resolve().parents[1]
cfg = yaml.safe_load((ROOT / "config/sources.yaml").read_text())
want = sys.argv[1:] or list(cfg)
log = []
for ds in want:
    for item in cfg[ds]["files"]:
        url, fn = item["url"], item["filename"]
        dest = ROOT / "data/raw" / ds / fn
        dest.parent.mkdir(parents=True, exist_ok=True)
        rec = dict(dataset=ds, url=url, dest=str(dest), kind=item.get("kind"), status=None)
        try:
            r = requests.get(url, timeout=120, headers={"User-Agent": "Mozilla/5.0 (research audit)"})
            rec.update(status=r.status_code, last_modified=r.headers.get("Last-Modified"), bytes=len(r.content))
            if r.ok:
                dest.write_bytes(r.content); rec["sha256"] = sha256(dest)
        except Exception as e:
            rec["error"] = repr(e)
        log.append(rec); print(rec["status"], url)
        time.sleep(1)
dump(f"fetch_log_{'_'.join(want)}.json", log)
