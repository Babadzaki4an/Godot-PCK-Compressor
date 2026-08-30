# app/routes/api.py
from app.utils.dialog import DialogHelper
from .router_base import BaseRouter
from ..models import CheckProjectRequest
import os
from fastapi import HTTPException



class CompressRouter(BaseRouter):
    def __init__(self, prefix: str = "/"):
        super().__init__(prefix=prefix)

    def register_routes(self):
        @self.get("/default-extensions")
        async def get_default_extensions():
            return {
                "extensions": [".backup", ".tmp", ".gz", ".img", ".import", ".old", ".png"]
            }