"""Unit tests for bounded last-N-lines file reads."""

from __future__ import annotations

from pathlib import Path

from backend.tail import MAX_READ_BYTES, read_last_lines


def test_read_last_lines_returns_trailing_lines(tmp_path: Path):
    log_file = tmp_path / "app.log"
    log_file.write_text("".join(f"line-{i}\n" for i in range(10)), encoding="utf-8")

    assert read_last_lines(str(log_file), 3) == ["line-7", "line-8", "line-9"]


def test_read_last_lines_caps_memory_on_huge_line_without_newlines(tmp_path: Path):
    """A multi-MB file with no newlines must not be slurped entirely into RAM."""
    log_file = tmp_path / "huge.log"
    # Larger than the read budget so an uncapped reader would keep growing.
    log_file.write_bytes(b"x" * (MAX_READ_BYTES + 2 * 1024 * 1024))

    lines = read_last_lines(str(log_file), 50)

    assert len(lines) == 1
    # Decoded length may be slightly under MAX_READ_BYTES if we stop mid-budget,
    # but must never exceed the cap (errors="replace" keeps 1:1 for ASCII).
    assert len(lines[0].encode("utf-8")) <= MAX_READ_BYTES


def test_read_last_lines_finds_trailing_lines_after_huge_prefix(tmp_path: Path):
    log_file = tmp_path / "mixed.log"
    payload = (b"x" * (MAX_READ_BYTES + 1024)) + b"\nkeep-a\nkeep-b\n"
    log_file.write_bytes(payload)

    assert read_last_lines(str(log_file), 2) == ["keep-a", "keep-b"]
