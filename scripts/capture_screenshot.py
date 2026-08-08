#!/usr/bin/env python3
"""Start the app briefly, seed demo data, and capture a README screenshot."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORT = 8765
BASE_URL = f"http://127.0.0.1:{PORT}"
SCREENSHOT_PATH = ROOT / "docs" / "screenshot.png"
SAMPLE_LOG = ROOT / "docs" / "fixtures" / "sample.log"
README_PATH = ROOT / "README.md"
SCREENSHOT_DATA_DIR = ROOT / "docs" / "fixtures" / ".screenshot-data"
SCREENSHOT_START = "<!-- APP_SCREENSHOT -->"
SCREENSHOT_END = "<!-- /APP_SCREENSHOT -->"


def wait_for_server(max_attempts: int = 40) -> None:
    for _ in range(max_attempts):
        try:
            with urllib.request.urlopen(f"{BASE_URL}/api/version", timeout=1) as res:
                if res.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError, OSError):
            pass
        time.sleep(0.5)
    raise RuntimeError("Screenshot server did not start in time")


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


def seed_demo_source() -> dict:
    payload = json.dumps(
        {"name": "ollama logs", "path": str(SAMPLE_LOG.resolve())}
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/api/sources",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode("utf-8"))


def capture_screenshot() -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "playwright is not installed. Run: pip install -r requirements-dev.txt "
            "&& playwright install chromium"
        ) from exc

    SCREENSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if SCREENSHOT_DATA_DIR.exists():
        shutil.rmtree(SCREENSHOT_DATA_DIR)
    SCREENSHOT_DATA_DIR.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["LOGS_HOME_DATA_DIR"] = str(SCREENSHOT_DATA_DIR)

    server = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(PORT),
        ],
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    browser = None
    try:
        wait_for_server()
        source = seed_demo_source()

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.goto(BASE_URL)
            page.wait_for_selector("#app-version:not([hidden])")
            page.locator(".source-item-info").first.click()
            page.wait_for_selector("#viewer:not([hidden])")
            page.locator("#highlight-enabled").check()
            page.locator("#highlight-pattern").fill("ERR")
            page.wait_for_timeout(300)
            page.screenshot(path=str(SCREENSHOT_PATH), full_page=True)
            browser.close()
            browser = None

        rel = SCREENSHOT_PATH.relative_to(ROOT)
        print(f"Screenshot saved to {rel} (source: {source['name']})")
        update_readme()
        print("README updated with screenshot")
    finally:
        if browser is not None:
            browser.close()
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
        if SCREENSHOT_DATA_DIR.exists():
            shutil.rmtree(SCREENSHOT_DATA_DIR, ignore_errors=True)


def main() -> int:
    try:
        capture_screenshot()
        return 0
    except Exception as exc:
        print(f"Screenshot failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
