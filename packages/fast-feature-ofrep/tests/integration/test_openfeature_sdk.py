from __future__ import annotations

import socket
import threading
import time

import uvicorn
from fastapi import FastAPI
from openfeature import api
from openfeature.contrib.provider.ofrep import OFREPProvider
from openfeature.evaluation_context import EvaluationContext
from openfeature.flag_evaluation import Reason

from fast_feature.core import Flag, FlagRepository
from fast_feature.ofrep import OfrepRouter


class FakeFlagRepository(FlagRepository):
    def __init__(self, flags: list[Flag] | None = None) -> None:
        self._flags = {flag.key: flag for flag in (flags or [])}

    async def get(self, key: str) -> Flag | None:
        return self._flags.get(key)

    async def list_all(self) -> list[Flag]:
        return list(self._flags.values())

    async def create(self, flag: Flag) -> Flag:
        self._flags[flag.key] = flag
        return flag

    async def update(self, flag: Flag) -> Flag:
        self._flags[flag.key] = flag
        return flag

    async def delete(self, key: str) -> None:
        del self._flags[key]


class LiveServer:
    """Runs a FastAPI app on an ephemeral port in a background thread."""

    def __init__(self, app: FastAPI) -> None:
        self._port = self._free_port()
        config = uvicorn.Config(app, host="127.0.0.1", port=self._port, log_level="warning")
        self._server = uvicorn.Server(config)
        self._thread = threading.Thread(target=self._server.run, daemon=True)

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self._port}"

    def __enter__(self) -> LiveServer:
        self._thread.start()
        deadline = time.monotonic() + 5.0
        while not self._server.started:
            if time.monotonic() > deadline:
                raise RuntimeError("uvicorn did not start in time")
            time.sleep(0.02)
        return self

    def __exit__(self, *exc: object) -> None:
        self._server.should_exit = True
        self._thread.join(timeout=5.0)

    @staticmethod
    def _free_port() -> int:
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            return int(probe.getsockname()[1])


class TestOpenFeatureSdkIntegration:
    """End-to-end: the real OpenFeature SDK + OFREP provider against our server."""

    @staticmethod
    def _app() -> FastAPI:
        flags = [
            Flag(
                key="new-dashboard",
                variants={"on": True, "off": False},
                default_variant="off",
                targeting={"if": [{"==": [{"var": "tier"}, "premium"]}, "on", "off"]},
            ),
            Flag(key="theme", variants={"blue": "blue", "red": "red"}, default_variant="blue"),
            Flag(
                key="limits",
                variants={"default": {"max": 10}, "pro": {"max": 100}},
                default_variant="default",
            ),
        ]
        app = FastAPI()
        app.include_router(OfrepRouter.build(FakeFlagRepository(flags)))
        return app

    def test_sdk_resolves_flags_through_ofrep(self) -> None:
        with LiveServer(self._app()) as server:
            api.set_provider(OFREPProvider(server.base_url))
            try:
                client = api.get_client()

                # static (no targeting)
                assert client.get_string_value("theme", "none") == "blue"
                assert client.get_object_value("limits", {}) == {"max": 10}

                # targeting match via evaluation context
                premium = EvaluationContext(targeting_key="u1", attributes={"tier": "premium"})
                details = client.get_boolean_details("new-dashboard", False, premium)
                assert details.value is True
                assert details.reason == Reason.TARGETING_MATCH
                assert details.variant == "on"

                # non-matching context falls through to the default variant
                free = EvaluationContext(targeting_key="u2", attributes={"tier": "free"})
                assert client.get_boolean_value("new-dashboard", True, free) is False

                # unknown flag returns the caller's default
                assert client.get_boolean_value("missing", True) is True
                missing = client.get_boolean_details("missing", False)
                assert missing.reason == Reason.ERROR
            finally:
                api.clear_providers()
