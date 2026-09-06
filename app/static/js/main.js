// main.js – только навигация и сворачивание меню
document.addEventListener('DOMContentLoaded', function () {
    // Сворачивание меню
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('toggleSidebarBtn');
    const content = document.getElementById('content');
    toggleBtn.addEventListener('click', function () {
        sidebar.classList.toggle('collapsed');
        content.classList.toggle('expanded');
    });

    // Переключение страниц
    const menuItems = document.querySelectorAll('.menu-item');
    const pages = {
        compress: document.getElementById('page-compress'),
        build: document.getElementById('page-build'),
        settings: document.getElementById('page-settings'),
        about: document.getElementById('page-about')
    };

    function switchPage(pageId) {
        Object.values(pages).forEach(p => p.classList.remove('active'));
        if (pages[pageId]) pages[pageId].classList.add('active');
        menuItems.forEach(item => {
            item.classList.remove('active');
            if (item.dataset.page === pageId) item.classList.add('active');
        });
    }

    menuItems.forEach(item => {
        item.addEventListener('click', function () {
            switchPage(this.dataset.page);
        });
    });

    // Активируем пункт меню, соответствующий начальной странице
    const activePage = document.querySelector('.page.active');
    if (activePage) {
        menuItems.forEach(item => {
            if (item.dataset.page === activePage.id.replace('page-', '')) {
                item.classList.add('active');
            }
        });
    }

    // Переключатель языков (в шапке и на странице настроек)
    const langSelects = document.querySelectorAll('#langSelect, #settingsLangSelect');
    if (langSelects.length > 0) {
        // Устанавливаем текущий язык из localStorage или по умолчанию
        const savedLang = localStorage.getItem('app:language') || 'ru';
        langSelects.forEach(sel => { sel.value = savedLang; });

        langSelects.forEach(function (langSelect) {
            langSelect.addEventListener('change', async function () {
                const lang = this.value;
                if (window.i18n) {
                    const success = await window.i18n.switchLanguage(lang);
                    if (success) {
                        // Синхронизируем все переключатели языка
                        langSelects.forEach(sel => { sel.value = lang; });
                    }
                }
            });
        });
    }

    // Обработчики кнопок выбора папок в настройках сборки движка
    const buildPathSelectors = [
        { btnId: 'selectEngineSrcBtn', inputId: 'engineSrcPath', title: 'Выберите папку с исходными файлами движка' },
        { btnId: 'selectEmsdkBtn', inputId: 'emsdkPath', title: 'Выберите папку с emsdk' },
        { btnId: 'selectWasmOptBtn', inputId: 'wasmOptPath', title: 'Выберите папку с wasm-opt' },
        { btnId: 'selectCustomScriptBtn', inputId: 'customBuildScript', title: 'Выберите папку со скриптами сборки' },
        { btnId: 'selectGdbuildBtn', inputId: 'gdbuildProfilesPath', title: 'Выберите папку с профилями .gdbuild' },
    ];

    buildPathSelectors.forEach(function (selector) {
        const btn = document.getElementById(selector.btnId);
        const input = document.getElementById(selector.inputId);
        if (btn && input) {
            btn.addEventListener('click', async function () {
                try {
                    const response = await fetch('/api/select-folder');
                    const data = await response.json();
                    if (data.path) {
                        input.value = data.path;
                        input.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                } catch (e) {
                    console.error('Ошибка выбора папки:', e);
                }
            });
        }
    });
});