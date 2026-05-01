import sys
import os
import re
import gzip
import shutil
import zipfile
from dataclasses import dataclass
from typing import List

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QLabel, QLineEdit, QPushButton,
                               QCheckBox, QComboBox, QSpinBox, QGroupBox,
                               QTextEdit, QProgressBar, QFileDialog, QMessageBox,
                               QFrame, QListWidget, QListWidgetItem)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QTextCursor


# ---------- ТЕМЫ (упрощённые, но рабочие) ----------
THEMES = {
    "Тёмная": """
        QMainWindow, QWidget { background-color: #2b2b2b; color: #ffffff; }
        QLabel, QCheckBox, QGroupBox { color: #ffffff; }
        QLineEdit, QTextEdit { background-color: #3c3f41; color: #fff; border: 1px solid #666; border-radius: 3px; }
        QPushButton { background-color: #4e5254; border: 1px solid #888; border-radius: 4px; padding: 5px; color: #fff; }
        QPushButton:hover { background-color: #5e6264; }
        QSpinBox { background-color: #3c3f41; color: #fff; border: 1px solid #666; }
        QComboBox { background-color: #3c3f41; color: #fff; border: 1px solid #666; }
        QGroupBox { border: 1px solid #666; margin-top: 12px; }
        QProgressBar { border: 1px solid #666; background-color: #3c3f41; color: #fff; }
        QProgressBar::chunk { background-color: #4e9a06; }
        QListWidget { background-color: #3c3f41; color: #fff; border: 1px solid #666; }
        QListWidget::item:selected { background-color: #4e9a06; }
    """,
    "Светлая": """
        QMainWindow, QWidget { background-color: #f5f5f5; color: #000; }
        QLabel, QCheckBox, QGroupBox { color: #000; }
        QLineEdit, QTextEdit { background-color: #fff; color: #000; border: 1px solid #aaa; border-radius: 3px; }
        QPushButton { background-color: #e0e0e0; border: 1px solid #888; border-radius: 4px; color: #000; }
        QPushButton:hover { background-color: #d0d0d0; }
        QSpinBox { background-color: #fff; color: #000; border: 1px solid #aaa; }
        QComboBox { background-color: #fff; color: #000; border: 1px solid #aaa; }
        QGroupBox { border: 1px solid #aaa; margin-top: 12px; }
        QProgressBar { border: 1px solid #aaa; background-color: #fff; color: #000; }
        QProgressBar::chunk { background-color: #0078d7; }
        QListWidget { background-color: #fff; color: #000; border: 1px solid #aaa; }
        QListWidget::item:selected { background-color: #0078d7; color: white; }
    """,
}


# ---------- ЗАМЕНЫ ФУНКЦИЙ (ТОЧНЫЕ СТРОКИ) ----------
# Эти строки взяты из вашего оригинального кода. Если в вашей версии Godot они другие – замените.
ORIG_LOADFETCH = """function loadFetch(file, tracker, fileSize, raw) {
\t\ttracker[file] = {
\t\t\ttotal: fileSize || 0,
\t\t\tloaded: 0,
\t\t\tdone: false,
\t\t};
\t\treturn fetch(file).then(function (response) {
\t\t\tif (!response.ok) {
\t\t\t\treturn Promise.reject(new Error(`Failed loading file '${file}'`));
\t\t\t}
\t\t\tconst tr = getTrackedResponse(response, tracker[file]);
\t\t\tif (raw) {
\t\t\t\treturn Promise.resolve(tr);
\t\t\t}
\t\t\treturn tr.arrayBuffer();
\t\t});
\t}"""

NEW_LOADFETCH = """//changed by autoPCK
function loadFetch(file, tracker, fileSize, raw) {
    var p_file = file;

    tracker[file] = {
        total: fileSize || 0,
        loaded: 0,
        done: false,
    };

    return fetch(file).then(function (response) {
        if (!response.ok) {
            return Promise.reject(new Error(`Failed loading file '${file}'`));
        }

        const tr = getTrackedResponse(response, tracker[p_file]);
        return Promise.resolve(tr.arrayBuffer().then(buffer => {
            return new Response(pako.inflate(buffer), { headers: tr.headers });
        }));
    });
}"""

ORIG_PRELOAD = """\tthis.preload = function (pathOrBuffer, destPath, fileSize) {
\t\tlet buffer = null;
\t\tif (typeof pathOrBuffer === 'string') {
\t\t\tconst me = this;
\t\t\treturn this.loadPromise(pathOrBuffer, fileSize).then(function (buf) {
\t\t\t\tme.preloadedFiles.push({
\t\t\t\t\tpath: destPath || pathOrBuffer,
\t\t\t\t\tbuffer: buf,
\t\t\t\t});
\t\t\t\treturn Promise.resolve();
\t\t\t});
\t\t} else if (pathOrBuffer instanceof ArrayBuffer) {
\t\t\tbuffer = new Uint8Array(pathOrBuffer);
\t\t} else if (ArrayBuffer.isView(pathOrBuffer)) {
\t\t\tbuffer = new Uint8Array(pathOrBuffer.buffer);
\t\t}
\t\tif (buffer) {
\t\t\tthis.preloadedFiles.push({
\t\t\t\tpath: destPath,
\t\t\t\tbuffer: pathOrBuffer,
\t\t\t});
\t\t\treturn Promise.resolve();
\t\t}
\t\treturn Promise.reject(new Error('Invalid object for preloading'));
\t};"""

NEW_PRELOAD = """//changed by autoPCK
this.preload = function (pathOrBuffer, destPath, fileSize) {
    let buffer = null;
    if (typeof pathOrBuffer === 'string') {
        const me = this;
        return this.loadPromise(pathOrBuffer, fileSize).then(function (buf) {
            buf.arrayBuffer().then(data => {
                me.preloadedFiles.push({
                    path: destPath || pathOrBuffer,
                    buffer: data,
                });
            });
            return Promise.resolve();
        });
    } else if (pathOrBuffer instanceof ArrayBuffer) {
        buffer = new Uint8Array(pathOrBuffer);
    } else if (ArrayBuffer.isView(pathOrBuffer)) {
        buffer = new Uint8Array(pathOrBuffer.buffer);
    }
    if (buffer) {
        this.preloadedFiles.push({
            path: destPath,
            buffer: pathOrBuffer,
        });
        return Promise.resolve();
    }
    return Promise.reject(new Error('Invalid object for preloading'));
};"""

FUNCTION_REPLACEMENTS = {ORIG_LOADFETCH: NEW_LOADFETCH, ORIG_PRELOAD: NEW_PRELOAD}


# ---------- ПОТОК ОБРАБОТКИ ----------
class Worker(QThread):
    log_signal = Signal(str)
    finished_signal = Signal(bool, str)

    def __init__(self, folder, filename, wasm_level, pck_level, backup, 
                 create_zip, exclude_exts, replace_functions):
        super().__init__()
        self.folder = folder
        self.filename = filename
        self.wasm_level = wasm_level
        self.pck_level = pck_level
        self.backup = backup
        self.create_zip = create_zip
        self.exclude_exts = exclude_exts
        self.replace_functions = replace_functions

    def run(self):
        try:
            self._process()
        except Exception as e:
            self.log_signal.emit(f"!!! Ошибка: {e}")
            self.finished_signal.emit(False, str(e))

    def _process(self):
        self.log_signal.emit("=== НАЧАЛО ОБРАБОТКИ ===")
        js_path = os.path.join(self.folder, f"{self.filename}.js")
        if not os.path.exists(js_path):
            self.finished_signal.emit(False, f"JS файл {self.filename}.js не найден")
            return

        # 1. Замена функций (если включена)
        if self.replace_functions:
            self.log_signal.emit("1. Замена функций в JavaScript...")
            with open(js_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if self.backup:
                shutil.copy2(js_path, js_path + ".backup")
                self.log_signal.emit("   Бэкап создан")
            replaced = 0
            for old, new in FUNCTION_REPLACEMENTS.items():
                if old in content:
                    content = content.replace(old, new)
                    replaced += 1
            if replaced:
                self.log_signal.emit(f"   Заменено {replaced} функций")
                with open(js_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                self.log_signal.emit("   Ни одна функция не найдена, изменений нет")
        else:
            self.log_signal.emit("1. Замена функций ОТКЛЮЧЕНА (пропуск)")

        # 2. Сжатие WASM и PCK
        for ext, level in [('wasm', self.wasm_level), ('pck', self.pck_level)]:
            path = os.path.join(self.folder, f"{self.filename}.{ext}")
            if os.path.exists(path):
                self.log_signal.emit(f"2. Сжатие {ext.upper()} (ур.{level})...")
                ok, msg = self._compress_file(path, level)
                self.log_signal.emit(msg)
            else:
                self.log_signal.emit(f"2. {ext.upper()} не найден, пропущено")

        # 3. Копирование pako_inflate.min.js
        self.log_signal.emit("3. Копирование pako_inflate.min.js...")
        if self._copy_pako():
            self.log_signal.emit("   Файл скопирован")
        else:
            self.log_signal.emit("   Файл pako_inflate.min.js не найден рядом с программой (пропуск)")

        # 4. Добавление pako в index.html
        html_path = os.path.join(self.folder, "index.html")
        if os.path.exists(html_path):
            self.log_signal.emit("4. Добавление pako в index.html...")
            if self._add_pako_to_html(html_path):
                self.log_signal.emit("   Готово")
            else:
                self.log_signal.emit("   Не удалось найти тег основного скрипта")
        else:
            self.log_signal.emit("4. index.html не найден, пропущено")

        # 5. Создание ZIP архива (без изменений содержимого файлов!)
        if self.create_zip:
            self.log_signal.emit("5. Создание ZIP архива...")
            self.log_signal.emit(self._create_zip())

        self.log_signal.emit("=== ОБРАБОТКА ЗАВЕРШЕНА ===")
        self.finished_signal.emit(True, "Успешно!")

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
        src = os.path.join(os.path.dirname(sys.argv[0]), "pako_inflate.min.js")
        dst = os.path.join(self.folder, "pako_inflate.min.js")
        if not os.path.exists(src):
            return False
        shutil.copy2(src, dst)
        return True

    def _add_pako_to_html(self, html_path):
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if self.backup:
            shutil.copy2(html_path, html_path + ".backup")
        pattern = rf'<script\s+src=["\']{re.escape(self.filename)}\.js["\']\s*></script>'
        match = re.search(pattern, content)
        if not match:
            return False
        pako_tag = '<script src="pako_inflate.min.js"></script>\n    '
        new_content = content[:match.start()] + pako_tag + content[match.start():]
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
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


# ---------- ГЛАВНОЕ ОКНО ----------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Godot Web Build Compressor")
        self.setMinimumSize(850, 750)
        self.folder_path = ""
        self.base_filename = "index"
        self.worker = None
        self.exclude_extensions = ['.backup', '.tmp', '.tmp.gz', '.zip']
        self._setup_ui()
        self.set_theme("Тёмная")
        self._update_status()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)

        title = QLabel("Godot Web Build Compressor")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        main_layout.addWidget(title)

        # Верхняя панель с темой
        top = QHBoxLayout()
        top.addStretch()
        top.addWidget(QLabel("Тема:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES.keys()))
        self.theme_combo.currentTextChanged.connect(self.set_theme)
        top.addWidget(self.theme_combo)
        main_layout.addLayout(top)

        # Папка
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Папка проекта:"))
        self.folder_edit = QLineEdit()
        self.folder_edit.textChanged.connect(self._on_folder_changed)
        row1.addWidget(self.folder_edit, 1)
        browse_btn = QPushButton("Обзор...")
        browse_btn.clicked.connect(self._browse_folder)
        row1.addWidget(browse_btn)
        open_btn = QPushButton("Открыть папку")
        open_btn.clicked.connect(self._open_folder)
        row1.addWidget(open_btn)
        main_layout.addLayout(row1)

        # Имя файла
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Имя главного файла:"))
        self.name_edit = QLineEdit("index")
        self.name_edit.textChanged.connect(self._on_name_changed)
        row2.addWidget(self.name_edit)
        main_layout.addLayout(row2)

        # Статус
        self.status_label = QLabel()
        self.status_label.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        main_layout.addWidget(self.status_label)

        # Группа параметров
        group = QGroupBox("Параметры")
        glay = QVBoxLayout()

        self.backup_cb = QCheckBox("Создавать бэкапы (.backup) перед изменениями")
        glay.addWidget(self.backup_cb)

        # Уровни сжатия
        h = QHBoxLayout()
        h.addWidget(QLabel("Сжатие WASM (0-9):"))
        self.wasm_spin = QSpinBox()
        self.wasm_spin.setRange(0, 9)
        self.wasm_spin.setValue(6)
        h.addWidget(self.wasm_spin)
        h.addSpacing(30)
        h.addWidget(QLabel("Сжатие PCK (0-9):"))
        self.pck_spin = QSpinBox()
        self.pck_spin.setRange(0, 9)
        self.pck_spin.setValue(6)
        h.addWidget(self.pck_spin)
        h.addStretch()
        glay.addLayout(h)

        # Замена функций (можно отключить)
        self.replace_func_cb = QCheckBox("Заменить функции loadFetch/preload (необходимо для работы pako)")
        self.replace_func_cb.setChecked(True)
        glay.addWidget(self.replace_func_cb)

        # ZIP
        self.zip_cb = QCheckBox("Упаковать все файлы в ZIP (исключая папки и существующие ZIP)")
        self.zip_cb.setChecked(True)
        glay.addWidget(self.zip_cb)

        # Исключения
        glay.addWidget(QLabel("Исключать из ZIP расширения:"))
        self.exclude_list = QListWidget()
        self.exclude_list.setMaximumHeight(80)
        for ext in self.exclude_extensions:
            self.exclude_list.addItem(ext)
        glay.addWidget(self.exclude_list)
        h2 = QHBoxLayout()
        self.new_ext_edit = QLineEdit()
        self.new_ext_edit.setPlaceholderText(".расширение")
        h2.addWidget(self.new_ext_edit)
        add_btn = QPushButton("Добавить")
        add_btn.clicked.connect(self._add_exclude)
        h2.addWidget(add_btn)
        del_btn = QPushButton("Удалить выбранное")
        del_btn.clicked.connect(self._remove_exclude)
        h2.addWidget(del_btn)
        glay.addLayout(h2)

        group.setLayout(glay)
        main_layout.addWidget(group)

        # Лог
        main_layout.addWidget(QLabel("Лог обработки:"))
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setMaximumHeight(200)
        main_layout.addWidget(self.log_text)

        # Прогресс
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        main_layout.addWidget(self.progress)

        # Кнопка
        self.process_btn = QPushButton("НАЧАТЬ ОБРАБОТКУ")
        self.process_btn.setMinimumHeight(40)
        self.process_btn.clicked.connect(self._start_processing)
        main_layout.addWidget(self.process_btn)

    def _add_exclude(self):
        ext = self.new_ext_edit.text().strip()
        if not ext:
            return
        if not ext.startswith('.'):
            ext = '.' + ext
        ext = ext.lower()
        if ext not in self.exclude_extensions:
            self.exclude_extensions.append(ext)
            self.exclude_list.addItem(ext)
            self.new_ext_edit.clear()

    def _remove_exclude(self):
        cur = self.exclude_list.currentItem()
        if cur:
            ext = cur.text()
            if ext in self.exclude_extensions:
                self.exclude_extensions.remove(ext)
            self.exclude_list.takeItem(self.exclude_list.row(cur))

    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку проекта")
        if folder:
            self.folder_edit.setText(folder)

    def _open_folder(self):
        if self.folder_path and os.path.exists(self.folder_path):
            if sys.platform == "win32":
                os.startfile(self.folder_path)
            else:
                os.system(f'xdg-open "{self.folder_path}"')
        else:
            QMessageBox.warning(self, "Внимание", "Сначала выберите папку проекта")

    def _on_folder_changed(self):
        self.folder_path = self.folder_edit.text()
        self._update_status()

    def _on_name_changed(self):
        self.base_filename = self.name_edit.text().strip() or "index"
        self._update_status()

    def _update_status(self):
        if not self.folder_path or not os.path.exists(self.folder_path):
            self.status_label.setText("❌ Папка не выбрана или не существует")
            self.status_label.setStyleSheet("color: #ff4444; font-weight: bold;")
            self.process_btn.setEnabled(False)
            return
        name = self.base_filename
        js = os.path.exists(os.path.join(self.folder_path, f"{name}.js"))
        html = os.path.exists(os.path.join(self.folder_path, "index.html"))
        wasm = os.path.exists(os.path.join(self.folder_path, f"{name}.wasm"))
        pck = os.path.exists(os.path.join(self.folder_path, f"{name}.pck"))
        text = f"JS: {'✓' if js else '✗'}   WASM: {'✓' if wasm else '✗'}   PCK: {'✓' if pck else '✗'}   HTML: {'✓' if html else '✗'}"
        self.status_label.setText(text)
        if js and html:
            self.status_label.setStyleSheet("color: #4e9a06; font-weight: bold;")
            self.process_btn.setEnabled(True)
        else:
            self.status_label.setStyleSheet("color: #ff4444; font-weight: bold;")
            self.process_btn.setEnabled(False)

    def set_theme(self, theme_name):
        self.setStyleSheet(THEMES[theme_name])
        self._update_status()

    def _start_processing(self):
        if not self.folder_path or not os.path.exists(self.folder_path):
            return
        self.process_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.log_text.clear()
        self.log("=== ЗАПУСК ОБРАБОТКИ ===")
        self.worker = Worker(
            folder=self.folder_path,
            filename=self.base_filename,
            wasm_level=self.wasm_spin.value(),
            pck_level=self.pck_spin.value(),
            backup=self.backup_cb.isChecked(),
            create_zip=self.zip_cb.isChecked(),
            exclude_exts=self.exclude_extensions,
            replace_functions=self.replace_func_cb.isChecked(),
        )
        self.worker.log_signal.connect(self.log)
        self.worker.finished_signal.connect(self._on_finished)
        self.worker.start()

    def log(self, msg):
        self.log_text.append(msg)
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_text.setTextCursor(cursor)
        QApplication.processEvents()

    def _on_finished(self, success, message):
        self.progress.setVisible(False)
        self.process_btn.setEnabled(True)
        if success:
            self.log(f"\n✅ {message}")
        else:
            self.log(f"\n❌ ОШИБКА: {message}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())