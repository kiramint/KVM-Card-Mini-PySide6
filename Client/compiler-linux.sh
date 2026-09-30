#!/usr/bin/env bash
# Build a Nuitka standalone Linux client (amd64 or arm64, matching the host).
set -euo pipefail

cd "$(dirname "$0")"

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "This script only runs on Linux." >&2
  exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required. Install: https://docs.astral.sh/uv/" >&2
  exit 1
fi

PYTHON_VERSION="${PYTHON_VERSION:-3.12}"
INSTALL_DEPS="${INSTALL_DEPS:-0}"

if [[ "$INSTALL_DEPS" == "1" ]]; then
  if ! command -v sudo >/dev/null 2>&1; then
    echo "INSTALL_DEPS=1 needs sudo." >&2
    exit 1
  fi
  sudo apt-get update
  sudo apt-get install -y --no-install-recommends \
    build-essential \
    ccache \
    patchelf \
    pkg-config \
    libhidapi-hidraw0 \
    libhidapi-libusb0 \
    libhidapi-dev \
    libgl1 \
    libegl1 \
    libfontconfig1 \
    libdbus-1-3 \
    libxcb-cursor0 \
    libxkbcommon-x11-0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-render-util0 \
    libxcb-xkb1 \
    libxcb-shape0 \
    libxcb-randr0 \
    libxcb-xinerama0 \
    libxcb-sync1 \
    libx11-xcb1 \
    libglib2.0-0 \
    libdrm2 \
    libgbm1 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-libav \
    libgstreamer1.0-0 \
    libgstreamer-plugins-base1.0-0
fi

if ! command -v gcc >/dev/null 2>&1 || ! command -v g++ >/dev/null 2>&1; then
  echo "gcc and g++ are required. On Debian/Ubuntu: sudo apt install build-essential" >&2
  echo "Or rerun with INSTALL_DEPS=1" >&2
  exit 1
fi

if ! command -v patchelf >/dev/null 2>&1; then
  echo "patchelf is required. On Debian/Ubuntu: sudo apt install patchelf" >&2
  echo "Or rerun with INSTALL_DEPS=1" >&2
  exit 1
fi

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

JOBS="$(nproc 2>/dev/null || echo 4)"
OUT_DIR=build_linux

if [[ -d "$OUT_DIR" ]]; then
  chmod -R u+w "$OUT_DIR" 2>/dev/null || true
  rm -rf "$OUT_DIR"
fi
mkdir -p "$OUT_DIR"

uv run --python "$PYTHON_VERSION" --group packaging python -m nuitka \
  --standalone \
  --static-libpython=no \
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

DIST_PATH=""
for candidate in \
  "$OUT_DIR/Mini-KVM.dist" \
  "$OUT_DIR/KVM-Card-Mini.dist"
do
  if [[ -d "$candidate" ]]; then
    DIST_PATH="$candidate"
    break
  fi
done

if [[ -z "$DIST_PATH" ]]; then
  echo "Nuitka finished but no .dist folder was found in $OUT_DIR" >&2
  ls -la "$OUT_DIR" >&2
  exit 1
fi

BIN_PATH="$DIST_PATH/KVM-Card-Mini"
if [[ ! -x "$BIN_PATH" ]]; then
  if [[ -f "$BIN_PATH" ]]; then
    chmod +x "$BIN_PATH"
  elif [[ -f "$DIST_PATH/Mini-KVM" ]]; then
    BIN_PATH="$DIST_PATH/Mini-KVM"
    chmod +x "$BIN_PATH"
  fi
fi

printf '%s' "$DIST_PATH" >"$OUT_DIR/.build-output"

echo
echo "Built: $BIN_PATH"
echo "Dist:  $DIST_PATH"
echo "Runtime still needs system hidapi and (for video) GStreamer plugins. See Docs/linux.md."
