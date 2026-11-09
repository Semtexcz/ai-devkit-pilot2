"""Verify the prepared Docker pilot and provision non-secret preflight evidence.

Run on the host, through mise. No sandbox or agent orchestration is implemented.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from cezar_review_guard import NAMESPACES

CONTAINER = "cezar-pilot2-isolated"
IMAGE = "sha256:94a1cde48f9cc284f4f30fd3affe49f4d343724408b76df8d211f0abbed991e5"
PYTHON = "/opt/mise/installs/python/3.13.18/bin/python3"


def check_runtime(info: dict[str, Any]) -> None:
    """Reject deviations from this explicitly reviewed disposable runtime."""
    host = info["HostConfig"]
    config = info["Config"]
    required = {
        "Privileged": False,
        "ReadonlyRootfs": True,
        "CapAdd": None,
        "CapDrop": ["ALL"],
        "SecurityOpt": ["no-new-privileges:true"],
        "PidMode": "",
        "IpcMode": "private",
        "CgroupnsMode": "private",
        "NetworkMode": "cezar-pilot2-isolated_pilot",
        "PortBindings": {"4322/tcp": [{"HostIp": "127.0.0.1", "HostPort": "4322"}]},
        "Devices": None,
        "DeviceCgroupRules": None,
        "DeviceRequests": None,
        "VolumesFrom": None,
        "Binds": [
            "cezar-pilot2-isolated_project:/workspace:rw",
            "cezar-pilot2-isolated_home:/home/pilot:rw",
        ],
        "UsernsMode": "",
        "UTSMode": "",
        "Runtime": "runc",
        "ReadonlyPaths": ["/proc/bus", "/proc/fs", "/proc/irq", "/proc/sys", "/proc/sysrq-trigger"],
        "PidsLimit": 512,
        "Memory": 8 * 1024**3,
        "NanoCpus": 4 * 10**9,
        "Init": True,
        "RestartPolicy": {"Name": "no", "MaximumRetryCount": 0},
        "Tmpfs": {
            "/tmp": "rw,nosuid,nodev,size=2g,mode=1777",
            "/run": "rw,nosuid,nodev,noexec,size=16m,mode=755",
        },
    }
    for key, expected in required.items():
        if host.get(key) != expected:
            raise ValueError(f"unapproved Docker setting: {key}")
    if not {
        "/proc/asound",
        "/proc/acpi",
        "/proc/interrupts",
        "/proc/kcore",
        "/proc/keys",
        "/proc/latency_stats",
        "/proc/timer_list",
        "/proc/timer_stats",
        "/proc/sched_debug",
        "/proc/scsi",
        "/sys/firmware",
        "/sys/devices/virtual/powercap",
    }.issubset(host.get("MaskedPaths") or []):
        raise ValueError("Docker default masked paths must remain protected")
    if (
        not info["State"]["Running"]
        or info["Image"] != IMAGE
        or config["User"] != "1000:1000"
        or info["AppArmorProfile"] != "docker-default"
        or config.get("WorkingDir") != "/workspace"
    ):
        raise ValueError("unexpected image, identity, AppArmor or container state")
    mounts = {(m["Type"], m.get("Name"), m["Destination"], m["RW"]) for m in info["Mounts"]}
    if len(info["Mounts"]) != 2 or mounts != {
        ("volume", "cezar-pilot2-isolated_project", "/workspace", True),
        ("volume", "cezar-pilot2-isolated_home", "/home/pilot", True),
    }:
        raise ValueError("unexpected mounts; only the two disposable volumes are allowed")
    env = dict(item.split("=", 1) for item in config["Env"])
    for key, expected in {
        "CEZ_CODEX_NETWORK": "1",
        "CEZ_DISPATCH": "0",
        "CEZ_AUTOMATIONS": "0",
        "CEZ_AUTONAME": "0",
        "CEZ_TITLE_UPDATES": "0",
        "CEZ_TELEMETRY": "0",
        "HOME": "/home/pilot",
        "CEZ_HOME": "/home/pilot/.cezar",
    }.items():
        if env.get(key) != expected:
            raise ValueError(f"unexpected container environment: {key}")
    for key in (
        "OPENAI_API_KEY",
        "CODEX_API_KEY",
        "DEEPSEEK_API_KEY",
        "SSH_AUTH_SOCK",
        "GH_TOKEN",
        "GITHUB_TOKEN",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "DOCKER_HOST",
        "CEZ_AGENT_MODELS_LOCKED",
    ):
        if env.get(key):
            raise ValueError(f"unexpected credential or override injection: {key}")


def docker(*args: str, input_text: str | None = None) -> str:
    return subprocess.check_output(["docker", *args], input=input_text, text=True)


def main() -> None:
    info = json.loads(docker("inspect", CONTAINER))[0]
    check_runtime(info)
    network = json.loads(docker("network", "inspect", "cezar-pilot2-isolated_pilot"))[0]
    if (
        network["Driver"] != "bridge"
        or network["Options"].get("com.docker.network.bridge.enable_icc") != "false"
    ):
        raise ValueError("unexpected Docker network policy")
    daemon = json.loads(docker("info", "--format", "{{json .SecurityOptions}}"))
    if "name=seccomp,profile=builtin" not in daemon or "name=apparmor" not in daemon:
        raise ValueError("default Docker seccomp/AppArmor are required")
    for name in ("cezar-pilot2-isolated_project", "cezar-pilot2-isolated_home"):
        volume = json.loads(docker("volume", "inspect", name))[0]
        if (
            volume["Driver"] != "local"
            or volume.get("Options")
            or volume["Mountpoint"] != f"/var/lib/docker/volumes/{name}/_data"
        ):
            raise ValueError("volume must be ordinary Docker storage, without driver options")
    # Execute the reviewed local guard source rather than a project-writable copy.
    source = Path(__file__).with_name("cezar_review_guard.py").read_text()
    probe = (
        source.split('if __name__ == "__main__":')[0] + "\nprint(json.dumps(container_state()))\n"
    )
    state_text = docker("exec", "-i", CONTAINER, PYTHON, "-I", "-S", "-", input_text=probe)
    state = json.loads(state_text)
    for name in NAMESPACES:
        if state["namespaces"][name] == os.readlink(f"/proc/self/ns/{name}"):
            raise ValueError(f"host {name} namespace is shared")
    # Inspect again before provisioning: do not bless a replacement/restarted container.
    after = json.loads(docker("inspect", CONTAINER))[0]
    check_runtime(after)
    if (info["Id"], info["State"]["StartedAt"]) != (after["Id"], after["State"]["StartedAt"]):
        raise ValueError("container changed during verification")
    provision = """import os, sys
from pathlib import Path
target = Path("/run/cezar-pilot-attestation.json")
temporary = target.with_suffix(".new")
flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
with os.fdopen(os.open(temporary, flags, 0o444), "w") as handle:
    handle.write(sys.stdin.read())
os.replace(temporary, target)
"""
    docker(
        "exec",
        "--user",
        "0:0",
        "-i",
        CONTAINER,
        PYTHON,
        "-I",
        "-S",
        "-c",
        provision,
        input_text=state_text,
    )
    print("Verified Docker isolation; provisioned root-owned runtime-bound preflight record")


if __name__ == "__main__":
    try:
        main()
    except (KeyError, ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"STOP: {error}", file=sys.stderr)
        sys.exit(1)
