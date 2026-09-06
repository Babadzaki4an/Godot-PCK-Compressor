// build.js — вкладка «Сборка движка»
document.addEventListener('DOMContentLoaded', () => {
    // Локализация
    const t = (key) => window.i18n?.t(key) || key;

    // --- Переключение основных вкладок (Сборка / Генерация) ---
    document.querySelectorAll('.build-tab').forEach((tab) => {
        tab.addEventListener('click', function () {
            document.querySelectorAll('.build-tab').forEach((tb) => tb.classList.remove('active'));
            document.querySelectorAll('.build-tab-content').forEach((tc) => tc.classList.remove('active'));
            this.classList.add('active');
            document.getElementById('tab-' + this.dataset.tab).classList.add('active');
        });
    });

    // --- Переключение групп (основные разделы параметров) ---
    const groupTabs = document.querySelectorAll('.group-tab');
    const groupContents = document.querySelectorAll('.group-content');

    const showGroup = (group) => {
        groupTabs.forEach((gt) => gt.classList.toggle('active', gt.dataset.group === group));
        groupContents.forEach((gc) => {
            gc.classList.toggle('active', gc.dataset.group === group);
            if (gc.dataset.group === group) {
                // Автоматически показать первую подгруппу (для модулей)
                const subTabs = gc.querySelectorAll('.subgroup-tab');
                if (subTabs.length) {
                    subTabs.forEach((st) => st.classList.remove('active'));
                    subTabs[0].classList.add('active');
                    gc.querySelectorAll('.subgroup-content').forEach((sc) => {
                        sc.classList.toggle('active', sc.dataset.subgroup === subTabs[0].dataset.subgroup);
                    });
                }
            }
        });
    };

    groupTabs.forEach((gt) => {
        gt.addEventListener('click', () => showGroup(gt.dataset.group));
    });

    // --- Переключение подгрупп (внутри модулей) ---
    document.querySelectorAll('.subgroup-tab').forEach((st) => {
        st.addEventListener('click', function () {
            const parent = this.closest('.group-content');
            parent.querySelectorAll('.subgroup-tab').forEach((t) => t.classList.remove('active'));
            this.classList.add('active');
            parent.querySelectorAll('.subgroup-content').forEach((sc) => {
                sc.classList.toggle('active', sc.dataset.subgroup === this.dataset.subgroup);
            });
        });
    });

    // По умолчанию показываем первую группу
    if (groupTabs.length) showGroup(groupTabs[0].dataset.group);

    // --- Работа со списком custom.py файлов ---
    const existingFilesSelect = document.getElementById('existingFiles');
    const refreshFilesBtn = document.getElementById('refreshFilesBtn');
    const customPyNameInput = document.getElementById('customPyName');

    // Загрузка списка файлов из папки, указанной в настройках
    const loadExistingCustomFiles = async () => {
        const path = (localStorage.getItem('app:customBuildScript') || '').trim();
        if (!path) {
            existingFilesSelect.innerHTML = `<option value="">${t('custom_py_no_path')}</option>`;
            return;
        }

        const currentSelected = existingFilesSelect.value; // сохраняем выбор

        try {
            const response = await fetch(`/build/list-files?path=${encodeURIComponent(path)}`);
            const data = await response.json();

            existingFilesSelect.innerHTML = '';
            if (!data.ok || !data.files?.length) {
                existingFilesSelect.innerHTML = `<option value="">${t('build_no_files')}</option>`;
                return;
            }

            data.files.forEach((name) => {
                const opt = document.createElement('option');
                opt.value = name;
                opt.textContent = name;
                existingFilesSelect.appendChild(opt);
            });

            // Восстанавливаем выбор, если файл всё ещё существует
            let selectedValue = '';
            const options = Array.from(existingFilesSelect.options);
            if (currentSelected && options.some((opt) => opt.value === currentSelected)) {
                selectedValue = currentSelected;
            } else {
                const first = options.find((opt) => opt.value !== '');
                if (first) selectedValue = first.value;
            }

            existingFilesSelect.value = selectedValue;
            if (selectedValue) {
                existingFilesSelect.dispatchEvent(new Event('change')); // загружаем параметры
            }
        } catch {
            existingFilesSelect.innerHTML = `<option value="">${t('build_no_files')}</option>`;
        }
    };

    // При выборе файла из списка — синхронизируем поле имени
    existingFilesSelect?.addEventListener('change', function () {
        if (this.value && customPyNameInput) {
            customPyNameInput.value = this.value;
        }
    });

    // Обновление списка по кнопке
    refreshFilesBtn?.addEventListener('click', loadExistingCustomFiles);

    // Обновление при переключении на вкладку «Генерация»
    document.getElementById('tabGenerateBtn')?.addEventListener('click', loadExistingCustomFiles);

    // --- Сбор параметров со всех элементов управления ---
    const collectParams = () => {
        const params = {};
        document.querySelectorAll('.build-param-input').forEach((ctrl) => {
            if (ctrl.value) params[ctrl.dataset.paramName] = ctrl.value;
        });
        document.querySelectorAll('.build-param-checkbox:checked').forEach((box) => {
            params[box.dataset.paramName] = box.value;
        });
        return params;
    };

    // --- Генерация нового custom.py файла ---
    document.getElementById('generateBtn')?.addEventListener('click', async function () {
        const path = (localStorage.getItem('app:customBuildScript') || '').trim();
        if (!path) {
            showToast(t('custom_py_no_path'), 'error', 3000);
            return;
        }
        const filename = (customPyNameInput?.value || 'custom.py').trim();

        try {
            const response = await fetch('/build/generate-custom-py', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ folder: path, params: collectParams(), filename }),
            });
            const data = await response.json();
            showToast(`${t(data.message)}<br>${data.message_extra}`, data.ok ? 'success' : 'error', 3000);
            loadExistingCustomFiles(); // обновляем список после создания
        } catch (e) {
            showToast(`${t('build_generated_failed')} ${e}`, 'error', 3000);
        }
    });

    // --- Загрузка параметров из выбранного custom.py файла ---
    const applyParamsFromFile = (params) => {
        document.querySelectorAll('[data-param-name]').forEach((control) => {
            const name = control.dataset.paramName;
            if (params && name in params) {
                const value = params[name];
                if (control.type === 'checkbox') {
                    control.checked = ['yes', 'true', '1', true].includes(value);
                } else {
                    control.value = value;
                }
            } else {
                // Сброс, если параметр отсутствует
                if (control.type === 'checkbox') {
                    control.checked = false;
                } else if (control.tagName === 'SELECT') {
                    if (control.options.length) control.selectedIndex = 0;
                } else {
                    control.value = '';
                }
            }
        });
    };

    const getCustomPyFile = async function () {
        const selectedFile = this.value;
        if (!selectedFile) return;

        const path = (localStorage.getItem('app:customBuildScript') || '').trim();
        try {
            const response = await fetch(
                `/build/get-custom-py/${encodeURIComponent(selectedFile)}?path=${encodeURIComponent(path)}`
            );
            const data = await response.json();

            applyParamsFromFile(data.params);

            // Синхронизируем поле имени
            if (customPyNameInput && customPyNameInput.value !== selectedFile) {
                customPyNameInput.value = selectedFile;
            }
        } catch (e) {
            showToast(e, 'error', 3000);
        }
    };

    existingFilesSelect?.addEventListener('change', getCustomPyFile);

    // --- Первоначальная загрузка списка и параметров ---
    loadExistingCustomFiles();
});