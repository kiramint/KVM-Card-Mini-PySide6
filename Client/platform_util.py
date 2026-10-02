import os
import shutil
import sys

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtWidgets import QApplication, QDialog

IS_WINDOWS = sys.platform.startswith("win")
IS_LINUX = sys.platform.startswith("linux")
IS_MACOS = sys.platform == "darwin"

APP_DISPLAY_NAME = "KVM Card Mini"

_UNLIMITED = 16777215

# Title bar + size grip; CustomizeWindowHint clips buttons on macOS.
_RESIZABLE_DIALOG_FLAGS = (
    Qt.Dialog
    | Qt.WindowTitleHint
    | Qt.WindowSystemMenuHint
    | Qt.WindowMinMaxButtonsHint
    | Qt.WindowCloseButtonHint
    | Qt.WindowStaysOnTopHint
)


def apply_resizable_dialog(
    dialog,
    min_width=0,
    min_height=0,
    default_width=None,
    default_height=None,
):
    """Unlock a child dialog so the user can grow its height (and width)."""
    dialog.setWindowFlags(_RESIZABLE_DIALOG_FLAGS)
    if isinstance(dialog, QDialog):
        dialog.setSizeGripEnabled(True)
    dialog.setMaximumSize(QSize(_UNLIMITED, _UNLIMITED))
    cur_min = dialog.minimumSize()
    width_min = max(int(min_width or 0), max(cur_min.width(), 0))
    height_min = max(int(min_height or 0), max(cur_min.height(), 0))
    if width_min or height_min:
        dialog.setMinimumSize(QSize(width_min, height_min))
    width = dialog.width()
    height = dialog.height()
    if default_width is not None:
        width = max(int(default_width), width_min)
    elif width_min:
        width = max(width, width_min)
    if default_height is not None:
        height = max(int(default_height), height_min)
    elif height_min:
        height = max(height, height_min)
    dialog.resize(width, height)


def is_bundled() -> bool:
    return bool(getattr(sys, "frozen", False) or globals().get("__compiled__"))


def user_data_dir() -> str:
    """Writable config/log directory.

    Linux AppImage and packaged macOS apps live on a read-only filesystem,
    so config cannot sit next to the executable the way it does in the
    Windows onefile and source-tree layouts.
    """
    if IS_LINUX:
        path = os.path.join(
            os.path.expanduser("~"), ".local", "share", "mini-kvm"
        )
        os.makedirs(path, exist_ok=True)
        return path
    if is_bundled() and IS_MACOS:
        path = os.path.join(
            os.path.expanduser("~"),
            "Library",
            "Application Support",
            APP_DISPLAY_NAME,
        )
        os.makedirs(path, exist_ok=True)
        return path
    return os.path.dirname(os.path.abspath(sys.argv[0]))


def qt_platform_name() -> str:
    app = QGuiApplication.instance()
    if app is None:
        return ""
    try:
        return app.platformName().lower()
    except Exception:
        return ""


def is_wayland() -> bool:
    return qt_platform_name() == "wayland"


def relative_mouse_warp_supported() -> bool:
    """QCursor.setPos is ignored by most Wayland compositors."""
    return not is_wayland()


def resolve_data_dir(base_dir: str) -> str:
    """Nuitka packages Data as data; the source tree keeps Data."""
    try:
        for name in os.listdir(base_dir):
            if name.lower() == "data":
                candidate = os.path.join(base_dir, name)
                if os.path.isdir(candidate):
                    return candidate
    except OSError:
        pass
    return os.path.join(base_dir, "data")


def ui_font() -> QFont:
    font = QFont()
    font.setBold(True)
    return font


def restart_current_process():
    from PySide6.QtCore import QProcess

    QProcess.startDetached(sys.executable, sys.argv)
    QApplication.quit()


def popen_first_available(commands) -> bool:
    for cmd in commands:
        exe = cmd.split()[0]
        if shutil.which(exe):
            os.popen(cmd)
            return True
    return False


WINDOWS_TOOLS = {
    0: ["osk"],
    1: ["calc"],
    2: ["SnippingTool"],
    3: ["notepad"],
    4: ["rundll32.exe shell32.dll, Control_RunDLL mmsys.cpl"],
    5: ["devmgmt.msc"],
}

LINUX_TOOLS = {
    1: ["gnome-calculator", "kcalc", "galculator", "qalculate"],
    2: [
        "flameshot gui",
        "spectacle",
        "gnome-screenshot",
        "xfce4-screenshooter",
        "grim",
    ],
    3: ["gedit", "kate", "mousepad", "xed", "leafpad"],
}

MACOS_TOOLS = {
    1: ["open -a Calculator"],
    2: ["screencapture -i -c"],
    3: ["open -a TextEdit"],
}


def launch_tool(index: int) -> bool:
    if IS_WINDOWS:
        commands = WINDOWS_TOOLS.get(index, [])
        if not commands:
            return False
        # Windows tools are often shell-resolved (.msc), not PATH executables.
        os.popen(commands[0])
        return True
    if IS_MACOS:
        return popen_first_available(MACOS_TOOLS.get(index, []))
    return popen_first_available(LINUX_TOOLS.get(index, []))
