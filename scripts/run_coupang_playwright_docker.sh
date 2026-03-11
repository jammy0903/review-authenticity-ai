#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_NAME="review-authenticity-ai-playwright"
HOST_URL_FILE="${1:-$ROOT_DIR/data/raw/coupang_seed_urls.txt}"
HOST_OUTPUT_DIR="${2:-$ROOT_DIR/data/raw/coupang_saved_html}"
HOST_COOKIES_FILE="${3:-}"
HOST_STORAGE_STATE_FILE="${4:-}"
CONTAINER_URL_FILE="/workspace/${HOST_URL_FILE#$ROOT_DIR/}"
CONTAINER_OUTPUT_DIR="/workspace/${HOST_OUTPUT_DIR#$ROOT_DIR/}"
CONTAINER_COOKIES_FILE=""
CONTAINER_STORAGE_STATE_FILE=""

if [[ -n "$HOST_COOKIES_FILE" ]]; then
  CONTAINER_COOKIES_FILE="/workspace/${HOST_COOKIES_FILE#$ROOT_DIR/}"
fi

if [[ -n "$HOST_STORAGE_STATE_FILE" ]]; then
  CONTAINER_STORAGE_STATE_FILE="/workspace/${HOST_STORAGE_STATE_FILE#$ROOT_DIR/}"
fi

docker build -f "$ROOT_DIR/docker/playwright.Dockerfile" -t "$IMAGE_NAME" "$ROOT_DIR"

docker run --rm \
  -v "$ROOT_DIR:/workspace" \
  -w /workspace \
  "$IMAGE_NAME" \
  node scripts/fetch_coupang_urls_playwright.js \
  "$CONTAINER_URL_FILE" \
  "$CONTAINER_OUTPUT_DIR" \
  "$CONTAINER_COOKIES_FILE" \
  "$CONTAINER_STORAGE_STATE_FILE"
