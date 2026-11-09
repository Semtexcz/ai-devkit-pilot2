# Changelog

Notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the
project uses semantic versioning. `AGENTS.md` states when an entry is required.

The ai-devkit overlay seeded this file with an empty `[Unreleased]` section and no
release history: everything below it is this project's own. After generation the
project developer owns this file, and a `copier update` keeps the entries you add.

## [Unreleased]

### Added

- Local Cezar v2 cross-agent review pilot with commit-bound review evidence,
  deterministic checks, two bounded repair attempts and human acceptance.

### Changed

### Fixed

- Allow Codex in the verified disposable Docker pilot without nested Bubblewrap,
  while retaining the host workspace-write requirement and all Docker restrictions.
