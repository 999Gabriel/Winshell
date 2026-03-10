#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

APP_NAME="WinShell"
VERSION="${VERSION:-0.1.0}"
BUILD_DIR="$ROOT_DIR/build/macos"
DIST_DIR="$ROOT_DIR/dist"
RELEASE_DIR="$ROOT_DIR/release"
VENV_DIR="$ROOT_DIR/.build-venv"
ICON_ICNS="$ROOT_DIR/assets/WinShell.icns"
ICON_JPG="$ROOT_DIR/assets/winshell_app_icon.jpg"
RUNTIME_SPEC="$ROOT_DIR/packaging/macos/winshell_runtime.spec"
LAUNCHER_SCRIPT="$ROOT_DIR/packaging/macos/launcher.applescript"

mkdir -p "$BUILD_DIR" "$DIST_DIR" "$RELEASE_DIR"

if [[ ! -d "$VENV_DIR" ]]; then
  python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip >/dev/null
python -m pip install -r requirements.txt pyinstaller >/dev/null

rm -rf build dist
pyinstaller --noconfirm --clean "$RUNTIME_SPEC"
mkdir -p "$BUILD_DIR"

RUNTIME_BIN="$ROOT_DIR/dist/winshell-runtime"
if [[ ! -x "$RUNTIME_BIN" ]]; then
  echo "Runtime binary missing: $RUNTIME_BIN" >&2
  exit 1
fi

APP_DIR="$BUILD_DIR/${APP_NAME}.app"
rm -rf "$APP_DIR"
osacompile -o "$APP_DIR" "$LAUNCHER_SCRIPT"

mkdir -p "$APP_DIR/Contents/Resources"
cp "$RUNTIME_BIN" "$APP_DIR/Contents/Resources/winshell-runtime"
chmod +x "$APP_DIR/Contents/Resources/winshell-runtime"

if [[ -f "$ICON_ICNS" ]]; then
  cp "$ICON_ICNS" "$APP_DIR/Contents/Resources/applet.icns"
fi

cat > "$APP_DIR/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleDisplayName</key><string>${APP_NAME}</string>
  <key>CFBundleExecutable</key><string>applet</string>
  <key>CFBundleIdentifier</key><string>ai.openclaw.winshell</string>
  <key>CFBundleName</key><string>${APP_NAME}</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleShortVersionString</key><string>${VERSION}</string>
  <key>CFBundleVersion</key><string>${VERSION}</string>
  <key>CFBundleIconFile</key><string>applet</string>
  <key>LSMinimumSystemVersion</key><string>12.0</string>
</dict>
</plist>
PLIST

SIGN_IDENTITY="${CODESIGN_IDENTITY:--}"
codesign --deep --force --verify --verbose --sign "$SIGN_IDENTITY" "$APP_DIR"

DMG_BG_PNG="$BUILD_DIR/dmg-background.png"
sips -s format png "$ICON_JPG" --out "$DMG_BG_PNG" >/dev/null 2>&1 || true

DMG_PATH="$RELEASE_DIR/${APP_NAME}-${VERSION}-macos-arm64.dmg"
rm -f "$DMG_PATH"

DMG_ARGS=(
  --volname "${APP_NAME} Installer"
  --window-pos 200 120
  --window-size 900 540
  --icon-size 110
  --icon "${APP_NAME}.app" 220 280
  --app-drop-link 680 280
  --hide-extension "${APP_NAME}.app"
  --no-internet-enable
)

if [[ -f "$DMG_BG_PNG" ]]; then
  DMG_ARGS+=(--background "$DMG_BG_PNG")
fi

create-dmg "${DMG_ARGS[@]}" "$DMG_PATH" "$APP_DIR"

if [[ -n "${NOTARY_KEYCHAIN_PROFILE:-}" && -n "${CODESIGN_IDENTITY:-}" ]]; then
  xcrun notarytool submit "$DMG_PATH" --keychain-profile "$NOTARY_KEYCHAIN_PROFILE" --wait
  xcrun stapler staple "$APP_DIR"
fi

echo "Built app: $APP_DIR"
echo "Built dmg: $DMG_PATH"
