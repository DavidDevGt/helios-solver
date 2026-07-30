# 0002. Environment and dependency manager: uv

Status: Accepted (de facto — see note below)

## Context

`PLAN.md` D-2 frames this as conditional on D-1: **`uv`** if the orbital
library ([`ADR-0001`](0001-orbital-mechanics-library.md)) resolves via a
plain wheel; **`conda`/`pixi`** if `pykep` or `cyipopt` need to be compiled
from source, since `uv` alone doesn't manage non-Python build toolchains
the way conda environments can.

## Decision

**`uv`.** `pyproject.toml`, `uv.lock`, and `.github/workflows/ci.yml`
(`astral-sh/setup-uv`) all already exist and are the only environment
mechanism in the repo — `README.md`'s quickstart is `uv sync --extra dev &&
uv run pytest`, and `CONTRIBUTING.md` documents no alternative. In practice
this decision has already been exercised, even though
[`PLAN.md §7`](../../PLAN.md#7-registro-de-decisiones) still lists D-2 as
"abierta" (open) — that status line is stale and should be updated to match
the lockfile that's already committed.

## Consequences

If D-1 ([`ADR-0001`](0001-orbital-mechanics-library.md)) resolves to
`pykep` and no wheel is available for the target platform, this decision
needs revisiting — either building `pykep` in a `uv`-managed venv via its
build backend, or falling back to conda/pixi as `PLAN.md` originally
scoped. That would be a real migration (regenerating `uv.lock`, rewriting
CI), not a one-line edit, so it's worth resolving D-1's timebox *before*
assuming this ADR is permanently closed.

**Correction to make alongside this ADR:** `PLAN.md §7`'s status column for
D-2 should read "aceptada" rather than "abierta" — flagged here rather than
silently changed, since it's the author's own decision log.
