# processor.py
import os
import gzip
import shutil
import zipfile
import threading
import re
from scripts.constants import FUNCTION_REPLACEMENTS

class Processor:
    def __init__(self, folder, filename, wasm_level, pck_level, backup,
                 create_zip, exclude_exts, replace_functions,
                 crazy_game, remove_icons,
                 log_callback, done_callback):
        self.folder = folder
        self.filename = filename
        self.wasm_level = wasm_level
        self.pck_level = pck_level
        self.backup = backup
        self.create_zip = create_zip
        self.exclude_exts = exclude_exts
        self.replace_functions = replace_functions
        self.crazy_game = crazy_game
        self.remove_icons = remove_icons
        self.log = log_callback
        self.done = done_callback

        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def start(self):
        thread = threading.Thread(target=self._process, daemon=True)
        thread.start()

    def _process(self):
        try:
            self._run()
        except Exception as e:
            self.log(f"!!! Критическая ошибка: {e}")
            self.done(False, str(e))

    def _run(self):
        self.log("=== НАЧАЛО ОБРАБОТКИ ===")
        js_path = os.path.join(self.folder, f"{self.filename}.js")
        if not os.path.exists(js_path):
            self.done(False, f"JS файл {self.filename}.js не найден")
            return

        if self.replace_functions:
            self.log("1. Замена функций в JavaScript...")
            with open(js_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if self.backup:
                shutil.copy2(js_path, js_path + ".backup")
                self.log("   Бэкап создан")
            replaced = 0
            for old, new in FUNCTION_REPLACEMENTS.items():
                if old in content:
                    content = content.replace(old, new)
                    replaced += 1
            if replaced:
                self.log(f"   Заменено {replaced} функций")
                with open(js_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                self.log("   Ни одна функция не найдена, изменений нет")
        else:
            self.log("1. Замена функций ОТКЛЮЧЕНА (пропуск)")

        for ext, level in [('wasm', self.wasm_level), ('pck', self.pck_level)]:
            path = os.path.join(self.folder, f"{self.filename}.{ext}")
            if os.path.exists(path):
                self.log(f"2. Сжатие {ext.upper()} (ур.{level})...")
                ok, msg = self._compress_file(path, level)
                self.log(msg)
            else:
                self.log(f"2. {ext.upper()} не найден, пропущено")

        self.log("3. Копирование pako_inflate.min.js...")
        if self._copy_pako():
            self.log("   Файл скопирован")
        else:
            self.log("   Файл pako_inflate.min.js не найден (пропуск)")

        html_path = os.path.join(self.folder, "index.html")
        if os.path.exists(html_path):
            self.log("4. Модификация index.html (pako, CrazyGame, иконки)...")
            if self._modify_html(html_path):
                self.log("   Готово")
            else:
                self.log("   Не удалось добавить pako (тег скрипта не найден)")
        else:
            self.log("4. index.html не найден, пропущено")

        if self.create_zip:
            self.log("5. Создание ZIP архива...")
            self.log(self._create_zip())

        self.log("=== ОБРАБОТКА ЗАВЕРШЕНА ===")
        self.done(True, "Успешно!")

    def _compress_file(self, path, level):
        temp = path + '.tmp.gz'
        try:
            orig = os.path.getsize(path)
            with open(path, 'rb') as f_in, gzip.open(temp, 'wb', compresslevel=level) as f_out:
                f_out.writelines(f_in)
            new = os.path.getsize(temp)
            os.remove(path)
            shutil.move(temp, path)
            diff = orig - new
            ratio = (1 - new/orig)*100 if orig else 0
            diff_s = f"{diff/(1024*1024):.2f} MB" if diff > 1024*1024 else f"{diff/1024:.1f} KB" if diff > 1024 else f"{diff} B"
            msg = f"   {os.path.basename(path)}: {self._fmt(orig)} → {self._fmt(new)} (-{diff_s}, {ratio:.1f}%)"
            return True, msg
        except Exception as e:
            if os.path.exists(temp):
                os.remove(temp)
            return False, f"   Ошибка: {e}"

    @staticmethod
    def _fmt(size):
        if size >= 1024*1024: return f"{size/(1024*1024):.2f} MB"
        if size >= 1024: return f"{size/1024:.2f} KB"
        return f"{size} B"

    def _copy_pako(self):
        src = os.path.join(self.root_dir, "resources", "pako_inflate.min.js")
        dst = os.path.join(self.folder, "pako_inflate.min.js")
        if not os.path.exists(src):
            return False
        shutil.copy2(src, dst)
        return True

    def _modify_html(self, html_path):
        """Добавляет pako, заменяет /sdk.js на CrazyGames SDK и удаляет иконки."""
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if self.backup:
            shutil.copy2(html_path, html_path + ".backup")

        modified = False

        # 1. Добавление pako перед основным скриптом
        pattern = rf'<script\s+src=["\']{re.escape(self.filename)}\.js["\']\s*></script>'
        match = re.search(pattern, content)
        if match:
            pako_tag = '<script src="pako_inflate.min.js"></script>\n    '
            content = content[:match.start()] + pako_tag + content[match.start():]
            modified = True
        else:
            # Если не нашли, просто пишем в лог, но продолжаем
            self.log("   Не удалось найти тег основного скрипта для pako")
            # но не возвращаем False, т.к. другие замены могут сработать

        # 2. Замена /sdk.js на CrazyGames SDK (если включено)
        if self.crazy_game:
            sdk_pattern = r'<script[^>]*src=["\']/sdk\.js["\'][^>]*>\s*</script>'
            if re.search(sdk_pattern, content, re.IGNORECASE):
                replacement = (
                    '<script src="https://sdk.crazygames.com/crazygames-sdk-v3.js"></script>\n'
                    '    <script>await window.CrazyGames.SDK.init();</script>'
                )
                content = re.sub(sdk_pattern, replacement, content, flags=re.IGNORECASE)
                modified = True
                self.log("   Заменён /sdk.js на CrazyGames SDK")
            else:
                self.log("   Строка /sdk.js не найдена, пропуск")

        # 3. Удаление иконок (если включено)
        if self.remove_icons:
            # Удаляем строку с id="-gd-engine-icon"
            icon_pattern1 = r'<link[^>]*id="-gd-engine-icon"[^>]*/?>'
            if re.search(icon_pattern1, content, re.IGNORECASE):
                content = re.sub(icon_pattern1, '', content, flags=re.IGNORECASE)
                modified = True
            # Удаляем строку с apple-touch-icon
            icon_pattern2 = r'<link[^>]*rel="apple-touch-icon"[^>]*/?>'
            if re.search(icon_pattern2, content, re.IGNORECASE):
                content = re.sub(icon_pattern2, '', content, flags=re.IGNORECASE)
                modified = True
            if modified:
                self.log("   Иконки удалены")
            else:
                self.log("   Иконки не найдены")

        if modified:
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        else:
            # Если не было никаких изменений, но файл не был изменён
            # Считаем успехом, т.к. могли быть только доп. изменения
            return True

    def _create_zip(self):
        zip_path = os.path.join(self.folder, f"{self.filename}.zip")
        files_to_zip = []
        for f in os.listdir(self.folder):
            fp = os.path.join(self.folder, f)
            if os.path.isfile(fp) and not f.lower().endswith('.zip'):
                ext = os.path.splitext(f)[1].lower()
                if ext not in self.exclude_exts:
                    files_to_zip.append(f)
        if not files_to_zip:
            return "   Нет файлов для архивации"
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for fname in files_to_zip:
                    zf.write(os.path.join(self.folder, fname), arcname=fname)
            return f"   Создан {self.filename}.zip ({len(files_to_zip)} файлов)"
        except Exception as e:
            return f"   Ошибка создания архива: {e}"