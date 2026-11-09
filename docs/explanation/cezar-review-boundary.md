# Cezar owns orchestration; Git and checks own evidence

The pilot uses Cezar 0.19.0's native v2 graph and durable loop counter. Its bundled
implement-review-pr is the starting point; local commits and a human acceptance
gate replace delivery. A small evidence guard validates Git and native run records.
It never launches an agent, chooses a next step, or manages a retry budget.
The simulation script exercises Cezar's own walker rather than implementing a
second production runtime.

A fresh session separates implementation from review context. It does not isolate
filesystem authority. Cezar's Codex backend defaults to full access; the pilot
startup explicitly selects workspace-write, which still allows edits and commits.
OpenCode retains broad host permissions. Neither a worktree nor a review prompt
creates an OS security boundary. The post-review guard detects final HEAD, index,
tracked and untracked changes; it cannot prove the absence of transient writes,
outside-worktree effects or reads. These limits require a disposable environment
and human acceptance.

Cezar autosaves, so an explicit commit node may have nothing left to commit. The
review anchor is the clean actual HEAD after that node, never its optional output
SHA. Both review verdict paths pass an evidence audit. Successful review also
requires another deterministic check and audit before the human gate. A new repair
therefore always receives a new commit-bound review.

The bound is two repair attempts after rejected reviews, not two total reviews.
Check or infrastructure failures stop immediately. Automatic usage-limit and
transient resumption is disabled in the isolated native Cezar workspace settings.
This keeps failure recovery a human decision without introducing another scheduler.

See [the pilot guide](../how-to/run-cross-agent-pilot.md) for the actual graph,
simulation coverage, permission details and exact startup procedure.
