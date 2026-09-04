import json
from pathlib import Path
from .resource_model import *

class ResourceManager():
    GZIP_JS_CHANGES_NAME: str = "gzip_js_changes.json"
    GZIP_DECODE_NAME: str = "pako_inflate.min.js"

    BROTLI_JS_CHANGES_NAME: str = "brotli_js_changes.json"
    BROTLI_DECODER_NAME: str = "brotli_inflate.min.js"

    @classmethod
    def _get_resource(cls, filename: str, resource_class: FromDictMixin) -> dict | list:
        path = str(Path(__file__).parent / "files" / filename)

        with open(path, 'r') as file:
            data = json.load(file)
            if isinstance(data, list):
                return list([resource_class.from_dict(val) for val in data])

            elif isinstance(data, dict):
                return resource_class.from_dict(data)

            else:
                return None


    @classmethod
    def get_gzip_js_changes(cls) -> list[ChangeResource]:
       """1 - loadFetch, 2 - preload"""
       return cls._get_resource(cls.GZIP_JS_CHANGES_NAME, ChangeResource)

    @classmethod
    def get_brotli_js_changes(cls) -> list[ChangeResource]:
        return cls._get_resource(cls.BROTLI_JS_CHANGES_NAME, ChangeResource)

    @classmethod
    def get_brotli_decoder_name(cls) -> str:
        return cls.BROTLI_DECODER_NAME

    @classmethod
    def get_brotli_decoder_path(cls) -> str:
        return str(Path(__file__).parent / "files" / cls.get_brotli_decoder_name())

    @classmethod
    def get_pako_path(cls) -> str:
        return str(Path(__file__).parent / "files" / cls.get_pako_name())

    @classmethod
    def get_pako_name(cls) -> str:
        return cls.GZIP_DECODE_NAME
