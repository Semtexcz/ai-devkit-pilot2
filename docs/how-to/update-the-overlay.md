# Update the shared overlay

The overlay files (`AGENTS.md`, `mise.toml`, `ruff.toml`, `mypy.ini`,
`pytest.ini`, `zensical.toml`, `docs/`, `tests/`, `.gitignore`) came from the
[ai-devkit](https://github.com/Semtexcz/ai-devkit) Copier template. Copier
recorded the source and version in `.copier-answers.yml`, so you can pull later
template changes without losing your own edits.

## Before you start

1. The project must be a Git repository with a clean working tree. Copier applies
   a diff and needs a known baseline.
   ```bash
   git status --short      # must print nothing
   ```
2. `.copier-answers.yml` must be committed and unmodified. It records
   `_src_path` and `_commit`; editing it by hand breaks the update.
3. `_commit` must exist in the template repository. A project copied from an
   uncommitted template working tree records a synthetic commit, and
   `copier update` then fails with `ValueError: Unknown revision`. Create such
   projects again from a tagged overlay release.
4. Use the Copier version pinned by the template author, here 9.19.1:
   ```bash
   uvx copier@9.19.1 --version
   ```

## Check for an update

```bash
uvx copier@9.19.1 check-update
```

Output is either `Project is up-to-date!` or the current and latest template
versions.

## Apply an update

```bash
uvx copier@9.19.1 update
```

Copier checks out the newest template tag, replays the answers you gave when the
project was created, and applies the difference. Add `--vcs-ref <tag>` to pin a
specific template release instead of the latest one:

```bash
uvx copier@9.19.1 update --vcs-ref v0.2.0
```

## Resolve conflicts

Conflicts appear as inline markers (`--conflict inline`, the default) or as
`.rej` files (`--conflict rej`). Resolve them by hand: keep your project's intent
where the two disagree, and never commit conflict markers.

If an update goes wrong, discard it and start again from a clean tree:

```bash
git checkout .
git status --short      # must print nothing
```

`uvx copier@9.19.1 recopy` is the fallback when the diff cannot be applied at
all. It rewrites overlay files from the template and keeps your answers, so
review the result as if it were a fresh overlay.

## What the update can and cannot touch

| Path | Update behavior |
|---|---|
| `AGENTS.md`, `mise.toml`, `ruff.toml`, `mypy.ini`, `pytest.ini`, `zensical.toml`, `docs/`, `tests/`, `.gitignore` | Updated; your edits may conflict |
| `main.py` | Never rendered by the overlay: it stays yours |
| `pyproject.toml`, `uv.lock`, `.venv/` | Never rendered by the overlay: uv owns them |
| `openspec/` | Not overlay content: OpenSpec owns the specifications and your changes |
| `.opencode/`, `.agents/` | Not overlay content: `openspec update` regenerates them |

An overlay update never changes a specification, a proposed change or an agent
integration file. Update those with OpenSpec's own commands — `openspec archive`
for a change, `openspec update` for the generated integrations — and never by
copying files between projects.

After resolving an update, run the full check and review the diff:

```bash
mise run check
git diff
```

## If the template version is wrong for you

Pin the version you want with `--vcs-ref` and record the result in the commit
message. Rolling back the overlay is a normal Git revert of the update commit,
not a hand edit of `.copier-answers.yml`.
