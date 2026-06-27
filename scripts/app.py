# app.py
import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import json

try:
    import pywinstyles
    HAS_PYWINSTYLES = True
except ImportError:
    HAS_PYWINSTYLES = False

from scripts.tab_compress import CompressTab
from scripts.tab_build import BuildTab
from scripts.tab_custom import CustomTab


class ConfigManager:
    def __init__(self, app_name="GodotWebCompressor"):
        if sys.platform == "win32":
            base_dir = os.getenv('APPDATA')
        else:
            base_dir = os.path.expanduser('~/.config')
        self.config_dir = os.path.join(base_dir, app_name)
        os.makedirs(self.config_dir, exist_ok=True)
        self.config_file = os.path.join(self.config_dir, "settings.json")
        self.data = self._load()

    def _load(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except:
            pass

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Godot Web Build Compressor")
        self.geometry("500x750")
        self.minsize(500, 750)

        self.config = ConfigManager()
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(self.root_dir, "resources", "icon.ico")
        try:
            self.iconbitmap(icon_path)
        except Exception as e:
            print(f"Не удалось загрузить иконку: {e}")

        self.style = ttk.Style()
        self.style.theme_use('clam')
        saved_theme = self.config.get("theme", "Тёмная")
        self.theme_var = tk.StringVar(value=saved_theme)

        self.outer_frame = tk.Frame(self, bd=2, relief="solid")
        self.outer_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        top_frame = ttk.Frame(self.outer_frame)
        top_frame.pack(fill=tk.X, padx=8, pady=(8, 0))
        ttk.Label(top_frame, text="Тема:").pack(side=tk.RIGHT, padx=(0, 5))
        theme_combo = ttk.Combobox(
            top_frame,
            textvariable=self.theme_var,
            values=["Тёмная", "Светлая"],
            state="readonly",
            width=10
        )
        theme_combo.pack(side=tk.RIGHT)
        theme_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_theme())

        self.notebook = ttk.Notebook(self.outer_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.tab_compress = CompressTab(self.notebook, self)
        self.tab_build = BuildTab(self.notebook, self)
        self.tab_custom = CustomTab(self.notebook, self)

        self.notebook.add(self.tab_compress, text="Сжатие")
        self.notebook.add(self.tab_build, text="Сборка")
        self.notebook.add(self.tab_custom, text="custom.py")

        self._apply_theme()
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _apply_theme(self):
        theme = self.theme_var.get()
        self.config.set("theme", theme)
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

        # Общие стили
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

        # Стиль для Notebook (вкладок)
        self.style.configure('TNotebook', background=bg, borderwidth=0)
        self.style.configure('TNotebook.Tab', background=entry_bg, foreground=fg, padding=[10, 2])
        self.style.map('TNotebook.Tab',
                       background=[('selected', select_bg), ('active', button_active_bg)],
                       foreground=[('selected', fg), ('active', fg)])

        # Применяем тему к вкладкам
        self.tab_compress.apply_theme(bg, fg, entry_bg, text_bg, select_bg, list_bg)
        self.tab_build.apply_theme(bg, fg, entry_bg, text_bg, select_bg)
        self.tab_custom.apply_theme(bg, fg, entry_bg, text_bg, select_bg)

    def _on_closing(self):
        self.tab_compress.save_config()
        self.tab_build.save_config()
        self.tab_custom.save_config()
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()