#!/usr/bin/env python3
"""Start the app briefly, seed demo data, and capture a README screenshot."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    try:
        from tests.helpers.screenshot import capture_readme_screenshot
    except ImportError as exc:
        print(
            "Screenshot failed: playwright is not installed. "
            "Run: pip install -r requirements-dev.txt && playwright install chromium",
            file=sys.stderr,
        )
        print(f"({exc})", file=sys.stderr)
        return 1

    try:
        capture_readme_screenshot()
        return 0
    except Exception as exc:
        print(f"Screenshot failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
