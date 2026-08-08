"""Unit tests for durable source persistence."""

from __future__ import annotations

import importlib
import json
import threading
from pathlib import Path

import pytest


@pytest.fixture
def sources_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LOGS_HOME_DATA_DIR", str(tmp_path))
    import backend.sources_store as sources_store

    return importlib.reload(sources_store)


def test_create_source_persists_atomically(sources_store, tmp_path: Path):
    log_file = tmp_path / "app.log"
    log_file.write_text("hello\n", encoding="utf-8")

    created = sources_store.create_source("app", str(log_file))
    on_disk = json.loads((tmp_path / "sources.json").read_text(encoding="utf-8"))

    assert len(on_disk) == 1
    assert on_disk[0]["id"] == created["id"]
    assert on_disk[0]["name"] == "app"
    assert on_disk[0]["path"] == str(log_file.resolve())
    assert list(tmp_path.glob("sources.*.tmp")) == []


def test_empty_sources_file_treated_as_empty_list(sources_store, tmp_path: Path):
    (tmp_path / "sources.json").write_text("", encoding="utf-8")
    assert sources_store.list_sources() == []


def test_corrupt_sources_file_raises_clear_error(sources_store, tmp_path: Path):
    (tmp_path / "sources.json").write_text("{not-json", encoding="utf-8")
    with pytest.raises(ValueError, match="Corrupt sources file"):
        sources_store.list_sources()


def test_concurrent_creates_do_not_lose_sources(sources_store, tmp_path: Path):
    log_files = []
    for i in range(20):
        path = tmp_path / f"app-{i}.log"
        path.write_text(f"line-{i}\n", encoding="utf-8")
        log_files.append(path)

    errors: list[BaseException] = []

    def worker(index: int) -> None:
        try:
            sources_store.create_source(f"app-{index}", str(log_files[index]))
        except BaseException as exc:  # noqa: BLE001 - collect for assertion
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(20)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []
    sources = sources_store.list_sources()
    assert len(sources) == 20
    assert {s["name"] for s in sources} == {f"app-{i}" for i in range(20)}


def test_delete_preserves_other_sources(sources_store, tmp_path: Path):
    paths = []
    for name in ("one", "two", "three"):
        path = tmp_path / f"{name}.log"
        path.write_text(name + "\n", encoding="utf-8")
        paths.append(sources_store.create_source(name, str(path)))

    assert sources_store.delete_source(paths[1]["id"]) is True
    remaining = sources_store.list_sources()
    assert {s["name"] for s in remaining} == {"one", "three"}
