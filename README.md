# Holdover

Self-hosted PWA for Oregon fishing: where to fish, when, and what to bring, plus a technical angler's journal. One container, one SQLite file, a local LLM for text only.

Status: version 0.5.0. Stocking map, weekly report and LLM pipeline, conditions (weather, USGS flow, Army Corps reservoir levels, NOAA flood status, fire danger and wildfire perimeters), planner, offline journal, optional accounts, gear database, three themes. See [docs/ROADMAP.md](docs/ROADMAP.md) for what is done and what is next.

## Run

The published image (amd64 and arm64, so a Raspberry Pi works) needs no checkout. Put `docker-compose.yml` and a `.env` in a folder:

    # .env
    USER_AGENT=Holdover/0.5 (you@example.com)   # identifies you to the data agencies; use a real contact

    docker compose pull && docker compose up -d
    docker compose exec holdover python -m app.cli create-user YOURNAME   # first account = admin; see docs/accounts.md
    ./install-basemap.sh    # one time: Oregon map tiles (scripts/install-basemap.sh in this repo); see docs/basemap.md

- `HOLDOVER_TAG` picks the image: `latest` (default) is the newest release, `0.5.0` pins one, `main` is whatever is on the main branch.
- To build from source instead: `cp .env.example .env`, then `docker compose up -d --build`.
- Data lives in the named volume `holdover-data` (mounted at `/data`: SQLite file, tiles, photos, backups). `down` keeps it; `down -v` deletes it.
- The app listens on `HOLDOVER_PORT` (default 8000). On first start it fetches every data source once, then keeps them fresh on a schedule (`docker compose logs holdover | grep job`).
- Without the basemap the app still works, with pins on a plain ground.
- Put a TLS reverse proxy or tunnel in front for real use (service workers, offline mode and Add to Home Screen need HTTPS; localhost is exempt).

## Develop

The easy way is the dev stack (API with reload on :8020, Vite on :5173, its own data volume): `docker compose -f docker-compose.dev.yml up --build`, then `scripts/dev-fetch.sh` once to load data. Or by hand:

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

## License

GPL-3.0, see [LICENSE](LICENSE). This is the same license as the sibling project Vertex, so code can move between the
two. Bundled third-party assets keep their own licenses: IBM Plex and Noto Sans under the SIL Open Font License
(`web/public/fonts/NOTICE.txt`), map data from OpenStreetMap contributors under the ODbL (credited in the app).

