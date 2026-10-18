#!/bin/sh
# Install the Oregon basemap (Protomaps PMTiles, OpenStreetMap data) into a running Holdover container.
# Run it from the folder that holds docker-compose.yml. It downloads the pmtiles CLI if you do not have it, finds a
# recent Protomaps daily build, extracts Oregon (about 500 MB), copies it into the data volume and restarts the app.
#
#   scripts/install-basemap.sh                # newest build from the last 7 days
#   scripts/install-basemap.sh 20261016       # a specific build date
#   SERVICE=holdover COMPOSE="docker compose" scripts/install-basemap.sh
set -eu

SERVICE="${SERVICE:-holdover}"
COMPOSE="${COMPOSE:-docker compose}"
BBOX="-124.9,41.9,-116.4,46.4"   # Oregon with margin; must match docs/basemap.md
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

say() { printf '\n==> %s\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

command -v curl >/dev/null || die "curl is required"
$COMPOSE ps --status running --services 2>/dev/null | grep -qx "$SERVICE" \
  || die "the '$SERVICE' container is not running here. cd to the folder with docker-compose.yml and run: $COMPOSE up -d"

# 1. the pmtiles CLI (a single Go binary)
if command -v pmtiles >/dev/null; then
  PM="$(command -v pmtiles)"
else
  case "$(uname -m)" in
    x86_64|amd64) ARCH=x86_64 ;;
    aarch64|arm64) ARCH=arm64 ;;
    *) die "unsupported CPU $(uname -m); install pmtiles from https://github.com/protomaps/go-pmtiles/releases and re-run" ;;
  esac
  [ "$(uname -s)" = Linux ] || die "this script downloads the Linux CLI; on other systems install pmtiles yourself and re-run"
  say "Downloading the pmtiles CLI ($ARCH)"
  URL="$(curl -fsSL https://api.github.com/repos/protomaps/go-pmtiles/releases/latest \
    | grep -o "https://[^\"]*Linux_${ARCH}\.tar\.gz" | head -n 1)"
  [ -n "$URL" ] || die "could not find the pmtiles release; install it manually from https://github.com/protomaps/go-pmtiles/releases"
  curl -fsSL "$URL" | tar -xz -C "$WORK" pmtiles
  PM="$WORK/pmtiles"
fi

# 2. a daily build that exists
if [ $# -ge 1 ]; then
  DAY="$1"
else
  DAY=""
  for i in 0 1 2 3 4 5 6 7; do
    d="$(date -u -d "-$i day" +%Y%m%d 2>/dev/null || date -u -v-"$i"d +%Y%m%d)"
    if [ "$(curl -sI -o /dev/null -w '%{http_code}' "https://build.protomaps.com/$d.pmtiles")" = 200 ]; then DAY="$d"; break; fi
  done
  [ -n "$DAY" ] || die "no Protomaps build found in the last 8 days; pass a date: $0 YYYYMMDD"
fi

# 3. extract Oregon
say "Extracting Oregon from the $DAY build (about 500 MB; a few minutes)"
"$PM" extract "https://build.protomaps.com/$DAY.pmtiles" "$WORK/oregon.pmtiles" --bbox="$BBOX"
[ -s "$WORK/oregon.pmtiles" ] || die "the extract is empty"
ls -lh "$WORK/oregon.pmtiles"

# 4. install into the volume (the app runs as a non-root user)
say "Installing into the '$SERVICE' container"
$COMPOSE exec -T -u root "$SERVICE" mkdir -p /data/tiles
$COMPOSE cp "$WORK/oregon.pmtiles" "$SERVICE:/data/tiles/oregon.pmtiles"
$COMPOSE exec -T -u root "$SERVICE" chown -R holdover /data/tiles 2>/dev/null || true   # the dev image runs as root and has no such user

# 5. /tiles is only mounted at startup if the folder exists
say "Restarting"
$COMPOSE restart "$SERVICE"
say "Done: Protomaps build $DAY. Reload the app; the map attribution should read OpenStreetMap contributors and Protomaps."
