#!/bin/bash
# End-to-end lobby + chat walkthrough with two independent cookie identities.
# Verifies: create -> waiting; explicit join -> live; ordered messages with
# correct me/other attribution; third visitor -> "full"; end -> read-only;
# posting after end -> 409. Self-contained: starts its own server on a temp DB.
#
# Run:  bash tests/walkthrough.sh
set -u
REPO="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$(mktemp -d)"
DB="$WORK/t3.db"
PORT=8113
BASE="http://127.0.0.1:$PORT"

cd "$REPO"
DATABASE_PATH="$DB" "$REPO/.venv/bin/uvicorn" app.main:app \
  --host 127.0.0.1 --port "$PORT" --log-level warning &
UV=$!
trap "kill $UV 2>/dev/null; rm -rf '$WORK'" EXIT

JA="$WORK/jarA"; JB="$WORK/jarB"; JC="$WORK/jarC"
strip() { sed 's/<[^>]*>/ /g' | tr -s ' ' | sed 's/^ *//' | grep -vE '^$'; }

curl -s --retry 25 --retry-connrefused --retry-delay 1 -o /dev/null "$BASE/healthz"

echo "== 1. Alice starts a session =="
loc=$(curl -s -o /dev/null -D - -c "$JA" -b "$JA" -X POST "$BASE/sessions" \
      --data-urlencode "display_name=Alice" \
      | grep -i '^location:' | tr -d '\r' | awk '{print $2}')
sid=${loc#/s/}; echo "   session id: $sid"

echo "== 2. Alice's room (expect waiting, Seat 1 Alice) =="
curl -s -b "$JA" "$BASE/s/$sid" | grep -E "Seat 1|Seat 2|Waiting for a second" | strip

echo "== 3. Bob visits, no cookie (expect join form) =="
curl -s -c "$JB" -b "$JB" "$BASE/s/$sid" | grep -E "joining a debate|Join debate" | strip | head -2

echo "== 4. Bob joins (expect redirect) =="
curl -s -o /dev/null -D - -c "$JB" -b "$JB" -X POST "$BASE/s/$sid/join" \
     --data-urlencode "display_name=Bob" | grep -i '^location:' | tr -d '\r'

echo "== 5. Alice's room now (expect Seat 2 Bob + composer) =="
curl -s -b "$JA" "$BASE/s/$sid" | grep -E "Seat 2|Write a message" | strip | head -3

echo "== 6. Both post =="
curl -s -o /dev/null -w "   Alice post -> %{http_code}\n" -b "$JA" \
     -X POST "$BASE/s/$sid/messages" --data-urlencode "content=I think congestion pricing reduces traffic."
curl -s -o /dev/null -w "   Bob post   -> %{http_code}\n" -b "$JB" \
     -X POST "$BASE/s/$sid/messages" --data-urlencode "content=But is it fair to outer-borough drivers?"

echo "== 7. Alice fetches messages (hers=me, Bob=other) =="
curl -s -b "$JA" "$BASE/s/$sid/messages" | strip

echo "== 8. Carol visits, no cookie (expect full) =="
curl -s -c "$JC" -b "$JC" "$BASE/s/$sid" | grep -E "session is full" | strip

echo "== 9. Alice ends; post then rejected =="
curl -s -o /dev/null -w "   Alice end -> %{http_code}\n" -b "$JA" -X POST "$BASE/s/$sid/end"
curl -s -b "$JA" "$BASE/s/$sid" | grep -E "has ended" | strip
curl -s -o /dev/null -w "   post-after-end -> %{http_code} (expect 409)\n" -b "$JA" \
     -X POST "$BASE/s/$sid/messages" --data-urlencode "content=too late"
echo "== DONE =="
