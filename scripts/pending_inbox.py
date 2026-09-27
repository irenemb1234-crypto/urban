"""Print inbox posts not yet catalogued in data/*.json nor listed in inbox/descartados.json."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INBOX = ROOT / "inbox" / "linkedin_inbox.json"
DESCARTADOS = ROOT / "inbox" / "descartados.json"
# LinkedIn URLs come as .../feed/update/urn:li:activity:NNN or .../posts/user_slug-activity-NNN-xyz
ID_RE = re.compile(r"(?:urn:li:|\b)(?:activity|ugcPost|share)[:-](\d{15,25})")

if not INBOX.exists():
    print("[]")
    sys.exit(0)

known = set()
for f in (ROOT / "data").glob("*.json"):
    known.update(ID_RE.findall(f.read_text(encoding="utf-8")))
if DESCARTADOS.exists():
    known.update(str(d["id"]) for d in json.loads(DESCARTADOS.read_text(encoding="utf-8")))

pending = [p for p in json.loads(INBOX.read_text(encoding="utf-8")) if p["id"] not in known]
json.dump(pending, sys.stdout, ensure_ascii=False, indent=2)
print(f"\n# {len(pending)} pendientes", file=sys.stderr)
