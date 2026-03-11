#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
URL_FILE="${1:-$ROOT_DIR/data/raw/coupang_seed_urls.txt}"
HTML_DIR="${2:-$ROOT_DIR/data/raw/coupang_saved_html}"
RAW_OUTPUT="${3:-$ROOT_DIR/data/raw/raw_reviews.csv}"
CDP_ENDPOINT="${4:-http://127.0.0.1:9222}"
MAX_PAGES="${5:-10}"
SLEEP_SECONDS="${6:-1800}"
LOG_FILE="${7:-$ROOT_DIR/data/raw/coupang_cdp_loop.log}"
NODE_BIN="${NODE_BIN:-/home/jammy/.nvm/versions/node/v22.22.0/bin/node}"
LOCK_DIR="${ROOT_DIR}/data/raw/.coupang_cdp_loop.lock"

mkdir -p "$(dirname "$LOG_FILE")" "$HTML_DIR"

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "Loop already running: $LOCK_DIR" >&2
  exit 1
fi

cleanup() {
  rmdir "$LOCK_DIR" 2>/dev/null || true
}

trap cleanup EXIT INT TERM

while true; do
  {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] fetch start"
    "$NODE_BIN" "$ROOT_DIR/scripts/fetch_coupang_urls_from_cdp.js" \
      "$URL_FILE" \
      "$HTML_DIR" \
      "$CDP_ENDPOINT" \
      "$MAX_PAGES"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] merge start"
    python3 "$ROOT_DIR/scripts/merge_coupang_raw.py" \
      --html-dir "$HTML_DIR" \
      --html-glob 'coupang_*_cdp_page_*.html' \
      --output "$RAW_OUTPUT"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] cycle done"
  } >>"$LOG_FILE" 2>&1

  sleep "$SLEEP_SECONDS"
done
