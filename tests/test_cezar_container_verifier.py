"""Reject weakened Docker configurations before any root provisioning occurs."""

import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def verifier(monkeypatch: pytest.MonkeyPatch) -> Any:
    scripts = Path(__file__).parents[1] / "scripts"
    monkeypatch.syspath_prepend(str(scripts))
    spec = importlib.util.spec_from_file_location("verifier", scripts / "verify_cezar_container.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def runtime() -> dict[str, Any]:
    fixture = Path(__file__).parent / "fixtures/cezar-docker-runtime.json"
    return dict(json.loads(fixture.read_text()))


def test_original_hardened_runtime_accepted(verifier: Any, runtime: dict[str, Any]) -> None:
    verifier.check_runtime(runtime)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("Privileged", True),
        ("ReadonlyRootfs", False),
        ("CapAdd", ["SYS_ADMIN"]),
        ("CapDrop", []),
        ("SecurityOpt", ["seccomp=unconfined"]),
        ("SecurityOpt", ["apparmor=unconfined"]),
        ("PidMode", "host"),
        ("IpcMode", "host"),
        ("CgroupnsMode", "host"),
        ("NetworkMode", "host"),
        ("UsernsMode", "host"),
        ("Binds", ["/home:/host-home"]),
        ("ReadonlyPaths", []),
        ("MaskedPaths", []),
        ("Tmpfs", {}),
        ("PortBindings", {"4322/tcp": [{"HostIp": "0.0.0.0", "HostPort": "4322"}]}),
    ],
)
def test_weakened_host_config_rejected(
    verifier: Any, runtime: dict[str, Any], field: str, value: Any
) -> None:
    runtime["HostConfig"][field] = value
    with pytest.raises(ValueError):
        verifier.check_runtime(runtime)


@pytest.mark.parametrize("problem", ["root", "apparmor", "image", "mount", "extra-mount", "env"])
def test_other_runtime_authority_changes_rejected(
    verifier: Any, runtime: dict[str, Any], problem: str
) -> None:
    if problem == "root":
        runtime["Config"]["User"] = "0:0"
    elif problem == "apparmor":
        runtime["AppArmorProfile"] = "unconfined"
    elif problem == "image":
        runtime["Image"] = "unreviewed-image"
    elif problem == "mount":
        runtime["Mounts"][0]["Type"] = "bind"
    elif problem == "extra-mount":
        runtime["Mounts"].append(runtime["Mounts"][0])
    else:
        runtime["Config"]["Env"].append("OPENAI_API_KEY=synthetic-only")
    with pytest.raises(ValueError):
        verifier.check_runtime(runtime)
