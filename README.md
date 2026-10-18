# Holdover

Self-hosted PWA for Oregon fishing: where to fish, when, and what to bring, plus a technical angler's journal. One container, one SQLite file, a local LLM for text only.

Status: phases 1 to 5 built (stocking map, report and LLM pipeline, conditions, offline journal, planner), plus a design pass (glass UI, custom icon set, three themes). Phase 6 items not started. **Read `docs/laptop-handoff.md` first**: it lists what was verified and what was not.

## Run

    cp .env.example .env   # set HOLDOVER_TOKEN and USER_AGENT; optionally HOLDOVER_PORT, HOME_LAT/LON
    docker compose up --build

- Data lives in the named volume `holdover-data` (mounted at `/data`: SQLite file and `tiles/`). It is not in the repo and is not created by `docker compose down`; `down -v` deletes it.
- The app listens on `HOLDOVER_PORT` (default 8000). Change it if something else holds 8000.
- **Basemap is a manual step**: the 503 MB Oregon PMTiles file is not downloaded for you. Install it once per machine or volume: see `docs/basemap.md`. Without it the app still works, with pins on a plain ground.
- Put a TLS reverse proxy in front for real use (service workers, offline mode and Add to Home Screen need HTTPS; localhost is exempt).

## Develop

    pip install -e '.[dev]'
    python -m app.cli migrate && python -m app.cli seed
    python -m app.cli ingest-fixtures tests/fixtures/odfw_stocking   # offline sample data
    HOLDOVER_TOKEN=dev RUN_SCHEDULER=false DATA_DIR=./data uvicorn app.main:app --reload
    cd web && npm install && npm run dev                              # proxies /api to :8000
    pytest                                                            # 75 tests
    # airplane-mode E2E: tests/e2e/README.md

## Notes

- Waterbody coordinates in `app/seed.py` are approximate and unverified. Waterbodies without one are listed, not pinned.
- Regulations are never restated; the app links to ODFW.
- Source terms: `docs/sources.md`. Basemap: `docs/basemap.md`.
- Design tokens (palette, glass tiers, hairlines) are in `web/src/theme.css`; the icon set and map marker art are in `web/src/lib/icons.js`. A theme is only a palette: components use no literal colours.
