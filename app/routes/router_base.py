from fastapi import APIRouter
from fastapi.templating import Jinja2Templates
from typing import Optional

class BaseRouter(APIRouter):
    """
    Базовый класс для всех роутеров.
    Содержит метод register_routes, который должен быть переопределён.
    """
    def __init__(
        self,
        prefix: str = "",
        tags: Optional[list] = None,
        templates: Optional[Jinja2Templates] = None
    ):
        super().__init__(prefix=prefix, tags=tags)
        self.templates = templates
        self.register_routes()

    def register_routes(self):
        """
        Переопределяемый метод для регистрации эндпоинтов.
        Внутри используйте self.get(), self.post() и т.д.
        """
        pass