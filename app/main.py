# app/main.py
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from .utils import Translator
from .routes import *

class App:
    """Главный класс приложения"""

    def __init__(self):
        self.fastapi = FastAPI(
            title="Godot PCK Compressor",
            version="1.0",
            description="Веб-интерфейс для сжатия билдов Godot"
        )

        base_dir = Path(__file__).parent

        self.templates = Jinja2Templates(directory=base_dir / "templates")
        self.translator = Translator(locales_dir=base_dir / "locales", default_lang="ru")
        self.templates.env.globals["_"] = self.translator.gettext

        # Настройка статики и роутов
        self._setup_static()
        self._setup_routes()

    def _setup_static(self):
        static_dir = Path(__file__).parent / "static"
        self.fastapi.mount("/static", StaticFiles(directory=static_dir), name="static")

    def _setup_routes(self):
        self.fastapi.include_router(MainPageRouter(templates=self.templates))
        self.fastapi.include_router(ApiRouter())
        self.fastapi.include_router(ParticalPageRouter(prefix="/partials", templates=self.templates))
        self.fastapi.include_router(CompressRouter(prefix="/compress"))

    @property
    def app(self) -> FastAPI:
        return self.fastapi