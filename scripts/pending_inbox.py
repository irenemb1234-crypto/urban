"""Print inbox posts whose LinkedIn activity ID is not yet in any data/*.json file."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INBOX = ROOT / "inbox" / "linkedin_inbox.json"
ID_RE = re.compile(r"urn:li:(?:activity|ugcPost|share):(\d+)")

if not INBOX.exists():
    print("[]")
    sys.exit(0)

known = set()
for f in (ROOT / "data").glob("*.json"):
    known.update(ID_RE.findall(f.read_text(encoding="utf-8")))

pending = [p for p in json.loads(INBOX.read_text(encoding="utf-8")) if p["id"] not in known]
json.dump(pending, sys.stdout, ensure_ascii=False, indent=2)
print(f"\n# {len(pending)} pendientes", file=sys.stderr)
