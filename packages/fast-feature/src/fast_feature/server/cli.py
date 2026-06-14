from __future__ import annotations

import argparse
from collections.abc import Sequence

from .app import Application


class Cli:
    """The ``fast-feature`` command-line entry point."""

    @classmethod
    def run(cls, argv: Sequence[str] | None = None) -> None:
        parser = argparse.ArgumentParser(prog="fast-feature")
        subparsers = parser.add_subparsers(dest="command", required=True)
        serve = subparsers.add_parser("serve", help="Run the OFREP server.")
        serve.add_argument("--host", default="127.0.0.1")
        serve.add_argument("--port", type=int, default=8000)

        args = parser.parse_args(argv)
        if args.command == "serve":
            cls._serve(args.host, args.port)

    @staticmethod
    def _serve(host: str, port: int) -> None:
        try:
            import uvicorn
        except ImportError as exc:  # pragma: no cover
            raise SystemExit("Install fast-feature[standalone] to run the server.") from exc
        uvicorn.run(Application.create(), host=host, port=port)
