// preview.js - launch build in iframe
document.addEventListener('DOMContentLoaded', () => {
    const pathInput = document.getElementById('previewHtmlPath');
    const frame = document.getElementById('previewFrame');
    const container = document.getElementById('previewContainer');
    if (!pathInput || !frame || !container) return;

    window.addEventListener('message', (e) => {
        const d = e.data;
        if (!d || d.type !== 'pck-timing') return;
        console.log([
            '[pck-timing] total: ' + (d.elapsed || 0).toFixed(2) + 's | '
            + 'load: ' + (d.fetch || 0).toFixed(2) + 's | '
            + 'decompress: ' + (d.decompress || 0).toFixed(2) + 's | '
            + 'decompressions: ' + (d.decompressCount || 0) + ' | '
            + (d.active === false ? 'LOADING FINISHED' : '...')
        ]);
        if (d.active === false) { console.log('[pck-timing] Final load values:', d); }
    });

    function startPreview() {
        const path = pathInput.value.trim();
        if (!path) { window.showToast?.('error', window.i18n?.t('preview_no_folder') || 'preview_no_folder'); return; }
        frame.src = '/preview/start?path=' + encodeURIComponent(path);
        container.classList.add('running');
    }
    document.getElementById('previewStartBtn').addEventListener('click', startPreview);
    document.getElementById('previewRestartBtn').addEventListener('click', startPreview);
    document.getElementById('previewStopBtn').addEventListener('click', () => {
        frame.src = 'about:blank';
        container.classList.remove('running');
        setMuted(false);
    });

    const muteBtn = document.getElementById('previewMuteBtn');
    const muteIcon = document.getElementById('previewMuteIcon');
    let muted = false;
    function setMuted(value) {
        muted = value;
        muteIcon.className = muted ? 'fas fa-volume-xmark' : 'fas fa-volume-high';
        const key = muted ? 'preview_unmute' : 'preview_mute';
        muteBtn.title = window.i18n?.t(key) || muteBtn.title;
        try { frame.contentWindow?.setGameMuted?.(muted); } catch (e) { console.error('Cannot toggle sound:', e); }
    }
    muteBtn.addEventListener('click', () => setMuted(!muted));

    document.querySelectorAll('.preview-controls .icon-btn[data-title-key]').forEach(btn => {
        const text = window.i18n?.t(btn.dataset.titleKey);
        if (text) btn.title = text;
    });

    document.getElementById('previewSelectFileBtn').addEventListener('click', async () => {
        try {
            const response = await fetch('/api/select-file?filter=html');
            const data = await response.json();
            if (data.path) {
                pathInput.value = data.path;
                localStorage.setItem('app:previewHtmlPath', data.path);
                startPreview();
            }
        } catch (e) { console.error('File select error:', e); }
    });
});
