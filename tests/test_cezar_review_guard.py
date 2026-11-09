"""Exercise the evidence guard against real disposable local Git repositories."""

import importlib.util
import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

import pytest

SCRIPT = Path(__file__).parents[1] / "scripts/cezar_review_guard.py"
SPEC = importlib.util.spec_from_file_location("cezar_guard", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
GUARD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GUARD)
LIVE_REVIEW = Path(__file__).parent / "fixtures/cezar-first-live-review.json"


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


@pytest.mark.parametrize("source", ["summary", "final_response", "combined_header"])
def test_first_live_review(repository: Path, source: str) -> None:
    """Replay verbatim native evidence, rebinding only SHA to a real test commit."""
    fixture = json.loads(LIVE_REVIEW.read_text())
    evidence = report()
    review = evidence["graphState"]["outputs"]["review"]
    summary = fixture["review"]["summary"]
    if source == "final_response":
        summary = fixture[source]
    elif source == "combined_header":
        summary = summary.replace("\nEvidence: verified", " Evidence: verified", 1)
    review.update(fixture["review"])
    review["summary"] = summary.replace(fixture["head"], GUARD.git("rev-parse", "HEAD"))
    GUARD.audit(evidence)


@pytest.mark.parametrize("verdict", ["approve", "changes"])
@pytest.mark.parametrize("combined", [False, True])
@pytest.mark.parametrize("native_marker", [False, True])
def test_header_and_marker_formats(
    repository: Path, verdict: str, combined: bool, native_marker: bool
) -> None:
    evidence = report(verdict)
    review = evidence["graphState"]["outputs"]["review"]
    if combined:
        review["summary"] = review["summary"].replace("\nEvidence:", " Evidence:")
    if native_marker:
        review["summary"] += f"\nCEZ:VERDICT {verdict}"
    GUARD.audit(evidence)


def test_approval_with_structured_nonblocking_finding(repository: Path) -> None:
    evidence = report()
    review = evidence["graphState"]["outputs"]["review"]
    review["summary"] = review["summary"].replace(
        "No blocking findings",
        "[nonblocking] F1 — code.txt:1 — Low; observed/expected/evidence\nNo blocking findings",
    )
    GUARD.audit(evidence)


@pytest.mark.parametrize("invalid_head", ["0" * 40, "a" * 39, "a" * 41, "A" * 40, ""])
def test_invalid_snapshot_rejected(repository: Path, invalid_head: str) -> None:
    evidence = report()
    evidence["graphState"]["outputs"]["snapshot"]["output"] = invalid_head
    with pytest.raises(ValueError, match="snapshot"):
        GUARD.audit(evidence)


@pytest.mark.parametrize("verdict", ["", "unverifiable", "APPROVE", "unknown"])
def test_native_verdict_always_required(repository: Path, verdict: str) -> None:
    evidence = report()
    review = evidence["graphState"]["outputs"]["review"]
    review["summary"] += "\nCEZ:VERDICT approve"
    review["verdict"] = verdict
    with pytest.raises(ValueError, match="verdict unavailable"):
        GUARD.audit(evidence)


@pytest.mark.parametrize(
    "header",
    [
        "Reviewed-commit: {head}\nReviewed-commit: {head}\nEvidence: verified",
        "Reviewed-commit: {head}\nReviewed-commit: {other}\nEvidence: verified",
        "Reviewed-commit: {head} Evidence: verified\nEvidence: verified",
        "Reviewed-commit: {head}\nEvidence: verified\nEvidence: unavailable",
        "Reviewed-commit: {head}\nEvidence: verified\n Evidence: verified",
        "Reviewed-commit: {head}\nEvidence: verified\n**Evidence: unavailable**",
        "Reviewed-commit: {head} Evidence: verified\n* Evidence: verified",
        "Reviewed-commit: {head}\nEvidence: verified\n**Reviewed-commit: {head}**",
        "Reviewed-commit: {head}\nEvidence: verified\nreviewed-commit: {other}",
        "Reviewed-commit: {other}\nEvidence: verified",
        "Reviewed-commit: {head}0\nEvidence: verified",
        "Reviewed-commit: {head:.12}\nEvidence: verified",
        "Reviewed-commit: {head}junk\nEvidence: verified",
        "Reviewed-commit: {head} Evidence: unavailable",
        "Reviewed-commit: {head} Evidence: verified trailing",
        "Reviewed-commit: {head} Evidence: verified Evidence: verified",
        "Reviewed-commit: {head}Evidence: verified",
        "Reviewed-commit: {head}",
        "Reviewed-commit: {head}\nEvidence: verified extra",
        "Reviewed-commit: {head}\nEvidence: unverified\nEvidence: verified",
        "Reviewed-commit: {head}\n**Evidence: verified**",
    ],
)
def test_reject_ambiguous_or_malformed_headers(repository: Path, header: str) -> None:
    evidence = report()
    evidence["graphState"]["outputs"]["review"]["summary"] = (
        header.format(head=GUARD.git("rev-parse", "HEAD"), other="0" * 40)
        + "\nNo blocking findings\nAPPROVE"
    )
    with pytest.raises(ValueError):
        GUARD.audit(evidence)


@pytest.mark.parametrize(
    "ending",
    [
        "REQUEST CHANGES\nAPPROVE",
        "APPROVE\nAPPROVE",
        "APPROVE\nCEZ:VERDICT changes",
        "APPROVE\nCEZ:VERDICT unverifiable",
        "APPROVE\nCEZ:VERDICT approve\nCEZ:VERDICT approve",
        "CEZ:VERDICT changes\nAPPROVE",
        "APPROVE CEZ:VERDICT approve",
        "APPROVE\nCEZ:VERDICT:approve",
        "CEZ:VERDICT approve",
        "APPROVE\ntrailing text",
    ],
)
def test_reject_conflicting_or_malformed_verdicts(repository: Path, ending: str) -> None:
    evidence = report()
    review = evidence["graphState"]["outputs"]["review"]
    review["summary"] = review["summary"].removesuffix("APPROVE") + ending
    with pytest.raises(ValueError):
        GUARD.audit(evidence)


@pytest.mark.parametrize(
    "finding",
    [
        "[blocking] F",
        "[blocking] F1",
        "[blocking] F1 — no location — defect",
        "[blocking] F1 — code.txt:0 — defect",
        "[blocking] F1 — code.txt:1 — ",
        "[blocking] F0 — code.txt:1 — defect",
        "[blocking] F1 — code.txt:1 — defect\n[blocking] F1 — code.txt:2 — duplicate",
        "[nonblocking] F1 — code.txt:1 — only nonblocking",
        "- F1 — Low, nonblocking — no location: detail",
        "[blocking] F1 — code.txt:1 — defect\nNo blocking findings",
        "[blocking] F1 — code.txt:1 — defect\n- F — code.txt:2 — missing ID",
    ],
)
def test_reject_malformed_repair_findings(repository: Path, finding: str) -> None:
    evidence = report("changes")
    head = GUARD.git("rev-parse", "HEAD")
    evidence["graphState"]["outputs"]["review"]["summary"] = (
        f"Reviewed-commit: {head}\nEvidence: verified\n{finding}\nREQUEST CHANGES"
    )
    with pytest.raises(ValueError):
        GUARD.audit(evidence)


def test_approval_cannot_contain_blocking_findings(repository: Path) -> None:
    evidence = report()
    review = evidence["graphState"]["outputs"]["review"]
    review["summary"] = review["summary"].replace(
        "No blocking findings", "[blocking] F1 — code.txt:1 — defect\nNo blocking findings"
    )
    with pytest.raises(ValueError):
        GUARD.audit(evidence)


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


@pytest.mark.parametrize("mode", [None, "", "true", "2", "1"])
def test_environment_alone_cannot_enable_full_access(
    monkeypatch: pytest.MonkeyPatch, mode: str | None, tmp_path: Path
) -> None:
    monkeypatch.setattr(GUARD, "ATTESTATION", tmp_path / "missing")
    monkeypatch.setenv("CEZ_PILOT_CONTAINER", "1")
    if mode is None:
        monkeypatch.delenv("CEZ_CODEX_NETWORK", raising=False)
    else:
        monkeypatch.setenv("CEZ_CODEX_NETWORK", mode)
    with pytest.raises(ValueError):
        GUARD.verify_codex_mode()


@pytest.fixture
def container_record(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    record = tmp_path / "verified.json"
    record.write_text(json.dumps({"schema": 1, "runtime": "current"}))
    record.chmod(0o444)
    monkeypatch.setattr(GUARD, "ATTESTATION", record)
    original_stat = Path.stat
    original_fstat = os.fstat

    def root_info(info: os.stat_result, *, mode: int | None = None) -> os.stat_result:
        fields = list(info)
        fields[4] = 0
        if mode is not None:
            fields[0] = mode
        return os.stat_result(fields)

    def protected_parent(path: Path, **kwargs: Any) -> os.stat_result:
        info = original_stat(path, **kwargs)
        return root_info(info, mode=stat.S_IFDIR | 0o755) if path in record.parents else info

    monkeypatch.setattr(Path, "stat", protected_parent)
    monkeypatch.setattr(os, "access", lambda *_args: False)
    monkeypatch.setattr(os, "fstat", lambda fd: root_info(original_fstat(fd)))
    monkeypatch.setattr(GUARD, "container_state", lambda: {"schema": 1, "runtime": "current"})
    monkeypatch.setattr(GUARD, "git", lambda *_args: "/workspace/.git")
    monkeypatch.setenv("HOME", "/home/pilot")
    monkeypatch.setenv("CEZ_HOME", "/home/pilot/.cezar")
    monkeypatch.setenv("CEZ_CODEX_NETWORK", "1")
    return record


def test_verified_record_permits_container_mode(container_record: Path) -> None:
    GUARD.verify_codex_mode()


@pytest.mark.parametrize(
    "problem", ["owner", "writable", "parent", "symlink", "stale", "home", "checkout"]
)
def test_untrusted_or_stale_container_record_rejected(
    container_record: Path, monkeypatch: pytest.MonkeyPatch, problem: str
) -> None:
    if problem == "owner":
        actual_fstat = os.fstat

        def workload_owned(fd: int) -> os.stat_result:
            fields = list(actual_fstat(fd))
            fields[4] = 1000
            return os.stat_result(fields)

        monkeypatch.setattr(os, "fstat", workload_owned)
    elif problem == "writable":
        container_record.chmod(0o644)
    elif problem == "parent":
        monkeypatch.setattr(os, "access", lambda *_args: True)
    elif problem == "symlink":
        link = container_record.with_name("symlink.json")
        link.symlink_to(container_record)
        monkeypatch.setattr(GUARD, "ATTESTATION", link)
    elif problem == "stale":
        monkeypatch.setattr(GUARD, "container_state", lambda: {"schema": 1, "runtime": "restarted"})
    elif problem == "home":
        monkeypatch.setenv("CEZ_HOME", "/workspace/user-controlled")
    else:
        monkeypatch.setattr(GUARD, "git", lambda *_args: "/another-project/.git")
    with pytest.raises(ValueError):
        GUARD.verify_codex_mode()


@pytest.mark.parametrize(
    "problem", [None, "root", "writable-root", "capability", "seccomp", "privileges", "apparmor"]
)
def test_kernel_restrictions_are_checked(
    monkeypatch: pytest.MonkeyPatch, problem: str | None
) -> None:
    from types import SimpleNamespace

    monkeypatch.setattr(os, "getuid", lambda: 0 if problem == "root" else 1000)
    monkeypatch.setattr(os, "geteuid", lambda: 1000)
    monkeypatch.setattr(os, "getgid", lambda: 1000)
    monkeypatch.setattr(
        os,
        "statvfs",
        lambda _path: SimpleNamespace(f_flag=0 if problem == "writable-root" else os.ST_RDONLY),
    )
    status = {key: "0" for key in ("CapInh", "CapPrm", "CapEff", "CapBnd", "CapAmb")}
    status.update(NoNewPrivs="1", Seccomp="2")
    if problem == "capability":
        status["CapBnd"] = "1"
    if problem == "seccomp":
        status["Seccomp"] = "0"
    if problem == "privileges":
        status["NoNewPrivs"] = "0"
    files = {
        "/proc/self/status": "\n".join(f"{key}: {value}" for key, value in status.items()),
        "/proc/self/attr/current": "unconfined"
        if problem == "apparmor"
        else "docker-default (enforce)",
        "/proc/1/stat": "1 (init) " + " ".join(["0"] * 20),
    }
    monkeypatch.setattr(Path, "read_text", lambda path: files[str(path)])
    monkeypatch.setattr(Path, "read_bytes", lambda _path: b"mount-table")
    monkeypatch.setattr(Path, "exists", lambda _path: False)
    monkeypatch.setattr(os, "readlink", lambda path: str(path))
    if problem is None:
        assert GUARD.container_state()["schema"] == 1
    else:
        with pytest.raises(ValueError):
            GUARD.container_state()
