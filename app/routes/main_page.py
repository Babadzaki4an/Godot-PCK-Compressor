# app/routes/main_page.py
from fastapi import Request
from .router_base import BaseRouter

class MainPageRouter(BaseRouter):
    def __init__(self, prefix: str = "", templates=None):
        super().__init__(prefix=prefix, templates=templates)

    def register_routes(self):
        @self.get("/")
        async def index(request: Request):
            return self.templates.TemplateResponse({"request": request}, "index.html")