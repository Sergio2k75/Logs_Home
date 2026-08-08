"""Log viewer: tail lines, line count, highlighting."""

from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import expect

from tests.helpers.home import HomePage

pytestmark = pytest.mark.e2e


def test_viewer_shows_fixture_lines(home: HomePage, sample_log_path: Path) -> None:
    home.goto()
    home.add_source("ollama logs", str(sample_log_path))
    home.select_source("ollama logs")
    log_output = home.page.locator("#log-output")
    expect(log_output).to_contain_text("ERR Connection timeout to backend")
    expect(log_output).to_contain_text("WARN GPU memory usage high")
    expect(log_output.locator(".log-line")).to_have_count(8)


def test_highlight_err_lines(home: HomePage, sample_log_path: Path) -> None:
    home.goto()
    home.add_source("highlight source", str(sample_log_path))
    home.select_source("highlight source")
    home.enable_highlight("ERR")

    highlighted = home.page.locator("#log-output .log-line.highlight-error")
    expect(highlighted).to_have_count(2)
    expect(highlighted.first).to_contain_text("ERR Connection timeout")


def test_preset_enables_highlight(home: HomePage, sample_log_path: Path) -> None:
    home.goto()
    home.add_source("preset source", str(sample_log_path))
    home.select_source("preset source")
    home.click_preset("WARN")

    expect(home.page.locator("#highlight-pattern")).to_have_value("WARN")
    expect(home.page.locator("#highlight-enabled")).to_be_checked()
    expect(home.page.locator("#log-output .log-line.highlight-warn")).to_have_count(1)
    expect(home.page.locator("#log-output .log-line.highlight-warn")).to_contain_text(
        "WARN GPU memory usage high"
    )


def test_line_count_control(home: HomePage, sample_log_path: Path) -> None:
    home.goto()
    home.add_source("lines source", str(sample_log_path))
    home.select_source("lines source")
    home.set_line_count("50")
    expect(home.page.locator("#line-count")).to_have_value("50")
    expect(home.page.locator("#log-output .log-line")).to_have_count(8)
