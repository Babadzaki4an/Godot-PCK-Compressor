# app/routes/api.py
import time

from app.utils.dialog import DialogHelper
from .router_base import BaseRouter
from app.models import PlatformRequest, CompressRequest, ZippackRequest
import os
from fastapi import HTTPException
from app.logic import ZipPacker


class CompressRouter(BaseRouter):
    def __init__(self, prefix: str = "/"):
        super().__init__(prefix=prefix)

        @self.post("/compress")
        async def compress(request: CompressRequest):
            time.sleep(1)
            # логика сжатия (использует compression_type, wasm_level, pck_level, create_backup)
            return {"success": True, "message": "Сжатие выполнено"}

        @self.post("/platform")
        async def platform(request: PlatformRequest):
            time.sleep(1)
            # логика интеграции SDK для указанной платформы (request.platform)
            return {"success": True, "message": f"{request.platform} SDK добавлено"}

        @self.post("/zippack")
        async def zippack(request: ZippackRequest):
            try:
                ZipPacker.create_zip(request.folder, request.filename, request.exclude_extensions)

            except Exception as e:
                return {"success": False, "message": f"{e}"}
            else:
                return {"success": True, "message": "Упаковано в ZIP"}