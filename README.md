<div align="center">

# 🛰️ helios-solver

**GPU-accelerated optimization of low-thrust spacecraft trajectories.**

[![CI](https://github.com/DavidDevGt/helios-solver/actions/workflows/ci.yml/badge.svg)](https://github.com/DavidDevGt/helios-solver/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)
[![Status: Phase 0](https://img.shields.io/badge/status-phase%200%20(bring--up)-orange.svg)](PLAN.md)

</div>

---

## Abstract

Electric propulsion thrusters (ion, Hall-effect) don't fire in short impulsive
burns — they push continuously, for months, at millinewton-scale thrust. The
optimal trajectory for this regime isn't a Hohmann ellipse; it's a continuous
**low-thrust spiral** whose throttle and steering profile has to be discovered
by solving a non-convex optimal control problem.

This is fundamentally a *software* problem, not a physics one. The equations
of motion have been known since Tsiolkovsky; the [Global Trajectory
Optimisation Competition](https://sophia.estec.esa.int/gtoc_portal/) (GTOC —
ESA/JPL's "orbital mechanics olympics") is won by the teams with the best
optimization engineering, parallelization, and compute budget.

**Thesis:** an engineer with a home GPU can compete in this space by building
better solvers — specifically, by using a neural surrogate to evaluate
trajectory segments in microseconds instead of numerically integrating them,
freeing the global search to spend its time on promising candidates instead
of on integrating ODEs for bad ones.

```
State:       x(t) = [r, v, m]            (position ∈ ℝ³, velocity ∈ ℝ³, mass)
Control:     u(t) = [T, α, β]            (thrust magnitude + direction)
Dynamics:    ṙ = v
             v̇ = -μ r/|r|³ + (T/m) û     (solar gravity + thrust)
             ṁ = -T/(Isp · g₀)           (propellant consumption)
Subject to:  0 ≤ T ≤ T_max
             x(t₀) = Earth state at t₀
             x(t_f) = Mars state at t_f  (full rendezvous: position AND velocity)
Objective:   max m(t_f)                  (arrive with maximum remaining mass)
```

The full problem write-up, the difficulty analysis (why this is non-convex,
chaotic, and expensive to evaluate), and the neural-surrogate research plan
live in [`IDEA.md`](IDEA.md). The task-by-task execution plan with acceptance
criteria and phase gates lives in [`PLAN.md`](PLAN.md). Both are written in
Spanish — the author's working language for design docs; this README is the
English-language entry point for the rest of the world.

## Status

🚧 **Phase 0 — environment bring-up and physics validation.** No trajectory
has been solved yet; the priority right now is proving the numerical
foundations are correct before anything gets optimized. See
[Roadmap](#roadmap) below.

## Quickstart

```bash
uv sync --extra dev
uv run pytest
```

## Repository layout

```
helios-solver/
├── src/helios/
│   ├── constants.py       # cited physical constants (μ_sun, AU, g₀, ...)
│   ├── rng.py              # seeded RNG for reproducible runs
│   ├── ephemeris.py        # Earth/Mars state vectors
│   ├── dynamics.py         # ODEs: gravity + thrust + mass depletion
│   ├── transcription.py    # Sims-Flanagan direct transcription
│   ├── solvers/            # local NLP (SLSQP/IPOPT) + global search (pygmo)
│   ├── surrogate/          # datagen + model + training (Phase 3)
│   └── viz.py              # the trajectory figure
├── tests/                  # physics oracles: Hohmann Δv, energy conservation, ...
├── benchmarks/             # versioned output figures and result tables
├── notebooks/              # exploration
└── data/                   # generated datasets (gitignored)
```

## Roadmap

| Milestone | What it proves | Phase |
|---|---|---|
| **M1** | A converged Earth→Mars spiral with a *real* rendezvous (position **and** velocity), rendered as one self-explanatory figure | 1 |
| **M2** | The launch window is auto-discovered by global search over a 2-year window, with no informed seed | 2 |
| **M3** | The neural surrogate delivers a verified ≥10x end-to-end speedup at equal solution quality | 3 |
| **M4** | A past GTOC problem solved within the top 50% of its historical leaderboard | 4 |

Full task-level breakdown, acceptance criteria, and phase gates: [`PLAN.md`](PLAN.md).

## Validation philosophy

Scientific software fails silently: a single wrong sign produces a trajectory
that looks plausible and is completely wrong. Non-negotiable tests:

1. **Energy conservation** with zero thrust — relative drift `< 1e-10` over one simulated year.
2. **Hohmann transfer** — the impulsive case matches the closed-form textbook Δv to 1%.
3. **Ephemeris round-trip** against frozen JPL Horizons fixtures (no network calls in CI).
4. **The surrogate never has the final word** — every accepted solution is re-verified by high-precision numerical integration before it's trusted.
5. **Fixed seeds** — CI runs are bit-reproducible.

## Contributing

This is currently a solo research project, but issues, questions, and PRs are
welcome. See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the dev workflow.

## Citation

If this project is useful to you, please cite it — see
[`CITATION.cff`](CITATION.cff) or:

```bibtex
@software{helios_solver,
  author  = {Josue},
  title   = {helios-solver: GPU-accelerated low-thrust trajectory optimization},
  year    = {2026},
  url     = {https://github.com/DavidDevGt/helios-solver}
}
```

## License

[MIT](LICENSE)
