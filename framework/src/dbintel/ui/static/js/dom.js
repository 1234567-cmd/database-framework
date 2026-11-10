// DOM construction. Every string becomes a text node, so database content can never become markup.
const SVG_NS = "http://www.w3.org/2000/svg";

// Only in-page links and same-origin paths are allowed; anything else, such as javascript:, is neutralized.
export function safeHref(url) {
  const text = String(url == null ? "" : url);
  return text.startsWith("#") || (text.startsWith("/") && !text.startsWith("//")) ? text : "#";
}

function apply(el, props, children) {
  for (const [key, value] of Object.entries(props || {})) {
    if (value === undefined || value === null || value === false) continue;
    if (key === "class") el.setAttribute("class", value);
    else if (key === "text") el.textContent = String(value);
    else if (key === "style") throw new Error("Inline style is not allowed; use classes or setCssVar.");
    else if (key === "href") el.setAttribute("href", safeHref(value));
    else if (key.startsWith("on") && typeof value === "function") el.addEventListener(key.slice(2).toLowerCase(), value);
    else if (key === "value" || key === "checked" || key === "disabled" || key === "selected" || key === "open") el[key] = value;
    else el.setAttribute(key, value === true ? "" : String(value));
  }
  for (const child of children.flat(Infinity)) {
    if (child === undefined || child === null || child === false) continue;
    el.appendChild(child.nodeType ? child : document.createTextNode(String(child)));
  }
  return el;
}

export function h(tag, props, ...children) { return apply(document.createElement(tag), props, children); }
export function s(tag, props, ...children) { return apply(document.createElementNS(SVG_NS, tag), props, children); }

export function clear(el) { while (el.firstChild) el.removeChild(el.firstChild); return el; }
export function mount(el, ...children) { clear(el); children.flat(Infinity).forEach((c) => c && el.appendChild(c.nodeType ? c : document.createTextNode(String(c)))); return el; }

export function fmtNumber(n) { return n === null || n === undefined ? "—" : Number(n).toLocaleString("en-US"); }
export function fmtPct(n) { return n === null || n === undefined ? "—" : `${Math.round(Number(n) * 100)}%`; }
export function fmtBytes(n) {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  if (n < 1024 * 1024 * 1024) return `${(n / (1024 * 1024)).toFixed(1)} MB`;
  return `${(n / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}
export function fmtDuration(seconds) {
  const total = Math.max(0, Math.round(Number(seconds) || 0));
  const m = Math.floor(total / 60);
  const sec = total % 60;
  return m ? `${m}m ${String(sec).padStart(2, "0")}s` : `${sec}s`;
}
export function titleCase(text) {
  return String(text || "").replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}
