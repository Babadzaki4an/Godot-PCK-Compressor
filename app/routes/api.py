# app/routes/api.py
from app.utils.dialog import DialogHelper
from .router_base import BaseRouter
from ..models import CheckProjectRequest
import os
from fastapi import HTTPException



class ApiRouter(BaseRouter):
    def __init__(self, prefix: str = "/api"):
        super().__init__(prefix=prefix)

    def register_routes(self):
        @self.get("/select-folder")
        async def select_folder():
            folder_path = DialogHelper.select_folder(title="Выберите папку с билдом Godot")
            return {"path": folder_path or ""}

        @self.get("/select-file")
        async def select_file():
            file_path = DialogHelper.select_file(
                title="Выберите файл",
                filetypes=[("HTML файлы", "*.html"), ("Все файлы", "*.*")]
            )
            return {"path": file_path or ""}

        @self.post("/check-project")
        async def check_project(request: CheckProjectRequest):
            folder = request.folder
            html_name = request.html_name
            if not folder or not os.path.isdir(folder):
                raise HTTPException(status_code=400, detail="Папка не существует")

            expected = {
                "js": f"{html_name}.js",
                "wasm": f"{html_name}.wasm",
                "pck": f"{html_name}.pck",
                "html": f"{html_name}.html"
            }
            result = {}
            all_exist = True
            missing = []
            for key, filename in expected.items():
                filepath = os.path.join(folder, filename)
                exists = os.path.isfile(filepath)
                result[key] = {"exists": exists, "name": filename}
                if not exists:
                    all_exist = False
                    missing.append(filename)

            message = "Все файлы найдены" if all_exist else f"Отсутствуют: {', '.join(missing)}"
            return {"valid": all_exist, "files": result, "message": message}

        @self.get("/default-extensions")
        async def get_default_extensions():
            return {
                "extensions": [".backup", ".tmp", ".gz", ".img", ".import", ".old", ".png"]
            }

        @self.get("/platforms")
        async def get_default_extensions():
            return {
                "platforms": ["None", "Yandex", "CrazyGames", "Poko", "PlayGamma"]
            }

        @self.get("/open-folder/{path:path}")
        async def open_folder(path: str = None):
            if not path:
                return {"ok": False, "error": "Путь не передан"}

            if not os.path.exists(path):
                return {"ok": False, "error": f"Путь не существует: {path}"}

            try:
                opened = DialogHelper.open_in_explorer(path)
                if opened:
                    return {"ok": True}
                return {"ok": False, "error": "open folder failed"}
            except Exception as e:
                return {"ok": False, "error": str(e)}