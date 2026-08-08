import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DATA_DIR = Path(os.environ.get("LOGS_HOME_DATA_DIR", Path(__file__).resolve().parent.parent / "data"))
SOURCES_FILE = DATA_DIR / "sources.json"


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_raw() -> list[dict[str, Any]]:
    _ensure_data_dir()
    if not SOURCES_FILE.exists():
        return []
    with SOURCES_FILE.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        return []
    return data


def _save_raw(sources: list[dict[str, Any]]) -> None:
    _ensure_data_dir()
    with SOURCES_FILE.open("w", encoding="utf-8") as f:
        json.dump(sources, f, indent=2)


def list_sources() -> list[dict[str, Any]]:
    return sorted(_load_raw(), key=lambda s: s.get("name", "").lower())


def get_source(source_id: str) -> dict[str, Any] | None:
    for source in _load_raw():
        if source.get("id") == source_id:
            return source
    return None


def create_source(name: str, path: str) -> dict[str, Any]:
    name = name.strip()
    if not name:
        raise ValueError("Name is required")

    normalized = str(Path(path).resolve())
    file_path = Path(normalized)
    if not file_path.exists():
        raise ValueError(f"File not found: {normalized}")
    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {normalized}")

    sources = _load_raw()
    for source in sources:
        if source.get("path") == normalized:
            raise ValueError(f"A source for this path already exists: {source.get('name')}")

    source = {
        "id": str(uuid.uuid4()),
        "name": name,
        "path": normalized,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    sources.append(source)
    _save_raw(sources)
    return source


def delete_source(source_id: str) -> bool:
    sources = _load_raw()
    updated = [s for s in sources if s.get("id") != source_id]
    if len(updated) == len(sources):
        return False
    _save_raw(updated)
    return True
