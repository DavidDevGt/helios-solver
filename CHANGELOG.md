# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
once a first tagged release exists.

## [Unreleased]

### Added

- Project scaffold: `src/helios` package layout (`constants`, `rng`,
  `ephemeris`, `dynamics`, `transcription`, `viz`, `solvers/`, `surrogate/`).
- Test oracles for Phase 0 (`test_hohmann.py`, `test_dynamics.py`), currently
  skipped pending the ephemeris/dynamics implementation they depend on.
- CI workflow (lint + tests via `uv`).
- Project governance docs: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`,
  `SECURITY.md`, `CITATION.cff`, MIT `LICENSE`.

## [0.1.0] - 2026-07-29

### Added

- Initial repository: `IDEA.md` (design rationale) and `PLAN.md` (execution
  plan with phase gates and acceptance criteria).
