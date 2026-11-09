# Run the local cross-agent pilot

This setup adapts Cezar **0.19.0**, native workflow format **v2**, from its bundled
`implement-review-pr`. The workflow is `.ai/cezar/workflows/pilot-cross-review.yaml`.
The user authorized configuration and offline simulation; no real agent turn ran.
The application still needs a separately approved OpenSpec change.

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

Not verified until a real pilot: provider inference, remaining quota/cost, actual
fresh-session IDs, native protocol handoff and persistence timing under real turns,
Codex OS sandbox operation, complete findings retention from real reviews, and
end-to-end human-gate UI behavior. Repeat setup validation after changing Cezar;
the guard consumes the pinned version's native run-record shape.
