from typing import List
from pydantic import BaseModel


class CheckProjectRequest(BaseModel):
    folder: str
    html_name: str = "index"

class Translation(BaseModel):
    lang: str = "en"

# ---------- Базовая модель с общими полями для сжатия----------
class BaseCompressRequest(BaseModel):
    """Общие поля для всех этапов сжатия"""
    folder: str
    filename: str = "index"
    

# ---------- Модель для эндпоинта /compress ----------
class CompressRequest(BaseCompressRequest):
    """Параметры сжатия (WASM, PCK, тип)"""
    compression_type: str = "zip"
    create_backup: bool = True
    wasm_level: int = 9
    pck_level: int = 9

# ---------- Модель для эндпоинта /platform ----------
class PlatformRequest(BaseCompressRequest):
    """Добавление SDK конкретной платформы"""
    platform: str

# ---------- Модель для эндпоинта /zippack ----------
class ZippackRequest(BaseCompressRequest):
    """Упаковка в ZIP (без дополнительных параметров)"""
    exclude_extensions: List[str] = []