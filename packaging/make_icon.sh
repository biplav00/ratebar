#!/usr/bin/env bash
# Generate packaging/ratebar.icns from the ring-gauge master (make_icon.py).
# Usage: packaging/make_icon.sh
set -euo pipefail
cd "$(dirname "$0")"   # packaging/

MASTER="/tmp/ratebar_icon.png"
ICONSET="$(mktemp -d)/ratebar.iconset"
mkdir -p "$ICONSET"

echo "==> Rendering master PNG"
uv run python make_icon.py "$MASTER"

echo "==> Building iconset (all required sizes)"
for size in 16 32 128 256 512; do
  sips -z "$size" "$size" "$MASTER" --out "$ICONSET/icon_${size}x${size}.png" >/dev/null
  d=$((size * 2))
  sips -z "$d" "$d" "$MASTER" --out "$ICONSET/icon_${size}x${size}@2x.png" >/dev/null
done

echo "==> Assembling ratebar.icns"
iconutil -c icns "$ICONSET" -o ratebar.icns
rm -rf "$(dirname "$ICONSET")"
echo "==> Done: $(pwd)/ratebar.icns"
ls -lh ratebar.icns
