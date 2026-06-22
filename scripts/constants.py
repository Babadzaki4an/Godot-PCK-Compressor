# constants.py
# Содержит строки для замены в JavaScript и словарь замен

ORIG_LOADFETCH = """function loadFetch(file, tracker, fileSize, raw) {
\t\ttracker[file] = {
\t\t\ttotal: fileSize || 0,
\t\t\tloaded: 0,
\t\t\tdone: false,
\t\t};
\t\treturn fetch(file).then(function (response) {
\t\t\tif (!response.ok) {
\t\t\t\treturn Promise.reject(new Error(`Failed loading file '${file}'`));
\t\t\t}
\t\t\tconst tr = getTrackedResponse(response, tracker[file]);
\t\t\tif (raw) {
\t\t\t\treturn Promise.resolve(tr);
\t\t\t}
\t\t\treturn tr.arrayBuffer();
\t\t});
\t}"""

NEW_LOADFETCH = """//changed by autoPCK
function loadFetch(file, tracker, fileSize, raw) {
    var p_file = file;

    tracker[file] = {
        total: fileSize || 0,
        loaded: 0,
        done: false,
    };

    return fetch(file).then(function (response) {
        if (!response.ok) {
            return Promise.reject(new Error(`Failed loading file '${file}'`));
        }

        const tr = getTrackedResponse(response, tracker[p_file]);
        return Promise.resolve(tr.arrayBuffer().then(buffer => {
            return new Response(pako.inflate(buffer), { headers: tr.headers });
        }));
    });
}"""

ORIG_PRELOAD = """\tthis.preload = function (pathOrBuffer, destPath, fileSize) {
\t\tlet buffer = null;
\t\tif (typeof pathOrBuffer === 'string') {
\t\t\tconst me = this;
\t\t\treturn this.loadPromise(pathOrBuffer, fileSize).then(function (buf) {
\t\t\t\tme.preloadedFiles.push({
\t\t\t\t\tpath: destPath || pathOrBuffer,
\t\t\t\t\tbuffer: buf,
\t\t\t\t});
\t\t\t\treturn Promise.resolve();
\t\t\t});
\t\t} else if (pathOrBuffer instanceof ArrayBuffer) {
\t\t\tbuffer = new Uint8Array(pathOrBuffer);
\t\t} else if (ArrayBuffer.isView(pathOrBuffer)) {
\t\t\tbuffer = new Uint8Array(pathOrBuffer.buffer);
\t\t}
\t\tif (buffer) {
\t\t\tthis.preloadedFiles.push({
\t\t\t\tpath: destPath,
\t\t\t\tbuffer: pathOrBuffer,
\t\t\t});
\t\t\treturn Promise.resolve();
\t\t}
\t\treturn Promise.reject(new Error('Invalid object for preloading'));
\t};"""

NEW_PRELOAD = """//changed by autoPCK
this.preload = function (pathOrBuffer, destPath, fileSize) {
    let buffer = null;
    if (typeof pathOrBuffer === 'string') {
        const me = this;
        return this.loadPromise(pathOrBuffer, fileSize).then(function (buf) {
            buf.arrayBuffer().then(data => {
                me.preloadedFiles.push({
                    path: destPath || pathOrBuffer,
                    buffer: data,
                });
            });
            return Promise.resolve();
        });
    } else if (pathOrBuffer instanceof ArrayBuffer) {
        buffer = new Uint8Array(pathOrBuffer);
    } else if (ArrayBuffer.isView(pathOrBuffer)) {
        buffer = new Uint8Array(pathOrBuffer.buffer);
    }
    if (buffer) {
        this.preloadedFiles.push({
            path: destPath,
            buffer: pathOrBuffer,
        });
        return Promise.resolve();
    }
    return Promise.reject(new Error('Invalid object for preloading'));
};"""

FUNCTION_REPLACEMENTS = {ORIG_LOADFETCH: NEW_LOADFETCH, ORIG_PRELOAD: NEW_PRELOAD}