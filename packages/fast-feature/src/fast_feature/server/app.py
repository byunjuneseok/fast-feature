from __future__ import annotations

from fastapi import FastAPI

from fast_feature.ofrep import OfrepRouter

from .repository_factory import RepositoryFactory
from .settings import Settings


class Application:
    """Composition root: wires settings -> repository -> routers into a FastAPI app."""

    @classmethod
    def create(cls, settings: Settings | None = None) -> FastAPI:
        resolved = settings or Settings()
        repository = RepositoryFactory.from_settings(resolved)

        app = FastAPI(title="fast-feature")
        app.include_router(OfrepRouter.build(repository))

        if resolved.admin:
            # Imported lazily so the admin distribution is only needed when enabled.
            from fast_feature.admin import AdminRouter

            app.include_router(AdminRouter.build(repository), prefix=resolved.admin_prefix)

        return app
