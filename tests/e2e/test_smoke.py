"""Smoke checks for the main UI."""

from __future__ import annotations

import pytest
from playwright.sync_api import expect

from tests.helpers.home import HomePage

pytestmark = pytest.mark.e2e


def test_app_version_visible(home: HomePage) -> None:
    home.goto()
    version = home.page.locator("#app-version")
    expect(version).to_be_visible()
    expect(version).not_to_have_text("")
    expect(version).to_contain_text("v")


def test_empty_state_before_sources(home: HomePage) -> None:
    home.goto()
    expect(home.page.locator("#viewer-empty")).to_be_visible()
    expect(home.page.locator("#viewer")).to_be_hidden()
    expect(home.page.locator(".source-empty")).to_contain_text("No sources yet")
