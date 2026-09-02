import os
import zipfile

class ZipPacker():

    @classmethod
    def create_zip(cls, folder: str, filename: str, exclude_list: list[str]):
        zip_path = os.path.join(folder, f"{filename}.zip")
        files_to_zip = []
        for f in os.listdir(folder):
            fp = os.path.join(folder, f)
            if os.path.isfile(fp) and not f.lower().endswith('.zip'):
                ext = os.path.splitext(f)[1].lower()
                if ext not in exclude_list:
                    files_to_zip.append(f)
        if not files_to_zip:
            return "   Нет файлов для архивации"
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for fname in files_to_zip:
                    zf.write(os.path.join(folder, fname), arcname=fname)
            return f"   Создан {filename}.zip ({len(files_to_zip)} файлов)"
        except Exception as e:
            return f"Ошибка создания архива: {e}"