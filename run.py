from pathlib import Path

import uvicorn
from app import App
import webview
import threading

USER_DATA_DIR = Path.home() / ".godot_pck_compressor" / "webview_data"
USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

def start_server():
    """Запускает Uvicorn-сервер на локальном хосте"""
    uvicorn.run(
        App().app,
        host="0.0.0.0",
        port=4000,
        log_level="info"
    )

if __name__ == "__main__":
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # Открываем WebView с адресом сервера
    window = webview.create_window(
        title="Godot PCK Compressor",
        url="http://127.0.0.1:4000",
        width=1024,
        height=768,
    )
    webview.start(
        icon='app/static/icons/favicon.ico',
        storage_path=str(USER_DATA_DIR),
        private_mode=False,
    )