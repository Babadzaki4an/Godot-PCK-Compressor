import os
import re
import shutil

from app.utils import replace_ignoring_whitespace
from app.resources import ChangeResource

class Compressor():

    @classmethod
    def compress(cls, folder: str, filename: str, pck_compress_level: int, wasm_compress_level: int, create_backups: bool) -> tuple[bool, str, str]:
        """1 - success, 2 - wasm message, 3 - pck message"""
        if create_backups:
            if not cls._create_backup(folder, filename, [".pck", ".wasm", ".js"]):
                return False, "", ""

        is_js_processed = cls._change_js(folder, filename)
        is_pck_compressed, pck_msg = cls._compress_file(folder, filename, ".pck", pck_compress_level)
        is_wasm_compressed, wasm_msg = cls._compress_file(folder, filename, ".wasm", wasm_compress_level)
        is_aditional_processed = cls._additional(folder, filename)
        
        return  all([is_js_processed, is_pck_compressed, is_wasm_compressed, is_aditional_processed]), wasm_msg, pck_msg

    @classmethod
    def _additional(cls, folder: str, filename: str,) -> bool:
        return True

    @classmethod
    def _change_js(cls, folder: str, filename: str) -> bool:
        return False

    @classmethod
    def _compress_file(cls, folder: str, filename: str, extention: str, compress_level: int) -> tuple[bool, str]:
        return False, ""

    @classmethod
    def _create_backup(cls, folder: str, filename: str, extentions: list[str]) -> bool:
        for extention in extentions:
            extention = cls._check_extention(extention)

            full_path = f"{folder}/{filename}{extention}"
            backup_path = full_path + ".backup"

            # Не затираем существующий бэкап повторным сжатием
            if os.path.exists(backup_path):
                continue

            shutil.copy2(full_path, backup_path)

        return True

    @classmethod
    def _check_extention(cls, extention: str) -> str:
        if not extention.startswith("."):
            extention = f".{extention}"

        return extention

    @classmethod
    def _fmt(cls, size):
        if size >= 1024*1024: return f"{size/(1024*1024):.2f} MB"
        if size >= 1024: return f"{size/1024:.2f} KB"
        return f"{size} B"

    @classmethod
    def _calculate_diff(cls, orig: float, new: float, extention: str) -> str:
        diff = orig - new
        ratio = (1 - new/orig)*100 if orig else 0
        diff_s = f"{diff/(1024*1024):.2f} MB" if diff > 1024*1024 else f"{diff/1024:.1f} KB" if diff > 1024 else f"{diff} B"
        return f"{extention}: {cls._fmt(orig)} → {cls._fmt(new)} (-{diff_s}, {ratio:.1f}%)"

    @classmethod
    def _do_change_js(cls, js_file: str, changes: list[ChangeResource]) -> bool:
        with open(js_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # JS уже пропатчен — считаем успехом (повторный запуск сжатия)
        if all(change.to in content for change in changes):
            return True

        for change in changes:
            old = change.change
            new = change.to
            content = replace_ignoring_whitespace(content, old, new)

        for change in changes:
            if change.to not in content:
                return False

        with open(js_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True

    @classmethod
    def _is_compressed(cls, filepath: str) -> bool:
        """Проверка на сжатие"""
        return False

    @classmethod
    def _is_compressed(cls, filepath: str) -> bool:
        return False