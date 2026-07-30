# 0003. Canonical (adimensional) units inside the solver

Status: Accepted (de facto — see note below)

## Context

`PLAN.md` D-3 poses the choice as SI (m, kg, s) throughout, versus
canonical/adimensional units (AU, TU — "distance/time units" scaled so the
Sun's gravitational parameter is 1) inside the solver, with SI only at the
I/O boundary. `PLAN.md` calls this "la decisión de mayor impacto y la más
fácil de subestimar" (the highest-impact and easiest-to-underestimate
decision): NLP solvers condition far better when state magnitudes are
O(1) instead of spanning `~1e8` km down to `~1e-3` (mass flow rates in
kg/s), and most failures in this class of project are attributed to
numerical scaling bugs, not physics bugs.

## Decision

Canonical units inside `dynamics.py` and `transcription.py`: `DU = 1 AU`,
`TU` defined so `μ_sun = 1` in `DU³/TU²`. SI conversion happens only at the
boundary (`ephemeris.py` output, `viz.py` input/annotations). This is
already implemented, not just planned: `constants.py` defines `DU_KM` and
`TU_S`, and both `dynamics.equations_of_motion` and
`transcription.matching_defect`'s docstrings state their inputs are in
canonical units. `PLAN.md §7` still marks D-3 as "propuesta" (proposed);
that should read "aceptada" given the code already commits to it.

## Consequences

Every function inside the solver boundary must document whether its
inputs/outputs are canonical or SI — mixing them silently is exactly the
"single wrong sign/scale produces a plausible-looking wrong trajectory"
failure mode `README.md`'s Validation philosophy section warns about. New
modules (`solvers/`, `surrogate/`) should default to canonical units
internally and convert only when handing results to `viz.py` or logging,
consistent with `ephemeris.py`'s existing contract of returning SI at its
own boundary. See [`numerical-methods.md`](../numerical-methods.md) for the
worked DU/TU definitions and why O(1) scaling matters for SLSQP/IPOPT
specifically.
