# Documentation map

This folder holds the engineering documentation for `helios-solver`: how the
system is structured, why key technical decisions were made, and the domain
vocabulary needed to read the code. It complements, and deliberately does not
duplicate, the documents at the repository root:

| Root doc | Answers | Audience |
|---|---|---|
| [`README.md`](../README.md) | What is this, and what's the status right now? | Anyone landing on the repo |
| [`IDEA.md`](../IDEA.md) | *Why* build this — the problem, the thesis, the research plan | The author's own design rationale (Spanish) |
| [`PLAN.md`](../PLAN.md) | *How*, in what order, with what acceptance criteria and phase gates | Execution tracking (Spanish) |
| [`CONTRIBUTING.md`](../CONTRIBUTING.md) | How do I set up and submit a change? | Contributors |

`docs/` answers a fourth question: **how is the system put together, and what
do its parts mean?** — the reference material an engineer needs once they've
decided to read or modify the code, as opposed to the vision or the task
backlog.

## Contents

- [`architecture/overview.md`](architecture/overview.md) — module map and
  system context (who talks to what).
- [`architecture/data-flow.md`](architecture/data-flow.md) — how a state
  vector moves through the classical solve, and how the Phase 3 surrogate
  pipeline plugs into it.
- [`adr/`](adr/README.md) — Architecture Decision Records: the full
  context/decision/consequences for each entry in
  [`PLAN.md §7`](../PLAN.md#7-registro-de-decisiones).
- [`domain/glossary.md`](domain/glossary.md) — astrodynamics and
  optimization vocabulary used throughout the codebase and docstrings.
- [`numerical-methods.md`](numerical-methods.md) — the equations, integrator
  choices, tolerances, and the acceptance numbers Phase 0/1 are graded
  against, consolidated in one place.

## A note on status

As of this writing the project is in **Phase 0** (see `PLAN.md`): almost
every module under `src/helios/` is a signature-complete stub
(`raise NotImplementedError("Pendiente T-x.y: ...")`). The diagrams in this
folder describe the **target architecture** — what the modules are meant to
do and how they're meant to connect — not a system that runs end-to-end yet.
Each diagram and doc says explicitly which pieces exist today versus which
are planned, and cross-references the `PLAN.md` task ID that will make them
real. Treat anything here as wrong the moment the code disagrees with it —
the code is the ground truth; these docs are a map, not the territory.

## Language

Root design docs (`IDEA.md`, `PLAN.md`) are in Spanish, the author's working
language for design rationale. `docs/`, like `README.md` and
`CONTRIBUTING.md`, is in English — this is the engineering-reference layer
meant to be legible to future collaborators (e.g. a GTOC team) without
requiring Spanish.
