# tab_compress.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import threading

from scripts.processor import Processor


class CompressTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.folder_path = ""
        self.base_filename = "index"
        self.exclude_extensions = ['.backup', '.tmp', '.tmp.gz', '.zip', '.img', '.import', '.old']

        self._build_ui()
        self._load_config()          # загружаем сохранённые значения
        self._update_status()

    def _build_ui(self):
        main = ttk.Frame(self, padding=8)
        main.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(main, text="Godot Web Build Compressor", font=('Segoe UI', 13, 'bold'))
        title.pack(pady=(0, 5))

        # Папка проекта
        folder_frame = ttk.Frame(main)
        folder_frame.pack(fill=tk.X, pady=2)
        ttk.Label(folder_frame, text="Папка проекта:").pack(side=tk.LEFT, padx=(0, 8))
        self.folder_entry = ttk.Entry(folder_frame)
        self.folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        ttk.Button(folder_frame, text="Обзор...", command=self._browse_folder).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(folder_frame, text="Открыть папку", command=self._open_folder).pack(side=tk.LEFT)

        # Имя главного файла
        name_frame = ttk.Frame(main)
        name_frame.pack(fill=tk.X, pady=2)
        ttk.Label(name_frame, text="Имя главного файла:").pack(side=tk.LEFT, padx=(0, 8))
        self.name_entry = ttk.Entry(name_frame)
        self.name_entry.insert(0, "index")
        self.name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.folder_entry.bind("<KeyRelease>", lambda e: self._on_folder_changed())
        self.name_entry.bind("<KeyRelease>", lambda e: self._on_name_changed())

        # Статус
        self.status_label = ttk.Label(main, text="", anchor=tk.CENTER, font=('Segoe UI', 9, 'bold'))
        self.status_label.pack(fill=tk.X, pady=4)

        # Параметры
        params = ttk.LabelFrame(main, text="Параметры", padding=6)
        params.pack(fill=tk.X, pady=4)

        self.backup_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(params, text="Создавать бэкапы (.backup) перед изменениями", variable=self.backup_var, command=self.save_config).pack(anchor=tk.W)

        levels_frame = ttk.Frame(params)
        levels_frame.pack(fill=tk.X, pady=3)
        ttk.Label(levels_frame, text="Сжатие WASM (0-9):").pack(side=tk.LEFT, padx=(0, 5))
        self.wasm_spin = ttk.Spinbox(levels_frame, from_=0, to=9, width=5, state="readonly")
        self.wasm_spin.set(6)
        self.wasm_spin.pack(side=tk.LEFT, padx=(0, 15))
        ttk.Label(levels_frame, text="Сжатие PCK (0-9):").pack(side=tk.LEFT, padx=(0, 5))
        self.pck_spin = ttk.Spinbox(levels_frame, from_=0, to=9, width=5, state="readonly")
        self.pck_spin.set(6)
        self.pck_spin.pack(side=tk.LEFT)

        # При изменении спинбоксов сохраняем
        self.wasm_spin.bind("<<Spinbox-Selected>>", lambda e: self.save_config())
        self.pck_spin.bind("<<Spinbox-Selected>>", lambda e: self.save_config())

        self.replace_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(params, text="Заменить функции loadFetch/preload (необходимо для работы pako)", variable=self.replace_var, command=self.save_config).pack(anchor=tk.W, pady=(3, 0))

        self.crazy_game_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(params, text="CrazyGame (заменить /sdk.js на SDK CrazyGames)", variable=self.crazy_game_var, command=self.save_config).pack(anchor=tk.W, pady=(3, 0))

        self.remove_icons_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(params, text="Убрать иконки (удалить link-теги иконок)", variable=self.remove_icons_var, command=self.save_config).pack(anchor=tk.W, pady=(3, 0))

        self.zip_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(params, text="Упаковать все файлы в ZIP (исключая папки и существующие ZIP)", variable=self.zip_var, command=self.save_config).pack(anchor=tk.W)

        ttk.Label(params, text="Исключать из ZIP расширения:").pack(anchor=tk.W, pady=(3, 0))
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
        self.new_ext_entry.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(add_frame, text="Добавить", command=self._add_exclude).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(add_frame, text="Удалить выбранное", command=self._remove_exclude).pack(side=tk.LEFT)

        # Лог
        ttk.Label(main, text="Лог обработки:").pack(anchor=tk.W, pady=(4, 0))
        log_frame = ttk.Frame(main)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=2)
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, font=('Consolas', 9), height=9)
        scroll_log = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_log.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scroll_log.set)

        # Прогресс
        self.progress = ttk.Progressbar(main, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=4)
        self.progress.pack_forget()

        # Кнопка старта
        self.process_btn = ttk.Button(main, text="НАЧАТЬ ОБРАБОТКУ", command=self._start_processing)
        self.process_btn.pack(pady=5)

    def apply_theme(self, bg, fg, entry_bg, text_bg, select_bg, list_bg):
        self.status_label.config(background=bg, foreground=fg)
        self.folder_entry.config(background=entry_bg, foreground=fg)
        self.name_entry.config(background=entry_bg, foreground=fg)
        self.new_ext_entry.config(background=entry_bg, foreground=fg)
        self.log_text.config(bg=text_bg, fg=fg, insertbackground=fg, selectbackground=select_bg)
        self.exclude_listbox.config(bg=list_bg, fg=fg, selectbackground=select_bg)

    # ---------- Загрузка/сохранение конфигурации ----------
    def _load_config(self):
        config = self.app.config
        # Папка проекта
        folder = config.get("compress_folder", "")
        if folder and os.path.exists(folder):
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)
            self.folder_path = folder
        # Имя файла
        name = config.get("compress_filename", "index")
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, name)
        self.base_filename = name
        # Параметры
        self.wasm_spin.set(config.get("compress_wasm_level", 6))
        self.pck_spin.set(config.get("compress_pck_level", 6))
        self.backup_var.set(config.get("compress_backup", False))
        self.replace_var.set(config.get("compress_replace", True))
        self.crazy_game_var.set(config.get("compress_crazy_game", False))
        self.remove_icons_var.set(config.get("compress_remove_icons", True))
        self.zip_var.set(config.get("compress_zip", True))
        # Исключения (список)
        exts = config.get("compress_exclude_exts", ['.backup', '.tmp', '.tmp.gz', '.zip', '.img', '.import', '.old'])
        self.exclude_extensions = exts
        self.exclude_listbox.delete(0, tk.END)
        for ext in exts:
            self.exclude_listbox.insert(tk.END, ext)

    def save_config(self, *args):
        config = self.app.config
        config.set("compress_folder", self.folder_path)
        config.set("compress_filename", self.base_filename)
        config.set("compress_wasm_level", int(self.wasm_spin.get()))
        config.set("compress_pck_level", int(self.pck_spin.get()))
        config.set("compress_backup", self.backup_var.get())
        config.set("compress_replace", self.replace_var.get())
        config.set("compress_crazy_game", self.crazy_game_var.get())
        config.set("compress_remove_icons", self.remove_icons_var.get())
        config.set("compress_zip", self.zip_var.get())
        config.set("compress_exclude_exts", self.exclude_extensions)

    # ---------- Остальные методы (без изменений) ----------
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
            self.save_config()

    def _remove_exclude(self):
        sel = self.exclude_listbox.curselection()
        if sel:
            idx = sel[0]
            ext = self.exclude_listbox.get(idx)
            if ext in self.exclude_extensions:
                self.exclude_extensions.remove(ext)
            self.exclude_listbox.delete(idx)
            self.save_config()

    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Выберите папку проекта")
        if folder:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)
            self._on_folder_changed()
            self.save_config()

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
        self.save_config()

    def _on_name_changed(self):
        self.base_filename = self.name_entry.get().strip() or "index"
        self._update_status()
        self.save_config()

    def _update_status(self):
        if not self.folder_path or not os.path.exists(self.folder_path):
            self.status_label.config(text="❌ Папка не выбрана или не существует", foreground="red")
            self.process_btn.config(state=tk.DISABLED)
            return
        name = self.base_filename
        folder = self.folder_path
        js = os.path.exists(os.path.join(folder, f"{name}.js"))
        html = os.path.exists(os.path.join(folder, "index.html"))
        wasm = os.path.exists(os.path.join(folder, f"{name}.wasm"))
        pck = os.path.exists(os.path.join(folder, f"{name}.pck"))
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
            crazy_game=self.crazy_game_var.get(),
            remove_icons=self.remove_icons_var.get(),
            log_callback=self.log,
            done_callback=self._on_processing_done
        )
        self.processor.start()

    def log(self, msg):
        self.app.after(0, lambda: self._append_log(msg))

    def _append_log(self, msg):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.app.update_idletasks()

    def _on_processing_done(self, success, message):
        self.app.after(0, lambda: self._finish_processing(success, message))

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