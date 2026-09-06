# app/routes/build.py
from fastapi import Query
from .router_base import BaseRouter
from app.logic import CustomPyGenerator
from app.models import CustomPyCreate


class BuildRouter(BaseRouter):
    def register_routes(self):
        @self.get("/list-files")
        async def list_files(path: str = Query(..., description="Путь к папке")):
            return CustomPyGenerator.list_py_files(path)

        @self.get("/get-custom-py/{file:path}")
        async def get_file(file: str, path: str = Query(..., description="Путь к папке")):
            return CustomPyGenerator.get_custompy_file(path, file)

        @self.post("/generate-custom-py")
        async def generate_custom_py(request: CustomPyCreate):
            return CustomPyGenerator.generate(request.folder, request.params, request.filename)

        @self.post("/run-build")
        async def run_build(request: dict):
            return {"ok": False, "message": "build_not_implemented"}
