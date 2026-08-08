from pathlib import Path


def read_last_lines(file_path: str, line_count: int = 200) -> list[str]:
    """Read the last N lines from a file efficiently by seeking from the end."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    line_count = max(1, min(line_count, 10_000))

    with path.open("rb") as f:
        f.seek(0, 2)
        file_size = f.tell()
        if file_size == 0:
            return []

        chunk_size = 8192
        buffer = b""
        position = file_size
        lines_found = 0

        while position > 0 and lines_found <= line_count:
            read_size = min(chunk_size, position)
            position -= read_size
            f.seek(position)
            buffer = f.read(read_size) + buffer
            lines_found = buffer.count(b"\n")

        text = buffer.decode("utf-8", errors="replace")
        all_lines = text.splitlines()
        return all_lines[-line_count:]
