import os
import importlib

def _try_import_native():
    return importlib.import_module("hil.core.native._native")

def _autobuild():
    # Build extension in-place using setuptools
    import subprocess
    import sys
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", root])

try:
    _native = _try_import_native()
except Exception as e:
    if os.environ.get("HIL_NATIVE_AUTOBUILD") == "1":
        _autobuild()
        _native = _try_import_native()
    else:
        raise ImportError(
            "Native HIL extension not built. "
            "Run `pip install -e .` from repo root, or set HIL_NATIVE_AUTOBUILD=1."
        ) from e

__all__ = ["_native"]
