# Holdover

Self-hosted PWA for Oregon fishing: where to fish, when, and what to bring, plus a technical angler's journal. One container, one SQLite file, a local LLM for text only.

Status: phases 1 to 5 built (stocking map, report and LLM pipeline, conditions, offline journal, planner), plus a design pass (glass UI, custom icon set, three themes). Phase 6 items not started. **Read `docs/laptop-handoff.md` first**: it lists what was verified and what was not.

## Run

    cp .env.example .env   # set USER_AGENT (with a contact address); optionally HOLDOVER_PORT, HOME_LAT/LON
    docker compose up --build
    docker compose exec holdover python -m app.cli create-user YOURNAME   # first account = admin; see docs/accounts.md

- Data lives in the named volume `holdover-data` (mounted at `/data`: SQLite file and `tiles/`). It is not in the repo and is not created by `docker compose down`; `down -v` deletes it.
- The app listens on `HOLDOVER_PORT` (default 8000). Change it if something else holds 8000.
- **Basemap is a manual step**: the 503 MB Oregon PMTiles file is not downloaded for you. Install it once per machine or volume: see `docs/basemap.md`. Without it the app still works, with pins on a plain ground.
- Put a TLS reverse proxy in front for real use (service workers, offline mode and Add to Home Screen need HTTPS; localhost is exempt).

## Develop

    pip install -e '.[dev]'
    python -m app.cli migrate && python -m app.cli seed
    python -m app.cli ingest-fixtures tests/fixtures/odfw_stocking   # offline sample data
    RUN_SCHEDULER=false DATA_DIR=./data uvicorn app.main:app --reload
    cd web && npm install && npm run dev                              # proxies /api to :8000
    pytest                                                            # backend tests
    cd web && npm test                                                # frontend unit tests
    # airplane-mode E2E: tests/e2e/README.md

## Documentation

| Read | For |
| --- | --- |
| [AGENTS.md](AGENTS.md) (and [CLAUDE.md](CLAUDE.md), which imports it) | Rules for anyone working on the code, human or agent |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Phases, their status and gates, and why plans changed |
| [docs/BUILD_LOG.md](docs/BUILD_LOG.md) | What was done and how it was verified |
| [docs/BRAND.md](docs/BRAND.md) | Look, voice, colour tokens, icons, map language |
| [docs/accounts.md](docs/accounts.md) | Optional accounts and the privacy model |
| [docs/operations.md](docs/operations.md) | Backups, restore, upgrades, running behind a proxy |
| [docs/reference/original-handoff.md](docs/reference/original-handoff.md) | The original brief (historical) |

## Notes

- Waterbody coordinates in `app/seed.py` are approximate and unverified. Waterbodies without one are listed, not pinned.
- Regulations are never restated; the app links to ODFW.
- Accounts are optional (browse and keep a local journal without one): `docs/accounts.md`.
- Source terms: `docs/sources.md`. Basemap: `docs/basemap.md`.
- Design tokens (palette, glass tiers, hairlines) are in `web/src/theme.css`; the icon set and map marker art are in `web/src/lib/icons.js`. A theme is only a palette: components use no literal colours.
