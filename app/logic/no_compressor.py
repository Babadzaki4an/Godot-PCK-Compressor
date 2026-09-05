import os

from .compressor import Compressor


class NoCompressor(Compressor):
    """Заглушка: не сжимает файлы, но проходит все шаги успешно."""

    @classmethod
    def compress(cls, folder: str, filename: str, pck_compress_level: int, wasm_compress_level: int, create_backups: bool) -> tuple[bool, str, str]:
        # Без сжатия — бэкапы не нужны, файлы не изменяются
        is_js_processed = cls._change_js(folder, filename)
        is_pck_compressed, pck_msg = cls._compress_file(folder, filename, ".pck", pck_compress_level)
        is_wasm_compressed, wasm_msg = cls._compress_file(folder, filename, ".wasm", wasm_compress_level)
        is_aditional_processed = cls._additional(folder, filename)
        return all([is_js_processed, is_pck_compressed, is_wasm_compressed, is_aditional_processed]), wasm_msg, pck_msg

    @classmethod
    def _change_js(cls, folder: str, filename: str) -> bool:
        # Nothing to patch — the build stays untouched.
        return True

    @classmethod
    def _compress_file(cls, folder: str, filename: str, extention: str, compress_level: int) -> tuple[bool, str]:
        path = os.path.join(folder, f"{filename}{cls._check_extention(extention)}")
        try:
            size = os.path.getsize(path)
        except OSError as e:
            return False, f"Ошибка: {e}"
        return True, f"{extention} пропущен (без сжатия) {cls._fmt(size)}"

    @classmethod
    def _additional(cls, folder: str, filename: str) -> bool:
        # Nothing extra to add.
        return True