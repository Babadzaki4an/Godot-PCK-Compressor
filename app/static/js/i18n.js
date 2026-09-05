// i18n.js – клиентский переводчик
(function () {
    'use strict';

    // Текущие переводы (объект)
    let translations = {};
    // Fallback-переводы (русский) — используются, если ключа нет в текущем языке
    let fallbackTranslations = {};
    // Текущий язык
    let currentLang = null;
    // Ключ в localStorage
    const STORAGE_KEY = 'app:language';

    // Функция перевода: текущий язык -> fallback (ru) -> ключ
    function t(key, fallback = key) {
        if (translations && translations[key] !== undefined) {
            return translations[key];
        }
        if (fallbackTranslations && fallbackTranslations[key] !== undefined) {
            return fallbackTranslations[key];
        }
        return fallback;
    }

    // Загрузка fallback-переводов (русский) — один раз
    async function loadFallback() {
        if (Object.keys(fallbackTranslations).length > 0) return;
        try {
            const response = await fetch('/api/get-translation', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ lang: 'ru' })
            });
            if (response.ok) {
                const data = await response.json();
                fallbackTranslations = data.t || {};
            }
        } catch (e) { /* fallback недоступен — не критично */ }
    }

    // Загрузка переводов для языка
    async function loadTranslations(lang) {
        try {
            await loadFallback();
            const response = await fetch('/api/get-translation', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ lang: lang })
            });
            if (!response.ok) {
                console.error('Ошибка загрузки переводов:', response.statusText);
                return false;
            }
            const data = await response.json();
            translations = data.t || {};
            currentLang = lang;
            localStorage.setItem(STORAGE_KEY, lang);
            return true;
        } catch (e) {
            console.error('Ошибка загрузки переводов:', e);
            return false;
        }
    }

    // Применение переводов к элементам DOM
    function applyTranslations() {
        if (!translations) return;

        // Обрабатываем элементы с атрибутом data-i18n
        const elements = document.querySelectorAll('[data-i18n]');
        elements.forEach(function (el) {
            const key = el.getAttribute('data-i18n');
            const value = t(key);
            if (value !== key) { // перевод найден
                // Если внутри есть HTML (иконки), заменяем только последний текстовый узел
                const textNodes = Array.from(el.childNodes).filter(function (n) {
                    return n.nodeType === Node.TEXT_NODE && n.textContent.trim() !== '';
                });
                if (textNodes.length > 0) {
                    textNodes[textNodes.length - 1].textContent = value;
                } else {
                    el.textContent = value;
                }
            }
        });

        // Обрабатываем placeholder'ы
        const placeholderElements = document.querySelectorAll('[data-i18n-placeholder]');
        placeholderElements.forEach(function (el) {
            const key = el.getAttribute('data-i18n-placeholder');
            const value = t(key);
            if (value !== key) {
                el.setAttribute('placeholder', value);
            }
        });
    }

    // Инициализация i18n
    async function initI18n(lang = null) {
        let language = lang || localStorage.getItem(STORAGE_KEY) || 'ru';
        const success = await loadTranslations(language);
        if (success) {
            applyTranslations();
        }
        return success;
    }

    // Переключение языка
    async function switchLanguage(lang) {
        if (lang === currentLang) return true;
        const success = await loadTranslations(lang);
        if (success) {
            applyTranslations();
            // Опционально: можно вызвать событие для страниц
            window.dispatchEvent(new CustomEvent('language-changed', {
                detail: { lang: lang }
            }));
        }
        return success;
    }

    // Перевод серверных сообщений: если текст является ключом — переводим, иначе возвращаем как есть
    function tf(text) {
        if (!text) return text;
        if (translations && Object.prototype.hasOwnProperty.call(translations, text)) return translations[text];
        if (fallbackTranslations && Object.prototype.hasOwnProperty.call(fallbackTranslations, text)) return fallbackTranslations[text];
        return text;
    }

    // Глобальный доступ
    window.i18n = {
        t: t,
        tf: tf,
        loadTranslations: loadTranslations,
        applyTranslations: applyTranslations,
        initI18n: initI18n,
        switchLanguage: switchLanguage,
        get currentLang() { return currentLang; },
        get translations() { return translations; }
    };

    // Инициализируем при загрузке страницы
    document.addEventListener('DOMContentLoaded', function () {
        initI18n();
    });
})();