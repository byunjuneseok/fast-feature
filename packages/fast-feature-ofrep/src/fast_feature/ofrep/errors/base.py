from __future__ import annotations


class OfrepError(Exception):
    """Base class for all OFREP-layer errors.

    Storage or engine failures are translated into this at the service
    boundary (with chaining) so the HTTP layer never couples to a dependency's
    concrete exception types.
    """
