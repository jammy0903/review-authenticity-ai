#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_NAME="review-authenticity-ai-python-ml"

docker build -f "$ROOT_DIR/docker/python-ml.Dockerfile" -t "$IMAGE_NAME" "$ROOT_DIR"

docker run --rm \
  -v "$ROOT_DIR:/workspace" \
  -w /workspace \
  "$IMAGE_NAME" \
  python scripts/run_baseline_pipeline.py
