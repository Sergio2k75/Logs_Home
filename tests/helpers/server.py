"""Start and stop a local uvicorn process for Playwright."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_server(base_url: str, max_attempts: int = 40) -> None:
    for _ in range(max_attempts):
        try:
            with urllib.request.urlopen(f"{base_url}/api/version", timeout=1) as res:
                if res.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError, OSError):
            pass
        time.sleep(0.5)
    raise RuntimeError(f"Server at {base_url} did not start in time")


@dataclass
class AppServer:
    """Running uvicorn instance with an isolated data directory."""

    base_url: str
    port: int
    data_dir: Path
    process: subprocess.Popen[bytes]

    def stop(self) -> None:
        self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=5)


def start_app_server(data_dir: Path, port: int | None = None) -> AppServer:
    """Launch uvicorn with LOGS_HOME_DATA_DIR pointing at data_dir."""
    data_dir.mkdir(parents=True, exist_ok=True)
    chosen_port = port if port is not None else find_free_port()
    base_url = f"http://127.0.0.1:{chosen_port}"

    env = os.environ.copy()
    env["LOGS_HOME_DATA_DIR"] = str(data_dir.resolve())

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(chosen_port),
        ],
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        wait_for_server(base_url)
    except Exception:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        raise

    return AppServer(
        base_url=base_url,
        port=chosen_port,
        data_dir=data_dir,
        process=process,
    )
