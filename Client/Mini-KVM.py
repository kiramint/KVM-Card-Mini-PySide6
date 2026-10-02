import datetime
import os
import sys
import tempfile
import traceback


def _log_dir():
    try:
        from platform_util import user_data_dir

        return user_data_dir()
    except Exception:
        pass
    if sys.platform.startswith("linux"):
        path = os.path.join(
            os.path.expanduser("~"), ".local", "share", "mini-kvm"
        )
    elif sys.platform == "darwin" and (
        getattr(sys, "frozen", False) or "__compiled__" in globals()
    ):
        path = os.path.join(
            os.path.expanduser("~"),
            "Library",
            "Application Support",
            "KVM Card Mini",
        )
    else:
        return os.path.dirname(os.path.abspath(sys.argv[0]))
    os.makedirs(path, exist_ok=True)
    return path


def error_log(msg):
    with open(os.path.join(_log_dir(), "error.log"), "w") as f:
        f.write(f"Error Occurred at {datetime.datetime.now()}:\n")
        f.write(f"{msg}\n")


def _dismiss_onefile_splash():
    parent = os.environ.get("NUITKA_ONEFILE_PARENT")
    if not parent:
        return
    splash = os.path.join(
        tempfile.gettempdir(),
        "onefile_%d_splash_feedback.tmp" % int(parent),
    )
    try:
        os.unlink(splash)
    except OSError:
        pass


try:
    from main import main

    _dismiss_onefile_splash()
    main()
except Exception:
    error_log(traceback.format_exc())
    sys.exit(1)
