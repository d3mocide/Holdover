# Operations: backups, restore, upgrades

How to keep a running Holdover safe. For first setup see the README; for accounts see [accounts.md](accounts.md).

## What lives where

Everything that matters is in the `holdover-data` Docker volume, mounted at `/data`:

| Path | What | Back it up? |
| --- | --- | --- |
| `/data/holdover.db` | The SQLite database: scraped data, accounts, journals, gear | **Yes** |
| `/data/photos/` | Journal and gear photos | **Yes** (not inside the database) |
| `/data/backup/` | Nightly database copies, the last 7 | Copy them off the machine |
| `/data/tiles/oregon.pmtiles` | The basemap | No: re-download (see [basemap.md](basemap.md)) |

The container is disposable; the volume is not. `docker compose down` keeps the volume, `down -v` **deletes it**.

## Backups

- A job runs at 03:30 every night (`VACUUM INTO`, which is a consistent copy even while the app is writing) and keeps
  the last 7 in `/data/backup/holdover-YYYYMMDD.db`. It only covers the database. **Photos are not included.**
- The nightly copies live in the same volume as the database, so they do not protect against losing the machine or
  the volume. Copy `/data/backup/` and `/data/photos/` somewhere else on a schedule (another disk, another machine).
- Take one now: `docker compose exec holdover python -c "from app.scheduler import backup; backup()"`
- Copy it out: `docker compose cp holdover:/data/backup/holdover-YYYYMMDD.db .`
- Photos: `docker compose cp holdover:/data/photos ./photos-backup`
- On Postgres the job does nothing (it only handles SQLite); use `pg_dump`.

## Restore

1. Stop the app: `docker compose down` (not `-v`).
2. Put the backup in place as `holdover.db` in the volume, owned by the container user (uid 10001):

       docker run --rm -v holdover_holdover-data:/data -v "$PWD":/in alpine \
         sh -c "cp /in/holdover-YYYYMMDD.db /data/holdover.db && chown 10001 /data/holdover.db"

   (`holdover_holdover-data` is the compose project name plus the volume name; `docker volume ls` shows yours.)
   Restore `photos/` the same way if you have it.
3. Start it: `docker compose up -d`. Startup runs the migrations, so restoring an older backup into a newer version
   upgrades it automatically.
4. Check: `/healthz` shows each source's last success, and you can sign in.

Sessions come back with the database, so people stay signed in. A restore loses anything written after the backup
was taken: for a journal that means trips logged since, which each person's device still holds until it syncs.

### Restore drill (done 2026-10-18)

A backup taken from the live container was restored into a brand-new container with an empty volume. The new
container served identical results: 51 map pins, 58 waterbodies, 16 gauges, source status preserved, schema at
the same migration. Repeat this before relying on backups, and after any change to how the volume is laid out:

    docker compose exec holdover python -c "from app.scheduler import backup; backup()"
    docker compose cp holdover:/data/backup/holdover-$(date +%Y%m%d).db /tmp/drill/holdover.db
    docker volume create drill-vol
    docker run --rm -v drill-vol:/data -v /tmp/drill:/in alpine sh -c "cp /in/holdover.db /data/ && chown -R 10001 /data"
    docker run -d --name drill -p 8013:8000 -v drill-vol:/data -e USER_AGENT=drill -e RUN_SCHEDULER=false holdover-holdover
    curl localhost:8013/healthz        # compare with the live app, then: docker rm -f drill && docker volume rm drill-vol

`RUN_SCHEDULER=false` keeps the drill container from polling the data sources.

## Running on Postgres instead of SQLite

SQLite is the default and is plenty for a handful of people. If you outgrow it, point `DATABASE_URL` at Postgres (the
image includes the driver): `DATABASE_URL=postgresql+psycopg://user:password@host:5432/holdover`. Startup creates the
schema with the same migrations.

- **Verified 2026-10-18** against Postgres 16: the whole `pytest` suite (115 tests; two SQLite-only backup tests skip)
  and the account and gear browser tests pass with the app running on it. To repeat:
  `TEST_DATABASE_URL=postgresql+psycopg://postgres:pw@localhost:5433/holdover_test pytest` (it wipes that database's
  `public` schema for every test, so use a scratch database) and `E2E_DATABASE_URL=... tests/e2e/setup.sh gear`.
- **Not covered:** the nightly backup (SQLite only; use `pg_dump`), performance and PostGIS (geometry is plain lat/lon).
- Existing SQLite data is not migrated automatically: there is no SQLite-to-Postgres copy tool yet.

## Upgrades

`git pull && docker compose up -d --build`. The container runs `alembic upgrade head` and the seed on start. Take a
backup first (above). Migrations are written to be reversible; `python -m alembic downgrade -1` inside the container
undoes the last one.

## Behind a reverse proxy

- Terminate HTTPS at the proxy (service workers and Add to Home Screen need it) and forward `X-Forwarded-Proto` so
  session cookies get the `Secure` flag.
- Set `TRUSTED_PROXY_HOPS=1` (the number of proxies in front) so the login throttle sees each caller's real address.
  With the default of 0 it uses the connection address, which behind a proxy is the proxy itself, so all
  failed logins share one limit. Never set it higher than the real number of proxies: the header is client-supplied
  to the left of your own proxies.
- Pass range requests through for `/tiles/oregon.pmtiles` (the map needs them) and do not cache `/api/auth/*`.
- Keep a single instance: the scheduler and the login throttle live in the process.
