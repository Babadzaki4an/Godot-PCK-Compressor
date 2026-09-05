# app/routes/api.py
import time

from app.utils.dialog import DialogHelper
from .router_base import BaseRouter
from app.models import PlatformRequest, CompressRequest, ZippackRequest
import os
from fastapi import HTTPException

from app.logic import ZipPacker, Compressor, GzipCompressor, BrotliCompressor, NoCompressor, PlatformSdkInjector
from app.resources import ResourceManager

class CompressRouter(BaseRouter):
    def __init__(self, prefix: str = "/"):
        super().__init__(prefix=prefix)

        @self.post("/compress")
        async def compress(request: CompressRequest):
            result = False
            compressor: Compressor = self._select_compressor(request.compression_type)

            try:
                result, wasm_msg, pck_msg = compressor.compress(
                    folder=request.folder,
                    filename=request.filename,
                    pck_compress_level=request.pck_level,
                    wasm_compress_level=request.wasm_level,
                    create_backups=request.create_backup,
                )
                return {
                    "success": result,
                    "message": "api_compress_done" if result else "api_compress_error",
                    "message_extra": f"{wasm_msg} {pck_msg}".strip() if (result or wasm_msg or pck_msg) else ""
                }

            except Exception as e:
                return {"success": False, "message": "api_error", "message_extra": str(e)}

             
        @self.post("/platform")
        async def platform(request: PlatformRequest):
            try:
                result = PlatformSdkInjector.inject_sdk(request.platform, request.folder, request.filename)
            except Exception as e:
                return {"success": False, "message": "api_sdk_failed", "message_extra": str(e)}
            if result:
                return {"success": True, "message": "api_sdk_added", "message_extra": request.platform}
            return {"success": False, "message": "api_sdk_failed", "message_extra": request.platform}

        @self.post("/zippack")
        async def zippack(request: ZippackRequest):
            try:
                ZipPacker.create_zip(request.folder, request.filename, request.exclude_extensions)

            except Exception as e:
                return {"success": False, "message": "api_zip_error", "message_extra": str(e)}
            else:
                return {"success": True, "message": "api_zipped"}

    def _select_compressor(self, compression_type: str) -> Compressor:
        match compression_type:
            case 'gzip':
                return GzipCompressor

            case 'brotli':
                return BrotliCompressor

            case 'none':
                return NoCompressor

            case _:
                return Compressor