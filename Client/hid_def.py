import ctypes
import sys
import threading
import time

import hid
from loguru import logger

product_id = 0x2107
vendor_id = 0x413D
usage_page = 0xFF00

DEBUG = False
VERBOSE = False

_hid_lock = threading.Lock()
h = hid.device()


def set_debug(debug):
    global DEBUG
    DEBUG = debug


def set_verbose(verbose):
    global VERBOSE
    VERBOSE = verbose


class _GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", ctypes.c_uint32),
        ("Data2", ctypes.c_uint16),
        ("Data3", ctypes.c_uint16),
        ("Data4", ctypes.c_ubyte * 8),
    ]


def _hid_interface_paths():
    """List HID interface paths without opening devices.

    hidapi's hid_enumerate() on Windows CreateFile()s every HID device
    (including the system keyboard) with desired_access=0, which can leave
    kbdhid/kbdclass unresponsive until reboot.
    """
    try:
        hid_dll = ctypes.WinDLL("hid")
        hid_dll.HidD_GetHidGuid.argtypes = [ctypes.POINTER(_GUID)]
        hid_dll.HidD_GetHidGuid.restype = None
        guid = _GUID()
        hid_dll.HidD_GetHidGuid(ctypes.byref(guid))

        cfg = ctypes.WinDLL("cfgmgr32")
        get_size = cfg.CM_Get_Device_Interface_List_SizeW
        get_list = cfg.CM_Get_Device_Interface_ListW
        get_size.argtypes = [
            ctypes.POINTER(ctypes.c_ulong),
            ctypes.POINTER(_GUID),
            ctypes.c_wchar_p,
            ctypes.c_ulong,
        ]
        get_size.restype = ctypes.c_uint32
        get_list.argtypes = [
            ctypes.POINTER(_GUID),
            ctypes.c_wchar_p,
            ctypes.c_wchar_p,
            ctypes.c_ulong,
            ctypes.c_ulong,
        ]
        get_list.restype = ctypes.c_uint32

        CR_SUCCESS = 0
        CR_BUFFER_SMALL = 26
        CM_GET_DEVICE_INTERFACE_LIST_PRESENT = 0

        size = ctypes.c_ulong()
        while True:
            cr = get_size(
                ctypes.byref(size),
                ctypes.byref(guid),
                None,
                CM_GET_DEVICE_INTERFACE_LIST_PRESENT,
            )
            if cr != CR_SUCCESS:
                logger.error(f"CM_Get_Device_Interface_List_SizeW failed: {cr}")
                return []
            buf = ctypes.create_unicode_buffer(size.value)
            cr = get_list(
                ctypes.byref(guid),
                None,
                buf,
                size,
                CM_GET_DEVICE_INTERFACE_LIST_PRESENT,
            )
            if cr == CR_BUFFER_SMALL:
                continue
            if cr != CR_SUCCESS:
                logger.error(f"CM_Get_Device_Interface_ListW failed: {cr}")
                return []
            break
        return [p for p in buf[: size.value].split("\x00") if p]
    except Exception as e:
        logger.error(f"Failed to list HID interfaces: {e}")
        return []


def _usage_page_from_descriptor(dev):
    try:
        desc = bytes(dev.get_report_descriptor())
    except Exception:
        return None
    if len(desc) >= 3 and desc[0] == 0x06:
        return desc[1] | (desc[2] << 8)
    if len(desc) >= 2 and desc[0] == 0x05:
        return desc[1]
    return None


def _find_kvm_hid_path(vid, pid, page):
    token = f"VID_{vid:04X}&PID_{pid:04X}".casefold()
    matched = None
    for path in _hid_interface_paths():
        if token not in path.casefold():
            continue
        path_arg = path.encode("utf-8")
        dev = hid.device()
        try:
            dev.open_path(path_arg)
            found_page = _usage_page_from_descriptor(dev)
            if found_page is None or found_page == page:
                matched = path_arg
        except Exception:
            continue
        finally:
            try:
                dev.close()
            except Exception:
                pass
    return matched


def close_usb():
    global h
    with _hid_lock:
        old = h
        h = hid.device()
        try:
            old.close()
        except Exception:
            pass


def init_usb(vendor_id, usage_page):
    if DEBUG:
        logger.debug(f"init_usb(vendor_id={vendor_id}, usage_page={usage_page})")
        return 0
    close_usb()
    global h
    if sys.platform.startswith("win"):
        device_path = _find_kvm_hid_path(vendor_id, product_id, usage_page)
        if not device_path:
            logger.error("Device not found")
            return 1
        with _hid_lock:
            try:
                h.open_path(device_path)
                h.set_nonblocking(1)
            except Exception as e:
                logger.error(f"Failed to open HID device: {e}")
                return 1
        return 0

    # Linux hidapi often reports usage_page as 0, so identify the KVM by VID/PID.
    # Do not hid.enumerate() the whole machine.
    with _hid_lock:
        try:
            h.open(vendor_id, product_id)
            h.set_nonblocking(1)
            logger.info(f"KVM Card Mini opened: {vendor_id:04x}:{product_id:04x}")
        except Exception as e:
            logger.error(
                f"Failed to open HID device {vendor_id:04x}:{product_id:04x}: {e}"
            )
            if sys.platform.startswith("linux"):
                logger.error(
                    "On Linux, install Docs/udev/99-kvm-card-mini.rules and "
                    "ensure your user can access /dev/hidraw*"
                )
            return 1
    return 0


def check_connection() -> bool:
    try:
        with _hid_lock:
            h.read(1)
        return True
    except Exception:
        return False


def hid_report(buffer=[], r_mode=False, report=0):
    if DEBUG:
        logger.debug(f"hid_report(buffer={buffer}, r_mode={r_mode}, report={report})")
        return 0
    buffer = buffer[-1:] + buffer[:-1]
    buffer[0] = 0
    if VERBOSE:
        logger.debug(f"hid < {buffer}")
    try:
        with _hid_lock:
            h.write(buffer)
            if r_mode:
                time_start = time.perf_counter()
                while 1:
                    try:
                        d = h.read(64)
                    except (OSError, ValueError):
                        logger.error("Error reading data from device")
                        return 2
                    if d:
                        if VERBOSE:
                            logger.debug(f"hid > {d}")
                        break
                    if time.perf_counter() - time_start > 2:
                        logger.error("Device response timeout")
                        d = 3
                        break
            else:
                d = 0
    except (OSError, ValueError):
        logger.error("Error writing data to device")
        return 1
    except NameError:
        logger.error("Uninitialized device")
        return 4
    return d
