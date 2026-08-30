import json
from pathlib import Path
from typing import Dict, Optional


class Translator:
    """
    Загружает переводы из JSON-файлов и предоставляет метод gettext.
    """

    def __init__(self, locales_dir: Path, default_lang: str = "ru"):
        self.locales_dir = locales_dir
        self.default_lang = default_lang
        self._translations: Dict[str, Dict[str, str]] = {}
        self._load_translations()

    def _load_translations(self):
        """Загружает все найденные JSON-файлы переводов."""
        for lang_dir in self.locales_dir.iterdir():
            if lang_dir.is_dir():
                lang_code = lang_dir.name
                json_file = lang_dir / "translations.json"
                if json_file.exists():
                    with open(json_file, "r", encoding="utf-8") as f:
                        self._translations[lang_code] = json.load(f)

    def get_translations(self, lang: Optional[str] = None) -> Dict[str, str]:
        """Возвращает словарь переводов для указанного языка (или default)."""
        if lang is None:
            lang = self.default_lang
        return self._translations.get(lang, self._translations.get(self.default_lang, {}))

    def gettext(self, key: str, lang: Optional[str] = None) -> str:
        """
        Возвращает перевод для ключа. Если ключ не найден — возвращает сам ключ.
        """
        translations = self.get_translations(lang)
        return translations.get(key, key)