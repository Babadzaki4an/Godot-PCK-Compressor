# constants.py
# Содержит строки для замены в JavaScript и словарь замен

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

def get_scons_cmd(target : str, threads : str, profile_path : str) -> list[str]:
    return f'scons platform=web target={target} threads={threads} build_profile="{profile_path}"'

def get_build_commands(emsdk_path : str, godot_path : str) -> str:
    return [
        'chcp 65001 > nul',
        f'cd /d "{emsdk_path}"',
        'call emsdk install latest',
        'call emsdk activate latest',
        'call emsdk_env.bat',
        f'cd /d "{godot_path}"',
    ]

DEFAULT_WASM_FLAGS = [
    "--converge",
    "--enable-exception-handling",
    "--enable-nontrapping-float-to-int",
    "--enable-bulk-memory",
    "--strip-debug",
    "--strip-dwarf",
    "--strip-producers",
    "--remove-unused-module-elements",
    "--duplicate-function-elimination",
    "--memory-packing",
    "--enable-simd"
]

OPTIMIZATION_LEVELS = {
    "-Oz": "Агрессивная оптимизация размера",
    "-Os": "Оптимизация размера",
    "-O3": "Максимальная оптимизация",
    "-O2": "Оптимизация",
    "-O1": "Базовая оптимизация",
    "-O0": "Без оптимизации"
}

def build_wasm_cmd(wasmopt_path: str, wasm_file: str, optimization_level: str = "-Oz", flags: list = None) -> list[str]:
    """
    Формирует команду для wasm-opt с заданными параметрами.
    
    Параметры:
        wasmopt_path: путь к исполняемому файлу wasm-opt
        wasm_file: путь к исходному .wasm файлу
        optimization_level: уровень оптимизации (-Oz, -Os, -O3, -O2, -O1, -O0)
        flags: список дополнительных флагов (по умолчанию DEFAULT_WASM_FLAGS)
    """
    if flags is None:
        flags = DEFAULT_WASM_FLAGS.copy()
    cmd = [wasmopt_path, wasm_file, optimization_level]
    cmd.extend(flags)
    cmd.extend(["-o", wasm_file + "_new"])
    return cmd

CUSTOM_PARAMS = {
    "production": {"type": "boolean", "default": "yes", "label": "Production"},
    "disable_3d": {"type": "boolean", "default": "yes", "label": "Disable 3D"},
    "disable_physics_3d": {"type": "boolean", "default": "yes", "label": "Disable Physics 3D"},
    "optimize": {"type": "choice", "default": "size", "choices": ["size", "speed", "debug", "auto"], "label": "Optimize"},
    "precision": {"type": "choice", "default": "double", "choices": ["double", "single"], "label": "Precision"},
    "disable_advanced_gui": {"type": "boolean", "default": "yes", "label": "Disable Advanced GUI"},
    "deprecated": {"type": "boolean", "default": "no", "label": "Deprecated"},
    "minizip": {"type": "boolean", "default": "no", "label": "minizip"},
    "brotli": {"type": "boolean", "default": "no", "label": "Brotli"},
    "vulkan": {"type": "boolean", "default": "no", "label": "Vulkan"},
    "opengl3": {"type": "boolean", "default": "no", "label": "OpenGL3"},
    "d3d12": {"type": "boolean", "default": "no", "label": "D3D12"},
    "use_volk": {"type": "boolean", "default": "no", "label": "Use Volk"},
}

CUSTOM_MODULES = {
    "module_basis_universal_enabled": "no",
    "module_bmp_enabled": "no",
    "module_camera_enabled": "no",
    "module_csg_enabled": "no",
    "module_dds_enabled": "no",
    "module_enet_enabled": "no",
    "module_freetype_enabled": "no",
    "module_gdscript_enabled": "no",
    "module_gltf_enabled": "no",
    "module_gridmap_enabled": "no",
    "module_hdr_enabled": "no",
    "module_jpg_enabled": "no",
    "module_jsonrpc_enabled": "no",
    "module_ktx_enabled": "no",
    "module_mbedtls_enabled": "no",
    "module_meshoptimizer_enabled": "no",
    "module_minimp3_enabled": "no",
    "module_mobile_vr_enabled": "no",
    "module_msdfgen_enabled": "no",
    "module_multiplayer_enabled": "no",
    "module_navigation_enabled": "no",
    "module_noise_enabled": "no",
    "module_ogg_enabled": "no",
    "module_openxr_enabled": "no",
    "module_raycast_enabled": "no",
    "module_regex_enabled": "no",
    "module_squish_enabled": "no",
    "module_svg_enabled": "no",
    "module_text_server_adv_enabled": "no",
    "module_text_server_fb_enabled": "no",
    "module_tga_enabled": "no",
    "module_theora_enabled": "no",
    "module_upnp_enabled": "no",
    "module_vhacd_enabled": "no",
    "module_vorbis_enabled": "no",
    "module_webrtc_enabled": "no",
    "module_websocket_enabled": "no",
    "module_webxr_enabled": "no",
    "module_zip_enabled": "no",
    "module_jolt_enabled": "no",
    "module_godot_physics_3d_enabled": "no",
}

# Описания для подсказок (можно дополнить для новых параметров)
CUSTOM_PARAMS_INFO = {
    "production": "Устанавливает параметры сборки для production-режима.",
    "disable_3d": "Отключает 3D-узлы, уменьшая размер бинарника.",
    "disable_physics_3d": "Отключает 3D-физику (уменьшает размер).",
    "optimize": "Оптимизация: size – размер, speed – скорость, debug – отладка, auto – автоматически.",
    "precision": "Точность чисел с плавающей точкой: double (двойная) или single (одинарная).",
    "disable_advanced_gui": "Отключает сложные GUI-элементы (Tree, GraphEdit).",
    "deprecated": "Включает устаревшие функции (увеличивает размер).",
    "minizip": "Включает поддержку ZIP-архивов (ZIPReader, ZIPWriter).",
    "brotli": "Включает сжатие Brotli (необходимо для WOFF2-шрифтов).",
    "vulkan": "Включает рендеринг через Vulkan (Forward+ и Mobile).",
    "opengl3": "Включает рендеринг через OpenGL 3.3/ES 3.0 (совместимость).",
    "d3d12": "Включает рендеринг через Direct3D 12 (только Windows).",
    "use_volk": "Использовать Volk для загрузки Vulkan (экспериментально).",
}

CUSTOM_MODULES_INFO = {
    "module_basis_universal_enabled": "Загрузка текстур Basis Universal.",
    "module_bmp_enabled": "Загрузка BMP-изображений.",
    "module_camera_enabled": "Поддержка веб-камеры.",
    "module_csg_enabled": "Узлы конструктивной геометрии (CSG).",
    "module_dds_enabled": "Загрузка DDS-изображений.",
    "module_enet_enabled": "Сетевое взаимодействие через ENet.",
    "module_freetype_enabled": "Рендеринг динамических шрифтов (FreeType).",
    "module_gdscript_enabled": "Поддержка скриптов GDScript.",
    "module_gltf_enabled": "Загрузка 3D-сцен в формате glTF.",
    "module_gridmap_enabled": "Узлы GridMap.",
    "module_hdr_enabled": "Загрузка HDR-изображений.",
    "module_jpg_enabled": "Загрузка JPEG-изображений.",
    "module_jsonrpc_enabled": "Класс JSON-RPC.",
    "module_ktx_enabled": "Загрузка KTX-изображений.",
    "module_mbedtls_enabled": "Безопасные HTTP-запросы (mbedTLS).",
    "module_meshoptimizer_enabled": "Оптимизация мешей (LOD, SurfaceTool).",
    "module_minimp3_enabled": "Воспроизведение MP3-аудио.",
    "module_mobile_vr_enabled": "VR на Android и iOS.",
    "module_msdfgen_enabled": "Многоканальные SDF-шрифты.",
    "module_multiplayer_enabled": "Система репликации (RPC).",
    "module_navigation_enabled": "Навигационный сервер.",
    "module_noise_enabled": "Генерация шума (FastNoiseLite).",
    "module_ogg_enabled": "Поддержка Ogg (для Vorbis).",
    "module_openxr_enabled": "VR/AR через OpenXR.",
    "module_raycast_enabled": "Окклюзионный кастинг лучей.",
    "module_regex_enabled": "Регулярные выражения (RegEx).",
    "module_squish_enabled": "Распаковка текстур Squish (S3TC).",
    "module_svg_enabled": "Загрузка SVG-изображений.",
    "module_text_server_adv_enabled": "Расширенный TextServer (RTL, сложные скрипты).",
    "module_text_server_fb_enabled": "Базовый TextServer (без RTL).",
    "module_tga_enabled": "Загрузка TGA-изображений.",
    "module_theora_enabled": "Воспроизведение видео Ogg Theora.",
    "module_upnp_enabled": "UPnP для обнаружения сети и проброса портов.",
    "module_vhacd_enabled": "Создание выпуклых коллизий (V-HACD).",
    "module_vorbis_enabled": "Воспроизведение Ogg Vorbis-аудио.",
    "module_webrtc_enabled": "WebRTC-соединения.",
    "module_websocket_enabled": "WebSocket-соединения.",
    "module_webxr_enabled": "AR/VR в браузерах.",
    "module_zip_enabled": "Работа с ZIP-архивами (требует minizip).",
    "module_jolt_enabled": "Использовать физику Jolt (альтернатива GodotPhysics).",
    "module_godot_physics_3d_enabled": "Использовать встроенную 3D-физику Godot.",
}

def generate_custom_py(params: dict, modules: dict) -> str:
    """
    Генерирует содержимое файла custom.py на основе словарей параметров и модулей.
    """
    lines = []
    # Сначала основные параметры
    for key, value in params.items():
        lines.append(f'{key} = "{value}"')
    # Затем модули
    for key, value in modules.items():
        lines.append(f'{key} = "{value}"')
    return "\n".join(lines)