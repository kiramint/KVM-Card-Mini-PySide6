import datetime
import os
import sys
import traceback


def _log_dir():
    if sys.platform == "darwin" and (
        getattr(sys, "frozen", False) or "__compiled__" in globals()
    ):
        path = os.path.join(
            os.path.expanduser("~"),
            "Library",
            "Application Support",
            "KVM Card Mini",
        )
        os.makedirs(path, exist_ok=True)
        return path
    return os.path.dirname(os.path.abspath(sys.argv[0]))


def error_log(msg):
    with open(os.path.join(_log_dir(), "error.log"), "w") as f:
        f.write(f"Error Occurred at {datetime.datetime.now()}:\n")
        f.write(f"{msg}\n")


try:
    from main import main

    main()
except Exception:
    error_log(traceback.format_exc())
    sys.exit(1)
