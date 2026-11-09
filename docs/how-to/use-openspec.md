# Work with OpenSpec

OpenSpec is the specification and change-checklist tool for this project. It
belongs to you: the project owns `openspec/`, and OpenSpec owns the agent
integration files it generated.

Upstream documentation: <https://github.com/Fission-AI/OpenSpec>.

## Check that it is initialized

```bash
openspec list            # prints the resolved root, or a root of null
```

If it reports `No OpenSpec root found`, initialize it once:

```bash
mise install             # OpenSpec and its Node.js runtime are pinned in mise.toml
openspec init --tools opencode,codex --profile core
```

`--profile core` selects the default workflow set: propose, explore, apply,
update, sync and archive. `--tools` names the agents to configure. Replace
`opencode,codex` with the tools you use, then commit `openspec/` together with the
generated directories.

Never copy another project's `openspec/` directory or hand-write the generated
commands: `openspec init` produced them for the pinned version, and
`openspec update` refreshes them after an upgrade.

## Propose a change

```bash
openspec new change add-greeting-name
openspec status --change add-greeting-name
```

`openspec/changes/add-greeting-name/` now needs:

| File | Content |
|---|---|
| `proposal.md` | why the change is needed, what changes, which capabilities it touches |
| `specs/<capability>/spec.md` | the behavioral requirements as a delta, with scenarios |
| `tasks.md` | the implementation steps, as checkboxes |

A harness with the OpenSpec integration can write these from one sentence: `/opsx-propose "add a --name argument"` in OpenCode, `$openspec-propose` in Codex.
Review what it produced before implementing anything.

## Validate

```bash
openspec validate add-greeting-name --strict --no-interactive
```

`--strict` is the same validation `mise run check` runs. The two failures you will
meet most often:

| Message | Fix |
|---|---|
| `Requirement must have at least one scenario` | add `#### Scenario: ...` with `- **WHEN**` and `- **THEN**` lines under the requirement |
| `Why section must be at least 50 characters` | explain the motivation in one sentence instead of a fragment |

A specification without a `## Purpose` section fails too. Fix the artifact; do not
weaken the check, and do not add `skip_specs: true` to silence a change that really
does change behavior.

## Implement, then archive

Work through `tasks.md`, ticking each box only when the work is done and
`mise run check` passes. Then archive the accepted change:

```bash
openspec archive add-greeting-name
mise run check
```

Archiving moves the change to `openspec/changes/archive/<date>-<name>/` and writes
the requirements into `openspec/specs/<capability>/spec.md`, so the specification
describes the project as it is now.

## Another agent

Replace the tool list in the initialization command:

| Harness | Command | Generated files |
|---|---|---|
| OpenCode | `openspec init --tools opencode --profile core` | `.opencode/commands/opsx-*.md`, `.opencode/skills/` |
| Codex | `openspec init --tools codex --profile core` | `.agents/skills/openspec-*/SKILL.md` |
| Cline | `openspec init --tools cline --profile core` | `.clinerules/workflows/opsx-*.md`, `.cline/skills/` |

`openspec update` refreshes those files for the installed version without touching
`openspec/specs/` or `openspec/changes/`.
