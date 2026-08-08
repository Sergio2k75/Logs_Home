#!/usr/bin/env python3
"""Point git core.hooksPath at scripts/git-hooks (replaces Husky)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOKS_DIR = ROOT / "scripts" / "git-hooks"


def main() -> int:
    if not (HOOKS_DIR / "pre-commit").exists():
        print(f"Missing hook: {HOOKS_DIR / 'pre-commit'}", file=sys.stderr)
        return 1

    subprocess.run(
        ["git", "config", "core.hooksPath", "scripts/git-hooks"],
        cwd=ROOT,
        check=True,
    )
    print("Git hooks installed: core.hooksPath=scripts/git-hooks")
    print("Pre-commit will refresh docs/screenshot.png and README.md.")
    print("Skip with SKIP_SCREENSHOT=1; force with REQUIRE_SCREENSHOT=1.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
