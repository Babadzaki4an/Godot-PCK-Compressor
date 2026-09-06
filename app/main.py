# app/main.py
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from .utils import Translator
from .routes import *
from .resources import ResourceManager

class App:
    """Главный класс приложения"""

    def __init__(self):
        #TODO add tranlation
        self.fastapi = FastAPI(
            title="Godot PCK Compressor",
            version="1.0",
            description="Веб-интерфейс для сжатия билдов Godot"
        )

        base_dir = Path(__file__).parent

        self.templates = Jinja2Templates(directory=base_dir / "templates")
        self.translator = Translator(locales_dir=base_dir / "locales", default_lang="en")
        self.templates.env.globals["_"] = self.translator.gettext

        self.templates.env.globals["langs"] = [
            (code, self.translator.get_translations(code).get("t_name", code))
            for code in self.translator.get_langs()
        ]

        # Настройка статики и роутов
        self._setup_static()
        self._setup_routes()

    def _setup_static(self):
        static_dir = Path(__file__).parent / "static"
        self.fastapi.mount("/static", StaticFiles(directory=static_dir), name="static")

        # Отключаем кэширование статики и страниц, чтобы правки JS/CSS всегда применялись
        @self.fastapi.middleware("http")
        async def no_cache_middleware(request: Request, call_next):
            response = await call_next(request)
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            return response

    def _setup_routes(self):
        from .resources import ResourceManager

        self.fastapi.include_router(MainPageRouter(templates=self.templates, build_params=ResourceManager.get_build_params()))
        self.fastapi.include_router(ApiRouter())
        self.fastapi.include_router(ParticalPageRouter(prefix="/partials", templates=self.templates))
        self.fastapi.include_router(CompressRouter(prefix="/compress"))
        self.fastapi.include_router(BuildRouter(prefix="/build"))

    @property
    def app(self) -> FastAPI:
        return self.fastapi