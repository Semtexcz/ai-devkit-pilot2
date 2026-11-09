"""Behavioral tests for the greeting script.

The tests run `main.py` as a subprocess with the interpreter that is running the
suite, so they exercise the real command-line entry point rather than a copied
function call. They cover the exact default and named output, help discovery,
invalid-argument rejection and execution without third-party site packages.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GREETING = "Hello from ai-devkit-pilot2!\n"


def run_main(*args: str, isolated: bool = False) -> subprocess.CompletedProcess[str]:
    """Run main.py with optional arguments, optionally without site packages."""
    command = [sys.executable]
    if isolated:
        command.append("-S")
    command.extend(["main.py", *args])
    return subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_main_runs_successfully() -> None:
    result = run_main()

    assert result.returncode == 0, f"main.py failed with stderr: {result.stderr!r}"
    assert result.stdout.strip(), "main.py produced no output"


def test_default_greeting_is_exact() -> None:
    result = run_main()

    assert result.returncode == 0
    assert result.stdout == DEFAULT_GREETING
    assert result.stderr == ""


def test_named_greeting_is_exact() -> None:
    result = run_main("--name", "Ada")

    assert result.returncode == 0
    assert result.stdout == "Hello from Ada!\n"
    assert result.stderr == ""


def test_help_documents_name_option() -> None:
    result = run_main("--help")

    assert result.returncode == 0
    assert result.stderr == ""
    assert "--name" in result.stdout
    assert "NAME" in result.stdout
    assert "Hello from" not in result.stdout


def test_unknown_argument_is_rejected() -> None:
    result = run_main("--unknown")

    assert result.returncode != 0
    assert result.stdout == ""
    assert result.stderr.strip()
    assert "--unknown" in result.stderr


def test_missing_name_value_is_rejected() -> None:
    result = run_main("--name")

    assert result.returncode != 0
    assert result.stdout == ""
    assert result.stderr.strip()
    assert "--name" in result.stderr


@pytest.mark.parametrize(
    ("args", "expected"),
    [((), DEFAULT_GREETING), (("--name", "Ada"), "Hello from Ada!\n")],
)
def test_success_scenarios_run_without_site_packages(args: tuple[str, ...], expected: str) -> None:
    result = run_main(*args, isolated=True)

    assert result.returncode == 0
    assert result.stdout == expected
    assert result.stderr == ""


def test_help_runs_without_site_packages() -> None:
    result = run_main("--help", isolated=True)

    assert result.returncode == 0
    assert result.stderr == ""
    assert "--name" in result.stdout
    assert "Hello from" not in result.stdout
