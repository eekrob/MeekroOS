#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="0.1.0"
DEST="${1:-${ROOT}/dist}"
mkdir -p "$DEST"
TEMP="$(mktemp -d)"
trap 'rm -rf "$TEMP"' EXIT
mkdir -p "$TEMP/meekro-welcome-$VERSION"
for item in meekro assets branding desktop scripts packaging pyproject.toml README.md LICENSE; do
  cp -a "$ROOT/$item" "$TEMP/meekro-welcome-$VERSION/"
done
find "$TEMP" -type d -name __pycache__ -prune -exec rm -rf {} +
tar -C "$TEMP" -czf "$DEST/meekro-welcome-$VERSION.tar.gz" "meekro-welcome-$VERSION"
printf 'Created %s\n' "$DEST/meekro-welcome-$VERSION.tar.gz"
