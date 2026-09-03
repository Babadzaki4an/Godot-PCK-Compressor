from .compressor import Compressor

class BrotliCompressor(Compressor):
    @classmethod
    def compress(cls, folder: str, filename: str, pck_compress_level: int, wasm_compress_level: int, create_backups: bool) -> bool:
        return False