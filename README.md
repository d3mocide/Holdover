# Holdover

Self-hosted PWA for Oregon fishing: where to fish, when, and what to bring, plus a technical angler's journal. One container, one SQLite file, a local LLM for text only.

Status: phases 1 to 5 built (stocking map, report and LLM pipeline, conditions, offline journal, planner). Phase 6 items not started. **Read `docs/laptop-handoff.md` first**: it lists what was verified and what was not.

## Run

    cp .env.example .env   # set HOLDOVER_TOKEN and USER_AGENT
    docker compose up --build

Then put a TLS reverse proxy in front (service workers need HTTPS).

## Develop

    pip install -e '.[dev]'
    python -m app.cli migrate && python -m app.cli seed
    python -m app.cli ingest-fixtures tests/fixtures/odfw_stocking   # offline sample data
    HOLDOVER_TOKEN=dev RUN_SCHEDULER=false DATA_DIR=./data uvicorn app.main:app --reload
    cd web && npm install && npm run dev                              # proxies /api to :8000
    pytest                                                            # 74 tests
    # airplane-mode E2E: tests/e2e/README.md

## Notes

- Waterbody coordinates in `app/seed.py` are approximate and unverified. Waterbodies without one are listed, not pinned.
- Regulations are never restated; the app links to ODFW.
- Source terms and the known 403 issue: `docs/sources.md`. Basemap: `docs/basemap.md`.
