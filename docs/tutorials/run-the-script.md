# Run and verify the script

This tutorial takes you from the generated project to a verified change. It
assumes the project already exists and that `mise` is installed.

You will install the pinned tools, run the script, change its message, and
confirm that the same command a reviewer runs still passes.

## Before you begin

The project directory contains `main.py`, `pyproject.toml` and `uv.lock` (created
by uv), plus `mise.toml` and the documentation seeds (created by the shared
overlay). Do not edit `uv.lock` by hand; uv owns it.

## Step 1: install the pinned tools

```bash
mise trust      # review mise.toml, then confirm
mise install    # Python and uv at the versions recorded in mise.toml
```

`mise trust` is required because `mise.toml` sets environment variables. Once
trusted, `mise run` and `mise exec` use the pinned versions without further
prompting.

## Step 2: create the environment

```bash
uv sync --locked
```

`--locked` refuses to resolve a new dependency graph: the environment must match
`uv.lock`. That refusal is the point — an unexpected update becomes a visible
failure instead of a silent change.

## Step 3: run the script

```bash
mise run start
```

This runs `uv run --locked python main.py`. The output is whatever `main.py`
prints.

## Step 4: change the message

Open `main.py` and change the printed text. Keep the type annotation on `main`:
`mypy --strict` requires it, and the annotation was added by you rather than by
the generator.

```python
def main() -> None:
    print("Your new message")
```

Then run the script again:

```bash
mise run start
```

## Step 5: verify

```bash
mise run check
```

Every check must pass before the change is complete: locked dependencies, lint,
formatting, types, tests, the documentation build and OpenSpec validation. The smoke
test in `tests/test_main.py` runs `main.py` as a subprocess and asserts only that it
succeeds and prints something, so it keeps passing when the message changes.

If a check fails, fix the cause. Do not relax the checker configuration in
`ruff.toml`, `mypy.ini` or `pytest.ini` to obtain a passing result.

The last check, `openspec validate --all --strict --no-interactive`, needs the
one-time `openspec init --tools opencode,codex --profile core` from the README; it
fails instead of skipping when the project has no `openspec/` root.

## What you have now

A project where one command, `mise run check`, verifies dependency locking, style,
types, behavior, documentation and specifications. To add a library, read
[Add a dependency](../how-to/add-a-dependency.md). To plan a change before
implementing it, read [Work with OpenSpec](../how-to/use-openspec.md). To understand
which tool owns which file, read [File ownership](../explanation/ownership.md).
