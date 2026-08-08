"""Ensure the app can import without optional GUI dependencies."""

from __future__ import annotations

import builtins
import importlib
import sys


def test_main_imports_when_tkinter_missing(monkeypatch):
    """Headless hosts without python3-tk must still be able to start the API."""
    monkeypatch.setitem(sys.modules, "tkinter", None)
    monkeypatch.setitem(sys.modules, "tkinter.filedialog", None)

    for name in [key for key in sys.modules if key == "backend" or key.startswith("backend.")]:
        del sys.modules[name]

    main = importlib.import_module("backend.main")
    assert main.app.title == "Logs Home"


def test_pick_log_file_reports_missing_tkinter(monkeypatch):
    import backend.file_picker as file_picker

    file_picker = importlib.reload(file_picker)
    real_import = builtins.__import__

    def blocked_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "tkinter" or name.startswith("tkinter."):
            raise ImportError("No module named 'tkinter'")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", blocked_import)

    try:
        file_picker.pick_log_file()
        raise AssertionError("expected RuntimeError")
    except RuntimeError as exc:
        assert "tkinter" in str(exc).lower()
