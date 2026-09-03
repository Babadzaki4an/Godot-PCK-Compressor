# app/utils/dialog.py
import os
import platform
import subprocess
from typing import Optional, List, Tuple
import webview


class DialogHelper:

    @staticmethod
    def _get_window():
        try:
            return webview.active_window()
        except Exception:
            return None

    @staticmethod
    def _format_filetypes(filetypes: Optional[List[Tuple[str, str]]]) -> Optional[List[str]]:
        if not filetypes:
            return None
        formatted = []
        for desc, mask in filetypes:
            # Формат: "Описание (*.ext)"
            formatted.append(f"{desc} ({mask})")
        return formatted

    @staticmethod
    def select_folder(
        title: str = "Выберите папку",
        initial_dir: Optional[str] = None
    ) -> Optional[str]:
        window = DialogHelper._get_window()
        if not window:
            print("Ошибка: окно pywebview не активно")
            return None
        try:
            result = window.create_file_dialog(
                webview.FileDialog.FOLDER,
                directory=initial_dir or ""
            )
            if result and isinstance(result, tuple) and len(result) > 0:
                return result[0]
            return None
        except Exception as e:
            print(f"Ошибка выбора папки: {e}")
            return None

    @staticmethod
    def select_file(
        title: str = "Выберите файл",
        initial_dir: Optional[str] = None,
        filetypes: Optional[List[Tuple[str, str]]] = None
    ) -> Optional[str]:
        window = DialogHelper._get_window()
        if not window:
            print("Ошибка: окно pywebview не активно")
            return None
        try:
            kwargs = {
                "dialog_type": webview.FileDialog.OPEN,
                "directory": initial_dir or ""
            }
            formatted = DialogHelper._format_filetypes(filetypes)
            if formatted:
                kwargs["file_types"] = formatted
            result = window.create_file_dialog(**kwargs)
            if result and isinstance(result, tuple) and len(result) > 0:
                return result[0]
            return None
        except Exception as e:
            print(f"Ошибка выбора файла: {e}")
            return None

    @staticmethod
    def select_save_file(
        title: str = "Сохранить файл как",
        initial_dir: Optional[str] = None,
        defaultextension: str = ".txt",
        filetypes: Optional[List[Tuple[str, str]]] = None
    ) -> Optional[str]:
        window = DialogHelper._get_window()
        if not window:
            print("Ошибка: окно pywebview не активно")
            return None
        try:
            kwargs = {
                "dialog_type": webview.FileDialog.SAVE,
                "directory": initial_dir or "",
                "save_filename": "file" + defaultextension
            }
            formatted = DialogHelper._format_filetypes(filetypes)
            if formatted:
                kwargs["file_types"] = formatted
            result = window.create_file_dialog(**kwargs)
            if result and isinstance(result, tuple) and len(result) > 0:
                return result[0]
            return None
        except Exception:
            # fallback, если SAVE не поддерживается
            try:
                kwargs = {
                    "dialog_type": webview.OPEN_DIALOG,
                    "directory": initial_dir or "",
                    "save_filename": "file" + defaultextension
                }
                if formatted:
                    kwargs["file_types"] = formatted
                result = window.create_file_dialog(**kwargs)
                if result and isinstance(result, tuple) and len(result) > 0:
                    return result[0]
                return None
            except Exception as e2:
                print(f"Ошибка сохранения: {e2}")
                return None

    @staticmethod
    def open_in_explorer(path: str) -> bool:
        if not os.path.exists(path):
            print(f"Путь не существует: {path}")
            return False
        abs_path = os.path.abspath(path)
        try:
            system = platform.system()
            if system == "Windows":
                if os.path.isdir(abs_path):
                    os.startfile(abs_path)
                else:
                    subprocess.run(["explorer", "/select,", abs_path], check=True)
            elif system == "Darwin":
                if os.path.isdir(abs_path):
                    subprocess.run(["open", abs_path], check=True)
                else:
                    script = f'''
                    tell application "Finder"
                        reveal (POSIX file "{abs_path}" as alias)
                        activate
                    end tell
                    '''
                    subprocess.run(["osascript", "-e", script], check=True)
            elif system == "Linux":
                if os.path.isdir(abs_path):
                    subprocess.run(["xdg-open", abs_path], check=True)
                else:
                    parent_dir = os.path.dirname(abs_path)
                    if os.path.exists(parent_dir):
                        subprocess.run(["xdg-open", parent_dir], check=True)
                    else:
                        return False
            else:
                print(f"Неподдерживаемая ОС: {system}")
                return False
            return True
        except Exception as e:
            print(f"Ошибка открытия в проводнике: {e}")
            return False