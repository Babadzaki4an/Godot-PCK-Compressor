import json
from pathlib import Path
from .resource_model import *

class ResourceManager():
    GZIP_JS_CHANGES_NAME: str = "gzip_js_changes.json"
    GZIP_DECODE_NAME: str = "pako_inflate.min.js"

    BROTLI_JS_CHANGES_NAME: str = "brotli_js_changes.json"
    BROTLI_DECODER_NAME: str = "brotli_inflate.min.js"

    FILES_DIR: Path = Path(__file__).parent / "files"
    PLATFORM_DIR: Path = FILES_DIR / "platforms"

    plarform_names: list[str] = []

    @classmethod
    def _get_resource(cls, filename: str, resource_class: FromDictMixin, path: Path = None) -> dict | list | None:
        if not path:
            path = cls.FILES_DIR

        path = path / filename
        
        if not path.exists():
            return None

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
    def get_pako_name(cls) -> str:
        return cls.GZIP_DECODE_NAME
    
    @classmethod
    def get_brotli_decoder_path(cls) -> str:
        return str(cls.FILES_DIR / cls.get_brotli_decoder_name())

    @classmethod
    def get_pako_path(cls) -> str:
        return str(cls.FILES_DIR / cls.get_pako_name())

    #SDK платформ
    @classmethod
    def get_plarform_names(cls) -> list[str]:
        if cls.plarform_names:
            return cls.plarform_names

        for platform_file in cls.PLATFORM_DIR.iterdir():
            if platform_file.is_file():
                platform_name = platform_file.name.removesuffix(".json")
                if platform_name not in cls.plarform_names:
                    cls.plarform_names.append(platform_name)

        cls.plarform_names.sort()
        cls.plarform_names.insert(0, "None")

        return cls.plarform_names

    @classmethod
    def get_platform_sdk_data(cls, platform_name: str) -> PlatformSDKData | None:        return cls._get_resource(f"{platform_name}.json", PlatformSDKData, cls.PLATFORM_DIR)