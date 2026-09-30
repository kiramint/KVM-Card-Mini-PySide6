#!/usr/bin/env bash
# Build a signed-enough macOS .app so Camera/Microphone TCC prompts work.
set -euo pipefail

cd "$(dirname "$0")"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This script only runs on macOS." >&2
  exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required. Install: https://docs.astral.sh/uv/" >&2
  exit 1
fi

if [[ ! -f icons/icon.icns ]]; then
  echo "Missing icons/icon.icns" >&2
  exit 1
fi

PYTHON_VERSION="${PYTHON_VERSION:-3.12}"

DATA_SRC=Data
if [[ ! -d "$DATA_SRC" && -d data ]]; then
  DATA_SRC=data
fi
if [[ ! -d "$DATA_SRC" ]]; then
  echo "Missing Data/ (or data/) directory" >&2
  exit 1
fi

uv python install "$PYTHON_VERSION"
uv sync --group packaging --python "$PYTHON_VERSION"

JOBS="$(sysctl -n hw.ncpu 2>/dev/null || echo 4)"
OUT_DIR=build_macos
APP_NAME="KVM Card Mini"
BUNDLE_ID="dev.kiramint.kvm-card-mini"

if [[ -d "$OUT_DIR" ]]; then
  chmod -R u+w "$OUT_DIR" 2>/dev/null || true
  rm -rf "$OUT_DIR"
fi
mkdir -p "$OUT_DIR"

uv run --python "$PYTHON_VERSION" --group packaging python -m nuitka \
  --standalone \
  --macos-create-app-bundle \
  --macos-app-mode=gui \
  --macos-app-console-mode=disable \
  --macos-app-name="$APP_NAME" \
  --macos-signed-app-name="$BUNDLE_ID" \
  --macos-app-version=0.1.0 \
  --macos-app-icon=icons/icon.icns \
  --macos-app-protected-resource="NSCameraUsageDescription:KVM Card Mini needs the HDMI capture card (camera) to show the remote display." \
  --macos-app-protected-resource="NSMicrophoneUsageDescription:KVM Card Mini needs the capture card audio input if you enable audio passthrough." \
  --enable-plugin=pyside6 \
  --include-qt-plugins=multimedia \
  --include-data-dir=icons=icons \
  --include-data-dir=web=web \
  --include-data-dir=web_s=web_s \
  --include-data-dir="${DATA_SRC}=data" \
  --include-data-files=trans_cn.qm=trans_cn.qm \
  --include-data-files=qtbase_cn.qm=qtbase_cn.qm \
  --include-module=hid \
  --nofollow-import-to=pythoncom \
  --nofollow-import-to=pyWinhook \
  --nofollow-import-to=win32api \
  --nofollow-import-to=win32con \
  --nofollow-import-to=win32gui \
  --nofollow-import-to=pywintypes \
  --output-dir="$OUT_DIR" \
  --output-filename="KVM-Card-Mini" \
  --jobs="$JOBS" \
  --lto=no \
  --assume-yes-for-downloads \
  --noinclude-qt-translations \
  --noinclude-dlls=libQt6Charts* \
  --noinclude-dlls=libQt6Quick3D* \
  --noinclude-dlls=libQt6Sensors* \
  --noinclude-dlls=libQt6Test* \
  --noinclude-dlls=libQt6WebEngine* \
  --noinclude-dlls=qt6web* \
  --noinclude-dlls=qt6pdf* \
  Mini-KVM.py

APP_PATH=""
for candidate in \
  "$OUT_DIR/$APP_NAME.app" \
  "$OUT_DIR/KVM-Card-Mini.app" \
  "$OUT_DIR/Mini-KVM.app"
do
  if [[ -d "$candidate" ]]; then
    APP_PATH="$candidate"
    break
  fi
done

if [[ -z "$APP_PATH" ]]; then
  echo "Nuitka finished but no .app bundle was found in $OUT_DIR" >&2
  ls -la "$OUT_DIR" >&2
  exit 1
fi

# Ad-hoc sign so Apple Silicon will actually launch the bundle.
codesign --force --deep --sign - "$APP_PATH"

printf '%s' "$APP_PATH" >"$OUT_DIR/.build-output"

echo
echo "Built: $APP_PATH"
echo "Open with: open \"$APP_PATH\""
echo "Camera permission is granted to this .app, not to Terminal/Python."
echo "Config/logs: ~/Library/Application Support/KVM Card Mini"
