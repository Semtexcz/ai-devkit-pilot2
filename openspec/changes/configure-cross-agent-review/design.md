# Design

## Context

Cezar 0.19.0 is installed in the npm execution cache, with native v2 graph
validation, verdict routing, durable loop counters and a human gate. See proposal.

## Goals / Non-Goals

Configure and simulate the existing orchestrator. No scheduler, custom retry
engine, actual agent turns, delivery, or upstream modifications.

## Decisions

Adapt implement-review-pr, removing GitHub nodes and OpenCode continuation.
Use a single native loop(max=2) for rejected reviews; failing deterministic
checks stop immediately. Each repair receives the saved review summary.
Use native git.commit, accepting its nothing port because Cezar autosaves.
Snapshot the actual clean HEAD afterwards, never rely on commit.sha, which is
absent on nothing. Audit both verdict paths before branching, consuming native
runs.json graph outputs without shell-interpolating model text. Missing, stale,
truncated or inconsistent evidence fails closed. A short bounded wait allows
Cezar's debounced index write to become visible; it never retries agents.

## Risks / Trade-offs

- Broad native agent permissions: document honestly; post-review checks detect
  final HEAD/index/worktree mutations, not transient writes or data access.
- Native summary cap: require a complete compact report below 3500 characters.
- Native runtime schema: guard pinned to installed 0.19.0 and fixture-tested.
- Runtime remains mutable by the same OS user; evidence is not tamper-proof.
- No real turns during setup: sandbox operation and model execution remain untested.

## Migration Plan

Commit reviewed setup locally before starting a task worktree. Select a separately
approved application change. Keep runtime ignored; removal of workflow/config
reverses setup. Human acceptance and archive remain separate.

## Verified container execution

The user authorizes CEZ_CODEX_NETWORK=1 only in the prepared hardened Docker
container because nested Bubblewrap fails there. Keep the workflow unchanged.
Host preflight still requires 0. A host-side verifier checks Docker's effective
configuration and records the current namespaces, mount table and PID 1 lifetime
in /run/cezar-pilot-attestation.json using a root provisioning exec. The record
and parent are root-owned and not writable by the workload. Preflight checks the
record, its ownership, live process restrictions and binding to this container
lifetime before allowing 1. It does not trust an environment marker, /.dockerenv,
or a project-writable file as isolation evidence. Restart clears /run and requires
verification again. The verifier is a diagnostic/provisioning step, not a sandbox
or orchestrator. Docker provides isolation; Cezar still owns all task execution.

This prevents accidental host/full-access startup and workload-created opt-ins.
It does not resist a hostile Docker administrator or an agent rewriting its own
project guard; those are outside the guard's authority. In-container checks cannot
independently prove host port binding or host mount provenance, which must be
checked with Docker inspect before the root-owned record is provisioned.
