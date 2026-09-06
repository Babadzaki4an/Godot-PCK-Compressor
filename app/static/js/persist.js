// persist.js – сохранение и восстановление полей
(function() {
    'use strict';

    // Список всех полей для сохранения: [id, key в localStorage]
    const fields = [
        ['folderPath', 'app:folderPath'],
        ['htmlFileName', 'app:htmlFileName'],
        ['engineSrcPath', 'app:engineSrcPath'],
        ['emsdkPath', 'app:emsdkPath'],
        ['wasmOptPath', 'app:wasmOptPath'],
        ['customBuildScript', 'app:customBuildScript'],
        ['gdbuildProfilesPath', 'app:gdbuildProfilesPath'],
    ];

    // --- Восстановление из localStorage ---
    fields.forEach(function ([id, key]) {
        const input = document.getElementById(id);
        if (!input) return;
        const saved = localStorage.getItem(key);
        if (saved !== null) {
            input.value = saved;
        }
        // --- Сохранение при изменении ---
        input.addEventListener('input', function () {
            localStorage.setItem(key, input.value);
        });
        input.addEventListener('blur', function () {
            localStorage.setItem(key, input.value);
        });
    });

    // Сохранение выбранного языка
    const langSelects = document.querySelectorAll('.lang-select');
    const savedLang = localStorage.getItem('app:language');
    if (savedLang) {
        langSelects.forEach(function (sel) {
            sel.value = savedLang;
        });
    }
})();