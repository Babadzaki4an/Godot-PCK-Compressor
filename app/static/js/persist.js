// persist.js – сохранение и восстановление полей
// Все input с атрибутом data-persist сохраняются в localStorage
// под ключом "app:<id>" и восстанавливаются при загрузке.
(function() {
    'use strict';

    const inputs = document.querySelectorAll('input[data-persist]');

    inputs.forEach(function (input) {
        const key = 'app:' + input.id;

        const saved = localStorage.getItem(key);
        if (saved !== null) {
            input.value = saved;
        }

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