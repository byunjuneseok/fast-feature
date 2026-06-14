"""Embed fast-feature's OFREP and admin routers in your own FastAPI app.

Run with: uvicorn examples.embed_in_fastapi:app
"""

from fastapi import FastAPI

from fast_feature.admin import AdminRouter
from fast_feature.core import Flag
from fast_feature.ofrep import OfrepRouter
from fast_feature.storage.inmemory import InMemoryFlagRepository

repository = InMemoryFlagRepository(
    [
        Flag(
            key="new-dashboard",
            variants={"on": True, "off": False},
            default_variant="off",
            targeting={"if": [{"==": [{"var": "tier"}, "premium"]}, "on", "off"]},
        ),
    ]
)

app = FastAPI()
app.include_router(OfrepRouter.build(repository))  # OFREP at /ofrep/v1/...
app.include_router(AdminRouter.build(repository), prefix="/admin")  # console at /admin/
