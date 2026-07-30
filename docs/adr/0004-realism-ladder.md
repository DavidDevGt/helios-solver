# 0004. Realism ladder (E1→E5) for Phase 1

Status: Accepted (de facto — see note below)

## Context

`PLAN.md` D-4 poses the MVP physical scope as a binary choice: start with
2D coplanar circular orbits, or go straight to 3D with real ephemerides.
`IDEA.md §9` names "the optimizer never converges" as a top risk, and its
mitigation is to isolate physics bugs from optimization bugs by adding
realism one layer at a time rather than debugging both at once.

## Decision

Five explicit steps, each gated on the previous one converging and each
producing its own committed figure under `benchmarks/`
(`PLAN.md §3`, "Escalera de realismo"):

| Step | Adds | Time-of-flight |
|---|---|---|
| E1 | 2D circular coplanar orbits, constant thrust | fixed |
| E2 | Variable thrust direction (discretized control) | fixed |
| E3 | — | free |
| E4 | 3D, real ephemerides, fixed dates | fixed |
| E5 | Full rendezvous (position **and** velocity) | — this is M1 |

`README.md`'s roadmap table and `PLAN.md §3` both already treat this
ladder as fixed structure — no document in the repo argues for skipping a
step — so this ADR records it as Accepted rather than the "propuesta"
status still shown in `PLAN.md §7`.

## Consequences

Any solver or transcription work that targets 3D dynamics, free
launch-window search, or a full 6-DOF rendezvous before E1–E3 converge in
2D is out of order per this decision, and per `PLAN.md §9`'s explicit
mitigation ("si el NLP no converge nunca... bajar a E1 con TOF fijo"). This
gives a concrete, low-ambiguity answer to "is this PR premature": it's
premature if it targets a rung above the highest one with a committed
figure in `benchmarks/`.
