# Proposal

## Why

The script currently prints a fixed greeting. An optional name makes this small
application useful for a bounded implementation and independent review pilot
while preserving the existing no-argument command.

## What Changes

- Accept `--name Ada` and print exactly `Hello from Ada!` as one output line.
- Preserve the exact default greeting, `Hello from ai-devkit-pilot2!`.
- Document `--name` in command-line help and reject invalid arguments with a
  diagnostic and a nonzero exit status.
- Keep the existing Python script entry point and require no new runtime dependency.

## Capabilities

### New Capabilities

- `greeting`: Command-line greeting selection, default compatibility, help and
  invalid-argument behavior.

### Modified Capabilities

None. There are no existing main specifications.

## Impact

Later implementation affects `main.py`, regression coverage in `tests/test_main.py`,
the usage tutorial and `CHANGELOG.md`. The current smoke test checks only successful
execution and nonempty output; exact output and argument behavior need coverage.
Runtime dependencies remain empty.

This proposal prepares specification artifacts only, pending human approval.
Implementation belongs to the existing Cezar `pilot-cross-review` workflow in a
later, separately authorized run. Cezar configuration changes, workflow execution,
commits, push, merge and archive are outside this preparation task.

No `design.md` is needed: this is a local script change without architectural,
dependency, data-model or migration complexity. No changelog entry is made during
preparation because application behavior has not changed; the implementation
checklist requires the user-visible entry and usage documentation together with
the feature.
