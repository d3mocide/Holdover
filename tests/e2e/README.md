# End-to-end: airplane-mode journal flow

Verified 2026-10-17 in headless Chromium against the built app, and again after the design pass. Not part of `pytest`.

    pip install -e '.[dev]' pmtiles mapbox-vector-tile
    python scripts/make_test_pmtiles.py data/tiles/oregon.pmtiles        # toy tiles, not real map data
    (cd web && npm ci && npm run build)
    export DATABASE_URL=sqlite:///./data/e2e.db HOLDOVER_TOKEN=testtoken RUN_SCHEDULER=false DATA_DIR=./data WEB_DIR=web/dist
    python -m app.cli migrate && python -m app.cli seed
    python -m app.cli ingest-fixtures tests/fixtures/odfw_stocking
    uvicorn app.main:app --port 8000 &
    npm i --no-save playwright-core
    E2E_DB=./data/e2e.db CHROMIUM=/path/to/chrome node tests/e2e/offline.mjs
    # if port 8000 is taken: uvicorn ... --port 8011  and  BASE_URL=http://localhost:8011/

It checks: service worker control, "Prepare for offline" saves tiles to IndexedDB, the app shell and cached
list load with the network off, a trip logs offline with cached conditions, it syncs after reconnect, and a
forced duplicate push creates no duplicate rows. Restart the server after deleting the DB file.
