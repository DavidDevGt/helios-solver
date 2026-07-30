# 0001. Orbital mechanics library: jplephem directly against a bundled kernel excerpt

Status: Accepted — see [`PLAN.md` D-1](../../PLAN.md#1-decisiones-a-cerrar-antes-de-escribir-código)

## Context

`ephemeris.py` needs a source of Earth/Mars state vectors (position,
velocity) at arbitrary epochs, accurate enough that the Hohmann Δv oracle
(`tests/test_hohmann.py`, T-0.5) closes to 1% — the project's own definition
of "nothing later is trustworthy if this doesn't hold"
(`PLAN.md`, Gate 0→1). Candidates considered:

- **`pykep`** (ESA) — ships Lambert solvers and a Sims-Flanagan
  implementation `helios.transcription` is expected to reimplement anyway,
  so it would also validate the project's own transcription against a
  reference. Risk: has historically required a compiled extension; wheel
  availability for the target Python/platform is unverified as of this
  writing.
- **`hapsira`** (maintained fork of the archived `poliastro`) + `jplephem`
  — pure-Python(-ish), lower installation risk, but no bundled
  Sims-Flanagan/Lambert reference to cross-check against.
- **Custom** — full control over units and API shape, but reimplements
  ephemeris interpolation the project doesn't need to own, and removes the
  cross-check value entirely.

## Decision

**Neither of the two candidates PLAN.md anticipated actually works**, and
the real decision is a third option the plan didn't name:

- `pykep==3.0.1` installs cleanly via `uv` (resolves, downloads, `Installed`)
  but **fails on `import pykep`** — its `trajopt.gym` submodule references a
  packaged data file (`_tops_cr3bp.json`) that isn't actually present in the
  PyPI wheel. This is a broken package, not an environment problem; the
  60-minute timebox correctly triggered the fallback.
- `hapsira==0.18.0` also installs, but **fails to import** against every
  astropy/numpy/scipy combination `uv` can currently resolve for it:
  astropy≥7 removed `matrix_product` (which `hapsira` still imports), and
  pinning astropy back far enough to have `matrix_product` requires a numpy
  old enough that current scipy no longer imports (`np.long` was removed).
  There is no astropy/numpy/scipy triple in today's PyPI index that
  satisfies both `hapsira`'s expectations and each other's.
- **Actual decision: read a SPICE/NAIF kernel directly with `jplephem`**
  (a small, stable library — its only dependency is `numpy`), bypassing
  both `pykep` and `hapsira` entirely. A ~750 KB excerpt of JPL's DE440s
  kernel (Sun, Earth, Mars; 2020-01-01..2035-01-01), built once with
  `python -m jplephem excerpt` directly against NAIF's public server and
  committed at `src/helios/kernels/de440s_excerpt.bsp`, gives exact
  DE440-grade ephemerides with **zero network calls at runtime or in CI**.
  `ephemeris.py` composes the SSB→body and SSB→Sun chains from the kernel,
  then rotates from the kernel's native ICRF frame into the mean ecliptic
  of J2000 by the IAU 1976 obliquity (`constants.ECLIPTIC_OBLIQUITY_J2000_DEG`).
  Verified against **live JPL Horizons** (not just self-consistency) in
  `tests/test_ephemeris.py`: position error is on the order of **10 meters**,
  four orders of magnitude inside the 1000 km T-0.7 tolerance.

## Consequences

`ephemeris.py` has no dependency on `pykep`'s Lambert/Sims-Flanagan
reference implementation, so `transcription.py`'s own Sims-Flanagan
(T-1.2) has no built-in cross-check from this library and relies instead
on the ballistic-coast self-consistency check in
`tests/test_transcription.py` (propagate forward and back with the same
EDO, expect the matching defect nulling to integration tolerance).

The bundled kernel only covers 2020-01-01 through 2035-01-01 and the
Sun/Earth/Mars chain — extending either (more bodies, a wider date range
for a later GTOC problem in Phase 4) means regenerating the excerpt with
`python -m jplephem excerpt`, not re-opening this ADR. `ephemeris.py`
still returns `(r, v)` in **SI units (km, km/s)** at its boundary per its
own docstring — the canonical-unit conversion
([`ADR-0003`](0003-canonical-units.md)) happens on the caller's side.

**Superseded assumption:** the "60 minute pykep timebox, hapsira fallback"
plan in `PLAN.md §9`'s risk table assumed *a* working fallback would exist.
It didn't — worth remembering next time a `PLAN.md` risk row names a
specific fallback library without having actually imported it.
