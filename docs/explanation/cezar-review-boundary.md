# Cezar owns orchestration; Git and checks own evidence

The pilot uses Cezar 0.19.0's native v2 graph and durable loop counter. Its bundled
implement-review-pr is the starting point; local commits and a human acceptance
gate replace delivery. A small evidence guard validates Git and native run records.
It never launches an agent, chooses a next step, or manages a retry budget.
The simulation script exercises Cezar's own walker rather than implementing a
second production runtime.

A fresh session separates implementation from review context. It does not isolate
filesystem authority. Cezar's Codex backend defaults to full access. Host startup
requires `CEZ_CODEX_NETWORK=0` (workspace-write, which still allows edits and commits).
The explicitly verified Docker pilot uses `CEZ_CODEX_NETWORK=1` (full access
**inside the container**); Docker supplies its filesystem and process boundary.
This avoids nested Bubblewrap, without granting capabilities or disabling Docker
seccomp/AppArmor. OpenCode also relies on that outer boundary. Neither a worktree nor a review prompt
creates an OS security boundary. The post-review guard detects final HEAD, index,
tracked and untracked changes; it cannot prove the absence of transient writes,
outside-worktree effects or reads. These limits require a disposable environment
and human acceptance.

An environment variable or `/.dockerenv` is not proof of isolation. The host-side
`scripts/verify_cezar_container.py` checks the pinned image, non-root UID, read-only
root filesystem, capabilities, default security profiles, namespaces, exact port
binding and two Docker-managed volumes (including volume driver options). It
provisions a non-secret root-owned read-only record in `/run`. The guard requires
protected parents, checks live kernel restrictions, and compares namespaces,
mount-table digest and PID 1 start time with that record. A restart requires
verification again. The short root provisioning process retains all container
restrictions and only writes this record; agents and Cezar run as UID 1000.

The host verifier requires Docker administrative access; the container has none.
Its image ID and paths intentionally target this one prepared pilot. This is a
startup guard against mistakes and workload-created opt-ins, not a new sandbox,
cryptographic remote attestation, or protection against a hostile Docker operator.
The workload can still rewrite its project guard and Cezar state. Docker's actual
boundary, human review and the absence of delivery credentials remain essential.
Full access inside Docker permits reads of the disposable native login stores;
it must never be used with host credentials or unrelated mounted data.

Cezar autosaves, so an explicit commit node may have nothing left to commit. The
review anchor is the clean actual HEAD after that node, never its optional output
SHA. Both review verdict paths pass an evidence audit. Successful review also
requires another deterministic check and audit before the human gate. A new repair
therefore always receives a new commit-bound review.

The evidence parser accepts one exact full-SHA `Reviewed-commit` header after
optional reviewer commentary. `Evidence: verified` must either immediately follow
on its own line or be appended to the SHA header with one space. Duplicate or
ambiguous headers fail closed. This accommodates the first live run's stored
summary, which contained commentary before the separate headers, and the combined
header reported from its display. It does not accept abbreviated SHAs or search
for an arbitrary matching SHA substring.

Cezar strips the trailing native verdict marker before persisting the summary.
The persisted native verdict and exactly one final human verdict must agree.
If a marker is present, it must be a single matching final line after that human
verdict. Findings require a unique positive F-number, status, positive file:line
location and nonempty explanation; the first live review's explicit nonblocking
format is also accepted. Approval cannot carry blocking findings, and rejection
must carry at least one. These checks establish report structure and consistency;
human review still judges the substance of the evidence.

The bound is two repair attempts after rejected reviews, not two total reviews.
Check or infrastructure failures stop immediately. Automatic usage-limit and
transient resumption is disabled in the isolated native Cezar workspace settings.
This keeps failure recovery a human decision without introducing another scheduler.

See [the pilot guide](../how-to/run-cross-agent-pilot.md) for the actual graph,
simulation coverage, permission details and exact startup procedure.
