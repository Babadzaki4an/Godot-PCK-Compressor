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
        home: document.getElementById('page-home'),
        compress: document.getElementById('page-compress'),
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
        // Инициализатор только для home (остальные сами себя инициализируют)
        if (pageId === 'home' && window.initHome) {
            window.initHome();
        }
    }

    menuItems.forEach(item => {
        item.addEventListener('click', function () {
            switchPage(this.dataset.page);
        });
    });

    // Инициализация home по умолчанию
    if (window.initHome) window.initHome();

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
});