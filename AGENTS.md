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
| `Docs/linux.md`, `Docs/macos.md` | Platform runbooks. |
| `Docs/udev/99-kvm-card-mini.rules` | Linux hidraw access. |

## Run

Python 3.10–3.13. Dependencies: `Client/pyproject.toml` + `Client/uv.lock`.

```bash
cd Client
uv sync
uv run python Mini-KVM.py
```

Windows-only packages (`pyWinhook`, `pywin32`) use `sys_platform == "win32"`.

macOS camera TCC is granted to the `.app`, not Terminal/Python:

```bash
cd Client
./compiler-macos.sh
open build_macos/Mini-KVM.app
```

Packaging group: `uv sync --group packaging` (Nuitka 4.2). Output bundle id `dev.kiramint.kvm-card-mini`. `QCameraPermission` / `QMicrophonePermission` are in `PySide6.QtCore`.

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
