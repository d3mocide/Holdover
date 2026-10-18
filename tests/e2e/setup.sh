#!/bin/bash
# Fresh throwaway instance for the browser tests: its own database and data dir, never your real one.
#   tests/e2e/setup.sh accounts   -> admin "boss" only (accounts.mjs registers "sam" through an invite)
#   tests/e2e/setup.sh gear       -> admin "boss" and a second user "sam" (gear.mjs checks isolation)
# Starts uvicorn on $PORT (default 8011) and writes its pid to $DIR/server.pid. Stop it with: kill $(cat $DIR/server.pid)
set -e
cd "$(dirname "$0")/../.."
MODE=${1:-accounts}; PORT=${PORT:-8011}; DIR=${E2E_DIR:-/tmp/holdover-e2e}
PY=${PY:-.venv/bin/python}
mkdir -p "$DIR/data"
[ -f "$DIR/server.pid" ] && kill "$(cat "$DIR/server.pid")" 2>/dev/null || true
sleep 1
if (echo > /dev/tcp/127.0.0.1/"$PORT") 2>/dev/null; then echo "port $PORT is already in use: stop whatever holds it (or set PORT=...) so the tests do not hit stale state" >&2; exit 1; fi
rm -f "$DIR"/data/e2e.db*
# E2E_DATABASE_URL runs the same tests on another database (e.g. postgresql+psycopg://user:pw@localhost:5433/db); it is wiped first.
export DATABASE_URL="${E2E_DATABASE_URL:-sqlite:///$DIR/data/e2e.db}" RUN_SCHEDULER=false DATA_DIR="$DIR/data" WEB_DIR=web/dist
case "$DATABASE_URL" in sqlite*) ;; *) $PY -c "
from sqlalchemy import text
from app.db import get_engine
with get_engine().begin() as c:
    c.execute(text('DROP SCHEMA public CASCADE')); c.execute(text('CREATE SCHEMA public'))" ;; esac
$PY -m app.cli migrate >/dev/null
$PY -m app.cli seed >/dev/null
$PY -m app.cli ingest-fixtures tests/fixtures/odfw_stocking >/dev/null
echo correct-horse-battery | $PY -m app.cli create-user boss --password-stdin
[ "$MODE" = gear ] && echo sams-long-password | $PY -m app.cli create-user sam --password-stdin
(nohup "${PY%/python}/uvicorn" app.main:app --port "$PORT" > "$DIR/server.log" 2>&1 & echo $! > "$DIR/server.pid")
sleep 4
curl -s -o /dev/null -w "up on :$PORT (%{http_code})\n" "localhost:$PORT/healthz"
