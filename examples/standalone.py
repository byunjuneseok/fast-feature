"""Run fast-feature as a standalone server.

    python examples/standalone.py

Equivalent to ``fast-feature serve`` with the admin console enabled.
"""

from fast_feature.server import Application, Settings

app = Application.create(Settings(admin=True))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
