from pathlib import Path

# Cap how much of a file we pull into memory when seeking last-N lines.
# Without this, a multi-GB file with few/no newlines (or auto-refresh against one)
# can OOM or hang the server via unbounded buffer growth.
MAX_READ_BYTES = 4 * 1024 * 1024


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
        chunks: list[bytes] = []
        bytes_read = 0
        position = file_size
        lines_found = 0

        while position > 0 and lines_found <= line_count and bytes_read < MAX_READ_BYTES:
            read_size = min(chunk_size, position, MAX_READ_BYTES - bytes_read)
            position -= read_size
            f.seek(position)
            chunk = f.read(read_size)
            chunks.append(chunk)
            bytes_read += len(chunk)
            lines_found += chunk.count(b"\n")

        # Chunks were collected from end → start; reverse to restore file order.
        buffer = b"".join(reversed(chunks))
        text = buffer.decode("utf-8", errors="replace")
        all_lines = text.splitlines()
        return all_lines[-line_count:]
