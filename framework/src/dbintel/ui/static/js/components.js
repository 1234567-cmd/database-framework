// Shared interface pieces. All text is placed through h(), which creates text nodes.
import { h, mount, clear, fmtNumber, titleCase } from "./dom.js";

export const SEVERITY_LABELS = { critical: "Critical", high: "High", medium: "Medium", low: "Low", informational: "Informational" };
export const KIND_LABELS = { confirmed_defect: "Confirmed defect", context_dependent: "Context dependent", optional_improvement: "Optional improvement" };

export function sevBadge(severity) {
  return h("span", { class: `badge sev-${severity}` }, h("span", { class: "dot" }), SEVERITY_LABELS[severity] || severity);
}
export function kindBadge(kind) {
  const cls = kind === "confirmed_defect" ? "badge-bad" : kind === "context_dependent" ? "badge-warn" : "badge-outline";
  return h("span", { class: `badge ${cls}` }, KIND_LABELS[kind] || titleCase(kind));
}
export function flagBadge(text, tone = "") { return h("span", { class: `badge ${tone ? "badge-" + tone : ""}` }, text); }

export function statusBadge(status) {
  const tone = status === "passed" ? "good" : status === "failed" ? "bad" : status === "partial" ? "warn" : "outline";
  const label = { passed: "Passed", failed: "Failed", not_testable: "Not testable", partial: "Partly tested" }[status] || status;
  return h("span", { class: `badge badge-${tone}` }, label);
}

export function skeleton(rows = 5) {
  return h("div", { class: "stack", "aria-busy": "true", "aria-label": "Loading" },
    Array.from({ length: rows }, () => h("div", { class: "skeleton" })));
}

export function emptyState(title, message, action) {
  return h("div", { class: "state" }, h("h3", {}, title), message ? h("p", {}, message) : null, action || null);
}

export function errorState(err, retry) {
  const message = err && err.message ? err.message : "Something went wrong.";
  return h("div", { class: "state", role: "alert" }, h("h3", {}, "This could not be loaded"), h("p", {}, message),
    retry ? h("button", { class: "btn", onClick: retry }, "Try again") : null);
}

export function notice(content, tone = "") { return h("div", { class: `notice ${tone ? "notice-" + tone : ""}`, role: tone === "bad" ? "alert" : null }, content); }

export function toast(message) {
  const host = document.getElementById("toasts");
  const node = h("div", { class: "toast" }, message);
  host.appendChild(node);
  setTimeout(() => node.remove(), 2600);
}

export function copyButton(text, label = "Copy") {
  const button = h("button", { class: "btn btn-small copy", type: "button", onClick: async () => {
    const value = typeof text === "function" ? text() : text;
    try {
      if (navigator.clipboard && window.isSecureContext !== false) await navigator.clipboard.writeText(value);
      else {
        const area = h("textarea", { value }); document.body.appendChild(area); area.select(); document.execCommand("copy"); area.remove();
      }
      toast("Copied");
    } catch (err) { toast("Copy failed. Select the text instead."); }
  } }, label);
  return button;
}

export function codeBlock(text, opts = {}) {
  const content = text && String(text).trim() ? String(text) : (opts.placeholder || "(none)");
  return h("div", { class: "code-block" }, h("pre", { class: "code", tabindex: "0" }, content), text ? copyButton(content, opts.copyLabel || "Copy") : null);
}

export function kv(pairs) {
  return h("dl", { class: "kv" }, pairs.filter(Boolean).map(([key, value]) => [h("dt", {}, key), h("dd", {}, value == null || value === "" ? "(none)" : value)]));
}

export function bullets(items) {
  return items && items.length ? h("ul", {}, items.map((item) => h("li", {}, typeof item === "object" && !item.nodeType ? objectText(item) : item))) : h("p", { class: "muted" }, "None.");
}

export function objectText(item) {
  return Object.entries(item).filter(([, v]) => v !== null && v !== "" && !(Array.isArray(v) && !v.length)).map(([k, v]) => `${titleCase(k)}: ${Array.isArray(v) ? v.join(", ") : v}`).join("; ");
}

export function tile(label, value) { return h("div", { class: "tile" }, h("div", { class: "tile-value" }, value), h("div", { class: "tile-label" }, label)); }

export function pager(state, onChange) {
  const { page, pages, total, size } = state;
  const first = total ? (page - 1) * size + 1 : 0;
  const last = Math.min(total, page * size);
  return h("div", { class: "pager" },
    h("span", { class: "muted" }, `${fmtNumber(first)} to ${fmtNumber(last)} of ${fmtNumber(total)}`),
    h("div", { class: "row" },
      h("button", { class: "btn btn-small", disabled: page <= 1, onClick: () => onChange(page - 1) }, "Previous"),
      h("span", { class: "small muted" }, `Page ${page} of ${pages}`),
      h("button", { class: "btn btn-small", disabled: page >= pages, onClick: () => onChange(page + 1) }, "Next")));
}

// columns: [{key, label, sortKey, render, class, num}]
export function dataTable(columns, rows, opts = {}) {
  const { sort, order, onSort, onRow, rowKey, emptyMessage } = opts;
  if (!rows.length) return emptyState(emptyMessage || "Nothing to show", opts.emptyHint || "Try clearing a filter or changing the search.");
  const headerCell = (col) => {
    const active = col.sortKey && sort === col.sortKey;
    const content = col.sortKey && onSort
      ? h("button", { class: "sort-btn", onClick: () => onSort(col.sortKey) }, col.label, h("span", { class: "arrow", "aria-hidden": "true" }, active ? (order === "desc" ? "▼" : "▲") : ""))
      : col.label;
    return h("th", { scope: "col", class: col.num ? "num" : "", "aria-sort": active ? (order === "desc" ? "descending" : "ascending") : null }, content);
  };
  return h("div", { class: "table-wrap" }, h("table", { class: "data" },
    h("thead", {}, h("tr", {}, columns.map(headerCell))),
    h("tbody", {}, rows.map((row) => {
      const tr = h("tr", { class: onRow ? "clickable" : "", tabindex: onRow ? "0" : null, "data-key": rowKey ? rowKey(row) : null,
        onClick: onRow ? (e) => { if (!e.target.closest("button,a")) onRow(row); } : null,
        onKeydown: onRow ? (e) => { if (e.key === "Enter") { e.preventDefault(); onRow(row); } } : null },
      columns.map((col) => h("td", { class: `${col.num ? "num " : ""}${col.class || ""}` }, col.render ? col.render(row) : row[col.key])));
      return tr;
    }))));
}

export function chip(label, count, pressed, onClick) {
  return h("button", { class: "chip", "aria-pressed": pressed ? "true" : "false", onClick }, label, count !== undefined ? h("span", { class: "count" }, fmtNumber(count)) : null);
}

export function selectField(id, label, options, value, onChange, opts = {}) {
  const select = h("select", { id, onChange: (e) => onChange(e.target.value) },
    (opts.includeAny ? [["", opts.anyLabel || "Any"]] : []).concat(options).map(([v, text]) => h("option", { value: v, selected: v === value }, text)));
  return h("label", { class: "field", for: id }, label, select);
}

export function openDrawer(content, onClose) {
  const root = document.getElementById("drawer-root");
  const lastFocus = document.activeElement;
  const close = () => {
    document.removeEventListener("keydown", onKey);
    clear(root);
    if (lastFocus && lastFocus.focus) lastFocus.focus();
    if (onClose) onClose();
  };
  const onKey = (e) => { if (e.key === "Escape") close(); else if (e.key === "Tab") trapFocus(e, panel); };
  const closeBtn = h("button", { class: "btn btn-small", onClick: close }, "Close");
  const body = h("div", { class: "drawer-body" });
  const panel = h("div", { class: "drawer", role: "dialog", "aria-modal": "true", tabindex: "-1" },
    h("div", { class: "drawer-head" }, content.head || h("div", {}), closeBtn), body);
  mount(root, h("div", { class: "drawer-scrim", onClick: close }), panel);
  document.addEventListener("keydown", onKey);
  panel.focus();
  return { body, close, panel };
}

function trapFocus(e, panel) {
  const items = panel.querySelectorAll("a[href],button:not([disabled]),input,select,textarea,[tabindex='0']");
  if (!items.length) return;
  const first = items[0];
  const last = items[items.length - 1];
  if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
  else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
}

export function confirmDialog({ title, message, confirmLabel = "Confirm", danger = false }) {
  return new Promise((resolve) => {
    const root = document.getElementById("modal-root");
    const lastFocus = document.activeElement;
    const finish = (value) => { document.removeEventListener("keydown", onKey); clear(root); if (lastFocus && lastFocus.focus) lastFocus.focus(); resolve(value); };
    const onKey = (e) => { if (e.key === "Escape") finish(false); };
    const confirmBtn = h("button", { class: `btn ${danger ? "btn-danger" : "btn-primary"}`, onClick: () => finish(true) }, confirmLabel);
    mount(root, h("div", { class: "modal-scrim", onClick: () => finish(false) }),
      h("div", { class: "modal", role: "alertdialog", "aria-modal": "true" }, h("h3", {}, title), h("p", {}, message),
        h("div", { class: "row" }, confirmBtn, h("button", { class: "btn", onClick: () => finish(false) }, "Cancel"))));
    document.addEventListener("keydown", onKey);
    confirmBtn.focus();
  });
}

export function menuButton(label, items) {
  const wrap = h("div", { class: "menu" });
  let open = false;
  const list = h("div", { class: "menu-list", hidden: true });
  const toggle = (next) => {
    open = next;
    list.hidden = !open;
    button.setAttribute("aria-expanded", open ? "true" : "false");
    if (open) document.addEventListener("click", onOutside, true);
    else document.removeEventListener("click", onOutside, true);
  };
  const onOutside = (e) => { if (!wrap.contains(e.target)) toggle(false); };
  const button = h("button", { class: "btn", "aria-haspopup": "true", "aria-expanded": "false", onClick: () => toggle(!open) }, label);
  items.forEach((item) => list.appendChild(item.note ? h("div", { class: "menu-note" }, item.note)
    : h("button", { onClick: () => { toggle(false); item.action(); } }, item.label)));
  wrap.append(button, list);
  return wrap;
}

export function linkRow(href, content) { return h("a", { href }, content); }
export function setBar(el, pct) { el.style.setProperty("width", `${Math.max(0, Math.min(100, pct))}%`); return el; }
