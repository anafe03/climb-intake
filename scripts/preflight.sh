#!/usr/bin/env bash
# Pre-demo check. Every line either PASSes or tells you what is wrong.
#   ./scripts/preflight.sh            # check the running container
#   ./scripts/preflight.sh --rebuild  # rebuild the image first
cd "$(dirname "$0")/.."
PY=.venv/bin/python
BASE=http://localhost:8080
pass=0; fail=0
ok(){ printf "  \033[32mPASS\033[0m  %s\n" "$1"; pass=$((pass+1)); }
no(){ printf "  \033[31mFAIL\033[0m  %s\n" "$1"; fail=$((fail+1)); }
chk(){ if [ "$2" = "$3" ]; then ok "$1"; else no "$1 (got '$2', want '$3')"; fi; }

command -v docker >/dev/null || export PATH="$HOME/.local/bin:$PATH"

echo "── container"
if [ "${1:-}" = "--rebuild" ]; then
  docker compose build >/dev/null 2>&1 && ok "image builds" || no "image build failed"
  docker compose up -d --force-recreate >/dev/null 2>&1
fi
for _ in $(seq 1 60); do curl -fs $BASE/health >/dev/null 2>&1 && break; sleep 1; done
[ -n "$(docker compose ps -q 2>/dev/null)" ] && ok "container running" || no "container not running"
[ "$(docker inspect --format '{{.State.Health.Status}}' $(docker compose ps -q) 2>/dev/null)" = "healthy" ] \
  && ok "docker healthcheck green" || no "healthcheck not green"
[ "$(docker exec $(docker compose ps -q) id -un 2>/dev/null)" = "climb" ] \
  && ok "runs as non-root" || no "not running as the climb user"
diff <(curl -s $BASE/) app/static/index.html >/dev/null \
  && ok "served page matches the working tree" || no "SERVING STALE CODE — rebuild"
diff <(curl -s $BASE/notes) app/static/presenter.html >/dev/null \
  && ok "presenter notes current at /notes" || no "/notes stale or missing"

echo "── api"
MODE=$(curl -s $BASE/health | $PY -c 'import json,sys;print(json.load(sys.stdin)["mode"])')
[ "$MODE" = "llm" ] && ok "model mode active ($(curl -s $BASE/health | $PY -c 'import json,sys;print(json.load(sys.stdin)["model"])'))" \
  || no "in '$MODE' mode — the demo wants a key present"
curl -s -X DELETE $BASE/tickets >/dev/null && ok "DELETE /tickets clears the log" || no "clear failed"
chk "POST /tickets rejects empty" "$(curl -s -o /dev/null -w '%{http_code}' -X POST $BASE/tickets -H 'content-type: application/json' -d '{"text":""}')" "422"
chk "GET unknown id 404s" "$(curl -s -o /dev/null -w '%{http_code}' $BASE/tickets/deadbeef1234)" "404"
chk "unknown fixture 400s" "$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/tickets/load-samples?fixture=nope")" "400"
chk "upload .txt" "$(curl -s -X POST $BASE/tickets/upload -F 'file=@/dev/stdin;filename=a.txt' <<< $'First ticket here.\n\nSecond ticket here.' | $PY -c 'import json,sys;print(json.load(sys.stdin)["count"])')" "2"
chk "upload .csv" "$(printf 'id,text\n9001,Export is broken.\n' | curl -s -X POST $BASE/tickets/upload -F 'file=@/dev/stdin;filename=a.csv' | $PY -c 'import json,sys;print(json.load(sys.stdin)["count"])')" "1"

echo "── the 10 Climb samples"
curl -s -X DELETE $BASE/tickets >/dev/null
curl -s -X POST "$BASE/tickets/load-samples?fixture=samples" -o /tmp/pf.json
$PY - <<'PYEOF'
import json
d=json.load(open("/tmp/pf.json")); rows={int(r["ticket"]["external_id"]):r for r in d["decisions"]}
g=lambda i: rows[i]["extraction"]
checks=[("#3 security escalates", g(3)["escalate"] and g(3)["category"]=="security"),
        ("#4 legal threat escalates", g(4)["escalate"] and g(4)["category"]=="legal_contract"),
        ("#7 executive mention escalates", g(7)["escalate"]),
        ("#9 data exposure escalates", g(9)["escalate"]),
        ("#5 spam not forced into a category", g(5)["category"]=="spam"),
        ("#10 severity inferred with no alarm words", g(10)["urgency"]=="critical"),
        ("#8 low-priority stays low", g(8)["urgency"]=="low"),
        ("all 10 classified by the model", all(r["mode"]=="llm" for r in d["decisions"])),
        ("every ticket got a queue", all(r["queue"] for r in d["decisions"])),
        ("every decision carries per-field reasoning",
         all(all(r["extraction"].get(k) for k in ("customer_reason","category_reason","urgency_reason","escalation_reason_text"))
             for r in d["decisions"]))]
for label, good in checks:
    print(("  \033[32mPASS\033[0m  " if good else "  \033[31mFAIL\033[0m  ")+label)
PYEOF

echo "── idempotency + audit"
B=$(curl -s $BASE/queues | $PY -c 'import json,sys;print(json.load(sys.stdin)["total"])')
curl -s -X POST "$BASE/tickets/load-samples?fixture=samples" -o /dev/null
A=$(curl -s $BASE/queues | $PY -c 'import json,sys;print(json.load(sys.stdin)["total"])')
chk "reloading a fixture does not duplicate" "$A" "$B"
ID=$(curl -s "$BASE/tickets?limit=1" | $PY -c 'import json,sys;print(json.load(sys.stdin)[0]["id"])')
curl -s "$BASE/tickets/$ID/explain" | grep -q "why:" && ok "explain endpoint shows per-field reasoning" || no "explain endpoint thin"
curl -s "$BASE/tickets/$ID" | $PY -c 'import json,sys;d=json.load(sys.stdin);exit(0 if all(k in d for k in ("llm_extraction","rule_hits","overrides","usage","latency_ms")) else 1)' \
  && ok "audit record keeps model output, rules and usage" || no "audit record missing fields"
docker compose logs 2>/dev/null | grep -q routing_decision && ok "JSON audit lines on stdout" || no "no audit lines on stdout"

echo "── deep links"
for X in who what urgency human route; do
  curl -s "$BASE/?t=$ID&x=$X" | grep -q "openField" && ok "?x=$X reachable" || no "?x=$X broken"
done

echo "── offline path"
docker run --rm -d --name pf-rules -p 8099:8080 -e CLASSIFIER_MODE=rules climb-intake-intake:latest >/dev/null 2>&1
for _ in $(seq 1 40); do curl -fs localhost:8099/health >/dev/null 2>&1 && break; sleep 1; done
chk "runs with no API key" "$(curl -s localhost:8099/health | $PY -c 'import json,sys;print(json.load(sys.stdin)["mode"])')" "rules"
chk "still escalates without a model" "$(curl -s -X POST localhost:8099/tickets -H 'content-type: application/json' -d '{"text":"A terminated employee just logged into the admin console with old credentials."}' | $PY -c 'import json,sys;print(json.load(sys.stdin)["extraction"]["escalate"])')" "True"
docker rm -f pf-rules >/dev/null 2>&1

echo "── repo"
TESTS=$($PY -m pytest -q -p no:cacheprovider 2>&1 | grep -E '^[0-9]+ (passed|failed)' | tail -1)
$PY -m pytest -q -p no:cacheprovider >/dev/null 2>&1 && ok "tests: ${TESTS:-ran}" || no "tests failing: ${TESTS:-see output}"
(cd infra/terraform && tofu validate >/dev/null 2>&1) && ok "terraform validates" || no "terraform invalid"
$PY - <<'PYEOF' && ok "documented numbers match the last eval run" || no "docs drifted from data/eval-results — re-run scripts/eval.py"
import json, pathlib, sys
try:
    llm=json.load(open("data/eval-results/llm.json"))["summary"]
    rul=json.load(open("data/eval-results/rules.json"))["summary"]
except FileNotFoundError:
    sys.exit(1)
want=f"| Urgency exact / within tolerance | {rul['urgency_exact']:.0%} / {rul['urgency_accuracy']:.0%} | {llm['urgency_exact']:.0%} / {llm['urgency_accuracy']:.0%} |"
docs=[pathlib.Path(f).read_text() for f in ("README.md","docs/HOW-IT-WORKS.md")]
sys.exit(0 if all(want in d for d in docs) and llm["n"]==rul["n"] else 1)
PYEOF
[ -z "$(git status --porcelain)" ] && ok "working tree clean" || no "uncommitted changes: $(git status --porcelain | wc -l | tr -d ' ') files"
git remote -v | grep -q . && ok "git remote configured" || no "no git remote — the 'source code in a git repository' deliverable"

echo
printf "  %d passed, %d failed\n" "$pass" "$fail"
[ "$fail" -eq 0 ] || exit 1
