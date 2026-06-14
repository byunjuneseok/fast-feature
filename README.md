# fast-feature

[![CI](https://github.com/byunjuneseok/fast-feature/actions/workflows/ci.yml/badge.svg)](https://github.com/byunjuneseok/fast-feature/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12%20|%203.13-blue?logo=python&logoColor=white)](https://github.com/byunjuneseok/fast-feature)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](./LICENSE)

A lightweight, **async**, [OpenFeature](https://openfeature.dev)-compatible
([OFREP](https://openfeature.dev/docs/reference/other-technologies/ofrep/))
feature flag server with a **powerful JsonLogic targeting engine** and
**pluggable storage** — usable as a standalone server or as routers you mount
into your own FastAPI app.

> ⚠️ **Status: early development.** APIs are not yet stable.

## Why

- **OpenFeature-native.** Implements the OpenFeature Remote Evaluation Protocol,
  so the official OpenFeature SDKs talk to it out of the box (verified end-to-end
  against `openfeature-provider-ofrep`).
- **Rich targeting.** Variants, a default variant, and JsonLogic targeting rules —
  including `fractional` rollouts, `sem_ver`, and `starts_with`/`ends_with`.
- **Library, not just a daemon.** Routers are the unit of composition — mount the
  OFREP and admin routers onto your existing FastAPI service.
- **Modular by distribution.** A [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/)
  of small packages sharing the `fast_feature` namespace; depend on exactly what you use.

## Packages

| Distribution | Module | Purpose |
| --- | --- | --- |
| `fast-feature` | `fast_feature.server` | Umbrella: settings, `Application` composition root, `serve` CLI |
| `fast-feature-core` | `fast_feature.core` | Domain model, `FlagRepository` contract, exceptions (no deps) |
| `fast-feature-engine` | `fast_feature.engine` | JsonLogic targeting & evaluation engine |
| `fast-feature-ofrep` | `fast_feature.ofrep` | OFREP HTTP layer (`OfrepRouter`) |
| `fast-feature-storage-inmemory` | `fast_feature.storage.inmemory` | In-memory backend |
| `fast-feature-storage-sqlalchemy` | `fast_feature.storage.sqlalchemy` | Async SQLAlchemy backend |
| `fast-feature-storage-postgresql` | `fast_feature.storage.postgresql` | PostgreSQL (asyncpg) |
| `fast-feature-admin` | `fast_feature.admin` | Admin JSON API + web console (`AdminRouter`) |
| `fast-feature-testing` | `fast_feature.testing` | `FlagRepositoryContract` for backend authors |

## Quickstart

### Run it standalone

```bash
pip install "fast-feature[standalone]"
fast-feature serve --host 0.0.0.0 --port 8000          # OFREP at /ofrep/v1/...
```

Configure via env (`FAST_FEATURE_BACKEND`, `FAST_FEATURE_DATABASE_URL`,
`FAST_FEATURE_ADMIN`). With `pip install "fast-feature[all]"` you also get the
PostgreSQL backend and the admin console.

### Mount it into your FastAPI app

```python
from fastapi import FastAPI
from fast_feature.core import Flag
from fast_feature.ofrep import OfrepRouter
from fast_feature.admin import AdminRouter
from fast_feature.storage.inmemory import InMemoryFlagRepository

repository = InMemoryFlagRepository([
    Flag(
        key="new-dashboard",
        variants={"on": True, "off": False},
        default_variant="off",
        targeting={"if": [{"==": [{"var": "tier"}, "premium"]}, "on", "off"]},
    ),
])

app = FastAPI()
app.include_router(OfrepRouter.build(repository))                 # /ofrep/v1/...
app.include_router(AdminRouter.build(repository), prefix="/admin")  # console at /admin/
```

### Evaluate directly

```python
from fast_feature.core import Flag
from fast_feature.engine import TargetingEngine

flag = Flag(
    key="discount-banner",
    variants={"on": True, "off": False},
    default_variant="off",
    targeting={"if": [{"==": [{"var": "plan"}, "premium"]}, "on", "off"]},
)
outcome = TargetingEngine().evaluate(flag, {"plan": "premium"})
assert outcome.value is True  # reason=TARGETING_MATCH
```

More in [`examples/`](./examples) and [`docs/architecture.md`](./docs/architecture.md).

## Development

```bash
uv sync
uv run ruff check . && uv run mypy && uv run pytest
```

Tests need no live database — the SQLAlchemy backend runs on `aiosqlite`.

## License

[Apache-2.0](./LICENSE)
