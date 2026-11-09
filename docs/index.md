# ai-devkit-pilot2

A small Python script project.

This site documents the project as it is today. It is deliberately small: a
README is the contract, and these pages explain the parts that need more than a
line.

## What works today

- `main.py` runs (`mise run start`).
- `mise run check` passes: locked dependency check, Ruff lint, Ruff format check,
  `mypy --strict`, pytest, this documentation build and OpenSpec validation.
- The project has its own `uv.lock` and `mise.lock`, so both dependency layers are
  reproducible.
- `openspec/` holds the specifications and the proposed changes, initialized once
  with `openspec init --tools opencode,codex --profile core`.

## Start here

| Section | Purpose | Start here |
|---|---|---|
| Tutorial | Learn the workflow by doing it | [Run and verify the script](tutorials/run-the-script.md) |
| How-to guide | Achieve a specific goal | [Add a dependency](how-to/add-a-dependency.md) |
| Reference | Look up exact commands and versions | [Commands and versions](reference/commands.md) |
| Explanation | Understand how the files relate | [File ownership](explanation/ownership.md) |

Planning a change before implementing it: [Work with OpenSpec](how-to/use-openspec.md).

Notable changes to this project are recorded in `CHANGELOG.md` at the project root.

The engineering rules that apply to changes in this project are in `AGENTS.md` at
the repository root.
