"""Validate local Git and Cezar evidence; orchestration belongs to Cezar."""

import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ATTESTATION = Path("/run/cezar-pilot-attestation.json")
NAMESPACES = ("pid", "mnt", "ipc", "uts", "net", "cgroup")


def container_state() -> dict[str, Any]:
    """Read kernel state, never an environment claim about container isolation."""
    if (os.getuid(), os.geteuid(), os.getgid()) != (1000, 1000, 1000):
        raise ValueError("container pilot requires uid/gid 1000")
    if not os.statvfs("/").f_flag & os.ST_RDONLY:
        raise ValueError("container root filesystem must be read-only")
    status = dict(
        line.split(":", 1)
        for line in Path("/proc/self/status").read_text().splitlines()
        if ":" in line
    )
    for key in ("CapInh", "CapPrm", "CapEff", "CapBnd", "CapAmb"):
        if int(status[key].strip(), 16):
            raise ValueError("container capabilities must all be zero")
    if status["NoNewPrivs"].strip() != "1" or status["Seccomp"].strip() != "2":
        raise ValueError("container requires no-new-privileges and seccomp")
    if Path("/proc/self/attr/current").read_text().strip() != "docker-default (enforce)":
        raise ValueError("container requires Docker default AppArmor")
    for path in ("/home/semtex", "/mnt/Data", "/var/run/docker.sock", "/run/podman"):
        if Path(path).exists():
            raise ValueError(f"unexpected host path in container: {path}")
    return {
        "schema": 1,
        "namespaces": {name: os.readlink(f"/proc/self/ns/{name}") for name in NAMESPACES},
        "mounts_sha256": hashlib.sha256(Path("/proc/self/mountinfo").read_bytes()).hexdigest(),
        "pid1_starttime": Path("/proc/1/stat").read_text().rsplit(")", 1)[1].split()[19],
    }


def verified_container() -> None:
    """Require host-provisioned evidence bound to this container lifetime."""
    for parent in ATTESTATION.parents:
        info = parent.stat()
        if info.st_uid != 0 or info.st_mode & 0o022 or os.access(parent, os.W_OK):
            raise ValueError("container attestation parent is not protected")
    with os.fdopen(os.open(ATTESTATION, os.O_RDONLY | os.O_NOFOLLOW)) as handle:
        info = os.fstat(handle.fileno())
        if info.st_uid != 0 or info.st_mode & 0o222 or not stat.S_ISREG(info.st_mode):
            raise ValueError("container attestation must be root-owned and read-only")
        attested = json.load(handle)
    if attested != container_state():
        raise ValueError("container attestation does not match live runtime")
    if (
        os.environ.get("HOME") != "/home/pilot"
        or os.environ.get("CEZ_HOME") != "/home/pilot/.cezar"
    ):
        raise ValueError("container pilot requires separate fixed agent/Cezar homes")
    if Path(git("rev-parse", "--git-common-dir")).resolve().parent != Path("/workspace"):
        raise ValueError("container pilot requires the disposable /workspace checkout")


def verify_codex_mode() -> None:
    mode = os.environ.get("CEZ_CODEX_NETWORK")
    if mode == "1":
        try:
            verified_container()
        except OSError as error:
            raise ValueError("verified container evidence unavailable") from error
    elif mode != "0":
        raise ValueError("start with CEZ_CODEX_NETWORK=0 (host) or verified container mode")


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
        verify_codex_mode()
        for key, expected in {
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
