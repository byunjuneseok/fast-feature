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
  evaluation and admin routers to your existing FastAPI service:

  ```python
  from fastapi import FastAPI
  from fast_feature import create_ofrep_router
  from fast_feature.repositories.inmemory import InMemoryFlagRepository

  repo = InMemoryFlagRepository()
  app = FastAPI()
  app.include_router(create_ofrep_router(repo))
  ```

- **Pluggable storage.** Pick a backend via extras; nothing else changes.

## Installation

```bash
pip install "fast-feature[inmemory]"      # zero-dependency, in-process
pip install "fast-feature[postgresql]"    # PostgreSQL (asyncpg)
pip install "fast-feature[admin]"         # admin JSON API + web console
pip install "fast-feature[standalone]"    # ready-to-run ASGI server
```

## License

[Apache-2.0](./LICENSE)
