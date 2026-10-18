# CLAUDE.md

@AGENTS.md

The rules above are the project's single source of rules, imported from `AGENTS.md`. **Do not add or restate rules
here.** This file holds only what is specific to working in Claude Code. If a rule needs to change, change it in
`AGENTS.md`.

## Commands

    python -m venv .venv && .venv/bin/pip install -e '.[dev]'    # once
    .venv/bin/pytest -q                                          # backend tests
    cd web && npm ci && npm run build                            # frontend build (also: npm test)
    docker compose up -d --build                                 # run it; the app is on HOLDOVER_PORT (default 8000)
    docker compose exec holdover python -m app.cli create-user NAME   # first user is the admin
    docker compose exec holdover python -m app.cli                 # prints usage: migrate, seed, create-user, reset-password, ...

The offline end-to-end test and its setup are in `tests/e2e/README.md`. Other helpers: `scripts/check_coords.py`
(pin cross-check), `scripts/make_test_pmtiles.py` (toy tiles for tests only).

## Claude Code specifics

- **Use the dedicated tools** (Read, Edit, Grep) for files and search; reserve Bash for running things.
- **Verify in the running app.** Build the container, drive it with Playwright (headless Chromium is installed under
  `~/.cache/ms-playwright`), and look at screenshots at phone, tablet and desktop widths in all three themes, before
  saying a UI change is done. Use a throwaway instance on another port with its own database for tests that create
  users or trips; never run tests against the owner's data volume.
- **Do not `pkill -f` by command text** (it matches your own shell). Kill by pid or port.
- **Scratch work** (screenshots, throwaway scripts) goes in the session scratchpad, not the repo.
- **Commit trailer:** end commit messages with the attribution line the harness gives you. Do not push or open PRs
  unless asked.
- **Long tasks:** use the task list to track phases, and keep ROADMAP and BUILD_LOG current as you go, not at the end.
