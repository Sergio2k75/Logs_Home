"""Source list: add, select, delete."""

from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import expect

from tests.helpers.home import HomePage

pytestmark = pytest.mark.e2e


def test_add_source(home: HomePage, sample_log_path: Path) -> None:
    home.goto()
    home.add_source("demo logs", str(sample_log_path))
    expect(home.page.locator(".source-item-name")).to_have_text("demo logs")
    expect(home.page.locator("#source-name")).to_have_value("")
    expect(home.page.locator("#source-path")).to_have_value("")


def test_select_source_opens_viewer(home: HomePage, sample_log_path: Path) -> None:
    home.goto()
    home.add_source("viewer source", str(sample_log_path))
    home.select_source("viewer source")
    expect(home.page.locator("#viewer-path")).to_contain_text(str(sample_log_path))
    expect(home.page.locator("#viewer-empty")).to_be_hidden()


def test_delete_source(home: HomePage, sample_log_path: Path) -> None:
    home.goto()
    home.add_source("temp source", str(sample_log_path))
    home.select_source("temp source")
    home.delete_source("temp source")
    expect(home.page.locator(".source-empty")).to_be_visible()
    expect(home.page.locator("#viewer-empty")).to_be_visible()
    expect(home.page.locator("#viewer")).to_be_hidden()
