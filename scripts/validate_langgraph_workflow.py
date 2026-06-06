from __future__ import annotations

from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.agents import run_ops_question  # noqa: E402


def main() -> None:
    report = run_ops_question(
        "Why did the production dashboard deployment fail and are there related blockers?"
    )

    print(f"intent={report.intent}")
    print(f"confidence={report.confidence}")
    print(f"citations={len(report.citations)}")
    print(f"errors={len(report.errors)}")
    print(f"answer={report.answer[:240]}")


if __name__ == "__main__":
    main()

