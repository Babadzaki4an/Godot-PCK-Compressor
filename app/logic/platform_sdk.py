import os
from pathlib import Path

from app.resources import ResourceManager, PlatformSDKData


class PlatformSdkInjector():
    """Вставляет скрипт и инициализацию SDK платформы в HTML билда."""

    @staticmethod
    def inject_sdk(platform: str, folder: str, filename: str) -> bool:
        # Платформа "None"/пустая — ничего не вставляем, считаем успехом
        if not platform or platform.lower() in ("none", "нет"):
            return True

        platform_data: PlatformSDKData | None = ResourceManager.get_platform_sdk_data(platform)
        if not platform_data:
            return False

        inject_string = f"{platform_data.sdk_script}{platform_data.sdk_init}"
        marker = f"<!-- added by auto-pck {platform} -->"

        path = Path(folder) / f"{filename}.html"
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()

        # SDK уже вставлен — не дублируем
        if platform_data.sdk_script in html and platform_data.sdk_init in html:
            return True

        snippet = f"{marker}{inject_string}"
        if "</head>" in html:
            html = html.replace("</head>", f"{snippet}\n</head>", 1)
        else:
            html += snippet

        with open(path, "w", encoding="utf-8") as f:
            f.write(html)

        return inject_string in html