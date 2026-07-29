# Contributing to helios-solver

Thanks for considering a contribution. This project is in **Phase 0**
(environment bring-up and physics validation — see [`PLAN.md`](PLAN.md)), so
the bar for any change is: *does it have a verifiable deliverable?* If it
can't be tested or plotted, it isn't a task yet, per the project's own rule
(see `PLAN.md`, top).

## Before you start

- Check [`PLAN.md`](PLAN.md) for the current phase gate and open task IDs
  (`T-x.y`). Work that jumps ahead of the active phase gate will likely be
  asked to wait — this is deliberate scope control, not a judgment on the
  idea (see the "Backlog congelado" section at the bottom of `PLAN.md`).
- For anything non-trivial, open an issue first to agree on approach before
  writing code.

## Development setup

This project uses [`uv`](https://docs.astral.sh/uv/) for environment and
dependency management.

```bash
uv sync --extra dev
uv run pytest
uv run ruff check src tests
uv run ruff format --check src tests
```

If you have [pre-commit](https://pre-commit.com/) installed, `pre-commit
install` will run the same lint/format checks automatically before each
commit.

## Code standards

- **Units are documented.** Any function returning a physical quantity
  states its units in the docstring. Silent unit bugs are the single
  biggest risk in this codebase (see `IDEA.md` §7).
- **No magic numbers.** Physical constants live in `src/helios/constants.py`
  with a cited source.
- **Tests are the oracle.** A physics change without a corresponding test in
  `tests/` (energy conservation, Hohmann Δv, ephemeris round-trip, etc.)
  won't be merged. See the Validation philosophy section in `README.md`.
- **Determinism.** Anything stochastic (multi-start, surrogate data
  generation) must go through `src/helios/rng.py` so CI runs are
  reproducible.
- **Figures are versioned.** If a change produces a new figure, it's
  committed under `benchmarks/`.

## Pull requests

- Keep PRs scoped to one task/idea. Small, reviewable diffs over large ones.
- Reference the `PLAN.md` task ID in the PR description when applicable.
- CI (lint + tests) must be green.
- Update `CHANGELOG.md` under `Unreleased` for user-facing changes.

## Reporting bugs / requesting features

Use the issue templates under `.github/ISSUE_TEMPLATE/`. For security
vulnerabilities, see [`SECURITY.md`](SECURITY.md) instead of opening a public
issue.
