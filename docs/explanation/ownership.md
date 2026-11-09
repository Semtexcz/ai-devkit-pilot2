# File ownership

Three tools created this project, and each owns a different set of files. Knowing
which is which explains why the overlay can be updated without touching your
code, and why `pyproject.toml` is never edited by the template.

## Who created what

| Layer | Concern | Files |
|---|---|---|
| Native `uv init` | the Python application | `main.py`, `pyproject.toml` |
| uv (ongoing) | environment, dependencies, lockfile | `pyproject.toml`, `uv.lock`, `.venv/` |
| mise | interpreter, tool versions, tasks | `mise.toml`, `mise.lock` |
| Copier overlay | standards and documentation seeds | `AGENTS.md`, `ruff.toml`, `mypy.ini`, `pytest.ini`, `zensical.toml`, `docs/`, `tests/`, `.gitignore`, `.copier-answers.yml` |
| OpenSpec `init` (ongoing) | specifications, change checklists, agent integrations | `openspec/`, `.opencode/`, `.agents/` |
| You | application behavior and the specifications you write | `main.py`, `openspec/specs/`, `openspec/changes/`, `CHANGELOG.md` |

`CHANGELOG.md` is the one file the overlay seeds and then hands over. It arrives with
an empty `[Unreleased]` section, and from that moment the project owns it: an overlay
update replays the difference between template revisions, so the template's copy
never overwrites the entries you add.

## Why the overlay does not own `pyproject.toml`

`pyproject.toml` is the file uv rewrites whenever a dependency changes. A template
that also rendered it would produce a second writer with a conflicting opinion,
and every dependency change would become a template conflict. The same reasoning
covers `uv.lock`, `.venv/` and `main.py`: uv and the developer own them, so the
overlay stays out of them entirely.

The template therefore renders configuration that is *policy* (how to lint, how to
type-check, how to test, how to build docs) and never configuration that is
*resolution* (which packages, which versions, which interpreter).

## Where the checker settings live

| Tool | File | Why not `pyproject.toml` |
|---|---|---|
| Ruff | `ruff.toml` | standalone file, no template edits inside a uv-owned file |
| mypy | `mypy.ini` | same |
| pytest | `pytest.ini` | same |

None of these files declares a dependency. Tool versions are installed by uv from
`pyproject.toml` and pinned in `mise.toml`; the checker files only state policy.

## The one project-owned edit

The scaffold produced by `uv init` defines its entry point without a return
annotation:

```python
def main():
```

`mypy --strict` rejects that, and weakening the standard to accept it would give
up the check most likely to catch a real defect. The annotation is therefore added
once, by you, as part of creating the project:

```python
def main() -> None:
```

Copier does not make this edit. It is a project-owned change to project-owned
code, so it must not arrive as a template overlay that could later conflict with
your own edits to `main.py`.

## Verification contract

`mise run check` runs the same commands a reviewer would:

```text
uv lock --check
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy --strict main.py
uv run --locked pytest
uv run --locked zensical build --strict
openspec validate --all --strict --no-interactive
```

The first six belong to tools uv runs and the overlay configures. The last one is
OpenSpec's own validation: it reads `openspec/specs/` and `openspec/changes/` and
fails on a malformed requirement, so a specification cannot drift into prose that no
tool can check.

The type-checking target is `main.py` only. Widen it in `mypy.ini` and in the
`typecheck` task when you add modules, so both stay in step.

## Provenance and updates

`.copier-answers.yml` records the template source (`_src_path`) and template
version (`_commit`). Commit it. It is what makes `copier update` possible: Copier
replays your answers against the newer template and applies the difference, so
project-owned files such as `main.py` and `pyproject.toml` are never overwritten.
The update procedure is in
[Update the shared overlay](../how-to/update-the-overlay.md).

## Limits

- Linux x86-64 is the verified platform. `mise.lock` covers `linux-x64` only.
- The project is an unpackaged application: there is no build backend and nothing
  is published.
- The documentation site is optional; the README carries the contract.
