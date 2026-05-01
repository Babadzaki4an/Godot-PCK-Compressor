import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import re
import gzip
import shutil
import zipfile
import sys

# Попытка импорта для изменения цвета заголовка окна (только Windows)
try:
    import pywinstyles
    HAS_PYWINSTYLES = True
except ImportError:
    HAS_PYWINSTYLES = False

# ---------- Константы замены функций ----------
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

# ---------- Класс фоновой обработки ----------
class Processor:
    def __init__(self, folder, filename, wasm_level, pck_level, backup,
                 create_zip, exclude_exts, replace_functions,
                 log_callback, done_callback):
        self.folder = folder
        self.filename = filename
        self.wasm_level = wasm_level
        self.pck_level = pck_level
        self.backup = backup
        self.create_zip = create_zip
        self.exclude_exts = exclude_exts
        self.replace_functions = replace_functions
        self.log = log_callback
        self.done = done_callback

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
            self.log("4. Добавление pako в index.html...")
            if self._add_pako_to_html(html_path):
                self.log("   Готово")
            else:
                self.log("   Не удалось найти тег основного скрипта")
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
        src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pako_inflate.min.js")
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


# ---------- ГЛАВНОЕ ПРИЛОЖЕНИЕ ----------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Godot Web Build Compressor")
        self.geometry("500x650")
        self.minsize(500, 650)

        self.folder_path = ""
        self.base_filename = "index"
        self.exclude_extensions = ['.backup', '.tmp', '.tmp.gz', '.zip']

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.current_theme = "dark"

        self.outer_frame = tk.Frame(self, bd=2, relief="solid")
        self.outer_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        self._setup_ui()
        self._apply_theme()
        self._update_status()

    def _setup_ui(self):
        main = ttk.Frame(self.outer_frame, padding=8)
        main.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(main, text="Godot Web Build Compressor", font=('Segoe UI', 13, 'bold'))
        title.pack(pady=(0, 5))

        top_frame = ttk.Frame(main)
        top_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(top_frame, text="Тема:").pack(side=tk.RIGHT, padx=(0,5))
        self.theme_var = tk.StringVar(value="Тёмная")
        theme_combo = ttk.Combobox(top_frame, textvariable=self.theme_var, values=["Тёмная", "Светлая"], state="readonly", width=10)
        theme_combo.pack(side=tk.RIGHT)
        theme_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_theme())

        folder_frame = ttk.Frame(main)
        folder_frame.pack(fill=tk.X, pady=2)
        ttk.Label(folder_frame, text="Папка проекта:").pack(side=tk.LEFT, padx=(0,8))
        self.folder_entry = ttk.Entry(folder_frame)
        self.folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,8))
        ttk.Button(folder_frame, text="Обзор...", command=self._browse_folder).pack(side=tk.LEFT, padx=(0,4))
        ttk.Button(folder_frame, text="Открыть папку", command=self._open_folder).pack(side=tk.LEFT)

        name_frame = ttk.Frame(main)
        name_frame.pack(fill=tk.X, pady=2)
        ttk.Label(name_frame, text="Имя главного файла:").pack(side=tk.LEFT, padx=(0,8))
        self.name_entry = ttk.Entry(name_frame)
        self.name_entry.insert(0, "index")
        self.name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.folder_entry.bind("<KeyRelease>", lambda e: self._on_folder_changed())
        self.name_entry.bind("<KeyRelease>", lambda e: self._on_name_changed())

        self.status_label = ttk.Label(main, text="", anchor=tk.CENTER, font=('Segoe UI', 9, 'bold'))
        self.status_label.pack(fill=tk.X, pady=4)

        params = ttk.LabelFrame(main, text="Параметры", padding=6)
        params.pack(fill=tk.X, pady=4)

        self.backup_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(params, text="Создавать бэкапы (.backup) перед изменениями", variable=self.backup_var).pack(anchor=tk.W)

        levels_frame = ttk.Frame(params)
        levels_frame.pack(fill=tk.X, pady=3)
        ttk.Label(levels_frame, text="Сжатие WASM (0-9):").pack(side=tk.LEFT, padx=(0,5))
        self.wasm_spin = ttk.Spinbox(levels_frame, from_=0, to=9, width=5, state="readonly")
        self.wasm_spin.set(6)
        self.wasm_spin.pack(side=tk.LEFT, padx=(0,15))
        ttk.Label(levels_frame, text="Сжатие PCK (0-9):").pack(side=tk.LEFT, padx=(0,5))
        self.pck_spin = ttk.Spinbox(levels_frame, from_=0, to=9, width=5, state="readonly")
        self.pck_spin.set(6)
        self.pck_spin.pack(side=tk.LEFT)

        self.replace_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(params, text="Заменить функции loadFetch/preload (необходимо для работы pako)", variable=self.replace_var).pack(anchor=tk.W, pady=(3,0))

        self.zip_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(params, text="Упаковать все файлы в ZIP (исключая папки и существующие ZIP)", variable=self.zip_var).pack(anchor=tk.W)

        ttk.Label(params, text="Исключать из ZIP расширения:").pack(anchor=tk.W, pady=(3,0))
        list_frame = ttk.Frame(params)
        list_frame.pack(fill=tk.X, pady=2)
        self.exclude_listbox = tk.Listbox(list_frame, height=3)
        self.exclude_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.exclude_listbox.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.exclude_listbox.config(yscrollcommand=scroll.set)
        for ext in self.exclude_extensions:
            self.exclude_listbox.insert(tk.END, ext)

        add_frame = ttk.Frame(params)
        add_frame.pack(fill=tk.X, pady=2)
        self.new_ext_entry = ttk.Entry(add_frame, width=12)
        self.new_ext_entry.pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(add_frame, text="Добавить", command=self._add_exclude).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(add_frame, text="Удалить выбранное", command=self._remove_exclude).pack(side=tk.LEFT)

        ttk.Label(main, text="Лог обработки:").pack(anchor=tk.W, pady=(4,0))
        log_frame = ttk.Frame(main)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=2)
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, font=('Consolas', 9), height=9)
        scroll_log = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_log.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scroll_log.set)

        self.progress = ttk.Progressbar(main, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=4)
        self.progress.pack_forget()

        self.process_btn = ttk.Button(main, text="НАЧАТЬ ОБРАБОТКУ", command=self._start_processing)
        self.process_btn.pack(pady=5)

    def _apply_theme(self):
        theme = self.theme_var.get()
        if theme == "Тёмная":
            bg = "#2b2b2b"
            fg = "#ffffff"
            entry_bg = "#3c3f41"
            text_bg = "#252526"
            button_bg = "#3c6e47"
            button_active_bg = "#2b5a3b"
            select_bg = "#4e9a06"
            progress = "#4e9a06"
            list_bg = "#3c3f41"
            border_color = "#3c3f41"
            check_active_bg = "#3c3f41"
            check_active_fg = fg
            if HAS_PYWINSTYLES and sys.platform == "win32":
                pywinstyles.change_header_color(self, color="#2b2b2b")
                pywinstyles.change_title_color(self, color="#ffffff")
        else:
            bg = "#f5f5f5"
            fg = "#000000"
            entry_bg = "#ffffff"
            text_bg = "#f9f9f9"
            button_bg = "#0078d7"
            button_active_bg = "#005a9e"
            select_bg = "#cce4ff"
            progress = "#0078d7"
            list_bg = "#ffffff"
            border_color = "#c0c0c0"
            check_active_bg = "#e0e0e0"
            check_active_fg = fg
            if HAS_PYWINSTYLES and sys.platform == "win32":
                pywinstyles.change_header_color(self, color="#f5f5f5")
                pywinstyles.change_title_color(self, color="#000000")

        self.configure(bg=bg)
        self.outer_frame.config(bg=border_color, highlightbackground=border_color)

        self.style.configure('TFrame', background=bg)
        self.style.configure('TLabel', background=bg, foreground=fg)
        self.style.configure('TLabelframe', background=bg, foreground=fg)
        self.style.configure('TLabelframe.Label', background=bg, foreground=fg)
        self.style.configure('TButton', background=button_bg, foreground=fg)
        self.style.map('TButton',
                       background=[('active', button_active_bg), ('pressed', button_active_bg)],
                       foreground=[('active', fg)])
        self.style.configure('TCheckbutton', background=bg, foreground=fg)
        self.style.map('TCheckbutton',
                       background=[('active', check_active_bg), ('selected', bg)],
                       foreground=[('active', check_active_fg), ('selected', fg)],
                       indicatorcolor=[('selected', select_bg)])
        self.style.configure('TProgressbar', background=progress, troughcolor=select_bg)
        self.style.configure('TEntry', fieldbackground=entry_bg, foreground=fg)
        self.style.configure('TSpinbox', fieldbackground=entry_bg, foreground=fg, arrowcolor=fg)
        self.style.configure('TCombobox', fieldbackground=entry_bg, foreground=fg)
        self.style.map('TCombobox', fieldbackground=[('readonly', entry_bg)], foreground=[('readonly', fg)])

        self.log_text.config(bg=text_bg, fg=fg, insertbackground=fg, selectbackground=select_bg)
        self.exclude_listbox.config(bg=list_bg, fg=fg, selectbackground=select_bg)
        self.status_label.config(background=bg, foreground=fg)
        self.folder_entry.config(background=entry_bg, foreground=fg)
        self.name_entry.config(background=entry_bg, foreground=fg)
        self.new_ext_entry.config(background=entry_bg, foreground=fg)

    def _add_exclude(self):
        ext = self.new_ext_entry.get().strip()
        if not ext:
            return
        if not ext.startswith('.'):
            ext = '.' + ext
        ext = ext.lower()
        if ext not in self.exclude_extensions:
            self.exclude_extensions.append(ext)
            self.exclude_listbox.insert(tk.END, ext)
            self.new_ext_entry.delete(0, tk.END)

    def _remove_exclude(self):
        sel = self.exclude_listbox.curselection()
        if sel:
            idx = sel[0]
            ext = self.exclude_listbox.get(idx)
            if ext in self.exclude_extensions:
                self.exclude_extensions.remove(ext)
            self.exclude_listbox.delete(idx)

    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Выберите папку проекта")
        if folder:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)
            self._on_folder_changed()

    def _open_folder(self):
        if self.folder_path and os.path.exists(self.folder_path):
            if sys.platform == "win32":
                os.startfile(self.folder_path)
            else:
                os.system(f'xdg-open "{self.folder_path}"')
        else:
            messagebox.showwarning("Внимание", "Сначала выберите папку проекта")

    def _on_folder_changed(self):
        self.folder_path = self.folder_entry.get().strip()
        self._update_status()

    def _on_name_changed(self):
        self.base_filename = self.name_entry.get().strip() or "index"
        self._update_status()

    def _update_status(self):
        if not self.folder_path or not os.path.exists(self.folder_path):
            self.status_label.config(text="❌ Папка не выбрана или не существует", foreground="red")
            self.process_btn.config(state=tk.DISABLED)
            return
        name = self.base_filename
        js = os.path.exists(os.path.join(self.folder_path, f"{name}.js"))
        html = os.path.exists(os.path.join(self.folder_path, "index.html"))
        wasm = os.path.exists(os.path.join(self.folder_path, f"{name}.wasm"))
        pck = os.path.exists(os.path.join(self.folder_path, f"{name}.pck"))
        text = f"JS: {'✓' if js else '✗'}   WASM: {'✓' if wasm else '✗'}   PCK: {'✓' if pck else '✗'}   HTML: {'✓' if html else '✗'}"
        if js and html:
            self.status_label.config(text=text, foreground="green")
            self.process_btn.config(state=tk.NORMAL)
        else:
            self.status_label.config(text=text, foreground="red")
            self.process_btn.config(state=tk.DISABLED)

    def _start_processing(self):
        if not self.folder_path or not os.path.exists(self.folder_path):
            return
        self.process_btn.config(state=tk.DISABLED)
        self.progress.pack(fill=tk.X, pady=4)
        self.progress.start()
        self.log_text.delete(1.0, tk.END)
        self.log("=== ЗАПУСК ОБРАБОТКИ ===")

        self.processor = Processor(
            folder=self.folder_path,
            filename=self.base_filename,
            wasm_level=int(self.wasm_spin.get()),
            pck_level=int(self.pck_spin.get()),
            backup=self.backup_var.get(),
            create_zip=self.zip_var.get(),
            exclude_exts=self.exclude_extensions.copy(),
            replace_functions=self.replace_var.get(),
            log_callback=self.log,
            done_callback=self._on_processing_done
        )
        self.processor.start()

    def log(self, msg):
        self.after(0, lambda: self._append_log(msg))

    def _append_log(self, msg):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.update_idletasks()

    def _on_processing_done(self, success, message):
        self.after(0, lambda: self._finish_processing(success, message))

    def _finish_processing(self, success, message):
        self.progress.stop()
        self.progress.pack_forget()
        self.process_btn.config(state=tk.NORMAL)
        if success:
            self.log_text.insert(tk.END, f"\n✅ {message}\n")
            messagebox.showinfo("Готово", message)
        else:
            self.log_text.insert(tk.END, f"\n❌ ОШИБКА: {message}\n")
            messagebox.showerror("Ошибка", f"Обработка не удалась:\n{message}")
        self.log_text.see(tk.END)


if __name__ == "__main__":
    app = App()
    app.mainloop()