"""Exercise the evidence guard against real disposable local Git repositories."""

import importlib.util
import subprocess
from pathlib import Path
from typing import Any

import pytest

SCRIPT = Path(__file__).parents[1] / "scripts/cezar_review_guard.py"
SPEC = importlib.util.spec_from_file_location("cezar_guard", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
GUARD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GUARD)


@pytest.fixture
def repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    for args in (
        ("init", "-q"),
        ("config", "user.name", "Pilot Test"),
        ("config", "user.email", "pilot@example.invalid"),
    ):
        subprocess.run(["git", *args], check=True)
    (tmp_path / "code.txt").write_text("initial\n")
    GUARD.git("add", "code.txt")
    GUARD.git("commit", "-qm", "initial")
    return tmp_path


def report(verdict: str = "approve") -> dict[str, Any]:
    head = GUARD.git("rev-parse", "HEAD")
    ending = (
        "No blocking findings\nAPPROVE"
        if verdict == "approve"
        else "[blocking] F1 — code.txt:1 — observed/expected/evidence\nREQUEST CHANGES"
    )
    return {
        "graphState": {
            "outputs": {
                "snapshot": {"output": head},
                "review": {
                    "summary": f"Reviewed-commit: {head}\nEvidence: verified\n{ending}",
                    "verdict": verdict,
                },
            }
        }
    }


@pytest.mark.parametrize("verdict", ["approve", "changes"])
def test_valid_current_report(repository: Path, verdict: str) -> None:
    GUARD.audit(report(verdict))


@pytest.mark.parametrize("mutation", ["unstaged", "staged", "untracked", "committed"])
def test_detect_reviewer_changes(repository: Path, mutation: str) -> None:
    evidence = report()
    target = "extra.txt" if mutation == "untracked" else "code.txt"
    (repository / target).write_text("unexpected\n")
    if mutation in ("staged", "committed"):
        GUARD.git("add", target)
    if mutation == "committed":
        GUARD.git("commit", "-qm", "reviewer edit (also models Cezar autosave)")
    with pytest.raises(ValueError):
        GUARD.audit(evidence)


@pytest.mark.parametrize(
    "problem", ["stale", "missing", "oversized", "unverified", "verdict", "no-findings"]
)
def test_reject_bad_evidence(repository: Path, problem: str) -> None:
    evidence = report()
    review = evidence["graphState"]["outputs"]["review"]
    if problem == "stale":
        review["summary"] = review["summary"].replace(GUARD.git("rev-parse", "HEAD"), "0" * 40)
    elif problem == "missing":
        review["summary"] = ""
    elif problem == "oversized":
        review["summary"] += "x" * 4000
    elif problem == "unverified":
        review["summary"] = review["summary"].replace("Evidence: verified", "Evidence: unavailable")
    elif problem == "verdict":
        review["verdict"] = "changes"
    else:
        review["summary"] = review["summary"].replace("No blocking findings", "")
    with pytest.raises(ValueError):
        GUARD.audit(evidence)


def test_native_record_selection(repository: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import json

    index = repository / ".ai/cezar/runs.json"
    index.parent.mkdir(parents=True)
    (repository / ".gitignore").write_text(".ai/\n")
    GUARD.git("add", ".gitignore")
    GUARD.git("commit", "-qm", "ignore runtime")
    evidence = report()
    evidence.update(id="pilot-test")
    evidence["graphState"]["cursor"] = "audit"
    index.write_text(json.dumps([evidence]))
    monkeypatch.setenv("CEZ_RUN_ID", "pilot-test")
    monkeypatch.setenv("CEZ_STEP_ID", "audit")
    GUARD.audit(GUARD.current_record())


@pytest.mark.parametrize("problem", [None, "network", "resume", "api-key", "in-place"])
def test_preflight_boundaries(
    repository: Path, monkeypatch: pytest.MonkeyPatch, problem: str | None
) -> None:
    import json
    import sys

    worktree = repository.parent / f"{repository.name}-task"
    GUARD.git("worktree", "add", "-qb", "pilot-task", str(worktree))
    monkeypatch.chdir(repository if problem == "in-place" else worktree)
    settings = repository.parent / f"{repository.name}-cezar-home"
    settings.mkdir()
    (settings / "config.json").write_text(
        json.dumps({"resources": {"autoResumeOnUsageLimit": problem == "resume"}})
    )
    monkeypatch.setenv("CEZ_HOME", str(settings))
    for key in ("CEZ_CODEX_NETWORK", "CEZ_DISPATCH", "CEZ_AUTOMATIONS", "CEZ_AUTONAME"):
        monkeypatch.setenv(key, "0")
    for key in ("OPENAI_API_KEY", "CODEX_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    if problem == "network":
        monkeypatch.setenv("CEZ_CODEX_NETWORK", "1")
    if problem == "api-key":
        monkeypatch.setenv("CODEX_API_KEY", "synthetic-test-override")
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "preflight"])
    if problem is None:
        GUARD.main()
    else:
        with pytest.raises(ValueError):
            GUARD.main()
