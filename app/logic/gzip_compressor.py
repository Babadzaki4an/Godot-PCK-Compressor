import gzip
import os
import re
import shutil

from .compressor import Compressor
from app.resources import ResourceManager

class GzipCompressor(Compressor):
    @classmethod
    def _change_js(cls, folder: str, filename: str) -> bool:
        changes = ResourceManager.get_gzip_js_changes()
        js_file = os.path.join(folder, f"{filename}.js")

        return cls._do_change_js(js_file, changes)

    @classmethod
    def _compress_file(cls, folder: str, filename: str, extention: str, compress_level: int) -> tuple[bool, str]:
        path = f"{folder}/{filename}{cls._check_extention(extention)}"
        temp = path + '.tmp.gz'
        try:
            orig = os.path.getsize(path)

            if cls._is_compressed(path):
                return True, f"{extention} уже сжат {cls._fmt(orig)}"

            with open(path, 'rb') as f_in, gzip.open(temp, 'wb', compresslevel=compress_level) as f_out:
                f_out.writelines(f_in)
            new = os.path.getsize(temp)
            os.remove(path)
            shutil.move(temp, path)

            return True, cls._calculate_diff(orig, new, extention)
        
        except Exception as e:
            if os.path.exists(temp):
                os.remove(temp)
            return False, f"Ошибка: {e}"

    @classmethod
    def _add_pako_inflate_in_folder(cls, folder: str) -> bool:
        pako = ResourceManager.get_pako_name()
        pako_path = ResourceManager.get_pako_path()
        
        full_path = f"{folder}/{pako}"
        shutil.copy2(pako_path, full_path)

        return True

    @classmethod
    def _add_pako_inflate_in_html(cls, folder: str, filename: str) -> bool:
        file_path = f"{folder}/{filename}.html"

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        pattern = rf'<script\s+src=["\']{re.escape(filename)}\.js["\']\s*></script>'
        match = re.search(pattern, content)

        if not match:
            return False

        pako_tag = f'<script src="{ResourceManager.get_pako_name()}"></script>\n'

        if not pako_tag in content:
            new_content = content[:match.start()] + pako_tag + content[match.start():]

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

        return True
        

    @classmethod
    def _additional(cls, folder: str, filename: str,) -> bool:
        return all([
            cls._add_pako_inflate_in_folder(folder),
            cls._add_pako_inflate_in_html(folder, filename)
        ])

    @classmethod
    def _is_compressed(cls, filepath: str) -> bool:
        with open(filepath, 'rb') as f:
            return f.read(2) == b'\x1f\x8b'