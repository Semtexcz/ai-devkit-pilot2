"""Smoke test: the script runs to completion.

The test is independent of the project name and of the greeting text: it runs
`main.py` as a subprocess with the interpreter that is running the suite, and it
asserts only that execution succeeds and prints something. That is the behavior
the project promises, so the test does not need to change when the message does.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_main_runs_successfully() -> None:
    result = subprocess.run(
        [sys.executable, "main.py"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, f"main.py failed with stderr: {result.stderr!r}"
    assert result.stdout.strip(), "main.py produced no output"
