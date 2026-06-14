from __future__ import annotations

from typing import Any

import pytest

from fast_feature.server.cli import Cli


class _UvicornRecorder:
    def __init__(self) -> None:
        self.calls: dict[str, Any] = {}

    def __call__(self, app: Any, host: str, port: int) -> None:
        self.calls = {"host": host, "port": port}


class TestCli:
    def test_serve_runs_uvicorn_with_args(self, monkeypatch: pytest.MonkeyPatch) -> None:
        recorder = _UvicornRecorder()
        monkeypatch.setattr("uvicorn.run", recorder)
        Cli.run(["serve", "--host", "0.0.0.0", "--port", "9100"])
        assert recorder.calls == {"host": "0.0.0.0", "port": 9100}

    def test_serve_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        recorder = _UvicornRecorder()
        monkeypatch.setattr("uvicorn.run", recorder)
        Cli.run(["serve"])
        assert recorder.calls == {"host": "127.0.0.1", "port": 8000}

    def test_requires_a_command(self) -> None:
        with pytest.raises(SystemExit):
            Cli.run([])
