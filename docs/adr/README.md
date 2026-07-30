# Architecture Decision Records

An ADR captures one technical decision with enough context that someone
(usually future-you) can tell *why* it was made without re-deriving it —
and can tell whether the reason still holds before overturning it.

## Relationship to `PLAN.md §7`

`PLAN.md`'s ["Registro de decisiones"](../../PLAN.md#7-registro-de-decisiones)
table (D-1 through D-4) is the terse index — one row per decision, meant to
be scanned in seconds. The files in this folder are the expanded record for
each of those rows: full context, the decision, and its consequences. Treat
`PLAN.md §7` as the table of contents and this folder as the chapters; if
they ever disagree, that's a bug to fix (usually `PLAN.md`'s status column
lagging reality), not a reason to trust one over the other silently.

| ID | Decision | ADR | Status |
|---|---|---|---|
| D-1 | Orbital mechanics library | [0001](0001-orbital-mechanics-library.md) | Accepted |
| D-2 | Environment manager | [0002](0002-environment-manager.md) | Accepted |
| D-3 | Canonical (adimensional) units | [0003](0003-canonical-units.md) | Accepted |
| D-4 | Realism ladder (E1→E5) | [0004](0004-realism-ladder.md) | Accepted |

## Format

Lightweight [MADR](https://adr.github.io/madr/)-style: Title, Status,
Context, Decision, Consequences. See [`template.md`](template.md).

## Statuses used here

- **Proposed** — a direction is recommended but not yet exercised by working
  code; can still change cheaply.
- **Accepted** — code already depends on this decision being true (e.g. a
  lockfile exists, a module implements it); reversing it means a real
  migration, not just an edit to a markdown file.
- **Superseded** — replaced by a later ADR, linked from both directions.

## Adding a new one

1. Copy `template.md` to `NNNN-short-title.md`, next number in sequence
   (never reused, even for rejected/superseded records).
2. If it corresponds to a `PLAN.md §7` decision, add/update that row.
3. Keep it to the four sections — an ADR that needs subsections is usually
   trying to also be a design doc; put the design detail in
   [`architecture/`](../architecture/overview.md) or
   [`numerical-methods.md`](../numerical-methods.md) instead and link to it.
