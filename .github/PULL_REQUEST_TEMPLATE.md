## What does this change?

<!-- One or two sentences. Reference the PLAN.md task ID if applicable (T-x.y). -->

## Why?

<!-- The motivation, not a restatement of the diff. -->

## How was this verified?

<!-- Which test(s) cover this? If it produces a figure, where is it committed under benchmarks/? -->

## Checklist

- [ ] Tests pass locally (`uv run pytest`) and new tests were added if behavior changed.
- [ ] `uv run ruff check src tests` and `uv run ruff format --check src tests` are clean.
- [ ] Physical quantities returned by any new/changed function document their units.
- [ ] New physical constants are in `src/helios/constants.py` with a cited source.
- [ ] `CHANGELOG.md` updated under `Unreleased` (if user-facing).
- [ ] If this changes a numeric result referenced in `README.md`, the README is updated in the same PR.
