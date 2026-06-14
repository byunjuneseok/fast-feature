<!-- PR titles and descriptions are in English. Use a Conventional Commits title, e.g. "feat(engine): add reduce aggregation". -->

## What & why

<!-- What does this change do, and why is it needed? Link any related issue. -->

## How

<!-- Key implementation notes a reviewer should know. -->

## Checklist

- [ ] Scoped to a single concern
- [ ] `uv run ruff check .` and `uv run ruff format --check .` pass
- [ ] `uv run mypy` passes
- [ ] `uv run pytest` passes (coverage gate ≥ 95%)
- [ ] Tests added/updated for the change
- [ ] Docs/README updated if behaviour or public API changed
