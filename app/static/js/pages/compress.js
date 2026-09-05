// compress.js – пошаговое сжатие: сжатие → платформа → ZIP
(function() {
    'use strict';
    if (window._compress_initialized) return;
    window._compress_initialized = true;

    // ----------------------------- Единое хранилище настроек -----------------------------
    const STORAGE_KEY = 'app:settings';

    const defaultSettings = {
        folderPath: '',
        htmlFileName: 'index',
        compressionTab: 'gzip',
        gzip: { createBackup: true, wasmLevel: 9, pckLevel: 9 },
        brotli: { createBackup: true, wasmLevel: 11, pckLevel: 11 },
        excludeEnabled: true,
        excludeCollapsed: false,
        compressionCollapsed: false,
        selectedPlatform: '',
        excludeExtensions: ['.backup', '.tmp', '.gz', '.img', '.import', '.old', '.png']
    };

    function loadSettings() {
        try {
            const raw = localStorage.getItem(STORAGE_KEY);
            if (raw) {
                const saved = JSON.parse(raw);
                return deepMerge(defaultSettings, saved);
            }
        } catch (e) {}
        return JSON.parse(JSON.stringify(defaultSettings));
    }

    function saveSettings(settings) {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
        } catch (e) {}
    }

    function deepMerge(target, source) {
        const result = { ...target };
        for (const key in source) {
            if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
                result[key] = deepMerge(target[key] || {}, source[key]);
            } else {
                result[key] = source[key];
            }
        }
        return result;
    }

    // ----------------------------- Вспомогательные функции -----------------------------
    function waitForElements(ids, callback, timeout = 5000) {
        const start = Date.now();
        const check = setInterval(() => {
            if (ids.every(id => document.getElementById(id) !== null)) {
                clearInterval(check);
                callback();
                return;
            }
            if (Date.now() - start > timeout) {
                clearInterval(check);
                console.warn('⚠️ Элементы не найдены:', ids);
            }
        }, 50);
    }

    // ----------------------------- Основная инициализация -----------------------------
    function initCompress() {
        let settings = loadSettings();

        const folderInput = document.getElementById('folderPath');
        const htmlInput = document.getElementById('htmlFileName');
        const selectFolderBtn = document.getElementById('selectFolderBtn');
        const openFolderBtn = document.getElementById('openFolderBtn');
        const selectHtmlBtn = document.getElementById('selectHtmlBtn');
        const startBtn = document.getElementById('startCompressBtn');

        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        const progressStatus = document.getElementById('progressStatus');

        if (!folderInput || !htmlInput || !selectFolderBtn || !openFolderBtn || !selectHtmlBtn || !startBtn) {
            console.error('Критические элементы не найдены');
            return;
        }

        // Восстановление путей
        folderInput.value = settings.folderPath || '';
        htmlInput.value = settings.htmlFileName || 'index';

        function saveAllSettings() {
            settings.folderPath = folderInput.value;
            settings.htmlFileName = htmlInput.value;
            saveSettings(settings);
        }

        // ----- Статус файлов -----
        const statusItems = {
            js: document.getElementById('status-js'),
            wasm: document.getElementById('status-wasm'),
            pck: document.getElementById('status-pck'),
            html: document.getElementById('status-html')
        };
        const displayNames = { js: 'JS', wasm: 'WASM', pck: 'PCK', html: 'HTML' };

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
                    icon.style.color = 'var(--danger)';
                }
                span.textContent = displayNames[key] || key.toUpperCase();
            }
        }

        function resetStatusIcons() {
            for (const key of Object.keys(statusItems)) {
                const item = statusItems[key];
                if (!item) continue;
                const icon = item.querySelector('i');
                const span = item.querySelector('span');
                icon.className = 'fas fa-circle';
                icon.style.color = 'gray';
                span.textContent = displayNames[key] || key.toUpperCase();
            }
        }

        function checkProject() {
            const folder = folderInput.value.trim();
            const htmlName = htmlInput.value.trim() || 'index';
            if (!folder) {
                resetStatusIcons();
                return;
            }

            fetch('/api/check-project', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ folder, html_name: htmlName })
            })
                .then(res => {
                    if (!res.ok) return res.json().then(err => { throw new Error(err.detail || i18n.t('toast_check_project_error')); });
                    return res.json();
                })
                .then(data => updateFileStatus(data))
                .catch(err => {
                    showToast(i18n.t('toast_check_project_error') + ': ' + i18n.tf(err.message), 'error');
                    resetStatusIcons();
                });
        }

        // ----- Обработчики выбора папки и HTML -----
        selectFolderBtn.addEventListener('click', () => {
            fetch('/api/select-folder')
                .then(res => res.json())
                .then(data => {
                    if (data.path) {
                        folderInput.value = data.path;
                        saveAllSettings();
                        checkProject();
                    }
                })
                .catch(() => showToast(i18n.t('toast_select_folder_failed'), 'error'));
        });

        openFolderBtn.addEventListener('click', () => {
            const folder = folderInput.value.trim();
            if (!folder) {
                showToast(i18n.t('toast_specify_folder_first'), 'warning');
                return;
            }
            fetch('/api/open-folder/' + encodeURIComponent(folder), { method: 'GET' })
                .then(res => res.json())
                .then(data => {
                    if (data.ok) {
                        showToast(i18n.t('toast_folder_opened'), 'success');
                    } else {
                        showToast(i18n.tf(data.error) || i18n.t('toast_open_folder_failed'), 'error');
                    }
                })
                .catch(() => showToast(i18n.t('toast_server_error'), 'error'));
        });

        selectHtmlBtn.addEventListener('click', () => {
            fetch('/api/select-file')
                .then(res => res.json())
                .then(data => {
                    if (data.path) {
                        const dir = data.path.substring(0, data.path.lastIndexOf('\\') + 1);
                        const fileName = data.path.substring(data.path.lastIndexOf('\\') + 1);
                        const nameWithoutExt = fileName.replace(/\.[^/.]+$/, '');
                        folderInput.value = dir;
                        htmlInput.value = nameWithoutExt;
                        saveAllSettings();
                        checkProject();
                    }
                })
                .catch(() => showToast(i18n.t('toast_select_html_failed'), 'error'));
        });

        folderInput.addEventListener('input', () => { saveAllSettings(); checkProject(); });
        htmlInput.addEventListener('input', () => { saveAllSettings(); checkProject(); });

        // ----- Блок выбора сжатия (сворачиваемый) -----
        const toggleCompressionBtn = document.getElementById('toggleCompressionBlock');
        const compressionContent = document.getElementById('compressionContent');
        const compressionSelect = document.getElementById('compressionSelect');

        if (settings.compressionCollapsed) {
            compressionContent.classList.remove('open');
            toggleCompressionBtn.classList.add('collapsed');
        } else {
            compressionContent.classList.add('open');
        }

        toggleCompressionBtn.addEventListener('click', () => {
            compressionContent.classList.toggle('open');
            toggleCompressionBtn.classList.toggle('collapsed');
            settings.compressionCollapsed = !compressionContent.classList.contains('open');
            saveSettings(settings);
        });

        compressionSelect.value = settings.compressionTab || 'gzip';

        function showSettingsForType(type) {
            document.getElementById('gzip-settings').style.display = (type === 'gzip') ? 'block' : 'none';
            document.getElementById('brotli-settings').style.display = (type === 'brotli') ? 'block' : 'none';
            settings.compressionTab = type;
            saveSettings(settings);
            loadSettingsForType(type);
        }

        function loadSettingsForType(type) {
            const typeSettings = settings[type] || { createBackup: true, wasmLevel: 9, pckLevel: 9 };
            const backup = document.getElementById(`${type}-createBackup`);
            const wasm = document.getElementById(`${type}-wasmLevel`);
            const pck = document.getElementById(`${type}-pckLevel`);
            if (backup) backup.checked = typeSettings.createBackup !== undefined ? typeSettings.createBackup : true;
            if (wasm) wasm.value = typeSettings.wasmLevel || 9;
            if (pck) pck.value = typeSettings.pckLevel || 9;
        }

        function saveSettingsForType(type) {
            const backup = document.getElementById(`${type}-createBackup`);
            const wasm = document.getElementById(`${type}-wasmLevel`);
            const pck = document.getElementById(`${type}-pckLevel`);
            if (!settings[type]) settings[type] = {};
            if (backup) settings[type].createBackup = backup.checked;
            if (wasm) settings[type].wasmLevel = parseInt(wasm.value) || 9;
            if (pck) settings[type].pckLevel = parseInt(pck.value) || 9;
            saveSettings(settings);
        }

        document.addEventListener('change', (e) => {
            const id = e.target.id;
            if (id && (id.endsWith('-createBackup') || id.endsWith('-wasmLevel') || id.endsWith('-pckLevel'))) {
                const type = id.split('-')[0];
                saveSettingsForType(type);
            }
        });
        document.addEventListener('input', (e) => {
            const id = e.target.id;
            if (id && (id.endsWith('-wasmLevel') || id.endsWith('-pckLevel'))) {
                const type = id.split('-')[0];
                saveSettingsForType(type);
            }
        });

        compressionSelect.addEventListener('change', function() {
            showSettingsForType(this.value);
        });

        showSettingsForType(compressionSelect.value);

        // ----- Блок исключения расширений -----
        const excludeEnabled = document.getElementById('excludeEnabled');
        const excludeContent = document.getElementById('excludeContent');
        const toggleExcludeBtn = document.getElementById('toggleExcludeBlock');

        excludeEnabled.checked = settings.excludeEnabled !== undefined ? settings.excludeEnabled : true;

        if (settings.excludeCollapsed) {
            excludeContent.classList.remove('open');
            toggleExcludeBtn.classList.add('collapsed');
        } else {
            excludeContent.classList.add('open');
        }

        excludeEnabled.addEventListener('change', () => {
            settings.excludeEnabled = excludeEnabled.checked;
            saveSettings(settings);
        });

        toggleExcludeBtn.addEventListener('click', () => {
            excludeContent.classList.toggle('open');
            toggleExcludeBtn.classList.toggle('collapsed');
            settings.excludeCollapsed = !excludeContent.classList.contains('open');
            saveSettings(settings);
        });

        // ----- Список расширений -----
        const excludeInput = document.getElementById('excludeExtensionInput');
        const addBtn = document.getElementById('addExtensionBtn');
        const extensionList = document.getElementById('extensionList');
        const removeBtn = document.getElementById('removeSelectedExtensionsBtn');

        let extensions = settings.excludeExtensions || ['.backup', '.tmp', '.gz', '.img', '.import', '.old', '.png'];

        function renderExtensions() {
            extensionList.innerHTML = '';
            extensions.forEach((ext, index) => {
                const li = document.createElement('li');
                li.innerHTML = `<input type="checkbox" data-index="${index}"> ${ext}`;
                extensionList.appendChild(li);
            });
        }

        function saveExtensions() {
            settings.excludeExtensions = extensions;
            saveSettings(settings);
        }

        function loadDefaultExtensions() {
            if (extensions && extensions.length > 0) {
                renderExtensions();
                return;
            }
            fetch('/api/default-extensions')
                .then(res => {
                    if (!res.ok) throw new Error();
                    return res.json();
                })
                .then(data => {
                    extensions = data.extensions || ['.backup', '.tmp', '.gz', '.img', '.import', '.old', '.png'];
                    saveExtensions();
                    renderExtensions();
                })
                .catch(() => {
                    extensions = ['.backup', '.tmp', '.gz', '.img', '.import', '.old', '.png'];
                    saveExtensions();
                    renderExtensions();
                });
        }

        addBtn.addEventListener('click', () => {
            const val = excludeInput.value.trim();
            if (val && !extensions.includes(val)) {
                extensions.push(val);
                excludeInput.value = '';
                renderExtensions();
                saveExtensions();
            }
        });

        removeBtn.addEventListener('click', () => {
            const checkboxes = extensionList.querySelectorAll('input[type="checkbox"]:checked');
            const indices = Array.from(checkboxes).map(cb => parseInt(cb.dataset.index));
            if (!indices.length) return;
            extensions = extensions.filter((_, i) => !indices.includes(i));
            renderExtensions();
            saveExtensions();
        });

        loadDefaultExtensions();

        // ----- Загрузка платформ -----
        const platformSelect = document.getElementById('platformSelect');

        function loadPlatforms() {
            fetch('/api/platforms')
                .then(res => {
                    if (!res.ok) throw new Error(i18n.t('toast_platforms_load_error'));
                    return res.json();
                })
                .then(data => {
                    const platforms = data.platforms || [];
                    const savedPlatform = settings.selectedPlatform || '';
                    platformSelect.innerHTML = '';
                    platforms.forEach(p => {
                        const option = document.createElement('option');
                        option.value = p;
                        option.textContent = p;
                        platformSelect.appendChild(option);
                    });
                    if (savedPlatform && platforms.includes(savedPlatform)) {
                        platformSelect.value = savedPlatform;
                    } else {
                        platformSelect.value = platforms[0] || '';
                    }
                })
                .catch(err => {
                    console.error('Ошибка загрузки платформ:', err);
                    platformSelect.innerHTML = '<option value="">' + i18n.t('platforms_load_failed') + '</option>';
                });
        }

        loadPlatforms();

        platformSelect.addEventListener('change', function() {
            settings.selectedPlatform = this.value;
            saveSettings(settings);
        });

        // ----- Пошаговое выполнение сжатия (сжатие → платформа → ZIP) -----
        startBtn.addEventListener('click', async function () {
            const folder = folderInput.value.trim();
            const htmlName = htmlInput.value.trim() || 'index';
            if (!folder) {
                showToast(i18n.t('toast_choose_folder'), 'warning');
                return;
            }

            const btnSpinner = document.getElementById('compressSpinner');
            const btnLabel = document.getElementById('compressBtnLabel');
            const compressionType = compressionSelect.value;
            const typeSettings = settings[compressionType] || { createBackup: true, wasmLevel: 9, pckLevel: 9 };
            const createBackup = typeSettings.createBackup;
            const wasmLevel = parseInt(typeSettings.wasmLevel) || 9;
            const pckLevel = parseInt(typeSettings.pckLevel) || 9;

            const includeInArchive = excludeEnabled.checked;
            if (!includeInArchive) {
                showToast(i18n.t('toast_zip_disabled'), 'info');
                return;
            }

            showToast(i18n.t('toast_compress_started'), 'info');
            const platform = platformSelect.value;
            
            
            const basePayload = {
                folder,
                filename: htmlName,
            };

            const stages = [];

            // 1. Сжатие – добавляем параметры сжатия
            stages.push({
                name: 'compress',
                label: i18n.t('stage_compress'),
                url: '/compress/compress',
                payload: {
                    ...basePayload,
                    compression_type: compressionType,
                    create_backup: createBackup,
                    wasm_level: wasmLevel,
                    pck_level: pckLevel
                }
            });

            // 2. Платформа – добавляем platform (если выбрана и не None)
            if (platform && platform !== 'None') {
                stages.push({
                    name: 'platform',
                    label: i18n.t('stage_platform'),
                    url: '/compress/platform',
                    payload: {
                        ...basePayload,
                        platform: platform
                    }
                });
            }

            // 3. Упаковка в ZIP – добавляем exclude_extensions (только здесь)
            stages.push({
                name: 'zippack',
                label: i18n.t('stage_zippack'),
                url: '/compress/zippack',
                payload: {
                    ...basePayload,
                    exclude_extensions: extensions
                }
            });

            // Блокируем кнопку и сбрасываем прогресс
            startBtn.disabled = true;
            if (btnSpinner) btnSpinner.style.display = 'inline-block';
            if (btnLabel) btnLabel.textContent = i18n.t('compress_running');
            progressFill.style.width = '0%';
            progressText.textContent = '0%';
            progressStatus.textContent = i18n.t('compress_preparing');

            let success = true;
            let currentStage = 0;
            const totalStages = stages.length;

            try {
                for (const stage of stages) {
                    currentStage++;
                    progressStatus.textContent = `${stage.label}... (${currentStage}/${totalStages})`;
                    const percent = Math.round((currentStage - 1) / totalStages * 100);
                    progressFill.style.width = percent + '%';
                    progressText.textContent = percent + '%';

                    const response = await fetch(stage.url, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(stage.payload)
                    });

                    if (!response.ok) {
                        const errData = await response.json().catch(() => ({}));
                        throw new Error(errData.detail || errData.message || `${i18n.t('stage_error_prefix')} ${stage.label}`);
                    }

                    const data = await response.json();
                    if (!data.success) {
                        throw new Error(data.message || `${i18n.t('stage_error_prefix')} ${stage.label}`);
                    }

                    const doneMsg = i18n.tf(data.message) || i18n.t('stage_done');
                    showToast(`${stage.label}: ${data.message_extra ? doneMsg + ' ' + data.message_extra : doneMsg}`, 'success');

                    const newPercent = Math.round(currentStage / totalStages * 100);
                    progressFill.style.width = newPercent + '%';
                    progressText.textContent = newPercent + '%';
                }

                progressStatus.textContent = i18n.t('compress_all_done');
                progressFill.style.width = '100%';
                progressText.textContent = '100%';

            } catch (error) {
                success = false;
                progressStatus.textContent = `${i18n.t('error_prefix')}: ${i18n.tf(error.message)}`;
                showToast(`${i18n.t('stage_error_prefix')} ${currentStage}: ${i18n.tf(error.message)}`, 'error');
            } finally {
                startBtn.disabled = false;
                if (btnSpinner) btnSpinner.style.display = 'none';
                if (btnLabel) btnLabel.textContent = i18n.t('compress_start');
            }
        });

        // Сохраняем пути и первичная проверка
        saveAllSettings();
        if (folderInput.value.trim()) setTimeout(checkProject, 200);
    }

    waitForElements(
        ['folderPath', 'htmlFileName', 'selectFolderBtn', 'selectHtmlBtn', 'startCompressBtn'],
        initCompress,
        10000
    );
})();