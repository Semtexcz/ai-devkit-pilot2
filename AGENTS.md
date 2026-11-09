# AGENTS.md

Engineering instructions for people and coding agents working on this project.

## Reuse first

1. Reuse a maintained tool that already solves the problem.
2. Configure it through its native configuration.
3. Extend it only where the maintained behavior stops.
4. Build only what is specific to this project.

Prefer the standard library and the dependencies already installed. Add a
dependency only when it removes more code than it adds, and record it with
`uv add` so `pyproject.toml` and `uv.lock` stay in step.

## Ownership

| Concern | Owner |
|---|---|
| Python interpreter, uv, Node.js and OpenSpec versions, tasks | `mise.toml` |
| `pyproject.toml`, `uv.lock`, `.venv/`, `main.py` | uv and this project |
| `AGENTS.md`, checker configuration, documentation seeds | the Copier overlay |
| `CHANGELOG.md` | this project, after the overlay seeded it once |
| `openspec/` specifications and proposed changes | OpenSpec, driven by this project |
| `.opencode/`, `.agents/` integration files | OpenSpec's `init` and `update` commands |
| Application behavior | you |

Work through mise so the pinned versions apply: `mise run <task>` or
`mise exec -- uv ...`. Do not add a `.python-version` file; `mise.toml` is the
single statement of the required interpreter.

Never hand-write OpenSpec's own integration files and never copy them from another
project: `openspec init` created them, `openspec update` refreshes them, and a
hand-edited copy silently diverges from the pinned CLI.

## Working with a change

OpenSpec owns behavioral requirements and change task lists. `AGENTS.md` owns
engineering rules, and `docs/explanation/` owns rationale. A change is proposed
before it is implemented:

```bash
openspec new change <name>       # or the harness command: /opsx-propose
openspec validate <name> --strict --no-interactive
openspec status --change <name>
```

`openspec/changes/<name>/` holds the proposal, the spec delta and the task list;
`openspec/specs/` holds what the project already promised. Mark a task complete in
`tasks.md` only when the work it describes is done and verified, and archive the
change with `openspec archive <name>` once it is accepted. There is no second
backlog: do not add a task file outside `openspec/`.

## Small, testable changes

- Read the relevant code before editing it.
- Keep one change reviewable on its own; do not mix a refactor with a behavior
  change.
- Cover every behavior change with a test. Keep the existing smoke test
  meaningful rather than decorative.
- Never weaken a check, delete a test or add a skip to obtain a passing result.

## Documentation

- Update the page that describes what changed, or state why no page needs to.
- Keep the documentation link-clean: `mise run docs` fails on a broken internal
  link.
- Record a significant decision as a short page under `docs/explanation/`.

## Changelog

`CHANGELOG.md` records this project's notable changes, and it is the only
changelog: do not add a second one.

- Record user-visible features, behavior changes and important fixes under
  `[Unreleased]` as part of the change that causes them.
- Skip formatting, typo and internal-refactor work; if you record nothing, say why.
- When you release a version, move the entries into a new version section, date it
  and leave `[Unreleased]` in place, empty.

The overlay seeded the file once. It is yours now, and `copier update` preserves the
entries you add, so never re-seed or overwrite it from the template.

## Definition of Done

A change is complete when:

- the requested behavior works;
- `mise run check` passes;
- tests cover the new behavior;
- documentation reflects the change;
- `CHANGELOG.md` records the change, or you state why no entry is needed;
- the diff contains no secrets, unrelated changes or unresolved conflicts.

## Security

- Never commit credentials, tokens or private keys. Local secrets belong in
  `.env`, which Git ignores.
- `AGENTS.md` is guidance, not a sandbox. Review the commands an agent proposes,
  especially anything destructive, privileged or network-facing.
- Do not run `sudo`, rewrite Git history or push without an explicit request.

## Verify

`mise run check` is the canonical verification command. It runs the locked
dependency check, Ruff lint and format check, `mypy --strict`, pytest, the strict
documentation build and native OpenSpec validation. See
`docs/reference/commands.md` for the individual tasks.

OpenSpec must be initialized before the check runs: `openspec validate` fails when
the project has no `openspec/` root. Initialization is a one-time step,
`openspec init --tools opencode,codex --profile core`.
