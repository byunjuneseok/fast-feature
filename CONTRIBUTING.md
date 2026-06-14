# Contributing to fast-feature

Thanks for your interest in improving fast-feature. This document describes how
we branch, commit, and merge.

## Branching model: GitHub Flow

`main` is always releasable. All work happens on short-lived branches cut from
`main` and lands back through a pull request.

```
main ──●──────────────●────────────●──▶   (always green, always releasable)
        \            /  \          /
         ●──●──●────●     ●──●────●         (short-lived feature branches)
```

1. Branch off the latest `main`.
2. Make focused, atomic commits.
3. Open a pull request against `main`.
4. Once CI is green (and conversations are resolved), **squash-merge**.
5. The branch is deleted automatically on merge.

Keep branches short-lived — rebase onto `main` rather than letting them drift.

### Branch naming

Use a `type/short-description` slug matching the change:

| Prefix      | For                                            |
| ----------- | ---------------------------------------------- |
| `feat/`     | New functionality                              |
| `fix/`      | Bug fixes                                      |
| `refactor/` | Behaviour-preserving restructuring             |
| `test/`     | Tests only                                     |
| `docs/`     | Documentation only                             |
| `chore/`    | Tooling, CI, packaging, housekeeping           |

Example: `feat/mysql-backend`, `fix/ofrep-etag-304`.

## Commits

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<optional scope>): <summary in the imperative>
```

Types mirror the branch prefixes (`feat`, `fix`, `refactor`, `test`, `docs`,
`chore`). Scope is usually the package, e.g. `feat(engine):`, `fix(ofrep):`.
Write commits that are atomic — one logical change each.

## Pull requests

- **Language: English** for PR titles and descriptions.
- Keep PRs scoped to one concern; split unrelated changes.
- Fill out the PR template.
- CI must pass on every supported Python version (3.10–3.13).
- `main` is squash-merged only — your PR becomes one commit, so a clear PR title
  matters more than a tidy intra-branch history.

### `main` protection

`main` enforces:

- Pull request required before merging.
- All CI checks (`quality (py3.10–3.13)`) must pass and the branch must be up to
  date with `main`.
- Linear history (no merge commits); force-pushes and deletions are blocked.
- Conversations must be resolved.

## Local development

This is a [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/)
of small distributions sharing the `fast_feature` namespace.

```bash
uv sync                                  # install the whole workspace + dev tools
uv run ruff check . && uv run ruff format --check .
uv run mypy
uv run pytest
```

Tests need no live database — the SQLAlchemy backend runs on `aiosqlite`, and the
OFREP/admin layers run against in-memory repositories over an ASGI transport.

### Where code and tests live

Each distribution lives under `packages/<dist>/`:

- Source: `packages/<dist>/src/fast_feature/<module>/` (one class per file, public
  surface controlled via `__init__.py`).
- Tests: `packages/<dist>/tests/unit-test/`, mirroring the source layout.

New storage backends should validate against the reusable
`FlagRepositoryContract` from `fast-feature-testing`.

## Code style

- Prefer well-separated classes, abstractions, and interfaces over loose
  module-level functions.
- Each module defines a Base exception; translate and chain to your own Base at
  boundaries.
- Keep the domain (`fast-feature-core`) free of infrastructure — no FastAPI,
  SQLAlchemy, or Pydantic leaking in.

## License

By contributing, you agree that your contributions are licensed under the
project's [Apache-2.0](./LICENSE) license.
