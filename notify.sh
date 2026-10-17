#!/usr/bin/env bash
# Post today's digest to Telegram. Silent when nothing is due.
#
# The digest is fetched with `docker exec`, not over the network, for two reasons:
# the container's IP changes every time it is recreated, and the public routes need
# a signed-in account that a cron job has no business holding a password for.
#
# Secrets come from /etc/dsa-prep.env (mode 600), never from argv, so they never
# appear in ps output. Expects: DIGEST_TOKEN, DIGEST_USER (the account to summarise),
# TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID.
set -euo pipefail

ENV_FILE="${DSA_PREP_ENV:-/etc/dsa-prep.env}"
CONTAINER="${DSA_PREP_CONTAINER:-dsa-prep}"

if [[ ! -r "$ENV_FILE" ]]; then
  echo "cannot read $ENV_FILE" >&2
  exit 1
fi
# shellcheck disable=SC1090
source "$ENV_FILE"

: "${DIGEST_TOKEN:?missing}" "${DIGEST_USER:?missing}" "${TELEGRAM_BOT_TOKEN:?missing}" "${TELEGRAM_CHAT_ID:?missing}"

digest=$(docker exec -e T="$DIGEST_TOKEN" -e U="$DIGEST_USER" "$CONTAINER" python -c '
import os, urllib.parse, urllib.request
url = "http://127.0.0.1:8080/digest?" + urllib.parse.urlencode({"token": os.environ["T"], "user": os.environ["U"]})
print(urllib.request.urlopen(url, timeout=10).read().decode(), end="")
')

# The first line is always the date header. Nothing after it means nothing is due,
# and a notification that fires on an empty day just trains you to ignore it.
if [[ $(printf '%s' "$digest" | grep -c '[^[:space:]]') -le 1 ]]; then
  echo "$(date -Is) nothing due, staying quiet"
  exit 0
fi

curl -fsS --max-time 10 -o /dev/null \
  "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
  --data-urlencode "text=${digest}" \
  --data-urlencode "disable_web_page_preview=true"

echo "$(date -Is) sent"
