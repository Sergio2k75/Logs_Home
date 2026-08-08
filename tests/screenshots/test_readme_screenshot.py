"""Optional pytest entrypoint for regenerating the README screenshot.

Deselected by default (see pytest.ini). Run with:

    pytest -m screenshot
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers.screenshot import SCREENSHOT_PATH, capture_readme_screenshot

pytestmark = pytest.mark.screenshot


def test_capture_readme_screenshot() -> None:
    path = capture_readme_screenshot()
    assert path == SCREENSHOT_PATH
    assert Path(path).is_file()
