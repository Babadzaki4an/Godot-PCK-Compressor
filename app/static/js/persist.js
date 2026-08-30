// compress.js – только сохранение и восстановление
(function() {
    'use strict';

    // Элементы
    const folderInput = document.getElementById('folderPath');
    const htmlInput = document.getElementById('htmlFileName');

    if (!folderInput || !htmlInput) {
        console.warn('❌ Поля не найдены');
        return;
    }

    // --- Восстановление из localStorage ---
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
    }

    // --- Привязка событий ---
    folderInput.addEventListener('input', saveAll);
    htmlInput.addEventListener('input', saveAll);
    // Сохраняем также при потере фокуса (на случай, если пользователь ввёл и сразу закрыл страницу)
    folderInput.addEventListener('blur', saveAll);
    htmlInput.addEventListener('blur', saveAll);

    console.log('✅ Сохранение/восстановление настроено');
})();