// main.js – навигация, переключение языка, выбор путей
document.addEventListener('DOMContentLoaded', () => {
    // --- Сворачивание меню ---
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('toggleSidebarBtn');
    const content = document.getElementById('content');
    toggleBtn.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
        content.classList.toggle('expanded');
    });

    // --- Переключение страниц ---
    const menuItems = document.querySelectorAll('.menu-item');
    const pages = {
        compress: document.getElementById('page-compress'),
        build: document.getElementById('page-build'),
        preview: document.getElementById('page-preview'),
        settings: document.getElementById('page-settings'),
        about: document.getElementById('page-about')
    };

    function switchPage(pageId) {
        Object.values(pages).forEach(p => p.classList.remove('active'));
        if (pages[pageId]) pages[pageId].classList.add('active');
        menuItems.forEach(item => {
            item.classList.toggle('active', item.dataset.page === pageId);
        });
    }

    menuItems.forEach(item => {
        item.addEventListener('click', () => switchPage(item.dataset.page));
    });

    // Активируем пункт меню для начальной страницы
    const activePage = document.querySelector('.page.active');
    if (activePage) {
        menuItems.forEach(item => {
            if (item.dataset.page === activePage.id.replace('page-', '')) {
                item.classList.add('active');
            }
        });
    }

    // --- Переключатель языков ---
    const langSelects = document.querySelectorAll('#langSelect, #settingsLangSelect');
    if (langSelects.length > 0) {
        const savedLang = localStorage.getItem('app:language') || 'ru';
        langSelects.forEach(sel => { sel.value = savedLang; });

        langSelects.forEach(langSelect => {
            langSelect.addEventListener('change', async function () {
                const lang = this.value;
                if (window.i18n) {
                    const success = await window.i18n.switchLanguage(lang);
                    if (success) {
                        langSelects.forEach(sel => { sel.value = lang; });
                    }
                }
            });
        });
    }

    // --- Выбор путей в настройках ---
    const pathSelectors = [
        { btnId: 'selectEngineSrcBtn', inputId: 'engineSrcPath', type: 'folder' },
        { btnId: 'selectEmsdkBtn', inputId: 'emsdkPath', type: 'folder' },
        { btnId: 'selectWasmOptBtn', inputId: 'wasmOptPath', type: 'file', filter: 'exe' },
        { btnId: 'selectCustomScriptBtn', inputId: 'customBuildScript', type: 'folder' },
        { btnId: 'selectGdbuildBtn', inputId: 'gdbuildProfilesPath', type: 'folder' },
    ];

    pathSelectors.forEach(({ btnId, inputId, type, filter }) => {
        const btn = document.getElementById(btnId);
        const input = document.getElementById(inputId);
        if (!btn || !input) return;

        btn.addEventListener('click', async () => {
            try {
                let endpoint = type === 'file' ? '/api/select-file' : '/api/select-folder';
                if (filter) endpoint += `?filter=${filter}`;
                const response = await fetch(endpoint);
                const data = await response.json();
                if (data.path) {
                    input.value = data.path;
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                }
            } catch (e) {
                console.error('Ошибка выбора пути:', e);
            }
        });
    });
});