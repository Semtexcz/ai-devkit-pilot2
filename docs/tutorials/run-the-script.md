# Run and verify the script

This tutorial takes you from the generated project to a verified change. It
assumes the project already exists and that `mise` is installed.

You will install the pinned tools, run the script, change its message temporarily,
and confirm that the same command a reviewer runs still passes once you restore the
default.

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

This runs `uv run --locked python main.py` and prints exactly:

```text
Hello from ai-devkit-pilot2!
```

Pass a name to replace the default:

```bash
uv run --locked python main.py --name Ada
```

That prints exactly `Hello from Ada!`. To discover the option and its value, run:

```bash
uv run --locked python main.py --help
```

The help lists `--name NAME`. An unknown argument, or `--name` without a value,
writes a diagnostic to stderr and exits with a nonzero status without printing a
greeting.

## Step 4: change the message temporarily

Open `main.py` and change `DEFAULT_NAME`. Keep the type annotations: the strict
`mypy` configuration requires them, and they were added by you rather than by the
generator.

```python
DEFAULT_NAME = "your-name"
```

Then run the script again:

```bash
mise run start
```

The default output is now `Hello from your-name!`, and `--name Ada` still
overrides it.

This edit is an exercise, not a change to the agreed behavior. The "Default
greeting" requirement in `openspec/specs/greeting/spec.md` and the exact-output
tests in `tests/test_main.py` both require `Hello from ai-devkit-pilot2!`, so
restore the default before you verify:

```python
DEFAULT_NAME = "ai-devkit-pilot2"
```

## Step 5: verify

```bash
mise run check
```

Every check must pass before the change is complete: locked dependencies, lint,
formatting, types, tests, the documentation build and OpenSpec validation. The tests
in `tests/test_main.py` run `main.py` as a subprocess and assert the exact default
and named output, help, invalid-argument behavior and execution without site
packages.

These checks verify the unchanged contract, so they pass with the default restored
as described in step 4; leaving `your-name` in place fails the exact-output tests.
If you want the customized greeting to stay, propose it as a separately approved
OpenSpec change that updates the specification and the expected output in
`tests/test_main.py` together with `main.py`.

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
