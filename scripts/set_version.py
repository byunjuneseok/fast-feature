#!/usr/bin/env python3
"""Set a single lockstep version across every workspace distribution.

Updates each ``packages/*/pyproject.toml`` so that:

* ``[project].version`` is the given version, and
* every first-party dependency (``fast-feature-*``) is pinned to ``==<version>``.

This keeps the whole workspace releasable as one coherent set. Run it, review the
diff, then commit and tag.

    python scripts/set_version.py 0.0.1
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Every distribution name in the workspace. A dependency on any of these is an
# internal edge that must be pinned to the release version.
FIRST_PARTY = (
    "fast-feature-core",
    "fast-feature-engine",
    "fast-feature-ofrep",
    "fast-feature-testing",
    "fast-feature-storage-inmemory",
    "fast-feature-storage-sqlalchemy",
    "fast-feature-storage-postgresql",
    "fast-feature-admin",
    "fast-feature",
)

_VERSION_RE = re.compile(r"^(?P<spec>\d+\.\d+\.\d+(?:[.\-+][0-9A-Za-z.\-+]+)?)$")
_PROJECT_VERSION_RE = re.compile(r'^version = "[^"]*"$', re.MULTILINE)


def _dependency_re(name: str) -> re.Pattern[str]:
    # Matches a quoted dependency token for exactly this distribution, whether it
    # is bare ("fast-feature-core") or already pinned ("fast-feature-core==0.0.1").
    # The lookbehind skips the project's own ``name = "..."`` field.
    return re.compile(rf'(?<!name = )"{re.escape(name)}(?:==[^"]*)?"')


def set_version(version: str) -> list[Path]:
    root = Path(__file__).resolve().parent.parent
    changed: list[Path] = []
    for pyproject in sorted(root.glob("packages/*/pyproject.toml")):
        original = pyproject.read_text()
        updated = _PROJECT_VERSION_RE.sub(f'version = "{version}"', original, count=1)
        for name in FIRST_PARTY:
            updated = _dependency_re(name).sub(f'"{name}=={version}"', updated)
        if updated != original:
            pyproject.write_text(updated)
            changed.append(pyproject)
    return changed


def main(argv: list[str]) -> int:
    if len(argv) != 1 or not _VERSION_RE.match(argv[0]):
        print("usage: python scripts/set_version.py <version>  (e.g. 0.0.1)", file=sys.stderr)
        return 2
    version = argv[0]
    changed = set_version(version)
    for path in changed:
        print(f"updated {path.relative_to(Path.cwd())}")
    print(f"\nSet {len(changed)} distributions to {version}. Run `uv lock`, then review the diff.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
