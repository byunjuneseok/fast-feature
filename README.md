# fast-feature

[![CI](https://github.com/byunjuneseok/fast-feature/actions/workflows/ci.yml/badge.svg)](https://github.com/byunjuneseok/fast-feature/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12%20|%203.13-blue?logo=python&logoColor=white)](https://github.com/byunjuneseok/fast-feature)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](./LICENSE)

A lightweight, **async**, [OpenFeature](https://openfeature.dev)-compatible
([OFREP](https://openfeature.dev/docs/reference/other-technologies/ofrep/))
feature flag server with a **powerful JsonLogic targeting engine** and
**pluggable storage** — packaged as a library you mount into your own FastAPI app.

> ⚠️ **Status: early development.** APIs are not yet stable.

## Why

- **OpenFeature-native.** Speaks the OpenFeature Remote Evaluation Protocol, so
  any OFREP provider can talk to it.
- **Rich targeting.** Variants, a default variant, and JsonLogic targeting rules
  — including `fractional` rollouts, `sem_ver`, and `starts_with`/`ends_with`.
- **Library, not just a daemon.** Routers are the unit of composition — attach
  evaluation and admin routers to your existing FastAPI app *(OFREP router lands
  in an upcoming milestone)*.
- **Modular by distribution.** Each concern is its own installable package, so
  you depend on exactly what you use.

## Packages

`fast-feature` is a [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/)
of small distributions sharing the `fast_feature` namespace:

| Distribution | Module | Purpose |
| --- | --- | --- |
| `fast-feature-core` | `fast_feature.core` | Domain model — flags, evaluation outcomes, storage interface (no deps) |
| `fast-feature-engine` | `fast_feature.engine` | JsonLogic targeting & evaluation engine |
| `fast-feature-postgresql` *(planned)* | `fast_feature.postgresql` | PostgreSQL storage (SQLAlchemy + asyncpg) |
| `fast-feature-mysql` *(planned)* | `fast_feature.mysql` | MySQL storage |
| `fast-feature-admin` *(planned)* | `fast_feature.admin` | Admin JSON API + web console |

```bash
pip install fast-feature-core fast-feature-engine
```

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

## License

[Apache-2.0](./LICENSE)
