#!/usr/bin/env bash
# Forced command for the GitHub Actions deploy key. Installed on TERMINUS as
# /home/ubuntu/bin/dsa-prep-deploy and wired in ~/.ssh/authorized_keys as
#
#   command="/home/ubuntu/bin/dsa-prep-deploy",restrict ssh-ed25519 AAAA... dsa-prep-deploy
#
# so the key can do exactly one thing. CI runs
#
#   ssh ubuntu@host "deploy <commit-sha>" < source.tgz
#
# The archive is checked, the database backed up, the image rebuilt and restarted. If
# the app is not healthy within 90 s the previous image is put back and the run fails.
#
# docker-compose.yml is never taken from the archive: it holds the basic-auth labels and
# the volume mounts, so a leaked deploy key cannot remove the login or mount host paths.
# Change it on the server by hand. Updating this script is also manual (see README).
set -euo pipefail
exec 2>&1

APP_DIR=/home/ubuntu/dsa-prep
MAX_BYTES=$((50 * 1024 * 1024))
KEEP_BACKUPS=5
HEALTH_TRIES=30   # x 3 s

log() { printf '[deploy %s] %s\n' "$(date -u +%FT%TZ)" "$*"; }

if [[ ! "${SSH_ORIGINAL_COMMAND:-}" =~ ^deploy\ ([0-9a-f]{7,40})$ ]]; then
  log "refused: expected 'deploy <commit-sha>'"
  exit 2
fi
sha="${BASH_REMATCH[1]}"

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
head -c "$((MAX_BYTES + 1))" > "$tmp/src.tgz"
size=$(stat -c %s "$tmp/src.tgz")
(( size > 0 )) || { log "refused: empty archive"; exit 2; }
(( size <= MAX_BYTES )) || { log "refused: archive is over $MAX_BYTES bytes"; exit 2; }

tar -tvzf "$tmp/src.tgz" > "$tmp/long" 2>/dev/null || { log "refused: not a gzip tar archive"; exit 2; }
tar -tzf "$tmp/src.tgz" | sed 's|^\./||' > "$tmp/list"
if grep -q '^[lh]' "$tmp/long"; then log "refused: archive contains links"; exit 2; fi
if grep -Eq '^/|(^|/)\.\.(/|$)' "$tmp/list"; then log "refused: unsafe path in archive"; exit 2; fi
if grep -Eq '(^|/)\.env$|(^|/)\.git(/|$)' "$tmp/list"; then log "refused: archive contains .env or .git"; exit 2; fi
for required in Dockerfile backend/app/main.py frontend/dist/index.html; do
  grep -qx "$required" "$tmp/list" || { log "refused: archive lacks $required"; exit 2; }
done

log "deploying $sha ($size bytes)"
cd "$APP_DIR"

if docker ps --format '{{.Names}}' | grep -qx dsa-prep; then
  stamp=$(date -u +%Y%m%dT%H%M%SZ)
  docker exec -i dsa-prep python - "$stamp" "$KEEP_BACKUPS" <<'PY'
import pathlib, sqlite3, sys
stamp, keep = sys.argv[1], int(sys.argv[2])
src = sqlite3.connect("/data/dsa-prep.db")
dst = sqlite3.connect(f"/data/backup-deploy-{stamp}.db")
src.backup(dst)
dst.close()
src.close()
for old in sorted(pathlib.Path("/data").glob("backup-deploy-*.db"))[:-keep]:
    old.unlink()
PY
  log "database backed up as backup-deploy-$stamp.db"
  docker image tag dsa-prep:local dsa-prep:prev
fi

tar -xzf "$tmp/src.tgz" -C "$APP_DIR" --no-same-owner --exclude=./docker-compose.yml --exclude=docker-compose.yml
find "$APP_DIR" -name '._*' -delete
entry=$(tar -tzf "$tmp/src.tgz" | grep -E '^(\./)?docker-compose\.yml$' || true)
if [[ -n "$entry" ]]; then
  tar -xzOf "$tmp/src.tgz" "$entry" > "$tmp/compose.yml"
  cmp -s "$tmp/compose.yml" "$APP_DIR/docker-compose.yml" ||
    log "note: docker-compose.yml in the repo differs from the server's copy; it was NOT applied (apply it by hand)"
fi

docker compose build -q
docker compose up -d

healthy() {
  docker exec dsa-prep python -c \
    "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=3)" >/dev/null 2>&1
}

for _ in $(seq 1 "$HEALTH_TRIES"); do
  if healthy; then
    echo "$sha $(date -u +%FT%TZ)" >> "$APP_DIR/.deploys"
    log "healthy: $sha is live"
    exit 0
  fi
  sleep 3
done

log "not healthy after $((HEALTH_TRIES * 3)) s; recent container output:"
docker compose logs --no-color --tail 40 dsa-prep || true
if docker image inspect dsa-prep:prev >/dev/null 2>&1; then
  log "restoring the previous image"
  docker image tag dsa-prep:prev dsa-prep:local
  docker compose up -d --force-recreate
  for _ in $(seq 1 "$HEALTH_TRIES"); do
    if healthy; then log "previous image is serving again; $sha was NOT deployed"; exit 1; fi
    sleep 3
  done
  log "previous image is not healthy either; the site needs a manual look"
fi
exit 1
