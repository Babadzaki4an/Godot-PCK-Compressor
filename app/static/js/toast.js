// toast.js – система уведомлений с звуком
(function() {
    'use strict';

    // Создаём контейнер для тостов (один раз)
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-width: 400px;
            width: 100%;
            pointer-events: none;
        `;
        document.body.appendChild(container);
    }

    // Генерация приятного звука (Web Audio)
    let _audioCtx = null;
    function playToastSound() {
        try {
            if (!_audioCtx) {
                _audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            }
            if (_audioCtx.state === 'suspended') {
                _audioCtx.resume().catch(() => {});
            }

            const now = _audioCtx.currentTime;
            const osc = _audioCtx.createOscillator();
            const gain = _audioCtx.createGain();
            osc.connect(gain);
            gain.connect(_audioCtx.destination);

            osc.frequency.value = 170;
            osc.type = 'triangle';
            gain.gain.setValueAtTime(0.15, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.2);

            osc.start(now);
            osc.stop(now + 0.2);

            // Автоочистка
            setTimeout(() => {
                try { osc.disconnect(); gain.disconnect(); } catch (e) {}
            }, 300);
        } catch (e) { /* тихо */ }
    }

    // Создание одного тоста
    function showToast(message, type = 'info', duration = 3000) {
        if (!message) return;

        // Играем звук
        playToastSound();

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.style.cssText = `
            padding: 14px 20px;
            border-radius: 8px;
            background: var(--bg-app);
            color: var(--text-primary);
            box-shadow: 0 8px 24px var(--shadow);
            border-left: 5px solid;
            pointer-events: auto;
            animation: slideIn 0.3s ease forwards;
            font-family: 'Segoe UI', sans-serif;
            font-size: 15px;
            line-height: 1.4;
            word-break: break-word;
        `;

        // Цвета для разных типов (из CSS-переменных темы)
        const colors = {
            info: 'var(--accent)',
            success: 'var(--success)',
            warning: 'var(--warning)',
            error: 'var(--danger)'
        };
        toast.style.borderLeftColor = colors[type] || colors.info;

        // Иконка (Font Awesome)
        const iconMap = {
            info: 'fa-info-circle',
            success: 'fa-check-circle',
            warning: 'fa-exclamation-triangle',
            error: 'fa-times-circle'
        };
        const iconClass = iconMap[type] || 'fa-info-circle';
        toast.innerHTML = `<i class="fas ${iconClass}" style="margin-right: 12px; color: ${colors[type] || colors.info};"></i>${message}`;

        container.appendChild(toast);

        // Удаление через duration
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(() => {
                if (toast.parentNode) toast.remove();
            }, 300);
        }, duration);
    }

    // Добавляем анимации в head (если ещё нет)
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        @keyframes slideOut {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(100%); opacity: 0; }
        }
    `;
    document.head.appendChild(style);

    // Глобальный доступ
    window.showToast = showToast;
})();