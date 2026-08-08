"""Pytest fixtures for Playwright e2e tests."""

from __future__ import annotations

import json
import shutil
import urllib.request
from pathlib import Path

import pytest

from tests.helpers.home import HomePage
from tests.helpers.server import ROOT, AppServer, start_app_server

SAMPLE_LOG = ROOT / "docs" / "fixtures" / "sample.log"


@pytest.fixture(scope="session")
def sample_log_path() -> Path:
    return SAMPLE_LOG.resolve()


@pytest.fixture(scope="session")
def app_server(tmp_path_factory: pytest.TempPathFactory):
    data_dir = tmp_path_factory.mktemp("logs-home-data")
    server = start_app_server(data_dir)
    try:
        yield server
    finally:
        server.stop()
        shutil.rmtree(data_dir, ignore_errors=True)


@pytest.fixture(scope="session")
def base_url(app_server: AppServer) -> str:
    return app_server.base_url


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict) -> dict:
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 800},
    }


def _list_source_ids(base_url: str) -> list[str]:
    with urllib.request.urlopen(f"{base_url}/api/sources") as res:
        sources = json.loads(res.read().decode("utf-8"))
    return [s["id"] for s in sources]


def _delete_source(base_url: str, source_id: str) -> None:
    req = urllib.request.Request(
        f"{base_url}/api/sources/{source_id}",
        method="DELETE",
    )
    with urllib.request.urlopen(req) as res:
        res.read()


@pytest.fixture(autouse=True)
def clear_sources(request: pytest.FixtureRequest):
    """Ensure each e2e test starts with an empty source list."""
    if request.node.get_closest_marker("screenshot"):
        yield
        return

    base_url: str = request.getfixturevalue("base_url")
    for source_id in _list_source_ids(base_url):
        _delete_source(base_url, source_id)
    yield
    for source_id in _list_source_ids(base_url):
        _delete_source(base_url, source_id)


@pytest.fixture
def home(page, base_url: str) -> HomePage:
    return HomePage(page, base_url)
