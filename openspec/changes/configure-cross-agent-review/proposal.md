# Proposal

## Why

Pilot one bounded cross-agent review using maintained Cezar instead of building
an orchestrator. The user explicitly authorizes setup and simulation, stopping
before real model execution.

## What Changes

- Adapt Cezar's implement-review-pr v2 graph for local checks, commits and review.
- Add a commit-bound evidence guard and offline native-graph simulations.
- Document permissions, runtime exclusions and real-pilot startup.
- Permit native Codex full access only inside the explicitly verified disposable
  Docker runtime, while retaining workspace-write for host execution. Verify the
  outer boundary independently, test rejection paths, and prepare native login
  and an empty cockpit without starting an application task.

## Capabilities

### New Capabilities

None: this is development tooling, with skip_specs enabled.

### Modified Capabilities

None. Application behavior is unchanged.

## Impact

Local .ai/cezar configuration, scripts, tests and documentation. No new dependency,
upstream ai-devkit modification, real agent execution, push or merge.
