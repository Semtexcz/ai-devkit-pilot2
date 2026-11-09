"""Validate local Git and Cezar evidence; orchestration belongs to Cezar."""

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def clean() -> None:
    if git("status", "--porcelain=v1", "--untracked-files=all"):
        raise ValueError("unexpected worktree/index/untracked changes")


def current_record() -> dict[str, Any]:
    run_id = os.environ["CEZ_RUN_ID"]
    common = Path(git("rev-parse", "--git-common-dir")).resolve()
    index = common.parent / ".ai/cezar/runs.json"
    # Cezar debounces index persistence. Wait for THIS node's checkpoint only.
    for _ in range(31):
        records = json.loads(index.read_text())
        for record in records:
            if (
                record["id"] == run_id
                and record.get("graphState", {}).get("cursor") == os.environ["CEZ_STEP_ID"]
            ):
                return dict(record)
        time.sleep(0.1)
    raise ValueError("current native run checkpoint unavailable")


def audit(record: dict[str, Any]) -> None:
    clean()
    outputs = record["graphState"]["outputs"]
    head = outputs["snapshot"]["output"].strip()
    if not re.fullmatch(r"[0-9a-f]{40}", head) or git("rev-parse", "HEAD") != head:
        raise ValueError("reviewer changed HEAD, or snapshot is invalid")
    report = outputs["review"]["summary"]
    verdict = outputs["review"]["verdict"]
    if not isinstance(report, str) or len(report) >= 3500:
        raise ValueError("review report missing, oversized or potentially truncated")
    lines = report.strip().splitlines()
    expected = {"approve": "APPROVE", "changes": "REQUEST CHANGES"}
    if verdict not in expected:
        raise ValueError("review verdict unavailable")
    if not lines or lines[0] != f"Reviewed-commit: {head}":
        raise ValueError("report does not refer to current committed HEAD")
    if lines[-1] != expected[verdict] or "Evidence: verified" not in lines:
        raise ValueError("unverifiable or inconsistent report")
    if verdict == "approve" and "No blocking findings" not in lines:
        raise ValueError("approval lacks explicit blocking-findings assessment")
    if verdict == "changes" and not any(line.startswith("[blocking] F") for line in lines):
        raise ValueError("rejection has no repair findings")


def main() -> None:
    mode = sys.argv[1]
    if mode == "preflight":
        clean()
        if (
            Path(git("rev-parse", "--git-dir")).resolve()
            == Path(git("rev-parse", "--git-common-dir")).resolve()
        ):
            raise ValueError("pilot requires an isolated linked task worktree")
        if any(os.environ.get(key) for key in ("OPENAI_API_KEY", "CODEX_API_KEY")):
            raise ValueError("remove API-key overrides; use existing subscription auth")
        for key, expected in {
            "CEZ_CODEX_NETWORK": "0",
            "CEZ_DISPATCH": "0",
            "CEZ_AUTOMATIONS": "0",
            "CEZ_AUTONAME": "0",
        }.items():
            if os.environ.get(key) != expected:
                raise ValueError(f"start with {key}={expected}")
        settings = Path(os.environ["CEZ_HOME"]) / "config.json"
        resources = json.loads(settings.read_text()).get("resources", {})
        if resources.get("autoResumeOnUsageLimit") is not False:
            raise ValueError("disable automatic usage-limit/transient resumption")
        print(git("rev-parse", "HEAD"))
    elif mode == "snapshot":
        clean()
        print(git("rev-parse", "HEAD"))
    elif mode == "audit":
        audit(current_record())
        print("verified: current commit and review evidence; worktree clean")
    else:
        raise ValueError("unknown guard mode")


if __name__ == "__main__":
    try:
        main()
    except (KeyError, ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"STOP: {error}", file=sys.stderr)
        sys.exit(1)
