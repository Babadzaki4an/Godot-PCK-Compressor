# app/routes/main_page.py
from fastapi import Request
from .router_base import BaseRouter
from app.resources import CustomPyComponent


class MainPageRouter(BaseRouter):
    def __init__(self, prefix: str = "", templates=None, build_params: list[CustomPyComponent] = None):
        super().__init__(prefix=prefix, templates=templates)
        self.build_params = build_params or []

    def register_routes(self):
        @self.get("/")
        async def index(request: Request):
            return self.templates.TemplateResponse(
                request=request,
                name="index.html",
                context={"build_params": self.build_params},
            )