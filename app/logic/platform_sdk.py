from pathlib import Path
from pprint import pprint

from app.resources import ResourceManager, PlatformSDKData
from app.utils import insert_before_ignoring_whitespace

class PlatformSdkInjector():
    """Вставляет скрипт и инициализацию SDK """
    @staticmethod
    def inject_sdk(platform: str, folder: str, filename: str) -> bool:
        # Платформа "None"/пустая — ничего не вставляем, считаем успехом
        if not platform or platform.lower() in ("none", "нет"):
            return True

        platform_data = ResourceManager.get_platform_sdk_data(platform)

        if not platform_data:
            return False

        inject_string = f"{platform_data.sdk_script}{platform_data.sdk_init}"

        path = Path(folder) / f"{filename}.html"
        head = "</head>"
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        is_sdk_alerady = False
        for i, line in enumerate(lines):
            if platform_data.sdk_script in line:
                is_sdk_alerady = True
            elif platform_data.sdk_init in line and is_sdk_alerady:
                print("already added")
                return True

            if head in line:
                line = f"//added by auto-pck {line.removeprefix(head)}{inject_string}\n{head}\n"
                lines[i] = line
                break

        with open(path, "w+", encoding="utf-8") as f:
            f.writelines(lines)

            f.seek(0)
            html = f.read()
            
        return inject_string in html