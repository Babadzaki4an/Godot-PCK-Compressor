# app/routes/api.py
import time

from app.utils.dialog import DialogHelper
from .router_base import BaseRouter
from app.models import CheckProjectRequest, CompressRequest
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

        @self.post("/compress")
        async def compress():
            time.sleep(1)

            return {"success": True, "message": "Сжатие выполнено"}