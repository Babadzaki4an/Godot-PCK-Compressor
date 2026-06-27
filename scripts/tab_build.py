# tab_build.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import threading
import subprocess
import glob
import shutil
import re
import zipfile
import tempfile

from scripts.constants import get_build_commands, get_scons_cmd, build_wasm_cmd, DEFAULT_WASM_FLAGS, OPTIMIZATION_LEVELS


class BuildTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.build_process = None
        self._build_ui()
        self._load_config()
        self._update_profile_list()
        self._update_script_list()

    def _build_ui(self):
        main = ttk.Frame(self, padding=8)
        main.pack(fill=tk.BOTH, expand=True)

        # Заголовок
        ttk.Label(main, text="Сборка Godot из исходников", font=('Segoe UI', 13, 'bold')).pack(pady=(0, 5))

        # ---- Кнопка показа/скрытия путей ----
        self.toggle_paths_btn = ttk.Button(main, text="▶ Показать пути", command=self._toggle_paths)
        self.toggle_paths_btn.pack(anchor=tk.W, pady=(0, 5))

        # ---------- Блок путей (скрываемый) ----------
        self.paths_frame = ttk.Frame(main)

        # emsdk
        row1 = ttk.Frame(self.paths_frame)
        row1.pack(fill=tk.X, pady=2)
        ttk.Label(row1, text="emsdk:", width=16, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 5))
        self.emsdk_entry = ttk.Entry(row1)
        self.emsdk_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(row1, text="Обзор", command=self._browse_emsdk, width=8).pack(side=tk.LEFT)

        # Godot
        row2 = ttk.Frame(self.paths_frame)
        row2.pack(fill=tk.X, pady=2)
        ttk.Label(row2, text="Godot:", width=16, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 5))
        self.godot_entry = ttk.Entry(row2)
        self.godot_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(row2, text="Обзор", command=self._browse_godot, width=8).pack(side=tk.LEFT)

        # Папка профилей
        row3 = ttk.Frame(self.paths_frame)
        row3.pack(fill=tk.X, pady=2)
        ttk.Label(row3, text="Папка профилей:", width=16, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 5))
        self.profile_dir_entry = ttk.Entry(row3)
        self.profile_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(row3, text="Обзор", command=self._browse_profile_dir, width=8).pack(side=tk.LEFT)

        # wasm-opt
        row4 = ttk.Frame(self.paths_frame)
        row4.pack(fill=tk.X, pady=2)
        ttk.Label(row4, text="wasm-opt:", width=16, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 5))
        self.wasmopt_entry = ttk.Entry(row4)
        self.wasmopt_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(row4, text="Обзор", command=self._browse_wasmopt, width=8).pack(side=tk.LEFT)

        # Папка со скриптами custom.py
        row5 = ttk.Frame(self.paths_frame)
        row5.pack(fill=tk.X, pady=2)
        ttk.Label(row5, text="Папка скриптов:", width=16, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 5))
        self.scripts_dir_entry = ttk.Entry(row5)
        self.scripts_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(row5, text="Обзор", command=self._browse_scripts_dir, width=8).pack(side=tk.LEFT)

        # (paths_frame пока не упаковываем)

        # ---- Кнопка показа/скрытия настроек WASM ----
        self.toggle_wasm_btn = ttk.Button(main, text="▶ Показать настройки WASM", command=self._toggle_wasm_settings)
        self.toggle_wasm_btn.pack(anchor=tk.W, pady=(5, 0))

        # ---------- Блок настроек WASM (скрываемый) ----------
        self.wasm_settings_frame = ttk.Frame(main)

        # Уровень оптимизации
        opt_frame = ttk.Frame(self.wasm_settings_frame)
        opt_frame.pack(fill=tk.X, pady=2)
        ttk.Label(opt_frame, text="Уровень оптимизации:", width=20, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 8))
        self.opt_level_var = tk.StringVar(value="-Oz")
        opt_combo = ttk.Combobox(opt_frame, textvariable=self.opt_level_var,
                                 values=list(OPTIMIZATION_LEVELS.keys()), state="readonly", width=10)
        opt_combo.pack(side=tk.LEFT)
        opt_combo.bind("<<ComboboxSelected>>", lambda e: self.save_config())

        # Флаги (две колонки)
        flags_frame = ttk.Frame(self.wasm_settings_frame)
        flags_frame.pack(fill=tk.X, pady=2)
        self.flag_vars = {}
        mid = len(DEFAULT_WASM_FLAGS) // 2
        left = ttk.Frame(flags_frame)
        left.pack(side=tk.LEFT, fill=tk.X, expand=True)
        right = ttk.Frame(flags_frame)
        right.pack(side=tk.LEFT, fill=tk.X, expand=True)

        for i, flag in enumerate(DEFAULT_WASM_FLAGS):
            var = tk.BooleanVar(value=True)
            self.flag_vars[flag] = var
            label = flag[2:] if flag.startswith('--') else flag
            chk = ttk.Checkbutton(left if i < mid else right, text=label, variable=var, command=self.save_config)
            chk.pack(anchor=tk.W)

        # (wasm_settings_frame пока не упаковываем)

        # ---------- Параметры сборки ----------
        self.params_frame = ttk.LabelFrame(main, text="Параметры сборки", padding=6)
        self.params_frame.pack(fill=tk.X, pady=6)

        grid_frame = ttk.Frame(self.params_frame)
        grid_frame.pack(fill=tk.X, expand=True)
        grid_frame.columnconfigure(0, weight=0, minsize=140)
        grid_frame.columnconfigure(1, weight=1)
        grid_frame.columnconfigure(2, weight=0)

        # Файл профиля
        ttk.Label(grid_frame, text="Файл профиля:").grid(row=0, column=0, sticky=tk.W, padx=(0, 8), pady=2)
        self.profile_combo = ttk.Combobox(grid_frame, state="readonly", width=30)
        self.profile_combo.grid(row=0, column=1, sticky=tk.W+tk.E, padx=(0, 8), pady=2)
        ttk.Button(grid_frame, text="Обновить", command=self._update_profile_list, width=10).grid(row=0, column=2, sticky=tk.W, pady=2)

        # Скрипт custom.py (только комбобокс)
        ttk.Label(grid_frame, text="Скрипт custom.py:").grid(row=1, column=0, sticky=tk.W, padx=(0, 8), pady=2)
        self.script_combo = ttk.Combobox(grid_frame, state="readonly", width=30)
        self.script_combo.grid(row=1, column=1, sticky=tk.W+tk.E, padx=(0, 8), pady=2)
        ttk.Button(grid_frame, text="Обновить", command=self._update_script_list, width=10).grid(row=1, column=2, sticky=tk.W, pady=2)

        # Target
        ttk.Label(grid_frame, text="Target:").grid(row=2, column=0, sticky=tk.W, padx=(0, 8), pady=2)
        self.build_target_var = tk.StringVar(value="template_release")
        target_combo = ttk.Combobox(grid_frame, textvariable=self.build_target_var,
                                    values=["template_release", "template_debug"], state="readonly", width=15)
        target_combo.grid(row=2, column=1, sticky=tk.W, padx=(0, 8), pady=2)
        target_combo.bind("<<ComboboxSelected>>", lambda e: self.save_config())

        # Threads
        self.build_threads_var = tk.BooleanVar(value=False)
        chk_threads = ttk.Checkbutton(grid_frame, text="Поддержка потоков (threads=yes)",
                                      variable=self.build_threads_var, command=self.save_config)
        chk_threads.grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=(0, 8), pady=2)

        # Сжатие wasm
        self.compress_wasm_var = tk.BooleanVar(value=True)
        chk_compress = ttk.Checkbutton(grid_frame, text="Сжать wasm через wasm-opt после сборки",
                                       variable=self.compress_wasm_var, command=self.save_config)
        chk_compress.grid(row=4, column=0, columnspan=2, sticky=tk.W, padx=(0, 8), pady=2)

        # Доп. аргументы
        ttk.Label(grid_frame, text="Доп. аргументы scons:").grid(row=5, column=0, sticky=tk.W, padx=(0, 8), pady=2)
        self.build_extra_entry = ttk.Entry(grid_frame)
        self.build_extra_entry.grid(row=5, column=1, columnspan=2, sticky=tk.W+tk.E, padx=(0, 8), pady=2)
        self.build_extra_entry.bind("<KeyRelease>", lambda e: self.save_config())

        # ---------- Статус, прогресс, кнопки, лог ----------
        self.build_status_label = ttk.Label(main, text="", anchor=tk.CENTER, font=('Segoe UI', 9, 'bold'))
        self.build_status_label.pack(fill=tk.X, pady=4)

        # Прогресс
        progress_frame = ttk.Frame(main)
        progress_frame.pack(fill=tk.X, pady=4)
        self.build_progress = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.build_progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.progress_label = ttk.Label(progress_frame, text="", width=8, anchor=tk.W)
        self.progress_label.pack(side=tk.RIGHT)
        self.progress_text = ttk.Label(main, text="", anchor=tk.W, font=('Segoe UI', 9))
        self.progress_text.pack(fill=tk.X, pady=(0, 4))
        progress_frame.pack_forget()
        self.progress_text.pack_forget()

        # Кнопки
        btn_frame = ttk.Frame(main)
        btn_frame.pack(pady=5)
        self.build_btn = ttk.Button(btn_frame, text="СОБРАТЬ ДВИЖОК", command=self._start_build)
        self.build_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn = ttk.Button(btn_frame, text="ОСТАНОВИТЬ", command=self._stop_build, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        self.open_bin_btn = ttk.Button(btn_frame, text="ОТКРЫТЬ BIN", command=self._open_bin)
        self.open_bin_btn.pack(side=tk.LEFT, padx=5)

        # Лог
        ttk.Label(main, text="Лог сборки:").pack(anchor=tk.W, pady=(4, 0))
        log_frame = ttk.Frame(main)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=2)
        self.build_log_text = tk.Text(log_frame, wrap=tk.WORD, font=('Consolas', 9), height=10)
        scroll_log = ttk.Scrollbar(log_frame, command=self.build_log_text.yview)
        self.build_log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_log.pack(side=tk.RIGHT, fill=tk.Y)
        self.build_log_text.config(yscrollcommand=scroll_log.set)

        # Привязка событий для автосохранения
        self.emsdk_entry.bind("<KeyRelease>", lambda e: [self._auto_detect_wasmopt(), self.save_config()])
        self.godot_entry.bind("<KeyRelease>", lambda e: self.save_config())
        self.profile_dir_entry.bind("<KeyRelease>", lambda e: [self.save_config(), self._update_profile_list()])
        self.wasmopt_entry.bind("<KeyRelease>", lambda e: self.save_config())
        self.scripts_dir_entry.bind("<KeyRelease>", lambda e: [self.save_config(), self._update_script_list()])
        self.profile_combo.bind("<<ComboboxSelected>>", lambda e: self.save_config())
        self.script_combo.bind("<<ComboboxSelected>>", lambda e: self.save_config())

        # По умолчанию скрываем оба фрейма
        self.paths_visible = False
        self.paths_frame.pack_forget()
        self.wasm_settings_visible = False
        self.wasm_settings_frame.pack_forget()

    # ---------- Автопоиск wasm-opt ----------
    def _auto_detect_wasmopt(self):
        emsdk = self.emsdk_entry.get().strip()
        if not emsdk or not os.path.isdir(emsdk):
            return
        possible = [
            os.path.join(emsdk, "upstream", "bin", "wasm-opt"),
            os.path.join(emsdk, "upstream", "bin", "wasm-opt.exe"),
        ]
        for p in possible:
            if os.path.isfile(p):
                current = self.wasmopt_entry.get().strip()
                if not current:
                    self.wasmopt_entry.delete(0, tk.END)
                    self.wasmopt_entry.insert(0, p)
                    self.save_config()
                break

    # ---------- Показать/скрыть пути ----------
    def _toggle_paths(self):
        if self.paths_visible:
            self.paths_frame.pack_forget()
            self.toggle_paths_btn.config(text="▶ Показать пути")
            self.paths_visible = False
        else:
            # Вставляем перед кнопкой WASM, чтобы блок путей шёл сразу после своей кнопки
            self.paths_frame.pack(fill=tk.X, pady=(0, 10), before=self.toggle_wasm_btn)
            self.toggle_paths_btn.config(text="▼ Скрыть пути")
            self.paths_visible = True
        self.save_config()

    # ---------- Показать/скрыть настройки WASM ----------
    def _toggle_wasm_settings(self):
        if self.wasm_settings_visible:
            self.wasm_settings_frame.pack_forget()
            self.toggle_wasm_btn.config(text="▶ Показать настройки WASM")
            self.wasm_settings_visible = False
        else:
            self.wasm_settings_frame.pack(fill=tk.X, pady=(0, 10), before=self.params_frame)
            self.toggle_wasm_btn.config(text="▼ Скрыть настройки WASM")
            self.wasm_settings_visible = True
        self.save_config()

    # ---------- Тема ----------
    def apply_theme(self, bg, fg, entry_bg, text_bg, select_bg):
        self.build_status_label.config(background=bg, foreground=fg)
        self.emsdk_entry.config(background=entry_bg, foreground=fg)
        self.godot_entry.config(background=entry_bg, foreground=fg)
        self.profile_dir_entry.config(background=entry_bg, foreground=fg)
        self.wasmopt_entry.config(background=entry_bg, foreground=fg)
        self.scripts_dir_entry.config(background=entry_bg, foreground=fg)
        self.build_extra_entry.config(background=entry_bg, foreground=fg)
        self.build_log_text.config(bg=text_bg, fg=fg, insertbackground=fg, selectbackground=select_bg)
        self.progress_text.config(background=bg, foreground=fg)

    # ---------- Сохранение / загрузка конфигурации ----------
    def _load_config(self):
        config = self.app.config
        self.emsdk_entry.delete(0, tk.END)
        self.emsdk_entry.insert(0, config.get("build_emsdk_path", ""))

        self.godot_entry.delete(0, tk.END)
        self.godot_entry.insert(0, config.get("build_godot_path", ""))

        self.profile_dir_entry.delete(0, tk.END)
        self.profile_dir_entry.insert(0, config.get("build_profile_dir", ""))

        self.wasmopt_entry.delete(0, tk.END)
        self.wasmopt_entry.insert(0, config.get("build_wasmopt_path", ""))

        self.scripts_dir_entry.delete(0, tk.END)
        self.scripts_dir_entry.insert(0, config.get("build_scripts_dir", ""))

        saved_profile = config.get("build_selected_profile", "")
        self.profile_combo.set(saved_profile)

        saved_script = config.get("build_selected_script", "")
        self.script_combo.set(saved_script)

        visible = config.get("build_paths_visible", False)
        if visible:
            self.paths_visible = False
            self._toggle_paths()

        wasm_visible = config.get("build_wasm_settings_visible", False)
        if wasm_visible:
            self.wasm_settings_visible = False
            self._toggle_wasm_settings()

        self.build_target_var.set(config.get("build_target", "template_release"))
        self.build_threads_var.set(config.get("build_threads", False))
        self.compress_wasm_var.set(config.get("build_compress_wasm", True))
        extra = config.get("build_extra", "")
        self.build_extra_entry.delete(0, tk.END)
        self.build_extra_entry.insert(0, extra)

        opt_level = config.get("build_wasm_opt_level", "-Oz")
        self.opt_level_var.set(opt_level)
        for flag in DEFAULT_WASM_FLAGS:
            var = self.flag_vars[flag]
            var.set(config.get(f"build_wasm_flag_{flag}", True))

        if not self.wasmopt_entry.get().strip():
            self._auto_detect_wasmopt()

    def save_config(self, *args):
        config = self.app.config
        config.set("build_emsdk_path", self.emsdk_entry.get().strip())
        config.set("build_godot_path", self.godot_entry.get().strip())
        config.set("build_profile_dir", self.profile_dir_entry.get().strip())
        config.set("build_wasmopt_path", self.wasmopt_entry.get().strip())
        config.set("build_scripts_dir", self.scripts_dir_entry.get().strip())
        config.set("build_selected_profile", self.profile_combo.get())
        config.set("build_selected_script", self.script_combo.get())
        config.set("build_paths_visible", self.paths_visible)
        config.set("build_wasm_settings_visible", self.wasm_settings_visible)
        config.set("build_target", self.build_target_var.get())
        config.set("build_threads", self.build_threads_var.get())
        config.set("build_compress_wasm", self.compress_wasm_var.get())
        config.set("build_extra", self.build_extra_entry.get().strip())
        config.set("build_wasm_opt_level", self.opt_level_var.get())
        for flag in DEFAULT_WASM_FLAGS:
            config.set(f"build_wasm_flag_{flag}", self.flag_vars[flag].get())

    # ---------- Обновление списка профилей ----------
    def _update_profile_list(self):
        folder = self.profile_dir_entry.get().strip()
        if not folder or not os.path.isdir(folder):
            self.profile_combo['values'] = []
            self.profile_combo.config(state="disabled")
            self.profile_combo.set('')
            return

        patterns = ['*.build', '*.gdbuild']
        files = []
        for pat in patterns:
            files.extend(glob.glob(os.path.join(folder, pat)))
        names = [os.path.basename(f) for f in files]
        names.sort()

        self.profile_combo['values'] = names
        if names:
            self.profile_combo.config(state="readonly")
        else:
            self.profile_combo.config(state="disabled")
            self.profile_combo.set('')
        current = self.profile_combo.get()
        if current and current not in names:
            self.profile_combo.set('')

    # ---------- Обновление списка скриптов ----------
    def _update_script_list(self):
        folder = self.scripts_dir_entry.get().strip()
        if not folder or not os.path.isdir(folder):
            self.script_combo['values'] = []
            self.script_combo.config(state="disabled")
            self.script_combo.set('')
            return

        files = glob.glob(os.path.join(folder, "*.py"))
        names = [os.path.basename(f) for f in files]
        names.sort()

        self.script_combo['values'] = names
        if names:
            self.script_combo.config(state="readonly")
        else:
            self.script_combo.config(state="disabled")
            self.script_combo.set('')
        current = self.script_combo.get()
        if current and current not in names:
            self.script_combo.set('')

    # ---------- Диалоги выбора папок ----------
    def _browse_emsdk(self):
        folder = filedialog.askdirectory(title="Выберите папку с emsdk")
        if folder:
            self.emsdk_entry.delete(0, tk.END)
            self.emsdk_entry.insert(0, folder)
            self._auto_detect_wasmopt()
            self.save_config()

    def _browse_godot(self):
        folder = filedialog.askdirectory(title="Выберите папку с исходниками Godot")
        if folder:
            self.godot_entry.delete(0, tk.END)
            self.godot_entry.insert(0, folder)
            self.save_config()

    def _browse_profile_dir(self):
        folder = filedialog.askdirectory(title="Выберите папку с профилями сборки (.build / .gdbuild)")
        if folder:
            self.profile_dir_entry.delete(0, tk.END)
            self.profile_dir_entry.insert(0, folder)
            self.save_config()
            self._update_profile_list()

    def _browse_wasmopt(self):
        filepath = filedialog.askopenfilename(title="Выберите исполняемый файл wasm-opt")
        if filepath:
            self.wasmopt_entry.delete(0, tk.END)
            self.wasmopt_entry.insert(0, filepath)
            self.save_config()

    def _browse_scripts_dir(self):
        folder = filedialog.askdirectory(title="Выберите папку со скриптами .py")
        if folder:
            self.scripts_dir_entry.delete(0, tk.END)
            self.scripts_dir_entry.insert(0, folder)
            self.save_config()
            self._update_script_list()

    # ---------- Управление прогрессом ----------
    def _update_progress(self, value, text):
        self.app.after(0, lambda: self._set_progress(text))

    def _set_progress(self, text):
        self.progress_text.config(text=text)
        self.build_progress.start(10)

    def _stop_progress(self):
        self.build_progress.stop()
        self.progress_text.config(text="")

    # ---------- Поиск .wasm файла и .zip архива ----------
    def _find_wasm_files(self, bin_dir, target, threads):
        wasm_files = glob.glob(os.path.join(bin_dir, "*.wasm"))
        threads_part = "nothreads" if threads == "no" else ""
        wasm = None
        for f in wasm_files:
            name = os.path.basename(f)
            if target in name and "wasm32" in name:
                if threads_part:
                    if threads_part in name:
                        wasm = f
                        break
                else:
                    if "nothreads" not in name:
                        wasm = f
                        break
        if not wasm:
            for f in wasm_files:
                if target in os.path.basename(f):
                    wasm = f
                    break

        zip_path = None
        if wasm:
            base = os.path.splitext(wasm)[0]
            possible_zip = base + ".zip"
            if os.path.isfile(possible_zip):
                zip_path = possible_zip
            else:
                zip_files = glob.glob(os.path.join(bin_dir, "*.zip"))
                for z in zip_files:
                    if target in os.path.basename(z):
                        zip_path = z
                        break
        return wasm, zip_path

    # ---------- Открыть папку bin ----------
    def _open_bin(self):
        godot_path = self.godot_entry.get().strip()
        if not godot_path:
            messagebox.showwarning("Внимание", "Сначала укажите путь к Godot")
            return
        bin_dir = os.path.join(godot_path, "bin")
        if not os.path.isdir(bin_dir):
            messagebox.showwarning("Внимание", "Папка bin не существует. Возможно, сборка ещё не выполнялась.")
            return
        if sys.platform == "win32":
            os.startfile(bin_dir)
        else:
            os.system(f'xdg-open "{bin_dir}"')

    # ---------- Остановка сборки ----------
    def _stop_build(self):
        if self.build_process and self.build_process.poll() is None:
            self.log_build("=== ОСТАНОВКА СБОРКИ ПО ЗАПРОСУ ПОЛЬЗОВАТЕЛЯ ===")
            self.build_process.terminate()
            try:
                self.build_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.build_process.kill()
            self.build_process = None
            self.stop_btn.config(state=tk.DISABLED)
            self.build_btn.config(state=tk.NORMAL)
            self._stop_progress()
            self._on_build_done(False, "Сборка остановлена пользователем")

    # ---------- Запуск сборки ----------
    def _start_build(self):
        emsdk_path = self.emsdk_entry.get().strip()
        godot_path = self.godot_entry.get().strip()
        profile_name = self.profile_combo.get().strip()
        profile_dir = self.profile_dir_entry.get().strip()
        wasmopt_path = self.wasmopt_entry.get().strip()
        script_name = self.script_combo.get().strip()
        scripts_dir = self.scripts_dir_entry.get().strip()

        if not emsdk_path or not os.path.exists(emsdk_path):
            messagebox.showerror("Ошибка", "Путь к emsdk не существует или не указан")
            return
        if not godot_path or not os.path.exists(godot_path):
            messagebox.showerror("Ошибка", "Путь к Godot не существует или не указан")
            return
        if not profile_name:
            messagebox.showerror("Ошибка", "Не выбран файл профиля сборки")
            return
        profile_path = os.path.join(profile_dir, profile_name)
        if not os.path.isfile(profile_path):
            messagebox.showerror("Ошибка", f"Файл профиля не найден: {profile_path}")
            return

        if self.compress_wasm_var.get() and (not wasmopt_path or not os.path.isfile(wasmopt_path)):
            messagebox.showerror("Ошибка", "wasm-opt не найден. Укажите путь к исполняемому файлу или установите emsdk.")
            return

        custom_src = None
        if script_name and scripts_dir:
            custom_src = os.path.join(scripts_dir, script_name)
            if not os.path.isfile(custom_src):
                messagebox.showerror("Ошибка", f"Файл скрипта не найден: {custom_src}")
                return

        self.build_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.open_bin_btn.config(state=tk.NORMAL)

        progress_frame = self.build_progress.master
        progress_frame.pack(fill=tk.X, pady=4)
        self.progress_text.pack(fill=tk.X, pady=(0, 4))
        self._set_progress("Подготовка...")
        self.build_log_text.delete(1.0, tk.END)
        self.log_build("=== ЗАПУСК СБОРКИ ДВИЖКА ===")

        threading.Thread(target=self._run_build, args=(emsdk_path, godot_path, profile_path, wasmopt_path, custom_src), daemon=True).start()

    def _run_build(self, emsdk_path, godot_path, profile_path, wasmopt_path, custom_src):
        target = self.build_target_var.get()
        threads = "yes" if self.build_threads_var.get() else "no"
        extra = self.build_extra_entry.get().strip()
        compress = self.compress_wasm_var.get()

        # Копирование custom.py
        if custom_src:
            custom_dst = os.path.join(godot_path, "custom.py")
            try:
                shutil.copy2(custom_src, custom_dst)
                self.log_build(f"Скопирован custom.py: {custom_src} -> {custom_dst}")
            except Exception as e:
                self.log_build(f"Ошибка копирования custom.py: {str(e)}")
                self._stop_progress()
                self._on_build_done(False, f"Ошибка копирования custom.py: {str(e)}")
                return

        self._update_progress(0, "Настройка emsdk...")
        cmd_parts = get_build_commands(emsdk_path, godot_path)
        scons_cmd = get_scons_cmd(target, threads, profile_path)
        if extra:
            scons_cmd += f' {extra}'
        cmd_parts.append(scons_cmd)
        full_cmd = ' && '.join(cmd_parts)

        self.log_build(f"Команда: {full_cmd}")

        try:
            self._update_progress(0, "Запуск сборки...")
            self.build_process = subprocess.Popen(
                full_cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=False,
                bufsize=0,
            )

            self._update_progress(0, "Сборка движка (это может занять время)...")
            prog_re = re.compile(rb'\[\s*(\d+)%\]')
            current_line = b""
            last_pct = -1
            while True:
                char = self.build_process.stdout.read(1)
                if not char:
                    break
                current_line += char
                if char in (b'\n', b'\r'):
                    line_str = current_line.decode('utf-8', errors='replace').strip()
                    if line_str:
                        self.log_build(line_str)
                        match = prog_re.search(current_line)
                        if match:
                            pct = int(match.group(1))
                            if pct != last_pct:
                                last_pct = pct
                                self._update_progress(0, f"Сборка: {pct}%")
                    current_line = b""

            self.build_process.stdout.close()
            return_code = self.build_process.wait()
            self.build_process = None

            if return_code != 0:
                self._stop_progress()
                self._on_build_done(False, f"Сборка завершилась с ошибкой (код {return_code})")
                return

            self._update_progress(0, "Сборка завершена")

            # Сжатие WASM
            if compress:
                self._update_progress(0, "Поиск WASM файла...")
                bin_dir = os.path.join(godot_path, "bin")
                wasm_file, zip_file = self._find_wasm_files(bin_dir, target, threads)

                if not wasm_file:
                    self.log_build("Ошибка: не найден .wasm файл в папке bin")
                    self._stop_progress()
                    self._on_build_done(False, "Не найден .wasm файл для сжатия")
                    return

                self.log_build(f"Найден WASM: {os.path.basename(wasm_file)}")
                if zip_file:
                    self.log_build(f"Найден ZIP: {os.path.basename(zip_file)}")

                original_size = os.path.getsize(wasm_file)

                backup_file = wasm_file + ".backup"
                shutil.copy2(wasm_file, backup_file)
                self.log_build(f"Создан бэкап: {backup_file}")

                opt_level = self.opt_level_var.get()
                flags = [flag for flag in DEFAULT_WASM_FLAGS if self.flag_vars[flag].get()]
                wasm_cmd = build_wasm_cmd(wasmopt_path, wasm_file, opt_level, flags)

                self._update_progress(0, "Выполняется wasm-opt...")
                proc_wasm = subprocess.run(wasm_cmd, capture_output=True, text=True, encoding='utf-8')
                if proc_wasm.returncode != 0:
                    self.log_build(f"Ошибка wasm-opt: {proc_wasm.stderr}")
                    self._stop_progress()
                    self._on_build_done(False, "Ошибка при сжатии wasm")
                    return

                new_file = wasm_file + "_new"
                if os.path.isfile(new_file):
                    new_size = os.path.getsize(new_file)
                    diff = original_size - new_size
                    diff_percent = (diff / original_size) * 100 if original_size > 0 else 0

                    def format_size(size):
                        if size >= 1024 * 1024:
                            return f"{size / (1024 * 1024):.2f} МБ"
                        elif size >= 1024:
                            return f"{size / 1024:.2f} КБ"
                        else:
                            return f"{size} Б"

                    self.log_build(f"Размер до сжатия: {format_size(original_size)}")
                    self.log_build(f"Размер после сжатия: {format_size(new_size)}")
                    self.log_build(f"Сэкономлено: {format_size(diff)} ({diff_percent:.1f}%)")

                    os.replace(new_file, wasm_file)
                    self.log_build("WASM успешно сжат и заменён.")

                    if zip_file:
                        self._update_progress(0, "Обновление ZIP архива...")
                        try:
                            with tempfile.TemporaryDirectory() as tmpdir:
                                with zipfile.ZipFile(zip_file, 'r') as zf:
                                    zf.extractall(tmpdir)
                                wasm_in_zip = os.path.join(tmpdir, "godot.wasm")
                                if os.path.isfile(wasm_in_zip):
                                    os.remove(wasm_in_zip)
                                shutil.copy2(wasm_file, wasm_in_zip)
                                with zipfile.ZipFile(zip_file, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
                                    for root, _, files in os.walk(tmpdir):
                                        for f in files:
                                            full_path = os.path.join(root, f)
                                            arcname = os.path.relpath(full_path, tmpdir)
                                            zf.write(full_path, arcname)
                                self.log_build(f"ZIP архив обновлён: {os.path.basename(zip_file)}")
                        except Exception as e:
                            self.log_build(f"Ошибка обновления ZIP: {e}")
                    self._update_progress(0, "Сжатие завершено")
                else:
                    self.log_build("Ошибка: временный файл не создан.")
                    self._stop_progress()
                    self._on_build_done(False, "Ошибка при сжатии wasm")
                    return
            else:
                self._update_progress(0, "Сжатие wasm пропущено")

            self._stop_progress()
            self._on_build_done(True, "Сборка и сжатие завершены успешно!")

        except Exception as e:
            self._stop_progress()
            self._on_build_done(False, f"Исключение при запуске сборки: {str(e)}")

    def log_build(self, msg):
        self.app.after(0, lambda: self._append_build_log(msg))

    def _append_build_log(self, msg):
        self.build_log_text.insert(tk.END, msg + "\n")
        self.build_log_text.see(tk.END)
        self.app.update_idletasks()

    def _on_build_done(self, success, message):
        self.app.after(0, lambda: self._finish_build(success, message))

    def _finish_build(self, success, message):
        self.build_progress.master.pack_forget()
        self.progress_text.pack_forget()
        self.build_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.open_bin_btn.config(state=tk.NORMAL)
        if success:
            self.build_log_text.insert(tk.END, f"\n✅ {message}\n")
            messagebox.showinfo("Готово", message)
        else:
            self.build_log_text.insert(tk.END, f"\n❌ ОШИБКА: {message}\n")
            messagebox.showerror("Ошибка", f"Сборка не удалась:\n{message}")
        self.build_log_text.see(tk.END)