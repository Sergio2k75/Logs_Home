"""Log viewer: tail lines, line count, highlighting."""

from __future__ import annotations

import re
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

    warn = home.page.locator(".preset[data-pattern='WARN']")
    err = home.page.locator(".preset[data-pattern='ERR']")
    expect(warn).to_have_class(re.compile(r"\bis-active\b"))
    expect(warn).to_have_attribute("aria-pressed", "true")
    expect(err).not_to_have_class(re.compile(r"\bis-active\b"))
    expect(err).to_have_attribute("aria-pressed", "false")

    pattern_box = home.page.locator("#highlight-pattern").bounding_box()
    nav_box = home.page.locator("#match-nav").bounding_box()
    warn_box = warn.bounding_box()
    assert pattern_box is not None and nav_box is not None and warn_box is not None
    assert nav_box["y"] >= pattern_box["y"] + pattern_box["height"] - 1
    assert abs(warn_box["y"] - pattern_box["y"]) < pattern_box["height"]

    home.page.locator("#highlight-pattern").fill("custom")
    expect(warn).not_to_have_class(re.compile(r"\bis-active\b"))
    expect(warn).to_have_attribute("aria-pressed", "false")


def test_highlight_match_count_and_navigation(home: HomePage, sample_log_path: Path) -> None:
    home.goto()
    home.add_source("match nav", str(sample_log_path))
    home.select_source("match nav")
    home.enable_highlight("ERR")

    status = home.page.locator("#match-status")
    current = home.page.locator("#log-output .log-line.highlight-current")
    expect(home.page.locator("#match-nav")).to_be_visible()
    expect(status).to_have_text("2 matches")
    expect(current).to_have_count(0)

    next_match = home.page.locator("#match-next")
    previous_match = home.page.locator("#match-prev")
    next_match.click()
    expect(status).to_have_text("1 / 2")
    expect(current).to_contain_text("ERR Connection timeout")

    next_match.click()
    expect(status).to_have_text("2 / 2")
    expect(current).to_contain_text("ERROR Fatal: out of memory")

    next_match.click()
    expect(status).to_have_text("1 / 2")
    expect(current).to_contain_text("ERR Connection timeout")

    previous_match.click()
    expect(status).to_have_text("2 / 2")
    expect(current).to_contain_text("ERROR Fatal: out of memory")


def test_single_match_can_be_focused(home: HomePage, sample_log_path: Path) -> None:
    home.goto()
    home.add_source("warn nav", str(sample_log_path))
    home.select_source("warn nav")
    home.click_preset("WARN")

    expect(home.page.locator("#match-status")).to_have_text("1 match")
    expect(home.page.locator("#match-next")).to_be_enabled()
    expect(home.page.locator("#match-prev")).to_be_enabled()

    home.page.locator("#match-next").click()
    expect(home.page.locator("#match-status")).to_have_text("1 / 1")
    expect(home.page.locator("#log-output .log-line.highlight-current")).to_contain_text(
        "WARN GPU memory usage high"
    )
    expect(home.page.locator("#follow-toggle")).to_have_text("Follow")


def test_enter_steps_and_pattern_edit_clears_current(
    home: HomePage, sample_log_path: Path
) -> None:
    home.goto()
    home.add_source("enter nav", str(sample_log_path))
    home.select_source("enter nav")
    home.enable_highlight("ERR")

    pattern = home.page.locator("#highlight-pattern")
    pattern.press("Enter")
    expect(home.page.locator("#match-status")).to_have_text("1 / 2")
    expect(home.page.locator("#log-output .log-line.highlight-current")).to_contain_text(
        "ERR Connection timeout"
    )

    pattern.fill("ERR ")
    expect(home.page.locator("#log-output .log-line.highlight-current")).to_have_count(0)
    expect(home.page.locator("#match-status")).to_have_text("2 matches")


def test_stepping_pauses_until_follow(home: HomePage, sample_log_path: Path, tmp_path: Path) -> None:
    log_path = tmp_path / "growing.log"
    log_path.write_text(sample_log_path.read_text(encoding="utf-8"), encoding="utf-8")

    home.goto()
    home.add_source("growing", str(log_path))
    home.select_source("growing")
    expect(home.page.locator("#follow-toggle")).to_have_text("Pause")

    home.enable_highlight("ERR")
    home.page.locator("#match-next").click()
    current = home.page.locator("#log-output .log-line.highlight-current")
    expect(home.page.locator("#follow-toggle")).to_have_text("Follow")
    expect(current).to_contain_text("ERR Connection timeout")

    home.page.locator("#refresh-btn").click()
    expect(current).to_contain_text("ERR Connection timeout")

    with log_path.open("a", encoding="utf-8") as handle:
        handle.write("\n2026-08-08 10:00:09 INFO appended after pause\n")

    home.page.wait_for_timeout(2500)
    expect(home.page.locator("#log-output")).not_to_contain_text("appended after pause")
    expect(current).to_contain_text("ERR Connection timeout")

    home.page.locator("#follow-toggle").click()
    expect(home.page.locator("#log-output")).to_contain_text("appended after pause")
    expect(home.page.locator("#follow-toggle")).to_have_text("Pause")
    expect(home.page.locator("#log-output .log-line.highlight-current")).to_have_count(0)


def test_highlight_no_matches_disables_navigation(home: HomePage, sample_log_path: Path) -> None:
    home.goto()
    home.add_source("no matches", str(sample_log_path))
    home.select_source("no matches")
    home.enable_highlight("ZZZ")

    expect(home.page.locator("#match-status")).to_have_text("0 matches")
    expect(home.page.locator("#match-prev")).to_be_disabled()
    expect(home.page.locator("#match-next")).to_be_disabled()


def test_line_count_control(home: HomePage, sample_log_path: Path) -> None:
    home.goto()
    home.add_source("lines source", str(sample_log_path))
    home.select_source("lines source")
    home.set_line_count("50")
    expect(home.page.locator("#line-count")).to_have_value("50")
    expect(home.page.locator("#log-output .log-line")).to_have_count(8)
