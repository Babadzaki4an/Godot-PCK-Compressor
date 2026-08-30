# app/routes/main_page.py
from fastapi import Response
from .router_base import BaseRouter
from pathlib import Path

class ParticalPageRouter(BaseRouter):
    def __init__(self, prefix: str = "", templates=None):
        super().__init__(prefix=prefix, templates=templates)

    def register_routes(self):
        @self.get("/{filename}")
        async def get_partial(filename: str):
            # Путь к папке с partials
            partials_dir = Path(__file__).parent.parent / "templates" / "partials"
            file_path = partials_dir / filename
            
            if not file_path.exists() or not file_path.is_file():
                return Response(status_code=404)
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            return Response(content=content, media_type="text/html")