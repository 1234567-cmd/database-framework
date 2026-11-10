// Calls the local API with the per-launch session token. The token comes from the launch URL fragment and is never sent as a URL parameter.
const STORAGE_KEY = "dbintel.session";
const TOKEN_HEADER = "X-DBIntel-Token";
let token = null;

export class ApiError extends Error {
  constructor(status, code, message, field) {
    super(message);
    this.status = status;
    this.code = code;
    this.field = field;
  }
}

export function loadToken() {
  const hash = window.location.hash || "";
  const match = hash.match(/^#token=([A-Za-z0-9_-]+)/);
  if (match) {
    token = match[1];
    try { window.localStorage.setItem(STORAGE_KEY, token); } catch (err) { /* storage can be blocked; the token stays in memory */ }
    window.history.replaceState(null, "", window.location.pathname + "#/");
    return token;
  }
  try { token = window.localStorage.getItem(STORAGE_KEY); } catch (err) { token = null; }
  return token;
}

export function setToken(value) {
  token = value;
  try { window.localStorage.setItem(STORAGE_KEY, value); } catch (err) { /* see above */ }
}
export function getToken() { return token; }

function headers(extra) { return { [TOKEN_HEADER]: token || "", ...(extra || {}) }; }

async function parseError(res) {
  let payload = {};
  try { payload = await res.json(); } catch (err) { /* non-JSON error body */ }
  return new ApiError(res.status, payload.code || "error", payload.error || `The request failed (${res.status}).`, payload.field);
}

export async function api(path, options = {}) {
  const { method = "GET", body, signal } = options;
  let res;
  try {
    res = await fetch(`/api${path}`, {
      method, signal, headers: headers(body !== undefined ? { "Content-Type": "application/json" } : {}),
      body: body !== undefined ? JSON.stringify(body) : undefined, credentials: "same-origin",
    });
  } catch (err) {
    if (err.name === "AbortError") throw err;
    throw new ApiError(0, "offline", "The local dbintel server cannot be reached. Is it still running?");
  }
  if (!res.ok) throw await parseError(res);
  return res.json();
}

export function uploadFile(slot, file, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `/api/uploads?slot=${encodeURIComponent(slot)}`);
    xhr.setRequestHeader(TOKEN_HEADER, token || "");
    xhr.setRequestHeader("X-Filename", encodeURIComponent(file.name));
    xhr.upload.onprogress = (e) => { if (e.lengthComputable && onProgress) onProgress(e.loaded, e.total); };
    xhr.onerror = () => reject(new ApiError(0, "offline", "The upload was interrupted. Is the server still running?"));
    xhr.onload = () => {
      let payload = {};
      try { payload = JSON.parse(xhr.responseText || "{}"); } catch (err) { /* ignored */ }
      if (xhr.status >= 200 && xhr.status < 300) resolve(payload);
      else reject(new ApiError(xhr.status, payload.code || "error", payload.error || `The upload failed (${xhr.status}).`, payload.field));
    };
    xhr.send(file);
  });
}

export async function download(path, filename) {
  const res = await fetch(`/api${path}`, { headers: headers() }).catch(() => {
    throw new ApiError(0, "offline", "The local dbintel server cannot be reached.");
  });
  if (!res.ok) throw await parseError(res);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}
