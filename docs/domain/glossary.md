# Domain glossary

Vocabulary used across the codebase, docstrings, and `IDEA.md`/`PLAN.md`.
Organized by topic rather than alphabetically, since most terms are only
meaningful next to their neighbors. Cross-references point to the module or
doc that operationalizes each term.

## Propulsion & the rocket equation

- **Low-thrust propulsion** — ion/Hall-effect thrusters producing
  millinewton-scale continuous force over months, as opposed to
  **impulsive** (chemical, near-instantaneous) burns. The whole project
  exists because low-thrust trajectories are spirals, not conics, and
  finding the optimal one is a control problem, not closed-form geometry
  (`IDEA.md §1`).
- **Specific impulse (Isp)** — thruster efficiency, in seconds; higher Isp
  means more Δv per kg of propellant burned. Reference case:
  Isp = 3000 s (`PLAN.md §3`).
- **g₀** — standard gravity (9.80665 m/s², `constants.G0_KM_S2`), the
  conversion constant between Isp (seconds) and effective exhaust velocity
  `v_e = Isp · g₀`.
- **Tsiolkovsky rocket equation** — `m_f/m_0 = exp(-Δv/v_e)`. Used in
  `PLAN.md §3` as a sanity check on any optimizer output: for the reference
  case (Δv ≈ 5.5–6.5 km/s, v_e ≈ 29.4 km/s), expect
  `m_f/m_0 ≈ 0.80–0.83`. A result far above 0.85 suggests the rendezvous
  isn't real (probably just crossing Mars's orbit); far below 0.70
  suggests inefficient control or an excessive number of revolutions.
- **Δv (delta-v)** — total "velocity change" a maneuver costs, km/s. The
  standard currency for comparing trajectories regardless of propulsion
  type.

## Orbital mechanics

- **State vector** — `(r, v)`, position and velocity in ℝ³ at an epoch;
  what `ephemeris.state_vector` returns.
- **Hohmann transfer** — the closed-form, two-impulse minimum-Δv transfer
  between two circular coplanar orbits. Used here purely as an **oracle**
  (`tests/test_hohmann.py`), not as a candidate trajectory — low-thrust
  spirals don't look like Hohmann ellipses, but the impulsive limit must
  still match the textbook number to 1%, or a units/sign bug is
  contaminating everything downstream (`PLAN.md`, Gate 0→1).
- **Rendezvous** — matching both position *and* velocity with the target
  body at arrival. Contrast with merely **crossing** the target orbit
  (matching position only), which is a much easier and much less
  meaningful thing to converge to — `PLAN.md §3`'s sanity check exists
  partly to catch a solver that's found the easy version by accident.
- **Synodic period / launch window** — because Earth and Mars orbit at
  different rates, favorable launch windows recur roughly every ~26
  months. Phase 2 (T-2.3) frees the departure date within a 2-year window
  specifically so the optimizer has to rediscover this window on its own
  rather than being told when to launch.
- **Ecliptic / heliocentric frame** — the reference frame `ephemeris.py`
  returns state vectors in (Sun-centered, referenced to Earth's orbital
  plane).

## Trajectory optimization

- **Optimal control problem** — choosing a control function `u(t)` (here,
  thrust magnitude + direction) over time to optimize an objective (here,
  maximize final mass) subject to dynamics and boundary constraints. See
  the formal problem statement in `README.md`'s Abstract.
- **Direct transcription** — converting the continuous optimal-control
  problem into a finite-dimensional nonlinear program (NLP) that a
  standard solver (SLSQP, IPOPT) can handle, by discretizing the control.
  Contrast with *indirect* methods (Pontryagin's minimum principle, costate
  equations), which this project deliberately does not use.
- **Sims-Flanagan transcription** — the specific direct-transcription
  scheme used here: split the arc into N segments of constant thrust; on
  each segment, integrate forward from the segment start and backward from
  the segment end to a shared midpoint; the **matching defect** is the gap
  between those two midpoint states. The NLP drives this defect to ~0 for
  every segment simultaneously with the boundary/rendezvous constraints.
  Implemented in `transcription.matching_defect`.
- **Multi-start** — running the same local optimizer (SLSQP/IPOPT) from
  many random seeds in parallel to escape local minima, before resorting to
  a full global-search method. T-1.5, via `joblib`.
- **Archipelago / island model** — `pygmo`'s parallel global-search
  architecture: multiple populations ("islands") evolve independently
  (DE, CMA-ES, self-adaptive DE, ...) with periodic migration between them.
  Maps naturally onto multi-core/multi-machine parallelism (`PLAN.md §4`).
- **Non-convexity here** — different numbers of spiral revolutions are
  different local optima (a 1.5-revolution transfer and a 2.5-revolution
  transfer are both locally optimal but not comparable by gradient descent
  alone), which is why Phase 2 needs a real global-search method and not
  just more multi-start (`IDEA.md §2`).

## Canonical units (see [`ADR-0003`](../adr/0003-canonical-units.md))

- **DU (distance unit)** — 1 AU, `constants.DU_KM`.
- **TU (time unit)** — defined so that `μ_sun = 1` in `DU³/TU²`,
  `constants.TU_S`.
- Everything inside `dynamics.py`/`transcription.py` is expected in DU/TU;
  everything crossing an I/O boundary (`ephemeris.py` output,
  `viz.py` input) is SI (km, km/s, kg, s). See
  [`numerical-methods.md`](../numerical-methods.md) for why this matters
  for solver conditioning, not just style.

## Determinism & reproducibility

- Every stochastic process in the project (multi-start seeding, Phase 3
  data generation) must draw from `helios.rng.get_rng(seed)`
  (NumPy PCG64), never a bare `np.random` call — this is what makes CI runs
  bit-reproducible (`PLAN.md T-0.8`).

## Neural surrogate (Phase 3)

- **Surrogate model** — here, `surrogate.model.SegmentMLP`, a small MLP
  trained to predict a segment's final state and mass consumption from its
  initial state, control, and duration — in microseconds, instead of
  numerically integrating it.
- **Screen-and-verify (two-tier search)** — the surrogate cheaply filters
  candidates in the global search; only survivors get a real, high-precision
  integration before a solution is accepted. See
  [`architecture/overview.md §3`](../architecture/overview.md#3-the-two-tier-execution-architecture-phase-3-target).
  The surrogate **never** has the final word on a solution's validity.

## Competition context

- **GTOC (Global Trajectory Optimisation Competition)** — ESA/JPL-run
  competition ("orbital mechanics olympics") that this project's Phase 4
  uses as an external, objective benchmark: reproduce a past GTOC problem
  and compare against its published historical leaderboard
  (`PLAN.md §6`).
