#!/bin/bash
set -e

APP_NAME="Clocker"
DMG_NAME="Clocker-macOS.dmg"
ENTRY_POINT="clock_app.py"

echo "=================================================="
echo "      BUILDING & PACKAGING ${APP_NAME}"
echo "=================================================="

# 1. Check for create-dmg dependency
if ! command -v create-dmg &> /dev/null; then
    echo "❌ Error: 'create-dmg' is not installed."
    echo "👉 Install it using: brew install create-dmg"
    exit 1
fi

# 2. Clean previous build artifacts
echo "🧹 Cleaning previous build directories..."
rm -rf build dist

# 3. Build .app bundle with PyInstaller
echo "⚙️  Building ${APP_NAME}.app bundle..."
pyinstaller --name "${APP_NAME}" \
            --windowed \
            --noconsole \
            --clean \
            --hidden-import Foundation \
            --hidden-import AppKit \
            "${ENTRY_POINT}"

# 4. Create DMG output directory
mkdir -p dist/dmg
test -f "dist/dmg/${DMG_NAME}" && rm "dist/dmg/${DMG_NAME}"

# 5. Generate .dmg disk image
echo "📦 Generating ${DMG_NAME}..."
create-dmg \
  --volname "${APP_NAME} Installer" \
  --window-pos 200 120 \
  --window-size 600 400 \
  --icon-size 100 \
  --icon "${APP_NAME}.app" 160 190 \
  --hide-extension "${APP_NAME}.app" \
  --app-drop-link 440 190 \
  "dist/dmg/${DMG_NAME}" \
  "dist/${APP_NAME}.app"

echo "=================================================="
echo "✅ BUILD SUCCESSFUL!"
echo "👉 Ready at: dist/dmg/${DMG_NAME}"
echo "=================================================="
