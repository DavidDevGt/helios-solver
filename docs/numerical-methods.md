# Numerical methods reference

This consolidates the equations, integrator/solver choices, and acceptance
numbers that are otherwise scattered across `README.md`, `IDEA.md`, and
`PLAN.md`. When those documents and this one disagree, the root docs win —
this file is a derived reference, not a second source of truth; if you
spot a mismatch, fix it here first (it's the more likely stale copy).

## 1. Equations of motion

State `x(t) = [r, v, m]` (position ∈ ℝ³, velocity ∈ ℝ³, mass). Control
`u(t) = [T, α, β]` (thrust magnitude and direction).

```
ṙ = v
v̇ = -μ r/|r|³ + (T/m) û      (solar gravity + thrust acceleration)
ṁ = -T/(Isp · g₀)             (Tsiolkovsky mass depletion)
```

subject to `0 ≤ T ≤ T_max`, `x(t₀) = Earth state at t₀`,
`x(t_f) = Mars state at t_f` (full rendezvous — position *and* velocity),
maximizing `m(t_f)`.

This is the exact statement from `README.md`'s Abstract; it's repeated here
because `dynamics.equations_of_motion` (T-1.1, currently a stub) is meant
to be a direct, literal implementation of it — not a reinterpretation. In
canonical units ([`ADR-0003`](adr/0003-canonical-units.md)), `μ = 1` by
construction.

## 2. Integration

- **Method:** `scipy.integrate.solve_ivp` with `DOP853` (an 8th-order
  explicit Runge-Kutta pair) — chosen for accuracy per unit step over
  months-long low-thrust arcs, per `IDEA.md §5`.
- **Tolerance:** `rtol=1e-12` for the T-0.6/T-1.9 verification integrations
  — this is the "trust this number" tolerance, deliberately tighter than
  whatever tolerance the per-segment Sims-Flanagan integrations inside the
  NLP loop use during search (a looser tolerance there is fine; the
  *final* accept/reject decision is what must be tight — see
  [`data-flow.md §1`](architecture/data-flow.md#1-classical-solve-target-for-m1m2)).
- **Escalation path:** if `DOP853` accuracy or speed becomes limiting,
  `IDEA.md §5` names Taylor-series integrators (`heyoka`) as the upgrade —
  not yet needed, no task opened for it.

## 3. Acceptance numbers (the oracles)

These are the numbers that gate Phase 0 → Phase 1 (`PLAN.md`, Gate 0→1).
None of this is negotiable per `README.md`'s Validation philosophy: a
single wrong sign produces a plausible-looking, completely wrong
trajectory, and these are the checks designed to catch exactly that.

| Check | Test | Tolerance | Why this number |
|---|---|---|---|
| Energy conservation, zero thrust, 1 simulated year | `test_dynamics.py` (T-0.6) | relative drift `< 1e-10` | `DOP853` at `rtol=1e-12` should hold two-body energy to near machine precision; anything looser means the EOM or integrator setup is wrong, not that the tolerance is unreasonable |
| Hohmann Δv, departure | `test_hohmann.py` (T-0.5) | ≈ 2.94 km/s, ±1% | Closed-form textbook value for 1 AU → 1.524 AU circular coplanar transfer |
| Hohmann Δv, arrival | `test_hohmann.py` | ≈ 2.65 km/s, ±1% | ″ |
| Hohmann Δv, total | `test_hohmann.py` | ≈ 5.6 km/s, ±1% | ″ |
| Hohmann time of flight | `test_hohmann.py` | ≈ 259 days, ±1% | ″ |
| Ephemeris vs. JPL Horizons | `test_ephemeris.py` (T-0.7, not yet written) | position error `< 1000 km` | Frozen fixture, no live network call in CI |
| Rendezvous position | `test_m1_solution.py` (T-1.9, not yet written) | `\|Δr\| < 1000 km` | M1 gate |
| Rendezvous velocity | `test_m1_solution.py` | `\|Δv\| < 1 m/s` | M1 gate |
| Final mass fraction, reference case | sanity check, `PLAN.md §3` | `m_f/m_0` ≈ 0.80–0.83 (concerning outside 0.70–0.85) | Tsiolkovsky cross-check — see [glossary](domain/glossary.md#propulsion--the-rocket-equation) |

**Reference case** (Phase 1, `PLAN.md §3`): Isp = 3000 s, T_max = 0.5 N,
m₀ = 1000 kg, TOF ≈ 300–400 days.

## 4. Why canonical units, concretely

SI magnitudes in this problem span roughly `1.5e8` km (position) down to
`~1e-4`–`1e-1` kg/s (mass flow), a spread of many orders of magnitude in
the same state vector. Gradient-based NLP solvers (SLSQP, IPOPT) use
finite-difference or quasi-Newton approximations whose numerical behavior
degrades badly when the variables they're differentiating with respect to
have wildly different scales — step sizes appropriate for one component
are wrong by orders of magnitude for another. Rescaling to `DU = 1 AU`,
`TU` such that `μ_sun = 1` brings position, velocity, and (with a
consistent mass scale) mass flow all to `O(1)`, which is why `PLAN.md`
calls D-3 the single highest-impact, easiest-to-underestimate decision in
the project. See [`ADR-0003`](adr/0003-canonical-units.md) for the decision
record and `constants.DU_KM`/`constants.TU_S` for the implementation.

## 5. NLP solvers

- **SLSQP** (`scipy.optimize.minimize`) — first solver, per T-1.3.
  Gradients validated by finite differences against an analytical
  derivative on a trivial case before trusting it on the real problem.
- **IPOPT** (via `cyipopt`) — escalation path (T-1.6, flag
  `--solver=ipopt`) if SLSQP stalls on larger segment counts. Acceptance
  bar: same optimum as SLSQP on E2, in fewer iterations — not a different
  answer, a faster path to the same one.
- **pygmo archipelago** (Phase 2, T-2.1/T-2.2) — global search: DE,
  self-adaptive DE, CMA-ES islands with migration, wrapping the *same*
  objective/constraint definition as the local solvers (no duplicated
  problem definition — see [`architecture/overview.md §2`](architecture/overview.md#2-module-map)).
