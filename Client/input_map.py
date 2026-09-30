"""Translate Qt key events into PC/AT Set-1 scancodes.

The HID layer (`keyboard_scancode2hid.yml`) expects Windows Set-1 codes.
Qt reports different native values on each platform:

- Windows: hardware Set-1 scancode
- Linux X11 (xcb): XKB keycode = Linux evdev + 8
- Linux Wayland: Linux evdev keycode
- macOS: nativeScanCode() is often 0; use nativeVirtualKey()
"""

from loguru import logger

from platform_util import IS_LINUX, IS_MACOS, qt_platform_name

# Extended evdev keys whose Set-1 encoding uses the 0xE0 prefix (stored as 0x01xx).
LINUX_EVDEV_TO_SET1 = {
    96: 0x011C,  # Keypad Enter
    97: 0x011D,  # Right Ctrl
    98: 0x0135,  # Keypad /
    99: 0x0137,  # Print Screen
    100: 0x0138,  # Right Alt
    102: 0x0147,  # Home
    103: 0x0148,  # Up
    104: 0x0149,  # Page Up
    105: 0x014B,  # Left
    106: 0x014D,  # Right
    107: 0x014F,  # End
    108: 0x0150,  # Down
    109: 0x0151,  # Page Down
    110: 0x0152,  # Insert
    111: 0x0153,  # Delete
    125: 0x015B,  # Left Super
    126: 0x015C,  # Right Super
    127: 0x015D,  # Menu
    139: 0x015D,  # Menu (alternate)
}

# Apple virtual key code -> PC/AT Set-1.
# Letter VKs are not ASCII-ordered; keep the whole table.
MACOS_VIRTUALKEY_TO_SET1 = {
    0x00: 0x1E,  # A
    0x01: 0x1F,  # S
    0x02: 0x20,  # D
    0x03: 0x21,  # F
    0x04: 0x23,  # H
    0x05: 0x22,  # G
    0x06: 0x2C,  # Z
    0x07: 0x2D,  # X
    0x08: 0x2E,  # C
    0x09: 0x2F,  # V
    0x0B: 0x30,  # B
    0x0C: 0x10,  # Q
    0x0D: 0x11,  # W
    0x0E: 0x12,  # E
    0x0F: 0x13,  # R
    0x10: 0x15,  # Y
    0x11: 0x14,  # T
    0x1F: 0x18,  # O
    0x20: 0x16,  # U
    0x22: 0x17,  # I
    0x23: 0x19,  # P
    0x25: 0x26,  # L
    0x26: 0x24,  # J
    0x28: 0x25,  # K
    0x2D: 0x31,  # N
    0x2E: 0x32,  # M
    0x12: 0x02,  # 1
    0x13: 0x03,  # 2
    0x14: 0x04,  # 3
    0x15: 0x05,  # 4
    0x17: 0x06,  # 5
    0x16: 0x07,  # 6
    0x1A: 0x08,  # 7
    0x1C: 0x09,  # 8
    0x19: 0x0A,  # 9
    0x1D: 0x0B,  # 0
    0x1B: 0x0C,  # -
    0x18: 0x0D,  # =
    0x21: 0x1A,  # [
    0x1E: 0x1B,  # ]
    0x29: 0x27,  # ;
    0x27: 0x28,  # '
    0x32: 0x29,  # `
    0x2A: 0x2B,  # backslash
    0x2B: 0x33,  # ,
    0x2F: 0x34,  # .
    0x2C: 0x35,  # /
    0x24: 0x1C,  # Return
    0x30: 0x0F,  # Tab
    0x31: 0x39,  # Space
    0x33: 0x0E,  # Mac Delete -> PC Backspace
    0x35: 0x01,  # Escape
    0x39: 0x3A,  # Caps Lock
    0x38: 0x002A,  # Left Shift
    0x3C: 0x0036,  # Right Shift
    0x3B: 0x001D,  # Left Control
    0x3E: 0x011D,  # Right Control
    0x3A: 0x0038,  # Left Option -> Left Alt
    0x3D: 0x0138,  # Right Option -> Right Alt
    0x37: 0x015B,  # Left Command -> Left Windows
    0x36: 0x015C,  # Right Command -> Right Windows
    0x7A: 0x3B,  # F1
    0x78: 0x3C,  # F2
    0x63: 0x3D,  # F3
    0x76: 0x3E,  # F4
    0x60: 0x3F,  # F5
    0x61: 0x40,  # F6
    0x62: 0x41,  # F7
    0x64: 0x42,  # F8
    0x65: 0x43,  # F9
    0x6D: 0x44,  # F10
    0x67: 0x57,  # F11
    0x6F: 0x58,  # F12
    0x72: 0x0152,  # Help -> Insert
    0x73: 0x0147,  # Home
    0x74: 0x0149,  # Page Up
    0x75: 0x0153,  # Forward Delete
    0x77: 0x014F,  # End
    0x79: 0x0151,  # Page Down
    0x7B: 0x014B,  # Left
    0x7C: 0x014D,  # Right
    0x7D: 0x0150,  # Down
    0x7E: 0x0148,  # Up
    0x41: 0x53,  # keypad .
    0x43: 0x37,  # keypad *
    0x45: 0x4E,  # keypad +
    0x47: 0x45,  # Clear -> Num Lock
    0x4B: 0x0135,  # keypad /
    0x4C: 0x011C,  # keypad Enter
    0x4E: 0x4A,  # keypad -
    0x52: 0x52,  # keypad 0
    0x53: 0x4F,  # keypad 1
    0x54: 0x50,  # keypad 2
    0x55: 0x51,  # keypad 3
    0x56: 0x4B,  # keypad 4
    0x57: 0x4C,  # keypad 5
    0x58: 0x4D,  # keypad 6
    0x59: 0x47,  # keypad 7
    0x5B: 0x48,  # keypad 8
    0x5C: 0x49,  # keypad 9
}


def _linux_native_to_set1(scancode: int) -> int:
    platform = qt_platform_name()
    if platform == "wayland":
        evdev_code = scancode
    else:
        # xcb and unknown Linux plugins historically report XKB = evdev + 8
        evdev_code = scancode - 8
        if evdev_code < 0:
            evdev_code = scancode
    return LINUX_EVDEV_TO_SET1.get(evdev_code, evdev_code)


def key_event_to_set1(event):
    """Return a Set-1 scancode, or None if the event cannot be mapped."""
    if IS_MACOS:
        virtual_key = event.nativeVirtualKey()
        scancode = MACOS_VIRTUALKEY_TO_SET1.get(virtual_key)
        if scancode is None:
            logger.debug(
                "Unmapped macOS key: virtual={} key={} text={!r} scan={}",
                virtual_key,
                event.key(),
                event.text(),
                event.nativeScanCode(),
            )
        return scancode

    scancode = event.nativeScanCode()
    if IS_LINUX:
        return _linux_native_to_set1(scancode)
    return scancode


# Built-in HID keyboard reports for keys the host OS usually swallows.
# Layout matches kb_buffer: [report=1, 0, modifiers, 0, key, ...]
SYSTEM_SHORTCUTS = [
    ("Ctrl+Alt+Del", [1, 0, 5, 0, 0x4C, 0]),
    ("Ctrl+Shift+Esc", [1, 0, 3, 0, 0x29, 0]),
    ("Alt+Tab", [1, 0, 4, 0, 0x2B, 0]),
    ("Alt+Shift+Tab", [1, 0, 6, 0, 0x2B, 0]),
    ("Alt+F4", [1, 0, 4, 0, 0x3D, 0]),
    ("Meta", [1, 0, 8, 0, 0, 0]),
    ("Meta+L", [1, 0, 8, 0, 0x0F, 0]),
    ("Meta+R", [1, 0, 8, 0, 0x15, 0]),
    ("Meta+D", [1, 0, 8, 0, 0x07, 0]),
    ("Meta+E", [1, 0, 8, 0, 0x08, 0]),
    ("Ctrl+Esc", [1, 0, 1, 0, 0x29, 0]),
    ("Print Screen", [1, 0, 0, 0, 0x46, 0]),
    ("Ctrl+Alt+Backspace", [1, 0, 5, 0, 0x2A, 0]),
]
