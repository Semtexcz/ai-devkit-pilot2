# Tasks

These tasks are for a later, human-approved implementation run through the
existing `pilot-cross-review` workflow. All remain unchecked during specification
preparation, including baseline verification to be repeated in that run.
`design.md` is deliberately omitted under the native conditional design guidance.

## 1. Baseline verification

- [ ] 1.1 Confirm the human-approved scope is this proposal and `specs/greeting/spec.md`; record the starting revision and verify the task worktree has no unrelated changes.
- [ ] 1.2 Run `mise run check` before implementation and record the result; confirm `mise exec -- python main.py` prints the existing default greeting and succeeds.

## 2. Implementation

- [ ] 2.1 Add optional name handling, default preservation, help and invalid-argument handling to the existing script; verify the Ada, default, help, unknown-option and missing-value scenarios with the supported interpreter, without changing runtime dependencies.

## 3. Regression testing

- [ ] 3.1 Extend `tests/test_main.py` with subprocess coverage for Ada and default exact stdout including the final newline, empty stderr and zero status; verify the targeted tests pass and retain meaningful smoke coverage.
- [ ] 3.2 Cover help documentation and both invalid-argument scenarios, checking output streams and exit statuses without tying diagnostics to exact wording; verify the targeted tests pass.
- [ ] 3.3 Verify the success scenarios with `mise exec -- python -S main.py` (with the respective arguments) and backward compatibility with `mise run start`; confirm no third-party runtime package is required and runtime dependencies remain empty.

## 4. Documentation and changelog

- [ ] 4.1 Update `docs/tutorials/run-the-script.md` to demonstrate the default greeting, `--name Ada`, help and invalid arguments; align its message-edit example and test description with the new exact-output contract, then verify the documented commands and `mise run docs`.
- [ ] 4.2 Add an entry under `[Unreleased]` in `CHANGELOG.md` describing the optional name, help and argument validation; verify it matches the implemented behavior and preserves existing entries.

## 5. Deterministic checks

- [ ] 5.1 Run `mise exec -- openspec validate add-greeting-name --strict --no-interactive` and `mise run check` after code, tests and documentation are complete; record actual results and resolve failures without weakening checks.

## 6. Independent review readiness

- [ ] 6.1 Check the final diff against every acceptance scenario and the approved scope; provide changed paths, commands and results for the existing independent review stage, with no unrelated edits, secrets or Cezar configuration changes.
- [ ] 6.2 Confirm the existing workflow has the implementation revision and deterministic-check evidence needed for its independent review; leave final acceptance to the human and perform no push, merge or archive as part of this change.
