# tab_custom.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import re

from scripts.constants import CUSTOM_PARAMS, CUSTOM_MODULES, generate_custom_py
from scripts.constants import CUSTOM_PARAMS_INFO, CUSTOM_MODULES_INFO


class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind('<Enter>', self.enter)
        widget.bind('<Leave>', self.leave)

    def enter(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("Segoe UI", 9))
        label.pack()

    def leave(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


class CustomTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.comboboxes = []
        self._build_ui()
        self._load_config()

    def _build_ui(self):
        main = ttk.Frame(self, padding=8)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="Генератор custom.py", font=('Segoe UI', 13, 'bold')).pack(pady=(0, 10))

        # ---- Секция: файл (одно поле) ----
        file_frame = ttk.LabelFrame(main, text="Файл", padding=6)
        file_frame.pack(fill=tk.X, pady=(0, 10))

        file_frame.columnconfigure(1, weight=1)
        file_frame.columnconfigure(3, weight=0)

        ttk.Label(file_frame, text="Путь к файлу:").grid(row=0, column=0, sticky=tk.W, padx=(0, 8))
        self.file_path_entry = ttk.Entry(file_frame)
        self.file_path_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=(0, 8))
        ttk.Button(file_frame, text="Обзор", command=self._browse_file).grid(row=0, column=2, padx=(0, 8))

        ttk.Button(file_frame, text="Сохранить", command=self._generate_and_save).grid(row=0, column=3, sticky=tk.W, padx=(0, 0))

        # ---- Основные параметры (2 колонки) ----
        params_frame = ttk.LabelFrame(main, text="Основные параметры", padding=6)
        params_frame.pack(fill=tk.X, pady=5)

        params_frame.columnconfigure(0, weight=1)
        params_frame.columnconfigure(1, weight=1)

        self.param_vars = {}
        row = 0
        col = 0
        for key, info in CUSTOM_PARAMS.items():
            container = ttk.Frame(params_frame)
            container.grid(row=row, column=col, sticky=tk.W+tk.E, padx=5, pady=2)
            container.columnconfigure(0, weight=0)
            container.columnconfigure(1, weight=1)

            label = ttk.Label(container, text=info["label"] + ":", width=20, anchor=tk.W)
            label.grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
            tip_text = CUSTOM_PARAMS_INFO.get(key, "")
            if tip_text:
                ToolTip(label, tip_text)

            if info["type"] == "boolean":
                var = tk.StringVar(value=info["default"])
                combo = ttk.Combobox(container, textvariable=var, values=["yes", "no"], state="readonly", width=10)
                combo.grid(row=0, column=1, sticky=tk.W)
                self.param_vars[key] = var
                self.comboboxes.append(combo)
            elif info["type"] == "choice":
                var = tk.StringVar(value=info["default"])
                combo = ttk.Combobox(container, textvariable=var, values=info["choices"], state="readonly", width=10)
                combo.grid(row=0, column=1, sticky=tk.W)
                self.param_vars[key] = var
                self.comboboxes.append(combo)

            if col == 0:
                col = 1
            else:
                col = 0
                row += 1

        # ---- Модули (три колонки, растянуты по высоте) ----
        modules_frame = ttk.LabelFrame(main, text="Модули (включить — yes)", padding=6)
        modules_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        modules_frame.rowconfigure(0, weight=1)
        modules_frame.columnconfigure(0, weight=1)
        modules_frame.columnconfigure(1, weight=0)

        canvas = tk.Canvas(modules_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(modules_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        self.canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def on_canvas_resize(event):
            canvas.itemconfig(self.canvas_window, width=event.width)

        canvas.bind("<Configure>", on_canvas_resize)

        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        for i in range(3):
            scrollable_frame.columnconfigure(i, weight=1)

        self.module_vars = {}
        module_items = list(CUSTOM_MODULES.items())
        total = len(module_items)
        cols = 3
        rows = (total + cols - 1) // cols

        for i, (key, default) in enumerate(module_items):
            col = i // rows
            row = i % rows
            label_text = key.replace("module_", "").replace("_enabled", "").capitalize()
            var = tk.BooleanVar(value=(default == "yes"))
            chk = ttk.Checkbutton(scrollable_frame, text=label_text, variable=var)
            chk.grid(row=row, column=col, sticky=tk.W, padx=15, pady=1)
            self.module_vars[key] = var
            tip_text = CUSTOM_MODULES_INFO.get(key, "")
            if tip_text:
                ToolTip(chk, tip_text)

        # Привязка событий для автосохранения
        self.file_path_entry.bind("<KeyRelease>", lambda e: self.save_config())
        for var in self.param_vars.values():
            var.trace_add("write", lambda *args: self.save_config())
        for var in self.module_vars.values():
            var.trace_add("write", lambda *args: self.save_config())

    # ---------- Применение темы ----------
    def apply_theme(self, bg, fg, entry_bg, text_bg, select_bg):
        for combo in self.comboboxes:
            combo.configure(style='TCombobox')

    # ---------- Выбор файла ----------
    def _browse_file(self):
        filepath = filedialog.askopenfilename(
            title="Выберите файл custom.py",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        if not filepath:
            return

        self.file_path_entry.delete(0, tk.END)
        self.file_path_entry.insert(0, filepath)

        if os.path.isfile(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                param_re = re.compile(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*"([^"]*)"')
                parsed = {}
                for line in content.splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    # Удаляем комментарий после значения
                    if "#" in line:
                        line = line.split("#")[0].strip()
                    match = param_re.match(line)
                    if match:
                        key, value = match.groups()
                        parsed[key] = value

                for key in CUSTOM_PARAMS:
                    if key in parsed:
                        self.param_vars[key].set(parsed[key])
                for key in CUSTOM_MODULES:
                    if key in parsed:
                        self.module_vars[key].set(parsed[key] == "yes")
                self.save_config()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить файл:\n{str(e)}")

    # ---------- Сохранение ----------
    def _generate_and_save(self):
        file_path = self.file_path_entry.get().strip()
        if not file_path:
            messagebox.showerror("Ошибка", "Укажите путь к файлу")
            return

        save_dir = os.path.dirname(file_path)
        if save_dir and not os.path.exists(save_dir):
            try:
                os.makedirs(save_dir)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось создать папку:\n{str(e)}")
                return

        params = {}
        for key in CUSTOM_PARAMS:
            params[key] = self.param_vars[key].get()
        modules = {}
        for key in CUSTOM_MODULES:
            modules[key] = "yes" if self.module_vars[key].get() else "no"

        content = generate_custom_py(params, modules)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            # Убрано уведомление об успехе
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{str(e)}")

    # ---------- Загрузка / сохранение конфига ----------
    def _load_config(self):
        config = self.app.config
        self.file_path_entry.delete(0, tk.END)
        self.file_path_entry.insert(0, config.get("custom_file_path", ""))

        for key in CUSTOM_PARAMS:
            if key in config.data:
                self.param_vars[key].set(config.get(key, CUSTOM_PARAMS[key]["default"]))
        for key in CUSTOM_MODULES:
            if key in config.data:
                self.module_vars[key].set(config.get(key, "no") == "yes")

    def save_config(self, *args):
        config = self.app.config
        config.set("custom_file_path", self.file_path_entry.get().strip())
        for key in CUSTOM_PARAMS:
            config.set(key, self.param_vars[key].get())
        for key in CUSTOM_MODULES:
            config.set(key, "yes" if self.module_vars[key].get() else "no")