// game_hook.js — внедряется в HTML игры при превью.
// Управление звуком из родительского окна + перехват внешних ссылок
// + замер времени загрузки и распаковки ресурсов игры.

// --- Замер времени: старт страницы, суммарный fetch и decompress ---
window.__pckTiming = {
    start: performance.now(),
    fetch: 0,          // суммарное время загрузки ресурсов, мс
    decompress: 0,     // суммарное время распаковки, мс
    decompressCount: 0
};

(function () {
    var t = window.__pckTiming;
    var lastActivity = performance.now();   // когда была последняя загрузка/распаковка

    // Родительскому окну интересны только завершённые замеры
    function report() {
        try {
            window.parent.postMessage({
                type: 'pck-timing',
                active: (performance.now() - lastActivity) < 2000,  // идёт ли ещё загрузка
                elapsed: (performance.now() - t.start) / 1000,
                fetch: t.fetch / 1000,
                decompress: t.decompress / 1000,
                decompressCount: t.decompressCount
            }, '*');
        } catch (e) { /* родитель недоступен */ }
    }

    // Суммируем время всех fetch'ей (загрузка wasm/pck и прочих ресурсов)
    var origFetch = window.fetch;
    window.fetch = function () {
        var started = performance.now();
        lastActivity = started;
        var result = origFetch.apply(this, arguments);
        result.then(
            function () { t.fetch += performance.now() - started; lastActivity = performance.now(); report(); },
            function () { t.fetch += performance.now() - started; lastActivity = performance.now(); }
        );
        return result;
    };

    // Оборачиваем декомпрессоры (появляются позже хука — ловим опросом)
    function wrapDecompressor(obj, name) {
        if (!obj || obj.__pckWrapped) return;
        var orig = obj[name];
        if (typeof orig !== 'function') return;
        obj[name] = function () {
            var started = performance.now();
            lastActivity = started;
            var result = orig.apply(this, arguments);
            t.decompress += performance.now() - started;
            t.decompressCount++;
            lastActivity = performance.now();
            report();
            return result;
        };
        obj.__pckWrapped = true;
    }

    var poll = setInterval(function () {
        wrapDecompressor(window.pako, 'inflate');
        wrapDecompressor(window.brotli, 'decompress');
        wrapDecompressor(window.fzstd, 'decompress');
    }, 200);
    setTimeout(function () { clearInterval(poll); }, 60000); // стоп через минуту

    // Периодический репорт, пока идёт загрузка; после 2 с бездействия —
    // финальный отчёт с active:false и остановка тиков
    var live = setInterval(function () {
        report();
        if ((performance.now() - lastActivity) >= 2000) {
            clearInterval(live);
        }
    }, 250);
})();

window.setGameMuted = (function () {
    var muted = false, ctxs = [], medias = [];
    var AC = window.AudioContext || window.webkitAudioContext;
    if (AC) {
        var Native = AC;
        window.AudioContext = window.webkitAudioContext = function () {
            var c = new Native();
            ctxs.push(c);
            if (muted) { try { c.suspend(); } catch (e) {} }
            return c;
        };
        var origResume = AC.prototype.resume;
        // Пока muted — игра не может "разбудить" звук через resume()
        AC.prototype.resume = function () {
            if (muted) return Promise.resolve();
            return origResume.apply(this, arguments);
        };
    }
    var play = HTMLMediaElement.prototype.play;
    HTMLMediaElement.prototype.play = function () {
        this.muted = muted;
        medias.push(this);
        return play.apply(this, arguments);
    };
    function enforce() {
        ctxs.forEach(function (c) { try { muted ? c.suspend() : c.resume(); } catch (e) {} });
        medias.forEach(function (m) { try { m.muted = muted; } catch (e) {} });
    }
    // Переподтверждаем мут на любое взаимодействие с игрой
    ['pointerdown', 'click', 'keydown', 'touchstart'].forEach(function (ev) {
        document.addEventListener(ev, function () { if (muted) enforce(); }, true);
    });
    return function (v) {
        muted = v;
        enforce();
    };
})();

// Блокируем открытие ссылок в системном браузере:
// window.open и target="_blank" навигают iframe вместо внешнего окна
window.open = function (url) {
    if (url) { try { window.location.href = url; } catch (e) {} }
    return null;
};
document.addEventListener('click', function (e) {
    var a = e.target && e.target.closest && e.target.closest('a[target="_blank"]');
    if (a) {
        e.preventDefault();
        if (a.href) window.location.href = a.href;
    }
}, true);