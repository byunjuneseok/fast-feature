# Architecture

`fast-feature` is a [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/)
of small distributions that share the PEP 420 namespace `fast_feature`. Each
distribution is independently installable and depends only on what it needs.

## Layers

```
                         fast-feature  (umbrella: server, settings, CLI)
                              │
        ┌─────────────────┬──┴───────────────┬───────────────────┐
   fast-feature-ofrep   fast-feature-admin   storage backends    │
        │  (HTTP)          │  (HTTP+UI)       (inmemory / sql)    │
        └───────┬──────────┴─────────┬────────────┬──────────────┘
        fast-feature-engine          │            │
                │                     │            │
                └──────────── fast-feature-core ───┘   (pure domain)
```

- **`fast-feature-core`** — the pure domain: `Flag`/`FlagState`, `EvaluationOutcome`,
  `Reason`/`ErrorCode`, the `FlagRepository` contract, and the exception hierarchy.
  No framework or storage imports.
- **`fast-feature-engine`** — a JsonLogic evaluator (`Operator` strategies behind an
  `OperatorRegistry`) plus the targeting operators (`fractional`, `sem_ver`,
  `starts_with`/`ends_with`) and `TargetingEngine`. Depends only on core.
- **storage backends** — implement core's `FlagRepository`. `inmemory` (no deps);
  `sqlalchemy` (async ORM, shared base); `postgresql` (asyncpg wiring). All pass the
  shared `FlagRepositoryContract` from `fast-feature-testing`.
- **`fast-feature-ofrep`** — the OFREP HTTP layer. `OfrepRouter.build(repo)` returns a
  pluggable `APIRouter`; `EvaluationService` orchestrates repository + engine.
- **`fast-feature-admin`** — JSON CRUD + a server-rendered console. `AdminRouter.build(repo)`.
- **`fast-feature`** — composition root: `Application.create(settings)` selects a backend
  and mounts the routers; the `serve` CLI runs it under uvicorn.

## Conventions

- **Dependency-inward.** `domain` knows nothing about FastAPI, SQLAlchemy, or HTTP.
  Frameworks live only in the packages that need them.
- **Exceptions.** Repositories fulfil core's contract exceptions
  (`FlagNotFoundError` / `FlagAlreadyExistsError`); backend-specific errors are
  translated at the boundary (e.g. SQLAlchemy `IntegrityError` →
  `FlagAlreadyExistsError`, chained).
- **Routers as units.** Public composition is via small classes
  (`OfrepRouter`, `AdminRouter`) that return an `APIRouter`; they never assume
  ownership of the host app.

## Schema management

`fast-feature-storage-sqlalchemy` exposes `Schema.create_all(engine)` for
development and tests. In production, manage the `feature_flags` table with your
own migration tooling against `Base.metadata`.
