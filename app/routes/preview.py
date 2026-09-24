# app/routes/preview.py
import os
import uuid
import mimetypes
from fastapi import Query
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, HTMLResponse
from .router_base import BaseRouter
from app.resources import ResourceManager


class PreviewRouter(BaseRouter):
    """Отдаёт файлы билда для просмотра в iframe.

    Схема: /preview/start?path=C:/build/index.html ->
    редирект на /preview/serve/{token}/index.html, откуда относительные
    ссылки (index.js, logo.png) корректно резолвятся в тот же префикс.
    """

    def __init__(self, prefix: str = ""):
        super().__init__(prefix=prefix)
        self._sessions: dict[str, str] = {}   # token -> папка билда
        self.MAX_SESSIONS = 32                # защита от бесконечного роста

    EXTRA_MIME = {
        '.wasm': 'application/wasm',
        '.pck': 'application/octet-stream',
        '.js': 'text/javascript',
        '.json': 'application/json',
    }

    @classmethod
    def _mime(cls, path: str) -> str:
        ext = os.path.splitext(path)[1].lower()
        return cls.EXTRA_MIME.get(ext) or mimetypes.guess_type(path)[0] or "application/octet-stream"

    @classmethod
    def _html_response(cls, path: str) -> FileResponse | HTMLResponse:
        """HTML с внедрённым хуком игры (game_hook.js); при ошибке чтения — как есть."""
        try:
            with open(path, 'r', encoding='utf-8', errors='strict') as f:
                html = f.read()
        except (UnicodeDecodeError, ValueError):
            return FileResponse(path, media_type='text/html')
        hook = f'<script>{ResourceManager.get_game_hook_js()}</script>'
        if '<head>' in html:
            html = html.replace('<head>', f'<head>{hook}', 1)
        else:
            html = hook + html
        return HTMLResponse(html, media_type='text/html')

    def register_routes(self):
        @self.get("/start")
        async def start(path: str = Query(...)):
            path = os.path.normpath(path)
            folder = os.path.dirname(path)
            name = os.path.basename(path)
            if not folder or not os.path.isdir(folder):
                return JSONResponse(
                    {"success": False, "error": "api_folder_not_exist"}, status_code=400
                )
            if not os.path.isfile(os.path.join(folder, name)):
                return JSONResponse(
                    {"success": False, "error": "api_path_not_exist"}, status_code=404
                )
            token = uuid.uuid4().hex
            if len(self._sessions) >= self.MAX_SESSIONS:
                self._sessions.pop(next(iter(self._sessions)))
            self._sessions[token] = folder
            return RedirectResponse(f"/preview/serve/{token}/{name}")

        @self.get("/serve/{token}/{file_path:path}")
        async def serve(token: str, file_path: str):
            folder = self._sessions.get(token)
            if not folder:
                return JSONResponse(
                    {"success": False, "error": "preview_no_folder"}, status_code=404
                )
            full = os.path.normpath(os.path.join(folder, file_path))
            # Защита от выхода за пределы папки билда
            if not full.startswith(os.path.normpath(folder)):
                return JSONResponse(
                    {"success": False, "error": "api_path_not_exist"}, status_code=400
                )
            if not os.path.isfile(full):
                return JSONResponse(
                    {"success": False, "error": "api_path_not_exist"}, status_code=404
                )
            if os.path.splitext(full)[1].lower() in ('.html', '.htm'):
                return self._html_response(full)
            return FileResponse(full, media_type=self._mime(full))