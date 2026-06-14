# fast-feature

The umbrella distribution for [fast-feature](https://github.com/byunjuneseok/fast-feature):
an async, OpenFeature-compatible (OFREP) feature flag server.

```bash
pip install "fast-feature[standalone]"        # + uvicorn, to run the server
pip install "fast-feature[postgresql]"        # + PostgreSQL backend
pip install "fast-feature[admin]"             # + admin console
pip install "fast-feature[all]"
```

Run it:

```bash
FAST_FEATURE_BACKEND=inmemory fast-feature serve --host 0.0.0.0 --port 8000
```

Or embed it:

```python
from fast_feature.server import Application, Settings

app = Application.create(Settings(admin=True))
```

See the [project README](https://github.com/byunjuneseok/fast-feature) for details.
