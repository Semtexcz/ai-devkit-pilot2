# Commands and versions

Exact commands, the tasks that wrap them, and the versions the project was
generated with. Tool and dependency versions are recorded in `mise.lock` and
`uv.lock`; this page explains how to look them up and how to change them.

## Tasks

| Task | Underlying command | Purpose |
|---|---|---|
| `mise run check` | every task below, in order | the single verification command |
| `mise run lock-check` | `uv lock --check` | `uv.lock` matches `pyproject.toml` |
| `mise run lint` | `uv run --locked ruff check .` | lint |
| `mise run format-check` | `uv run --locked ruff format --check .` | formatting, without rewriting |
| `mise run format` | `uv run --locked ruff format . && uv run --locked ruff check --fix .` | apply formatting and safe fixes |
| `mise run typecheck` | `uv run --locked mypy --strict main.py` | types |
| `mise run test` | `uv run --locked pytest` | tests |
| `mise run docs` | `uv run --locked zensical build --strict` | documentation, fails on a broken link |
| `mise run docs-serve` | `uv run --locked zensical serve` | local preview |
| `mise run spec-check` | `openspec validate --all --strict --no-interactive` | specifications and proposed changes |
| `mise run start` | `uv run --locked python main.py` | run the script |
| `mise run lock-tools` | `mise lock` | regenerate `mise.lock` |

`mise run check` runs: `uv lock --check`, then lint, format check, type check,
tests, the documentation build and OpenSpec validation. Any failure stops the run
with a nonzero exit code. `[settings] jobs = 1` in `mise.toml` runs the checks one
at a time, so they cannot race when `.venv` does not exist yet.

## Specifications

OpenSpec is initialized once per project, with `openspec init --tools
opencode,codex --profile core`; see [Work with OpenSpec](../how-to/use-openspec.md).

| Command | Purpose |
|---|---|
| `openspec list` | changes in `openspec/changes/`; `--specs` lists the specifications |
| `openspec new change <name>` | create a change directory |
| `openspec status --change <name>` | which artifacts of a change exist |
| `openspec validate <name> --strict` | validate one change |
| `openspec validate --all --strict --no-interactive` | what `mise run spec-check` runs |
| `openspec archive <name>` | move an accepted change and update the main specification |

`openspec validate` fails when the project has no `openspec/` root, which is why the
one-time initialization comes before the first `mise run check`. It also passes with
`No items found to validate.` when no specification exists yet: an empty scope is
not evidence that validation works, so treat the first real specification as the
proof.

## Versions

| Tool | Version | Recorded in | Owner |
|---|---|---|---|
| Python | 3.13.18 | `mise.toml` | mise |
| uv | 0.13.7 | `mise.toml` | mise |
| Node.js | 24.22.2 | `mise.toml` | mise |
| OpenSpec | 1.16.0 | `mise.toml` | mise |
| Ruff | 0.17.3 | `pyproject.toml`, `uv.lock` | uv |
| mypy | 2.4.1 | `pyproject.toml`, `uv.lock` | uv |
| pytest | 9.2.0 | `pyproject.toml`, `uv.lock` | uv |
| Zensical | 0.0.74 | `pyproject.toml`, `uv.lock` | uv |

Confirm what is installed:

```bash
mise exec -- python --version
mise exec -- uv --version
mise exec -- node --version
mise exec -- openspec --version
uv run --locked ruff --version
uv run --locked mypy --version
uv run --locked pytest --version
uv run --locked zensical --version
```

OpenSpec is a Node.js CLI, so Node.js is pinned next to it in `mise.toml`: the
executable must not depend on a Node.js installation from the host.

## Lockfiles

There are two, one per ownership boundary:

| File | Scope | Regenerate with |
|---|---|---|
| `mise.lock` | interpreter, uv and other CLI releases, with checksums | `mise lock` |
| `uv.lock` | the resolved Python dependency graph, with hashes | `uv lock` (or any `uv add` / `uv remove`) |

Both are committed. Never hand-edit either one: regenerate and review the diff.

### Generate `mise.lock`

The project ships without `mise.lock`, because the lock describes the machine
that generated it. Create and commit it once, on the platform you support:

```bash
mise lock                     # same as `mise run lock-tools`
git add mise.lock .mise/locks/
git commit -m "chore: lock tool versions"
```

Commit both, because a reproducible install needs both:

| Path | Contents |
|---|---|
| `mise.lock` | the resolved version, checksum and download URL of every tool in `[tools]` |
| `.mise/locks/` | the npm sidecar lock for a tool mise installs from npm — here `npm:@fission-ai-openspec` — which records that CLI's transitive dependency graph |

OpenSpec is a Node.js CLI, so mise resolves its dependencies through npm and
keeps that graph next to `mise.lock`. Staging only `mise.lock` leaves the sidecar
untracked, and a fresh checkout then re-resolves the npm graph instead of
installing the reviewed one.

After that, `mise install --locked` installs only the recorded versions and
verifies their checksums. Update the lock the same way after changing `[tools]`
in `mise.toml`; the diff should show the changed tool plus the sidecar entry for
an npm tool.

## Environment behavior

`mise.toml` sets two environment variables so that Python has one owner:

| Variable | Effect |
|---|---|
| `UV_NO_MANAGED_PYTHON=1` | uv must use a system interpreter; it implies "only-system" preference |
| `UV_PYTHON_DOWNLOADS=never` | uv must not download an interpreter |

Set `UV_PYTHON_PREFERENCE` nowhere: uv rejects it together with
`UV_NO_MANAGED_PYTHON` ("cannot be used with `--python-preference`"). The
equivalent `[tool.uv]` settings belong in `pyproject.toml`, which uv owns.

Verify that the environment uses the interpreter mise selects:

```bash
mise which python
readlink -f .venv/bin/python
[ "$(readlink -f .venv/bin/python)" = "$(readlink -f "$(mise which python)")" ] \
  && echo "OK: the virtual environment uses the mise-selected interpreter"
```

There is no `.python-version` file: `mise.toml` is the only statement of the
required interpreter.
