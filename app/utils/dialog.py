# app/utils/dialog.py
from wdlg import filedialog
from typing import Optional

class DialogHelper:
    @staticmethod
    def select_folder(title: str = "Выберите папку", initial_dir: Optional[str] = None) -> Optional[str]:
        """
        Открывает диалог выбора папки.
        """
        try:
            # wdlg.filedialog.askdirectory не принимает title,
            # поэтому используем только initial_dir
            folder_path = filedialog.askdirectory(initialdir=initial_dir)
            return folder_path if folder_path else None
        except Exception as e:
            print(f"Ошибка при открытии диалога выбора папки: {e}")
            return None

    @staticmethod
    def select_file(
        title: str = "Выберите файл",
        initial_dir: Optional[str] = None,
        filetypes: Optional[list] = None
    ) -> Optional[str]:
        """
        Открывает диалог выбора файла.
        """
        try:
            # wdlg.filedialog.askopenfilename не принимает title,
            # поэтому используем только initial_dir и filetypes
            file_path = filedialog.askopenfilename(
                initialdir=initial_dir,
                filetypes=filetypes
            )
            return file_path if file_path else None
        except Exception as e:
            print(f"Ошибка при открытии диалога выбора файла: {e}")
            return None

    @staticmethod
    def select_save_file(
        title: str = "Сохранить файл как",
        initial_dir: Optional[str] = None,
        defaultextension: str = ".txt",
        filetypes: Optional[list] = None
    ) -> Optional[str]:
        """
        Открывает диалог сохранения файла.
        """
        try:
            file_path = filedialog.asksaveasfilename(
                initialdir=initial_dir,
                defaultextension=defaultextension,
                filetypes=filetypes
            )
            return file_path if file_path else None
        except Exception as e:
            print(f"Ошибка при открытии диалога сохранения: {e}")
            return None