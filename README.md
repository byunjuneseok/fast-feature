# fast-feature

[![CI](https://github.com/byunjuneseok/fast-feature/actions/workflows/ci.yml/badge.svg)](https://github.com/byunjuneseok/fast-feature/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12%20|%203.13-blue?logo=python&logoColor=white)](https://github.com/byunjuneseok/fast-feature)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](./LICENSE)

A lightweight, **async**, [OpenFeature](https://openfeature.dev)-compatible
([OFREP](https://openfeature.dev/docs/reference/other-technologies/ofrep/))
feature flag server with a **powerful JsonLogic targeting engine** and
**pluggable storage**. Use it as a standalone server, or as routers you mount
into your own FastAPI app.

> ⚠️ **Status: early development.** APIs are not yet stable.

## Why

- **OpenFeature-native.** Implements the OpenFeature Remote Evaluation Protocol,
  so the official OpenFeature SDKs talk to it out of the box (verified end to end
  against `openfeature-provider-ofrep`).
- **Rich targeting.** Variants, a default variant, and JsonLogic targeting rules,
  including `fractional` rollouts, `sem_ver`, and `starts_with`/`ends_with`.
- **Library, not just a daemon.** Routers are the unit of composition: mount the
  OFREP and admin routers onto your existing FastAPI service.
- **Modular by distribution.** A [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/)
  of small packages sharing the `fast_feature` namespace; depend on exactly what you use.

## Contents

- [Packages](#packages)
- [Installation](#installation)
- [Quickstart](#quickstart)
- [Storage backends](#storage-backends)
- [Module guide](#module-guide)
  - [`fast_feature.core`](#fast_featurecore-domain-model)
  - [`fast_feature.engine`](#fast_featureengine-targeting-engine)
  - [`fast_feature.ofrep`](#fast_featureofrep-ofrep-http-layer)
  - [`fast_feature.admin`](#fast_featureadmin-management-api--console)
  - [`fast_feature.server`](#fast_featureserver-standalone-server)
  - [`fast_feature.testing`](#fast_featuretesting-backend-contract)
- [Targeting rules](#targeting-rules)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

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

## Installation

Install the umbrella `fast-feature` package and pick the backend and features you
need with extras. The base package includes the core, engine, OFREP layer, and
the in-memory backend:

```bash
pip install fast-feature                 # core + engine + ofrep + in-memory
pip install "fast-feature[sqlalchemy]"   # + SQL backend (bring your own async engine)
pip install "fast-feature[postgresql]"   # + PostgreSQL backend (asyncpg)
pip install "fast-feature[admin]"        # + admin API & web console
pip install "fast-feature[standalone]"   # + uvicorn (run the CLI server)
pip install "fast-feature[all]"          # everything above
```

Extras compose, so ask for exactly what you embed:

```bash
pip install "fast-feature[sqlalchemy,admin]"   # SQL backend + admin, no server
```

> **Advanced: individual distributions.** Every layer is also published as its own
> distribution, so you can depend on a single piece without the umbrella. The one
> thing extras can't express is "engine without the base batteries", since the
> umbrella always ships the OFREP layer and the in-memory backend:
>
> ```bash
> pip install fast-feature-engine          # core + engine only, no web framework
> ```

## Quickstart

### Run it standalone

```bash
pip install "fast-feature[standalone]"
fast-feature serve --host 0.0.0.0 --port 8000          # OFREP at /ofrep/v1/...
```

Configure via env vars (see [`fast_feature.server`](#fast_featureserver-standalone-server)).
With `pip install "fast-feature[all]"` you also get the PostgreSQL backend and the
admin console.

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
app.include_router(OfrepRouter.build(repository))                   # /ofrep/v1/...
app.include_router(AdminRouter.build(repository), prefix="/admin")  # console at /admin/
```

### Evaluate directly (no HTTP)

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
assert outcome.value is True            # outcome.reason == Reason.TARGETING_MATCH
```

More runnable examples in [`examples/`](./examples).

## Storage backends

Every backend implements the same [`FlagRepository`](#fast_featurecore-domain-model)
interface, so the engine, OFREP, and admin layers don't care where flags live.
Pick one and pass it to the routers.

### In-memory

Zero dependencies. Ideal for tests, demos, and read-only flag sets defined in
code. Stored flags are deep-copied, so later mutation of your objects can't leak
into the repository.

```python
from fast_feature.storage.inmemory import InMemoryFlagRepository

repository = InMemoryFlagRepository(flags=[...])   # flags is optional
```

### SQLAlchemy (any async driver)

The `[sqlalchemy]` extra works with any SQLAlchemy async driver. Provide an
`async_sessionmaker` and the host app keeps full ownership of the engine and
connection pool. `Schema.create_all` is a convenience for dev and tests; manage
the `feature_flags` table with migrations in production.

```bash
pip install "fast-feature[sqlalchemy]" aiosqlite
```

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from fast_feature.storage.sqlalchemy import SqlAlchemyFlagRepository, Schema

engine = create_async_engine("sqlite+aiosqlite:///flags.db")
await Schema.create_all(engine)                                  # dev convenience
session_factory = async_sessionmaker(engine, expire_on_commit=False)

repository = SqlAlchemyFlagRepository(session_factory)
```

### PostgreSQL

The `[postgresql]` extra wraps the SQLAlchemy backend with an asyncpg engine.
`from_dsn` normalizes a plain `postgresql://` DSN to `postgresql+asyncpg://`.

```bash
pip install "fast-feature[postgresql]"
```

```python
from fast_feature.storage.postgresql import PostgresStorage

storage = PostgresStorage.from_dsn("postgresql://user:pass@localhost:5432/flags")
await storage.create_schema()        # dev convenience; use migrations in prod
repository = storage.repository

# storage.engine exposes the underlying AsyncEngine if you need it.
```

> **Standalone server + PostgreSQL:** the CLI server does not create the schema
> automatically. Ensure the `feature_flags` table exists (via your migrations or
> a one-off `create_schema()`) before starting `fast-feature serve`.

### Bring your own backend

Implement [`FlagRepository`](#fast_featurecore-domain-model) and validate it
against the reusable [`FlagRepositoryContract`](#fast_featuretesting-backend-contract).

## Module guide

### `fast_feature.core` (domain model)

Pure-Python domain with no infrastructure dependencies. Everything else builds on
these types.

**`Flag`** is a dataclass describing a flag and its variants:

```python
Flag(
    key: str,                                  # must match ^[A-Za-z0-9_.-]+$
    variants: dict[str, JsonValue],            # at least one; values are any JSON
    default_variant: str,                      # must be one of variants
    state: FlagState = FlagState.ENABLED,
    targeting: dict[str, JsonValue] | None = None,   # JsonLogic rule
    metadata: dict[str, JsonValue] = {},
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
)
```

Construction validates the key, the non-empty variant set, and that
`default_variant` exists, raising `InvalidFlagError` otherwise. Helpers:
`flag.default_value`, `flag.value_of(variant)`, `flag.has_variant(variant)`.

**`FlagState`** is `ENABLED` or `DISABLED`. A disabled flag always resolves to its
default variant with reason `DISABLED`.

**`EvaluationOutcome`** is the result of one evaluation:

| Field | Type | Notes |
| --- | --- | --- |
| `key` | `str` | the flag key |
| `reason` | `Reason` | why this value was chosen |
| `value` | `JsonValue` | the resolved variant value |
| `variant` | `str \| None` | the resolved variant name |
| `metadata` | `dict \| None` | flag metadata, if any |
| `error_code` | `ErrorCode \| None` | set only on errors |
| `error_details` | `str \| None` | human-readable error detail |

`outcome.is_error` is `True` when `error_code` is set. `EvaluationOutcome.error(key, error_code, details=None)` builds an error outcome.

**`Reason`** values: `STATIC`, `DEFAULT`, `TARGETING_MATCH`, `SPLIT`, `DISABLED`,
`CACHED`, `UNKNOWN`, `ERROR`.

**`ErrorCode`** values: `FLAG_NOT_FOUND`, `PARSE_ERROR`, `TYPE_MISMATCH`,
`INVALID_CONTEXT`, `TARGETING_KEY_MISSING`, `PROVIDER_NOT_READY`, `GENERAL`.

**`FlagRepository`** is the storage boundary (an ABC). Implement these:

```python
async def get(self, key: str) -> Flag | None
async def list_all(self) -> list[Flag]                 # ordered by key
async def create(self, flag: Flag) -> Flag             # raises FlagAlreadyExistsError
async def update(self, flag: Flag) -> Flag             # raises FlagNotFoundError
async def delete(self, key: str) -> None               # raises FlagNotFoundError
async def exists(self, key: str) -> bool               # provided (calls get)
```

**Exceptions:** `CoreError` (base), `FlagNotFoundError`, `FlagAlreadyExistsError`,
`InvalidFlagError`. Storage backends translate their native errors into these and
chain the cause.

### `fast_feature.engine` (targeting engine)

A JsonLogic evaluator plus feature-flag extension operators.

```python
from fast_feature.engine import TargetingEngine

engine = TargetingEngine()                     # optional: TargetingEngine(hasher=...)
outcome = engine.evaluate(flag, context={"plan": "premium"})   # context is optional
```

`evaluate(flag, context=None) -> EvaluationOutcome` follows these semantics:

| Situation | `reason` | value returned |
| --- | --- | --- |
| flag is `DISABLED` | `DISABLED` | default variant |
| no targeting rule | `STATIC` | default variant |
| targeting returns a known variant name | `TARGETING_MATCH` | that variant |
| targeting returns `null` | `DEFAULT` | default variant |
| targeting errors or returns an unknown variant | `ERROR` (`PARSE_ERROR`) | default variant |

A caller always gets a usable value, even on error. The flag's own key is
available to rules as `{"var": "$flag.key"}`.

The engine is also composable: `OperatorRegistry`, `Operator`/`SimpleOperator`,
`JsonLogicEvaluator`, `StandardOperators`, `TargetingOperators`, `SemanticVersion`,
and the `Hasher`/`Murmur3Hasher` used for deterministic `fractional` bucketing are
all public. See [Targeting rules](#targeting-rules) for the operator set.

### `fast_feature.ofrep` (OFREP HTTP layer)

`OfrepRouter` exposes the OpenFeature Remote Evaluation Protocol under
`/ofrep/v1`. It is evaluation-only; there is no flag-definition retrieval in the
OFREP spec (use the admin API for that).

```python
from fast_feature.ofrep import OfrepRouter

app.include_router(OfrepRouter.build(repository))                 # default engine
app.include_router(OfrepRouter.build(repository, engine=my_engine))
```

| Method & path | Body | Responses |
| --- | --- | --- |
| `POST /ofrep/v1/evaluate/flags/{key}` | `{"context": {...}}` | `200` success, `404` flag not found, `400` evaluation error |
| `POST /ofrep/v1/evaluate/flags` | `{"context": {...}}` | `200` bulk result with `ETag`; `304` when `If-None-Match` matches |

Single-flag success body:

```json
{ "key": "new-dashboard", "reason": "TARGETING_MATCH", "value": true, "variant": "on", "metadata": {} }
```

```bash
curl -X POST localhost:8000/ofrep/v1/evaluate/flags/new-dashboard \
  -H 'content-type: application/json' \
  -d '{"context": {"tier": "premium"}}'
```

`EvaluationService` (the framework-free evaluation use case behind the router) and
`OfrepError` are also exported.

### `fast_feature.admin` (management API & console)

`AdminRouter` provides JSON CRUD under `/api/flags` plus an optional
server-rendered web console at the router root.

```python
from fast_feature.admin import AdminRouter

# Full admin (JSON API + web UI) at /admin
app.include_router(AdminRouter.build(repository), prefix="/admin")

# JSON API only (no HTML console)
app.include_router(AdminRouter.build(repository, ui=False), prefix="/admin")

# Protect every route with your own dependency (e.g. an auth guard)
from fastapi import Depends
app.include_router(
    AdminRouter.build(repository, dependencies=[Depends(require_admin)]),
    prefix="/admin",
)
```

JSON API (relative to the mount prefix):

| Method & path | Body | Result |
| --- | --- | --- |
| `GET /api/flags` | none | `200` list of flags |
| `POST /api/flags` | `FlagCreate` | `201` created, `409` exists, `422` invalid |
| `GET /api/flags/{key}` | none | `200`, `404` |
| `PUT /api/flags/{key}` | `FlagUpdate` | `200`, `404`, `422` |
| `PATCH /api/flags/{key}` | `{"enabled": bool}` | `200` (toggle), `404` |
| `DELETE /api/flags/{key}` | none | `204`, `404` |

Web console routes (HTML): `GET /` (list), `GET /new` & `POST /new` (create),
`GET /{key}/edit` & `POST /{key}/edit` (update), `POST /{key}/toggle`,
`POST /{key}/delete`.

Request and response shapes:

- **`FlagCreate`**: `key`, `variants`, `default_variant`, `state` (default
  `ENABLED`), `targeting` (optional), `metadata` (default `{}`).
- **`FlagUpdate`**: same as `FlagCreate` without `key` (taken from the path).
- **`FlagToggle`**: `{"enabled": bool}`.
- **`FlagView`**: the full flag including `created_at` and `updated_at`.

`ManagementService` (the use cases behind the router: `list_flags`, `get_flag`,
`create_flag`, `update_flag`, `delete_flag`, `toggle`) is exported for reuse.

### `fast_feature.server` (standalone server)

The umbrella distribution wires settings, repository, and routers into a ready
FastAPI app.

**`Settings`** is read from `FAST_FEATURE_*` environment variables:

| Env var | Field | Default | Notes |
| --- | --- | --- | --- |
| `FAST_FEATURE_BACKEND` | `backend` | `inmemory` | `inmemory` or `postgresql` |
| `FAST_FEATURE_DATABASE_URL` | `database_url` | `None` | required for `postgresql` |
| `FAST_FEATURE_ADMIN` | `admin` | `false` | mount the admin router |
| `FAST_FEATURE_ADMIN_PREFIX` | `admin_prefix` | `/admin` | admin mount path |

**`Application.create(settings=None) -> FastAPI`** builds the app, always mounting
OFREP and mounting admin when `admin` is enabled. **`RepositoryFactory.from_settings(settings)`**
builds the configured repository (raising `ValueError` if `postgresql` is selected
without a `database_url`).

```python
from fast_feature.server import Application, Settings

app = Application.create(Settings(backend="inmemory", admin=True))
```

The CLI is `fast-feature serve [--host 127.0.0.1] [--port 8000]` (requires the
`standalone` extra for uvicorn).

```bash
export FAST_FEATURE_BACKEND=postgresql
export FAST_FEATURE_DATABASE_URL=postgresql://user:pass@localhost:5432/flags
export FAST_FEATURE_ADMIN=true
fast-feature serve
```

### `fast_feature.testing` (backend contract)

`FlagRepositoryContract` is a reusable pytest base class that exercises the full
`FlagRepository` contract (CRUD, ordering, error cases, input isolation). Subclass
it and provide a `repository` fixture:

```python
import pytest
from fast_feature.testing import FlagRepositoryContract
from fast_feature.storage.inmemory import InMemoryFlagRepository

class TestInMemory(FlagRepositoryContract):
    @pytest.fixture
    def repository(self):
        return InMemoryFlagRepository()
```

## Targeting rules

A flag's `targeting` is a [JsonLogic](https://jsonlogic.com/) rule that must
resolve to a **variant name** (a string in the flag's `variants`). Returning
`null` falls back to the default variant; returning anything else is an error.

Built-in operators:

| Group | Operators |
| --- | --- |
| Data | `var`, `missing`, `missing_some` |
| Logic | `if` (`?:`), `and`, `or`, `!`, `!!` |
| Comparison | `==`, `!=`, `===`, `!==`, `<`, `<=`, `>`, `>=` |
| Arithmetic | `+`, `-`, `*`, `/`, `%`, `min`, `max` |
| Array / string | `in`, `cat`, `substr`, `merge`, `map`, `filter`, `reduce`, `all`, `some`, `none` |
| Targeting extensions | `starts_with`, `ends_with`, `sem_ver`, `fractional` |

### Equality match

Resolve to `on` when a context value matches, `off` otherwise:

```python
{"if": [{"==": [{"var": "color"}, "yellow"]}, "on", "off"]}
```

### Version gating

`sem_ver` compares semantic versions:

```python
{"if": [{"sem_ver": [{"var": "appVersion"}, ">=", "2.4.0"]}, "new", "old"]}
```

### Percentage rollout

`fractional` does deterministic, sticky percentage rollouts by hashing a bucketing
key. Here an even four-way split is bucketed by the flag key plus the user's
email, so each user sticks to one variant, and only internal users are rolled out
at all (everyone else falls back to the default via the `null` branch):

```python
{
    "if": [
        {"in": ["@acme.com", {"var": "email"}]},
        {
            "fractional": [
                {"cat": [{"var": "$flag.key"}, {"var": "email"}]},
                ["red", 25],
                ["blue", 25],
                ["green", 25],
                ["yellow", 25],
            ]
        },
        None,
    ]
}
```

A simpler rollout bucketed directly by `targetingKey`:

```python
{"fractional": [{"var": "targetingKey"}, ["on", 20], ["off", 80]]}
```

These configurations are exercised in
[`packages/fast-feature-engine/tests`](./packages/fast-feature-engine/tests).

## Development

```bash
uv sync
uv run ruff check . && uv run ruff format --check .
uv run mypy
uv run pytest
```

Tests need no live database. The SQLAlchemy backend runs on `aiosqlite`, and the
OFREP and admin layers run against in-memory repositories over an ASGI transport.
See [`docs/architecture.md`](./docs/architecture.md) for the design.

## Contributing

We use [GitHub Flow](./CONTRIBUTING.md): branch off `main`, open a pull request,
and squash-merge once CI is green. See [CONTRIBUTING.md](./CONTRIBUTING.md) for
branch naming, commit conventions, and the local workflow.

## License

[Apache-2.0](./LICENSE)
