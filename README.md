# Godot PCK Compressor


A desktop app for compressing Godot web builds: shrinks `.pck` and `.wasm` files and automatically patches the engine loader so the game can decompress them in the browser.

> The `web` branch — FastAPI + pywebview UI (a native window with a web UI inside).

## Features

- **Gzip compression** (levels 0–9) — decompression in the browser via [pako](https://github.com/nodeca/pako).
- **Brotli compression** (levels 0–11) — decompression via the built-in `brotli_inflate.min.js` decoder.
- **ZStandard compression** (levels 1–22) — decompression via the built-in `zstd_inflate.min.js` decoder.
- Separate compression levels for `.wasm` and `.pck`.
- **JS patching**: the build's main JS file is modified so compressed `.wasm`/`.pck` files are decompressed when the game loads.
- A decoder (`pako_inflate.min.js` / `brotli_inflate.min.js` / `zstd_inflate.min.js`) is copied into the build folder and included via a `<script>` tag in the `.html` before the main script.
- **Backups**: `.pck.backup`, `.wasm.backup`, `.js.backup` copies are created before compression (optional).
- **ZIP packaging** with exclusion of unneeded files (`.backup`, `.import`, `.png`, etc.).
- Platform selection (YandexGames, CrazyGames, Poki, PlayGama).
- **`custom.py` generator** — a visual editor for Godot web engine build options (modules, optimization, rendering, etc.) that generates a `custom.py` file.

## Installation

Requires **Python 3.10+** (Windows).

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

A native app window will open (inside — a local server on `127.0.0.1:4000`, which can also be opened in a regular browser).

## Usage

1. **Select the folder** with an exported Godot web build.
2. **Specify the HTML file** of the build (e.g. `index.html`).
3. Click **"Check project"** — the app will verify that `{name}.js`, `{name}.wasm`, `{name}.pck` are present.
4. Choose a **compression algorithm** (Gzip, Brotli or ZStandard) and compression levels for `.wasm` and `.pck`.
5. Keep **backups** enabled and click **"Compress"**.
6. Optionally select a **platform** and/or build a **ZIP** (exclusions are configurable).

After compression the build is ready to upload to hosting — decompression happens in the browser when the game loads.

## What compression actually does

| Step | Gzip | Brotli | ZStandard |
|---|---|---|---|
| `{name}.js` patching | `new Response(pako.inflate(buffer), ...)` | `new Response(brotli.decompress(new Uint8Array(buffer)), ...)` | `new Response(fzstd.decompress(new Uint8Array(buffer)), ...)` |
| Decoder included | `pako_inflate.min.js` (~21 KB) | `brotli_inflate.min.js` (~145 KB) | `zstd_inflate.min.js` (~19 KB, fzstd) |
| `.pck` / `.wasm` compression | `gzip`, levels 0–9 | `brotli`, levels 0–11 | `zstandard`, levels 1–22 |
| Re-compression protection | `gzip` magic signature `\x1f\x8b` | streaming decompressor check of the first 4 MB; gzip files by signature | signature `\x28\xb5\x2f\xfd` |

## custom.py generator

The **"Engine build → Generate custom.py"** tab lets you visually assemble a `custom.py` file for building Godot for the web (used with `scons`).

- Options are **grouped** into sections: Modules, Optimization, Rendering, Web, Features.
  - Modules are further split into subgroups: images, audio/video, 3D, physics, networking, text/fonts, other.
- You set the **file name** and pick a folder (the `custom.py` path is taken from Settings).
- The **"Generate custom.py"** button creates a file like:
  ```python
  module_basis_universal_enabled = "no"
  module_bmp_enabled = "no"
  optimize = "size"
  ```
- A dropdown lets you pick an **existing** `.py` file — its options are loaded into the form for editing.

## License

GPLv3 — see [LICENSE](LICENSE).

