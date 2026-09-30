# AGENTS.md

Notes for agents working in this repository.

## Scope

- Desktop client lives in `Client/`. That is the usual change surface.
- Leave `Firmware/` and `Server_Standalone/` alone unless the user asks.
- Do not change `Server_Standalone` listen ports to match the client. The client web UI default is **5001**; the standalone server still defaults to **5000**.

## Layout

| Path | Role |
|------|------|
| `Client/Mini-KVM.py` | Entry. Wraps `main.py` and writes `error.log`. |
| `Client/main.py` | Main window, HID, camera, child dialogs. |
| `Client/about_dialog.py` | Multi-page About dialog. |
| `Client/platform_util.py` | OS helpers, config dir, resizable-dialog flags. |
| `Client/input_map.py` | Key mapping and `SYSTEM_SHORTCUTS`. |
| `Client/hid_def.py` | HID open: Windows cfgmgr32 paths; Linux/macOS `hid.open(vid, pid)`. |
| `Client/ui/` | Qt Designer `.ui` plus generated `*_ui.py`. Edit both. |
| `Client/Data/` | Keyboard maps and images. Bundled as `data`. |
| `Client/compiler-macos.sh` | Nuitka macOS .app (Apple Silicon). |
| `Client/compiler-linux.sh` | Nuitka Linux standalone (host arch). |
| `Client/compiler-windows.ps1` | Nuitka Windows standalone (host arch). `compiler.ps1` forwards here. |
| `Docs/linux.md`, `Docs/macos.md` | Platform runbooks. |
| `Docs/udev/99-kvm-card-mini.rules` | Linux hidraw access. |
| `.github/workflows/build.yml` | Multi-arch client builds on push. |

## Run

Python 3.10–3.13. Dependencies: `Client/pyproject.toml` + `Client/uv.lock`.

```bash
cd Client
uv sync
uv run python Mini-KVM.py
```

Windows-only packages: `pywin32` is `sys_platform == "win32"`; `pyWinhook` is also `platform_machine == "AMD64"` (wheels exist for cp310/cp311 win_amd64 only). On Windows ARM64 the System hook menu is hidden.

Packaging is Nuitka standalone via `uv sync --group packaging`. Scripts pin Python 3.11 on Windows (pyWinhook wheels) and 3.12 on Linux/macOS (`PYTHON_VERSION` overrides).

```bash
cd Client
./compiler-macos.sh          # build_macos/*.app  (Apple Silicon)
./compiler-linux.sh          # build_linux/*.dist (INSTALL_DEPS=1 on Ubuntu)
pwsh -File compiler-windows.ps1
```

macOS camera TCC is granted to the `.app`, not Terminal/Python. Bundle id `dev.kiramint.kvm-card-mini`. `QCameraPermission` / `QMicrophonePermission` are in `PySide6.QtCore`.

GitHub Actions: `.github/workflows/build.yml` on push / `workflow_dispatch`. Native runners: `windows-latest`, `windows-11-arm`, `ubuntu-24.04`, `ubuntu-24.04-arm`, `macos-15`. Artifacts: `KVM-Card-Mini-{windows-amd64,windows-arm64,linux-amd64,linux-arm64,macos-arm64}`.

## Conventions

- Capture-card HID is VID `0x413D` PID `0x2107`, usage page `0xFF00`. Video is UVC.
- Client KVM web port default is `kvmSetPortSpin` in `Client/ui/main.ui` and `Client/ui/main_ui.py` (**5001**). macOS AirPlay occupies 5000.
- Bundled macOS config and `error.log` go to `~/Library/Application Support/KVM Card Mini/` via `user_data_dir()`.
- Source data dir is `Client/Data` (also accepts `data/`). Nuitka packages it as `data`.
- Child dialogs must stay height-resizable: `apply_resizable_dialog()` in `platform_util.py`. Do not lock height with `setFixedHeight`, `setMaximumHeight`, or `Qt.CustomizeWindowHint`.
- About menu opens `AboutDialog`. Credits: Jackadminx, ElluIFX, https://github.com/kiramint/, Grok (xAI). Do not put the two original authors back as standalone menu links.
- Global system hook is Windows-only. Linux/macOS use in-window input plus **Keyboard → System shortcuts**.
- Mouse hover on macOS: Qt6 `QVideoWidget` uses a native renderer that swallows hover `MouseMove` (clicks still bubble). Keep `MouseCaptureLayer` as a **sibling** on `viewport_host` with `WA_AlwaysStackOnTop` + `WA_NativeWindow`. Do not parent the overlay inside `QVideoWidget`, and do not use a stylesheet with window opacity ~0 (Cocoa skips hit-testing). While capture is on, `mouse_report_timeout` also samples `QCursor.pos()` so tracking still works if Qt drops hover events.
- UI strings are English in source; Chinese is `Client/trans_cn.ts` → `trans_cn.qm`. After string changes: `pyside6-lupdate` then `pyside6-lrelease`.
- Importing `Client/main.py` without a trailing `debug` argv swallows stdout. Offscreen smoke tests should pass `debug` and set `QT_QPA_PLATFORM=offscreen`.

## Input notes

- Windows HID open lists paths with cfgmgr32; do not enumerate every HID device (causes keyboard stutter).
- Linux hidapi often reports `usage_page` 0.
- `hid.open` without the card raises `OSError` quickly on macOS.
- `relative_mouse_warp_supported()` is false on Wayland (`QCursor.setPos` is ignored).
- Qt on macOS often returns `nativeScanCode() == 0`; mapping uses `nativeVirtualKey()`.
