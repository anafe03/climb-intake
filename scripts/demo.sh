#!/usr/bin/env bash
# One command to (re)start the service and show it working.
#   ./scripts/demo.sh            # start server, ingest the 10 samples, print the routing table
#   ./scripts/demo.sh eval       # also run the gold-set eval and the rules-vs-model comparison
set -euo pipefail
cd "$(dirname "$0")/.."
PY=.venv/bin/python
[ -f .env ] && { set -a; . ./.env; set +a; }

pkill -f "uvicorn app.main:app" 2>/dev/null || true
sleep 1
$PY -m uvicorn app.main:app --host 127.0.0.1 --port 8080 > /tmp/climb-intake.log 2>&1 &
for _ in $(seq 1 30); do curl -fs localhost:8080/health >/dev/null && break; sleep 0.5; done

echo "== health"
curl -s localhost:8080/health | $PY -m json.tool
echo
echo "== ingesting the 10 Climb samples"
curl -s -X DELETE localhost:8080/tickets >/dev/null
curl -s -X POST localhost:8080/tickets/load-samples >/dev/null
$PY - <<'PYEOF'
import json, urllib.request
rows = json.load(urllib.request.urlopen("http://localhost:8080/tickets?limit=50"))
rows.sort(key=lambda d: int(d["ticket"]["external_id"] or 0))
print(f'{"#":<3}{"category":<16}{"urgency":<10}{"esc":<5}{"queue"}')
for d in rows:
    x = d["extraction"]
    print(f'{d["ticket"]["external_id"]:<3}{x["category"]:<16}{x["urgency"]:<10}{"YES" if x["escalate"] else "-":<5}{d["queue"]}'
          + (f' + {d["escalation_queue"]}' if d["escalation_queue"] else ""))
errs = [d for d in rows if d.get("error")]
if errs:
    print(f'\n!! {len(errs)}/{len(rows)} fell back to rules: {errs[0]["error"][:160]}')
PYEOF
echo
echo "== open http://localhost:8080  (server log: /tmp/climb-intake.log)"

if [ "${1:-}" = "eval" ]; then
  echo
  $PY scripts/eval.py
  echo
  $PY scripts/compare_evals.py || true
fi
