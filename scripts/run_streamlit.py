from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def main() -> None:
    port = os.getenv("STREAMLIT_PORT", "8501")
    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "streamlit_app.py",
        "--server.address",
        "127.0.0.1",
        "--server.port",
        port,
    ]
    raise SystemExit(subprocess.call(command, cwd=ROOT_DIR))


if __name__ == "__main__":
    main()

