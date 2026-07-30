# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
once a first tagged release exists.

## [Unreleased]

### Added

- Project scaffold: `src/helios` package layout (`constants`, `rng`,
  `ephemeris`, `dynamics`, `transcription`, `viz`, `solvers/`, `surrogate/`).
- CI workflow (lint + tests via `uv`).
- Project governance docs: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`,
  `SECURITY.md`, `CITATION.cff`, MIT `LICENSE`.
- `docs/`: architecture overview and data-flow diagrams, ADRs formalizing
  D-1 through D-4, a domain glossary, and a numerical-methods reference
  (see `docs/README.md`).
- **Gate 0 → 1 closed.** `ephemeris.py` (`jplephem` against a bundled,
  versioned DE440s excerpt kernel — no network calls at runtime or in CI;
  D-1 resolved after both `pykep` and `hapsira` failed to import cleanly,
  see `docs/adr/0001`), `dynamics.py` (equations of motion in canonical
  units, gravity + thrust + mass depletion), `tests/test_hohmann.py`
  (closed-form oracle), `tests/test_dynamics.py` (energy conservation,
  <1e-10 relative drift over 1 simulated year), and `tests/test_ephemeris.py`
  (new — position error ~10 m against live JPL Horizons, frozen fixture).
- Phase 1: `transcription.py` (Sims-Flanagan matching defect, T-1.2),
  `solvers/local.py` (`solve_slsqp`, T-1.3), `viz.py` (`plot_trajectory`,
  T-1.8's function, not yet fed a rendezvous solution).
- E1 (first realism-ladder rung) solved: a constant-tangential-thrust
  spiral departing Earth's orbit, reaching Mars's orbital radius by
  construction — `benchmarks/e1_constant_tangential_thrust.py` /
  `.png`, regression-tested in `tests/test_e1_scenario.py`. Not a
  rendezvous; no optimizer involved yet (that's E2 onward).
- E2 solved: steering angle per segment optimized with `solve_slsqp`
  (minimum control effort subject to hard terminal constraints; fixed
  thrust magnitude and time of flight, matching PLAN.md's definition of
  the rung) — `benchmarks/e2_optimized_steering.py` / `.png`. Reliably
  reaches a genuine quasi-circular insertion at Mars's orbital radius
  (matches both radius and speed) from every seed tested, closing
  T-1.4's mass-final part of its acceptance criterion literally.
  Regression-tested in `tests/test_e2_scenario.py`.
- **Audit finding, kept as a permanent regression test rather than
  papered over**: E2's optimal steering *profile* is not unique — 2
  terminal constraints under-determine 8 control variables (a 6-DOF
  solution manifold), confirmed across three independent objective
  formulations. Different seeds reliably satisfy the same constraints
  but land on different profiles. Expected non-convexity (IDEA.md §2),
  not a bug; the concrete motivation for T-1.5 and Phase 2 rather than
  trusting a single local SLSQP solve. Also fixed two related gaps found
  in the same audit pass: `transcription.matching_defect` was previously
  verified only under zero-thrust coasting (mass-matching under real
  thrust was untested), and several error paths (`ephemeris.state_vector`
  on an unknown body or an out-of-kernel-range epoch, `solve_slsqp` on
  non-convergence) existed but were never exercised by a test.
- E3 solved: time of flight added as a decision variable alongside the
  per-segment steering angles, minimizing TOF subject to the same hard
  terminal constraints as E2 — `benchmarks/e3_free_tof.py` / `.png`.
  With thrust magnitude fixed, minimum TOF is literally maximum final
  mass (the project's actual objective, not a proxy like E2's control
  effort). Converges to TOF ≈ 169.2 days (vs. E2's fixed 180) and
  m_f/m_0 ≈ 75.1% (vs. E2's 73.6%) — and, unlike E2, converges to the
  *same* optimum from every seed tested (within ~1 day of TOF), because
  a genuine objective is much better-conditioned than a degenerate one.
  Regression-tested in `tests/test_e3_scenario.py`, including a direct
  test of that same-optimum-vs-E2 contrast.
- Found and fixed during E3 development: naively bounding the periodic
  steering angles to `[-π, π]` let SLSQP get stuck against that boundary
  instead of continuing to a better solution just past it (verified by
  widening the bounds and watching the objective improve). Bounds
  widened to `[-2π, 2π]`; documented in `e3_free_tof.py`'s docstring as
  a reusable lesson for any future segment-direction parametrization.

## [0.1.0] - 2026-07-29

### Added

- Initial repository: `IDEA.md` (design rationale) and `PLAN.md` (execution
  plan with phase gates and acceptance criteria).
