# AGENTS.md: rules for any coding agent working on Holdover

This is the **single source of rules**. Tool-specific files (for example `CLAUDE.md`) import this file and add only
tool-specific notes. Never copy a rule into another file; link to it. `tests/test_docs.py` fails if the two drift.

Holdover is a self-hosted PWA for Oregon fishing: where to fish, when, and what to bring, plus a private angler's
journal and gear database. One container, one SQLite file, a local LLM used for text only. Accounts are optional.

## 1. Read first, in this order

| Read | For |
| --- | --- |
| This file | Rules |
| [docs/ROADMAP.md](docs/ROADMAP.md) | What is planned, the status of each phase, decisions and why plans changed |
| [docs/BUILD_LOG.md](docs/BUILD_LOG.md) | What was done and how it was verified. The latest entry is where work stands |
| [docs/BRAND.md](docs/BRAND.md) | Anything visual or any user-facing wording. The authority over the original design notes |
| [docs/accounts.md](docs/accounts.md) | The account, session and privacy model |
| [docs/basemap.md](docs/basemap.md), [docs/sources.md](docs/sources.md), [docs/waterbody-pins.md](docs/waterbody-pins.md) | Map data, source terms, pin provenance |
| [docs/reference/original-handoff.md](docs/reference/original-handoff.md) | The original brief. Historical: do not edit |

## 2. Non-negotiable rules

These come from the product's promises. Breaking one is a bug even if every test passes.

**Safety and honesty**
1. **Never state regulations, limits, seasons or closures as fact.** Link to official ODFW pages.
2. **The LLM reads and writes text. It never decides facts.** Numbers, dates, species, places and rankings come
   from the database. Generated text is checked against its inputs, labelled as generated with a time, and has a
   template fallback. The UI must work with the model off.
3. **Label uncertainty:** USGS values are provisional; stocking is a *week* and may change; scores are unvalidated
   starting points; every conditions value shows an "as of" time.
4. **Do not invent data.** No fabricated coordinates, readings, catches or quotes. Sample data is labelled as sample.
   A pin's coordinate has provenance (see `COORD_UPDATES` in `app/seed.py`); do not geocode silently.

**Data**
5. **Store the raw response before parsing** (`raw_fetch`). Parsers are pure functions of stored bodies, tested
   against `tests/fixtures/`. A parse failure keeps the last good data and marks the source stale. It never shows
   wrong data as fresh.
6. **Scraped data is append-only.** Stocking is snapshotted, never overwritten. Scrapers never touch personal tables.
7. **Be a polite client:** identifying `USER_AGENT`, low poll rates, honour caching, back off on 429 and 5xx. Read a
   site's terms and robots before the first scrape of a new source and record the outcome in `docs/sources.md`.
8. **Single uvicorn worker.** The scheduler and the login throttle live in the process.
9. **Portable SQL.** SQLite today, Postgres later: no SQLite-only SQL outside `app/db.py`, migrations and the backup
   job. Schema changes go through Alembic (batch mode for SQLite) with a `downgrade`.

**People and privacy**
10. **Personal data belongs to its owner.** Trips, catches, pins, photos, gear, setups, favorites and home are
    per-account. Every query over them filters by the signed-in user's id; ids from the client are never trusted
    (a uuid that belongs to someone else is refused, and so is a reference to someone else's row or photo). **Any new
    personal table needs an `owner_id`, owner-scoped sync, and an isolation test** (user B cannot read, overwrite,
    delete or reference user A's rows).
11. **Public by default, personal by sign-in.** Reads of public data stay open with no login; anonymous use (a local
    journal, home and favorites on the device) must keep working. Never make signing in mandatory.
12. **No secrets in the repo or in browser storage.** Config comes from environment variables; `.env` is ignored. The
    session is an HttpOnly cookie. Passwords are hashed with scrypt. State-changing calls carry the `X-Holdover`
    header.
13. **Offline-first for anything personal:** write to IndexedDB first with a client uuid, sync later, last write wins.
    New personal features need the airplane-mode e2e.

## 3. Engineering rules

- **Tests are part of the change.** Run before saying done:
  - `pytest` (all must pass; do not weaken or delete a test to make it pass)
  - `cd web && npm run build` (and `npm test` for the pure-logic unit tests)
  - the browser tests in [tests/e2e/README.md](tests/e2e/README.md) (offline, accounts, gear) when sync, auth, gear or
    offline code changed
  - an axe-core pass on the views you touched, in all three themes, desktop and phone (zero violations)
- **New behaviour gets a test that fails without it**, especially isolation, validation and sync edge cases.
- **Fix the cause.** If a test exposes a real bug, fix the bug and say what it was. Do not paper over it.
- **Match the surrounding code:** naming, comment density, idiom. Prefer small modules, no new dependency without a
  reason, no speculative abstractions.
- **UI work follows [docs/BRAND.md](docs/BRAND.md):** colours only from tokens in `web/src/theme.css` (no literal
  colours in components), icons only from `web/src/lib/icons.js`, dense glass under any text, 16 px gutters, 44 px
  targets, no meaning carried by colour alone. Check phone, tablet and desktop and all three themes. Take screenshots.
- **Licensing:** the project is GPL-3.0 (see `LICENSE`), the same as Vertex. A new dependency or bundled asset must be
  GPL-3.0 compatible (MIT, BSD, Apache-2.0, OFL and public-domain data are fine); keep third-party notices with the
  asset. Do not paste in code under an incompatible or unknown license. Moving code between Holdover and Vertex is fine.
- **Data migrations are guarded:** never overwrite a value a person set deliberately; say what changed and why.

## 4. Documentation discipline (how drift is prevented)

1. **One home per fact.** Rules live here. Plans and status live in the roadmap. History and evidence live in the
   build log. Visuals and voice live in the brand guide. Other files link, they do not restate.
2. **A change that finishes or alters a roadmap item updates [docs/ROADMAP.md](docs/ROADMAP.md) in the same commit**
   (tick the item, change the phase status only when its gate's evidence exists) **and appends an entry to
   [docs/BUILD_LOG.md](docs/BUILD_LOG.md)** (what, how it was verified, what was found, what was *not* checked).
3. **Never edit history.** Do not rewrite old build-log entries or the original handoff. Add a correction entry.
4. **A visual change updates BRAND.md** (token blocks and the contrast table must match `theme.css`; the test
   checks this).
5. **A phase is Done only with evidence.** A gate met only against fixtures or a mock stays listed under "Carried
   forward". Statuses are `Done`, `In progress`, `Planned`.

## 5. Working with the human

**Ask before** doing any of these; approval for one does not cover another:
- pushing, opening or merging a PR, force-pushing, or rewriting history
- deleting or overwriting data, volumes, databases or files you did not create; destructive git commands
- adding a new outside service, scraping a new source, or sending data off the machine
- changing the account or privacy model, adding fees or paid services
- spending real effort on something outside the current phase

**Stop at each phase gate** and report. **Report faithfully:** if a test fails, say so with the output; if a check
was skipped, say so; do not call something done that was only partly verified. When something is done and verified,
say that plainly.

Git: work on a branch off `main`, small commits with clear messages, never commit `.env`, `data/`, `node_modules/`,
`*.pmtiles` or build output. Do not push unless asked.

## 6. Definition of done

- [ ] Behaviour works and is covered by a test that would fail without it
- [ ] `pytest` and `npm run build` pass; e2e and axe run where the change touches sync, auth, offline or UI
- [ ] Ran it, not just the tests: looked at the real screen or response
- [ ] No rule in section 2 is bent; any new personal table has owner scoping and an isolation test
- [ ] Roadmap updated and a build-log entry added, in the same commit
- [ ] BRAND.md updated if anything visual changed
- [ ] Anything not verified is listed as not verified
