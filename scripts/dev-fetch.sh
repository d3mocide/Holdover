#!/bin/sh
# Run every data job once in the dev stack (its scheduler is off by default), so the app has something to show.
set -e
docker compose -f "$(dirname "$0")/../docker-compose.dev.yml" exec -T api python -c "
from app.scheduler import run_stocking, run_usgs, run_nws, run_oha, run_corps, run_odf_fire, run_nifc, run_nwps
for f in (run_stocking, run_usgs, run_oha, run_corps, run_odf_fire, run_nifc, run_nwps, run_nws):
    print(f.__name__, f())
"
