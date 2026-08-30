// compress.js – полностью самодостаточный
(function() {
    'use strict';
    if (window._compress_initialized) return;
    window._compress_initialized = true;

    function waitForElements(ids, callback, timeout = 5000) {
        const startTime = Date.now();
        const check = setInterval(() => {
            const allExist = ids.every(id => document.getElementById(id) !== null);
            if (allExist) {
                clearInterval(check);
                callback();
            } else if (Date.now() - startTime > timeout) {
                clearInterval(check);
                console.warn('❌ Элементы не найдены за', timeout, 'ms:', ids);
            }
        }, 50);
    }

    function initCompress() {
        console.log('🔧 Инициализация страницы сжатия');

        const folderInput = document.getElementById('folderPath');
        const htmlInput = document.getElementById('htmlFileName');
        const selectFolderBtn = document.getElementById('selectFolderBtn');
        const selectHtmlBtn = document.getElementById('selectHtmlBtn');
        const startBtn = document.getElementById('startCompressBtn');

        if (!folderInput || !htmlInput || !selectFolderBtn || !selectHtmlBtn || !startBtn) {
            console.error('❌ Не все элементы найдены');
            return;
        }

        // --- Загрузка из localStorage ---
        const savedFolder = localStorage.getItem('app:folderPath');
        const savedHtml = localStorage.getItem('app:htmlFileName');
        if (savedFolder !== null) {
            folderInput.value = savedFolder;
            console.log('✅ Восстановлено folderPath:', savedFolder);
        }
        if (savedHtml !== null) {
            htmlInput.value = savedHtml;
            console.log('✅ Восстановлено htmlFileName:', savedHtml);
        }

        // --- Сохранение ---
        function saveAll() {
            localStorage.setItem('app:folderPath', folderInput.value);
            localStorage.setItem('app:htmlFileName', htmlInput.value);
            console.log('💾 Сохранено folderPath:', folderInput.value);
            console.log('💾 Сохранено htmlFileName:', htmlInput.value);
        }

        // --- Статусы ---
        const statusItems = {
            js: document.getElementById('status-js'),
            wasm: document.getElementById('status-wasm'),
            pck: document.getElementById('status-pck'),
            html: document.getElementById('status-html')
        };
        for (const key of Object.keys(statusItems)) {
            if (!statusItems[key]) console.warn('⚠️ Статус не найден:', key);
        }

        function updateFileStatus(data) {
            for (const [key, info] of Object.entries(data.files)) {
                const item = statusItems[key];
                if (!item) continue;
                const icon = item.querySelector('i');
                const span = item.querySelector('span');
                if (info.exists) {
                    icon.className = 'fas fa-check-circle';
                    icon.style.color = 'var(--success)';
                } else {
                    icon.className = 'fas fa-times-circle';
                    icon.style.color = '#ff5555';
                }
                span.textContent = info.name;
            }
        }

        function checkProject() {
            const folder = folderInput.value.trim();
            const htmlName = htmlInput.value.trim() || 'index';
            console.log('🔍 Проверка проекта:', folder, htmlName);

            if (!folder) {
                for (const key of Object.keys(statusItems)) {
                    const item = statusItems[key];
                    const icon = item.querySelector('i');
                    const span = item.querySelector('span');
                    icon.className = 'fas fa-circle';
                    icon.style.color = 'gray';
                    span.textContent = key.toUpperCase();
                }
                return;
            }

            fetch('/api/check-project', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ folder, html_name: htmlName })
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => {
                        throw new Error(err.detail || 'Ошибка проверки');
                    });
                }
                return response.json();
            })
            .then(data => {
                updateFileStatus(data);
            })
            .catch(error => {
                console.error('❌ Ошибка проверки проекта:', error);
                for (const key of Object.keys(statusItems)) {
                    const item = statusItems[key];
                    const icon = item.querySelector('i');
                    const span = item.querySelector('span');
                    icon.className = 'fas fa-circle';
                    icon.style.color = 'gray';
                    span.textContent = key.toUpperCase();
                }
            });
        }

        // --- Обработчики с сохранением ---
        selectFolderBtn.addEventListener('click', function () {
            fetch('/api/select-folder')
                .then(res => res.json())
                .then(data => {
                    if (data.path) {
                        folderInput.value = data.path;
                        saveAll();
                        checkProject();
                    }
                })
                .catch(err => console.error('Ошибка выбора папки:', err));
        });

        selectHtmlBtn.addEventListener('click', function () {
            fetch('/api/select-file')
                .then(res => res.json())
                .then(data => {
                    if (data.path) {
                        const path = data.path;
                        const dir = path.substring(0, path.lastIndexOf('\\') + 1);
                        const fileName = path.substring(path.lastIndexOf('\\') + 1);
                        const nameWithoutExt = fileName.replace(/\.[^/.]+$/, '');
                        folderInput.value = dir;
                        htmlInput.value = nameWithoutExt;
                        saveAll();
                        checkProject();
                    }
                })
                .catch(err => console.error('Ошибка выбора HTML-файла:', err));
        });

        folderInput.addEventListener('input', function() {
            saveAll();
            checkProject();
        });
        htmlInput.addEventListener('input', function() {
            saveAll();
            checkProject();
        });

        // ---------- ОБНОВЛЁННЫЙ startBtn с исключаемыми расширениями ----------
        startBtn.addEventListener('click', function () {
            const folder = folderInput.value.trim();
            const htmlName = htmlInput.value.trim() || 'index';
            if (!folder) {
                alert('Выберите папку с билдом');
                return;
            }
            const compressionType = localStorage.getItem('app:compressionTab') || 'zip';
            const createBackup = localStorage.getItem('app:createBackup') === 'true';
            const wasmLevel = localStorage.getItem('app:wasmCompressionLevel') || '9';
            const pckLevel = localStorage.getItem('app:pckCompressionLevel') || '9';
            // Читаем исключаемые расширения
            let excludeExtensions = [];
            try {
                const extData = localStorage.getItem('app:excludeExtensions');
                if (extData) {
                    excludeExtensions = JSON.parse(extData);
                }
            } catch(e) { excludeExtensions = []; }
            const excludeStr = excludeExtensions.length ? excludeExtensions.join(', ') : 'нет';

            alert(`Запуск сжатия:\nПапка: ${folder}\nHTML-файл: ${htmlName}\nТип: ${compressionType}\nBackup: ${createBackup ? 'Да' : 'Нет'}\nWASM уровень: ${wasmLevel}\nPCK уровень: ${pckLevel}\nИсключаемые расширения: ${excludeStr}`);
        });

        // --- Выпадающий список типа сжатия ---
        const compressionSelect = document.getElementById('compressionSelect');
        const settingsBlocks = {
            zip: document.getElementById('zip-settings'),
            gzip: document.getElementById('gzip-settings'),
            brotli: document.getElementById('brotli-settings')
        };

        const savedType = localStorage.getItem('app:compressionTab') || 'zip';
        compressionSelect.value = savedType;

        function showSettings(type) {
            Object.keys(settingsBlocks).forEach(key => {
                settingsBlocks[key].style.display = (key === type) ? 'block' : 'none';
            });
            localStorage.setItem('app:compressionTab', type);
        }
        showSettings(savedType);
        compressionSelect.addEventListener('change', function() {
            showSettings(this.value);
        });

        // ---------- Исключение расширений (с сервера) ----------
        const excludeInput = document.getElementById('excludeExtensionInput');
        const addBtn = document.getElementById('addExtensionBtn');
        const extensionList = document.getElementById('extensionList');
        const removeBtn = document.getElementById('removeSelectedExtensionsBtn');

        let extensions = [];

        function renderExtensions() {
            extensionList.innerHTML = '';
            extensions.forEach((ext, index) => {
                const li = document.createElement('li');
                li.innerHTML = `<input type="checkbox" data-index="${index}"> ${ext}`;
                extensionList.appendChild(li);
            });
        }

        function saveExtensions() {
            localStorage.setItem('app:excludeExtensions', JSON.stringify(extensions));
        }

        function loadDefaultExtensions() {
            fetch('/compress/default-extensions')
                .then(res => {
                    if (!res.ok) throw new Error('Ошибка загрузки');
                    return res.json();
                })
                .then(data => {
                    const defaults = data.extensions || ['.backup', '.tmp', '.gz', '.img', '.import', '.old', '.png'];
                    const saved = localStorage.getItem('app:excludeExtensions');
                    if (saved) {
                        try {
                            const parsed = JSON.parse(saved);
                            if (Array.isArray(parsed) && parsed.length > 0) {
                                extensions = parsed;
                            } else {
                                extensions = defaults;
                                saveExtensions();
                            }
                        } catch {
                            extensions = defaults;
                            saveExtensions();
                        }
                    } else {
                        extensions = defaults;
                        saveExtensions();
                    }
                    renderExtensions();
                })
                .catch(() => {
                    extensions = ['.backup', '.tmp', '.gz', '.img', '.import', '.old', '.png'];
                    saveExtensions();
                    renderExtensions();
                });
        }

        addBtn.addEventListener('click', function() {
            const val = excludeInput.value.trim();
            if (val && !extensions.includes(val)) {
                extensions.push(val);
                excludeInput.value = '';
                renderExtensions();
                saveExtensions();
            }
        });

        removeBtn.addEventListener('click', function() {
            const checkboxes = extensionList.querySelectorAll('input[type="checkbox"]:checked');
            const indices = Array.from(checkboxes).map(cb => parseInt(cb.dataset.index));
            extensions = extensions.filter((_, i) => !indices.includes(i));
            renderExtensions();
            saveExtensions();
        });

        loadDefaultExtensions();

        // ---------- Настройки Gzip ----------
        const createBackupCheckbox = document.getElementById('createBackup');
        const wasmLevelInput = document.getElementById('wasmCompressionLevel');
        const pckLevelInput = document.getElementById('pckCompressionLevel');
        if (createBackupCheckbox && wasmLevelInput && pckLevelInput) {
            // Восстановление
            const savedBackup = localStorage.getItem('app:createBackup');
            if (savedBackup !== null) {
                createBackupCheckbox.checked = savedBackup === 'true';
            } else {
                createBackupCheckbox.checked = true;
            }
            const savedWasm = localStorage.getItem('app:wasmCompressionLevel');
            if (savedWasm !== null) {
                wasmLevelInput.value = savedWasm;
            } else {
                wasmLevelInput.value = 9;
            }
            const savedPck = localStorage.getItem('app:pckCompressionLevel');
            if (savedPck !== null) {
                pckLevelInput.value = savedPck;
            } else {
                pckLevelInput.value = 9;
            }

            // Сохранение при изменениях
            createBackupCheckbox.addEventListener('change', function() {
                localStorage.setItem('app:createBackup', this.checked);
            });
            wasmLevelInput.addEventListener('input', function() {
                localStorage.setItem('app:wasmCompressionLevel', this.value);
            });
            pckLevelInput.addEventListener('input', function() {
                localStorage.setItem('app:pckCompressionLevel', this.value);
            });
        }

        // --- Принудительное сохранение дефолтных значений ---
        saveAll();

        // --- Проверка, если папка уже есть ---
        if (folderInput.value.trim()) {
            setTimeout(checkProject, 200);
        }
    }

    waitForElements(
        ['folderPath', 'htmlFileName', 'selectFolderBtn', 'selectHtmlBtn', 'startCompressBtn'],
        initCompress,
        10000
    );
})();