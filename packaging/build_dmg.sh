#!/usr/bin/env bash
# Build Ratebar.app with PyInstaller, then package it into a drag-to-install .dmg.
# Output: packaging/dist/Ratebar.app and packaging/dist/Ratebar.dmg
# Usage: packaging/build_dmg.sh
set -euo pipefail

cd "$(dirname "$0")"   # packaging/

echo "==> Cleaning previous build"
rm -rf build dist

echo "==> Building .app with PyInstaller"
uv run pyinstaller --noconfirm ratebar.spec

APP="dist/Ratebar.app"
DMG="dist/Ratebar.dmg"
[ -d "$APP" ] || { echo "ERROR: $APP not produced"; exit 1; }

echo "==> Staging .dmg contents"
STAGE="$(mktemp -d)"
cp -R "$APP" "$STAGE/"
ln -s /Applications "$STAGE/Applications"   # drag-to-install target

echo "==> Creating $DMG"
rm -f "$DMG"
hdiutil create -volname "Ratebar" -srcfolder "$STAGE" -ov -format UDZO "$DMG" >/dev/null
rm -rf "$STAGE"

echo "==> Done"
ls -lh "$DMG"
