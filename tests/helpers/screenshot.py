"""Capture the README screenshot and refresh the README image block."""

from __future__ import annotations

import json
import re
import shutil
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

from tests.helpers.server import ROOT, start_app_server

SCREENSHOT_PATH = ROOT / "docs" / "screenshot.png"
SAMPLE_LOG = ROOT / "docs" / "fixtures" / "sample.log"
README_PATH = ROOT / "README.md"
SCREENSHOT_DATA_DIR = ROOT / "docs" / "fixtures" / ".screenshot-data"
SCREENSHOT_PORT = 8765
SCREENSHOT_START = "<!-- APP_SCREENSHOT -->"
SCREENSHOT_END = "<!-- /APP_SCREENSHOT -->"


def update_readme() -> None:
    readme = README_PATH.read_text(encoding="utf-8")
    block = f"{SCREENSHOT_START}\n![Logs Home screenshot](docs/screenshot.png)\n{SCREENSHOT_END}"
    pattern = re.compile(
        re.escape(SCREENSHOT_START) + r"[\s\S]*?" + re.escape(SCREENSHOT_END)
    )
    if pattern.search(readme):
        updated = pattern.sub(block, readme)
    else:
        updated = re.sub(r"^# Logs Home\r?\n", f"# Logs Home\n\n{block}\n", readme, count=1)
    README_PATH.write_text(updated, encoding="utf-8")


def seed_demo_source(base_url: str) -> dict:
    payload = json.dumps(
        {"name": "ollama logs", "path": str(SAMPLE_LOG.resolve())}
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}/api/sources",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode("utf-8"))


def capture_readme_screenshot() -> Path:
    """Start a temp server, seed demo data, write docs/screenshot.png, update README."""
    SCREENSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if SCREENSHOT_DATA_DIR.exists():
        shutil.rmtree(SCREENSHOT_DATA_DIR)

    server = start_app_server(SCREENSHOT_DATA_DIR, port=SCREENSHOT_PORT)
    try:
        source = seed_demo_source(server.base_url)

        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                page = browser.new_page(viewport={"width": 1280, "height": 800})
                page.goto(server.base_url)
                page.wait_for_selector("#app-version:not([hidden])")
                page.locator(".source-item-info").first.click()
                page.wait_for_selector("#viewer:not([hidden])")
                page.locator("#highlight-enabled").check()
                page.locator("#highlight-pattern").fill("ERR")
                page.wait_for_timeout(300)
                page.screenshot(path=str(SCREENSHOT_PATH), full_page=True)
            finally:
                browser.close()

        update_readme()
        print(f"Screenshot saved to {SCREENSHOT_PATH.relative_to(ROOT)} (source: {source['name']})")
        print("README updated with screenshot")
        return SCREENSHOT_PATH
    finally:
        server.stop()
        if SCREENSHOT_DATA_DIR.exists():
            shutil.rmtree(SCREENSHOT_DATA_DIR, ignore_errors=True)
