# Run the local cross-agent pilot

This setup adapts Cezar **0.19.0**, native workflow format **v2**, from its bundled
`implement-review-pr`. The workflow is `.ai/cezar/workflows/pilot-cross-review.yaml`.
Setup used offline simulation. The first live application run later reached
independent review and stopped at the evidence audit; see the investigation below.
Application runs require a separately approved OpenSpec change.

Sources: [Cezar official reference](https://github.com/open-mercato/cezar/blob/main/docs/reference.md),
[installed-version source](https://github.com/open-mercato/cezar/tree/v0.19.0/packages/cezar),
and [ai-devkit review procedure](https://github.com/Semtexcz/ai-devkit/blob/main/docs/how-to/review-and-repair-one-change.md).
The reference guide is upstream, not present in this pilot checkout.
Implementation details were checked against the installed package, rather than
assuming that the moving main-branch documentation describes this version.

## Actual graph

```text
start → preflight → implement(OpenCode/DeepSeek Flash)
      → check(mise run check) → git.commit → snapshot(clean actual HEAD)
      → review(fresh Codex/gpt-6.1-sol)
          approve OR changes → audit(commit/report/worktree)
            approve → final-check(mise run check) → final-audit → human gate
              accept → end(success); reject/timeout → stop
            changes → repairs(loop,max=2)
              repeat → repair(fresh OpenCode/DeepSeek Flash) → check → ...
              exhausted → end(failed; escalate with latest findings)
          unverifiable OR failed/missing verdict → end(failed)
```

Every check failure and every agent/commit failure stops. No check-failure repair
loop exists: the two repair attempts are reserved for independent review findings.
There can be one implementation, two repairs and three independent reviews.
A third rejection means the second repair failed; no third repair starts.
No GitHub, push, merge, PR, release, tag or deployment node exists.

Cezar may autosave before verification, periodically, and after agent turns.
The explicit native `git.commit` can therefore return `nothing`: both `done` and
`nothing` lead to a clean actual-HEAD snapshot. The snapshot, not a potentially
stale or absent `commit.sha`, anchors every review. A failed check may leave an
unverified local autosave commit, but it cannot reach review or acceptance.

Both review verdicts pass the guard before routing. It reads the current native
`runs.json` checkpoint, waits at most three seconds for Cezar's debounced write,
and requires current full HEAD, matching report SHA/verdict and evidence format.
It never executes model text as shell code. Repair uses `{{nodes.review.summary}}`
automatically. Reports must be complete and shorter than 3500 characters because
Cezar keeps only the final 4000. Oversized, stale, malformed and unavailable reports
stop. `APPROVE` maps to `CEZ:VERDICT approve`, `REQUEST CHANGES` to
`CEZ:VERDICT changes`; `CEZ:VERDICT unverifiable` stops. A missing native verdict
gets Cezar's one built-in same-session reminder, then fails; the whole report must
be repeated after a reminder. This is bounded and is not another repair attempt.

There is no `session.continue` on any node. Each review and repair starts fresh.
The reviewer receives task scope and exact Git SHAs, not the implementation summary.
Its first instructed evidence is the actual fixed-base-to-current-HEAD diff and log.

## Verification performed during setup

- Cezar native loader/schema and `graphIssues` accepted the workflow.
- Eighteen offline scenarios passed through Cezar's own `enterGraph`/`advance`:
  approval, first/second repair success, exhaustion, six guard/check failures,
  four infrastructure failures, human rejection/timeout, unverifiable output and missing verdict.
- Native verdict parsing, report interpolation into repair, explicit runner/model
  pins, fresh-session declarations and absence of delivery nodes were asserted.
- Guard tests use temporary Git repositories and real local commits. They cover
  valid approvals/rejections; unstaged, staged, untracked and committed reviewer
  changes; stale/missing/oversized/unverified/inconsistent reports; native record
  selection, linked-worktree preflight, sandbox flags, automatic resume and API-key
  override rejection. These are synthetic reports, not actual reviews.
- Host binaries detected: OpenCode and Codex (`codex-cli 0.167.0`).
- Native catalog probes (metadata only) list `deepseek/deepseek-flash` and
  `gpt-6.1-sol`. `codex login status` reports **Logged in using ChatGPT**.
  Catalog visibility does not establish inference availability or remaining quota.
- Canonical project verification: `UV_CACHE_DIR="$PWD/.cache/uv" mise run check`.
  All checks passed; 19 pytest cases pass after the preflight tests were added.

Reproduce offline graph assertions, without running any checks or agents:

```bash
export CEZAR_DIST=/home/semtex/.npm/_npx/2f81180a4ed294ed/node_modules/@open-mercato/cezar/dist
mise exec -- node scripts/simulate-cezar.mjs
```

This is a test harness calling the maintained graph walker, not a replacement
runtime. It supplies node outcomes; it does not test actual protocol execution.
`CEZ_DRY_RUN` was deliberately not used: it is documented around the Claude mock
and fake GitHub operations, not as proof that mixed-runner turns are never invoked.

## Effective permissions and limitations

There are two distinct execution models. The host mode below **requires**
`CEZ_CODEX_NETWORK=0`; it does not provide the requested outer isolation for
OpenCode. Use the verified container mode for this live pilot. The workflow graph,
model pins, two-repair bound and final human gate are identical in both modes.

### Verified disposable Docker pilot

The prepared configuration is
`/tmp/cezar-pilot2-isolated-20261109/compose.yaml`. It preserves non-root UID 1000,
a read-only root filesystem, all capabilities dropped, no-new-privileges, Docker
default seccomp/AppArmor, private namespaces, two disposable named volumes,
runtime tmpfs, and only `127.0.0.1:4322:4322` published on a dedicated bridge.
No host paths, credentials or sockets are bound into it. Only the Compose service
environment overrides `CEZ_CODEX_NETWORK` to `1`; the base image and host retain
`0`. The Docker daemon is rootful; the workload is not.

Cezar 0.19.0's installed `codexThreadOverrides` selects `workspace-write` exactly
when this variable equals `0`; otherwise it selects `danger-full-access`, always
with `approvalPolicy: never`. The name is misleading: `1` changes sandbox mode,
not just networking. The nested workspace-write Bubblewrap probe failed inside
the hardened container. The full-access native shell probe succeeds without
inference and keeps the outer Docker boundary. No security profile is disabled.

Prepare/restart the idle container and verify it **from the host project root**:

```bash
docker compose -f /tmp/cezar-pilot2-isolated-20261109/compose.yaml up -d --no-build
mise exec -- python scripts/verify_cezar_container.py
```

The verifier fails closed on deviations and writes a root-owned read-only
`/run/cezar-pilot-attestation.json`. The project preflight accepts `1` only with
that protected record and matching live runtime state, fixed agent/Cezar homes
and `/workspace` Git common directory. Environment-only opt-ins, writable records,
symlinks, stale records and changed namespaces/mounts fail. See
[the boundary rationale](../explanation/cezar-review-boundary.md).

Authenticate directly in a human terminal, without copying host credentials:

```bash
docker exec -it cezar-pilot2-isolated mise exec -- codex login --device-auth
docker exec -it cezar-pilot2-isolated mise exec -- opencode auth login deepseek
docker exec cezar-pilot2-isolated mise exec -- codex login status
docker exec cezar-pilot2-isolated mise exec -- opencode auth list
```

Enter provider secrets only in the native terminal prompt. Skip DeepSeek login if
already connected. Metadata discovery and login status are not proof of successful
inference or quota. Do not run an inference during setup.

Transfer the reviewed tooling update to the disposable checkout, run
`mise run check`, native graph simulation and OpenSpec validation **inside** it,
and commit the setup locally there so new task worktrees contain it. Do not commit
credentials, runtime state or delivery authority. After verification and human
authentication, start only the cockpit:

```bash
docker exec -d cezar-pilot2-isolated bash -c 'umask 077; exec mise exec -- cezar --repo /workspace --bind-host 0.0.0.0 --port 4322 --no-open > /home/pilot/cezar.log 2>&1'
```

Docker publishes that container listener only on host loopback. Open
`http://127.0.0.1:4322`, confirm `pilot-cross-review` is listed, and leave the task
form empty. No start action is authorized during setup. The server uses its fresh
HOME/CEZ_HOME with maxParallel=1, autoResumeOnUsageLimit=false, no fallback accounts,
dispatch/automations/autonaming/title updates/telemetry disabled, worktree task
workspace and review landing. No GitHub/delivery login is configured.

Stop with `docker compose -f /tmp/cezar-pilot2-isolated-20261109/compose.yaml stop`.
Restart with `start`, then rerun the host verifier (the `/run` record was cleared),
confirm native login status and start the cockpit with the same command. Project
and authentication data persist only in the disposable volumes. `/tmp` preparation
files can be removed by host cleanup; retain the reviewed configuration before
reboot if needed. The original host service is independent and must remain intact.

### Original host mode (not the live isolated pilot)

The setup agent's sandbox allows writes to this repository and `/tmp`, restricts
network access and has read-only access elsewhere. Metadata probes initially failed
because native CLIs tried writing their logs/caches outside that boundary. The
approved metadata-only probes ran outside that setup sandbox; no model turn ran.
This chat's sandbox does **not** automatically apply to a separately launched Cezar.

Cezar's Codex runner explicitly sets `approvalPolicy: never`. Its default is
`danger-full-access`; the startup below uses **`CEZ_CODEX_NETWORK=0`**, which selects
**workspace-write**, network-disabled tool execution, plus writable run artifacts.
That still permits reviewer edits, local commands and commits. It is not read-only.
Its sandbox availability in this host has not been tested with an actual turn.
Existing native Codex settings may add other writable locations or MCP tools.
`allowedTools` is ignored by both runners. OpenCode's runner grants broad permission
and answers permission requests; it is not restricted to this worktree by Cezar.
Shell checks execute as the host user via `bash -lc`, inherit the server environment
and applicable check-audience secrets, and can source shell startup files.
This version rejects an empty `secrets: []` binding; the isolated Cezar home below
must have no registered project/workspace secrets. Do not run with unrelated secrets
exported or shell startup files that inject keys. Credentials are used only by the
native clients; do not paste, inspect or copy credential files.

The guard detects final changes to tracked files, index, untracked files or HEAD,
including changes autosaved into a new commit. It does not detect transient writes
that were reverted, ignored-file changes, outside-worktree changes, reads, network
exfiltration, Git configuration/ref changes, or malicious tampering with the guard
or Cezar state by the same OS user. Format and SHA checks cannot prove that a model
actually inspected the diff or that its evidence is true. Git and reproduced tests
remain the evidence, and a human assesses the final review.

The graph cannot push or merge automatically. Its prompts prohibit those actions,
but broad shell access is not an OS-enforced ban on arbitrary agent commands.
Use only the stipulated disposable environment with no unrelated mounted projects,
credentials or delivery authority. A worktree by itself is not that security boundary.
If stronger containment is required, enforce it outside Cezar before the real run.
No custom sandbox/orchestrator was installed for this pilot.

The project ignore policy tracks only `config.json` and workflow definitions under
`.ai/cezar`; logs, launch-key, runs, worktrees, artifacts, secrets and local-home stay
ignored. Runtime state is not a second backlog: OpenSpec tasks own implementation
scope, native Cezar records own run evidence, Git owns commits.

## Start exactly one real pilot (not executed during setup)

1. Review this setup diff, run the checks and create a local setup commit so Cezar's
   task worktree contains the workflow, guard, tests and docs. This setup session
   leaves the changes uncommitted for your review. Create/approve one application
   change with proposal, delta specs and tasks; commit its artifacts locally too.
   Do not use this tooling change as the application's approved scope.
2. Use the disposable environment described above. The native Codex login must be
   the existing ChatGPT subscription; [OpenAI authentication documentation](https://learn.chatgpt.com/docs/auth)
   describes that mode. No API key setup is needed. Do not use model-lock mode,
   runner/model overrides, fallback accounts, autonomous tasks or in-place tasks.
3. From the pilot root, run the following. These commands start the real cockpit,
   but only the subsequent explicit task start should invoke workflow agents:

```bash
export CEZAR_DIST=/home/semtex/.npm/_npx/2f81180a4ed294ed/node_modules/@open-mercato/cezar/dist
export CEZ_HOME="$PWD/.ai/cezar/local-home"
mkdir -p "$CEZ_HOME"
cat > "$CEZ_HOME/config.json" <<'JSON'
{"resources":{"maxParallel":1,"autoResumeOnUsageLimit":false,"monitoringWakeIntervalMinutes":null}}
JSON
unset OPENAI_API_KEY CODEX_API_KEY CEZ_AGENT_MODELS_LOCKED
export CEZ_AUTONAME=0 CEZ_TITLE_UPDATES=0 CEZ_DISPATCH=0 CEZ_AUTOMATIONS=0
export CEZ_TELEMETRY=0 CEZ_CODEX_NETWORK=0
export UV_CACHE_DIR="$PWD/.cache/uv"
mise exec -- node "$CEZAR_DIST/index.js" --repo "$PWD" --no-open
```

4. Open the loopback URL printed by Cezar. Confirm Resources has automatic resume
   disabled, task workspace is **worktree**, and landing is **review**. Select the
   workflow **pilot-cross-review**, OpenCode, no model override, no fallback. Start
   **one** task with this text, substituting the actual approved change name:

```text
Implement the approved OpenSpec change <change-name> at
openspec/changes/<change-name>/. Its committed proposal, delta specs, design and
tasks define the entire approved scope. Run pilot-cross-review. Keep all work in
the isolated local task worktree. Stop for human acceptance. No push, merge, tag,
release, publishing, deployment, unrelated project access or credential reading.
```

5. Leave orchestration to the graph. On stop/exhaustion, inspect the latest native
   review and check output; do not blindly Continue or reset retry counters. On the
   human gate, independently confirm the full reviewed SHA still equals current
   task HEAD and the tree is clean. Accept/reject the local result only. External
   CI/merge-candidate status is unavailable: nothing was pushed or merged.

Expected human interactions: approve the scoped change and start one task, then
one final acceptance/rejection; successful repair rounds require no intervention.
Any infrastructure/evidence/check failure or two failed repairs adds one human
investigation. A missing verdict may add one automatic reminder. The human gate
expires after 24 hours; cancellation/Finish is a manual intervention, not evidence
of approval or a successful pilot. Accepting a gate causes no delivery action.

Originally not verified during setup: provider inference, remaining quota/cost, actual
fresh-session IDs, native protocol handoff and persistence timing under real turns,
Codex OS sandbox operation, complete findings retention from real reviews, and
end-to-end human-gate UI behavior. Repeat setup validation after changing Cezar;
the guard consumes the pinned version's native run-record shape.

## First live run: evidence formatting repair

Run `215e70d7-f8af-4154-9dc6-dcb84ae37d04` on 2026-11-09 implemented
`add-greeting-name` and passed its pre-review checks (70 tests). Its independent
Codex review returned native `approve`, human `APPROVE`, no blocking findings and
one low, nonblocking tutorial observation. The clean implementation remains on
`cez/215e70d7` at `2f577f52acb3822a61d9c4f74fc9fa3dc436f339` in the container.
This tooling fix neither accepts that task nor resolves its documentation finding.

The exact transcript final message (event 751) has separate `Reviewed-commit` and
`Evidence: verified` lines and ends with `APPROVE` and `CEZ:VERDICT approve` on
separate lines. The displayed combined-header example in the failure report is
also covered by regression. Crucially, the native stored `review.summary` begins
with the reviewer's earlier “I’ll verify HEAD first…” commentary, before those
headers. Cezar also removes the trailing native marker. The old guard assumed the
first stored line was the SHA header, so it stopped with
`STOP: report does not refer to current committed HEAD` despite the correct SHA.
Checking the unstripped final response exposed a second format incompatibility:
the old guard required the human verdict to be the last line.

`tests/fixtures/cezar-first-live-review.json` preserves the exact final response,
stored summary, native verdict, implementation SHA and run ID. Tests replay them
against disposable committed Git repositories, replacing only that SHA with the
test commit's SHA. Before the fix, 9 of 11 positive format cases failed, including
the original summary and the combined header. The updated parser accepts a unique
exact header after commentary, either supported evidence-header format, and a
consistent optional final native marker. The native record verdict remains
mandatory. See [the evidence boundary](../explanation/cezar-review-boundary.md)
for the strict rejection rules and unchanged security limitations.

The reviewer prompt now explicitly requires two separate plain header lines,
structured findings, one human verdict line and one separate final native marker
line. Agent/model pins, graph edges, two-repair limit, check commands, container
preflight and checkpoint-selection rules are unchanged. No real workflow was
started, no audit result was manually changed, and no runtime record was rewritten
during this repair.

Repair verification: `UV_CACHE_DIR="$PWD/.cache/uv" mise run check` passed all
checks with 126 tests, including 102 guard tests (64 added regression cases).
All 18 existing native graph scenarios passed, with additional assertions against
the real final response and Cezar's marker-stripping function. SHA-256 checks of
the original `runs.json` and run transcript were identical before and after the
repair, and the original task worktree remained clean at its reviewed SHA.

### Why the task used origin/main

The container's local `main` contains three setup commits after `3c1357d`:
`8f2ad08` (container compatibility), `170772d` (transferred file permissions) and
`28ddb5f` (authentication/cockpit verification documentation). `origin/main`
instead contains `c9c201a`, the consolidated host setup commit, after that same
ancestor. Their commit histories diverge, but `main` and `origin/main` both have
tree `863fbcf02db595b6763a3ce47d0b10ac7bffc5d2` and their full Git diff is empty,
including file modes. No required local-only setup content was excluded.
The task's preflight output confirms its base was the full `c9c201a` SHA.

Installed Cezar 0.19.0's `git-worktree.js` (`chooseForkBase` / `resolveBaseRef`)
prefers the remote when the default branch diverges, and emits the observed note.
It preserves a current local branch when equal to or ahead of the remote; for a
nondefault checked-out branch it also preserves diverged local work. The host's
`main` and `origin/main` were both `c9c201a` before the isolated fix branch was
created. No branch was reset and no commit was discarded.

### Recovery and the next live run

The original run is terminal `failed`: its graph took `audit.fail->stopped` and
has no persisted cursor. In installed 0.19.0, `workflows/run.js` clears the cursor
when the walk ends. `RunManager.recover` resumes interrupted live checkpoints,
not terminal failed walks. `continueRun` creates a new synthetic agent step and
invokes inference; it does not replay just the failed audit and remaining graph.
The run also retains its original `workflowDef`. Editing the project prompt does
not retroactively replace that definition. The container and host copies of
`workflows/run.js`, `workflows/graph.js` and `git-worktree.js` were hash-identical.

There is no supported no-inference resume for this failed run in the inspected
version. Changing its status/cursor/outputs manually would falsify evidence.
Keep its branch, run record and transcript intact. After separate authorization,
the minimal new-run procedure is:

1. Import the verified tooling-fix branch into the disposable checkout using a
   local bundle/transfer. Check out a **new nondefault branch** containing that
   fix and the unchanged approved greeting artifacts. Leave the original task
   branch and divergent `main` intact. With the current unset `baseBranch`, Cezar
   will fork from that checked-out branch; verify no project override selects
   another base. Do not push or merge to make the default branch usable.
2. Reverify the container boundary, clean Git state, `mise run check` and native
   graph simulations on that base. Confirm the cockpit loads the corrected
   workflow and retains the existing model pins and disabled automatic resume.
3. Explicitly start one new `pilot-cross-review` task for the same approved
   `add-greeting-name` change. This executes fresh implementation/review inference
   and the normal audits; stop at its human gate. Check the new preflight SHA
   equals the intended fixed base. Preserve the old implementation and review
   as historical evidence rather than transplanting their verdict onto a new SHA.

The original task has not reached `final-check`, `final-audit` or human acceptance.
No new live run is part of the tooling repair.
