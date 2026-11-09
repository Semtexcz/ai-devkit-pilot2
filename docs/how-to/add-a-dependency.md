# Add a dependency

Use `uv` for every dependency change. It edits `pyproject.toml` and `uv.lock`
together and installs the result, so no file is left inconsistent.

## Add a runtime dependency

```bash
uv add requests
```

This adds `requests` to `[project] dependencies` in `pyproject.toml`, updates
`uv.lock`, and installs it into `.venv`. Then verify:

```bash
mise run check
```

## Add a development dependency

Development tools live in the `dev` dependency group, which is where Ruff, mypy,
pytest and Zensical already are:

```bash
uv add --dev respx
```

## Remove a dependency

```bash
uv remove requests
uv remove --dev respx
```

## Update a dependency on purpose

```bash
uv lock --upgrade-package requests   # one package
uv lock --upgrade                    # the whole resolved graph
```

Review the `uv.lock` diff before accepting it. An unrelated package moving is a
reason to stop and ask why, not to re-lock until the build passes.

## Verify that the lockfile still matches

```bash
uv lock --check
```

`mise run check` runs this first, so a `pyproject.toml` edit that was not followed
by a lock update fails immediately and visibly.

## Do not edit these files by hand

| File | Owner |
|---|---|
| `pyproject.toml` | uv (via `uv add`, `uv remove`) |
| `uv.lock` | uv (`uv lock`, `uv add`, `uv sync`) |

If you need a version constraint that `uv add` cannot express, edit
`pyproject.toml` and then run `uv lock` — never edit `uv.lock` directly.

## Tool versions are not dependencies

Python, uv and the other CLIs are pinned in `mise.toml`, not in
`pyproject.toml`. Changing a tool version is a `mise.toml` edit followed by
`mise lock`, which regenerates `mise.lock`; see
[Commands and versions](../reference/commands.md).
