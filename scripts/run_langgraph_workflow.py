from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.agents import run_ops_question  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the LangGraph multi-agent AI ops workflow.")
    parser.add_argument("question", help="Enterprise operations question to answer.")
    args = parser.parse_args()

    report = run_ops_question(args.question)
    print(json.dumps(report.model_dump(), indent=2))


if __name__ == "__main__":
    main()

