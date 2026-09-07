import os
import re
import shutil

import zstandard

from .compressor import Compressor
from app.resources import ResourceManager


class ZstdCompressor(Compressor):
    """Сжатие файлов Godot алгоритмом ZStandard."""

    # Магические байты ZStandard (стандартный magic number):
    # 0x28 0xB5 0x2F 0xFD
    ZSTD_MAGIC = b'\x28\xb5\x2f\xfd'

    CHUNK_SIZE = 1024 * 1024  # 1 МБ — размер чанка для потоковой обработки

    @classmethod
    def _change_js(cls, folder: str, filename: str) -> bool:
        changes = ResourceManager.get_zstd_js_changes()
        js_file = os.path.join(folder, f"{filename}.js")
        return cls._do_change_js(js_file, changes)

    @classmethod
    def _compress_file(cls, folder: str, filename: str, extention: str, compress_level: int) -> tuple[bool, str]:
        path = os.path.join(folder, f"{filename}{cls._check_extention(extention)}")
        temp = path + '.tmp.zst'
        try:
            orig = os.path.getsize(path)

            if cls._is_compressed(path):
                return True, f"{extention} уже сжат {cls._fmt(orig)}"

            # Потоковое сжатие: читаем и пишем кусками, файл не грузится в память целиком
            compressor = zstandard.ZstdCompressor(level=compress_level).compressobj()
            with open(path, 'rb') as f_in, open(temp, 'wb') as f_out:
                while chunk := f_in.read(cls.CHUNK_SIZE):
                    f_out.write(compressor.compress(chunk))
                f_out.write(compressor.flush())

            new = os.path.getsize(temp)
            os.remove(path)
            shutil.move(temp, path)

            return True, cls._calculate_diff(orig, new, extention)

        except Exception as e:
            if os.path.exists(temp):
                os.remove(temp)
            return False, f"Ошибка: {e}"

    @classmethod
    def _is_compressed(cls, filepath: str) -> bool:
        with open(filepath, 'rb') as f:
            return f.read(4) == cls.ZSTD_MAGIC

    @classmethod
    def _add_decoder_in_folder(cls, folder: str) -> bool:
        name = ResourceManager.get_zstd_decoder_name()
        src = ResourceManager.get_zstd_decoder_path()
        shutil.copy2(src, os.path.join(folder, name))
        return True

    @classmethod
    def _add_decoder_in_html(cls, folder: str, filename: str) -> bool:
        file_path = os.path.join(folder, f"{filename}.html")
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        pattern = rf'<script\s+src=["\']{re.escape(filename)}\.js["\']\s*></script>'
        match = re.search(pattern, content)
        if not match:
            return False
        tag = f'<script src="{ResourceManager.get_zstd_decoder_name()}"></script>\n'
        if tag not in content:
            new_content = content[:match.start()] + tag + content[match.start():]
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
        return True

    @classmethod
    def _additional(cls, folder: str, filename: str) -> bool:
        return all([
            cls._add_decoder_in_folder(folder),
            cls._add_decoder_in_html(folder, filename),
        ])