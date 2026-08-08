import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGE_JSON = ROOT / "package.json"


def get_app_version() -> str:
    if PACKAGE_JSON.exists():
        data = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
        return str(data.get("version", "0.0.0"))
    return "0.0.0"
