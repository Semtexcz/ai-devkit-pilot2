# Changelog

Notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the
project uses semantic versioning. `AGENTS.md` states when an entry is required.

The ai-devkit overlay seeded this file with an empty `[Unreleased]` section and no
release history: everything below it is this project's own. After generation the
project developer owns this file, and a `copier update` keeps the entries you add.

## [Unreleased]

### Added

- Optional `--name` greeting, command-line help and invalid-argument validation;
  the default `Hello from ai-devkit-pilot2!` output is unchanged.
- Local Cezar v2 cross-agent review pilot with commit-bound review evidence,
  deterministic checks, two bounded repair attempts and human acceptance.

### Changed

### Fixed

- Accept unambiguous commit-bound Cezar review evidence with commentary before
  the headers, a combined SHA/evidence header, or a stripped native verdict marker;
  reject duplicate headers, conflicting verdicts and malformed repair findings.
- Allow Codex in the verified disposable Docker pilot without nested Bubblewrap,
  while retaining the host workspace-write requirement and all Docker restrictions.
