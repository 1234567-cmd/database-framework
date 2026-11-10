// Application shell: session, navigation, routing and the shared job watcher.
import { h, mount, fmtDuration } from "./dom.js";
import { api, ApiError, download, getToken, loadToken, setToken } from "./api.js";
import { parseHash, routeHref, navigate } from "./router.js";
import { emptyState, errorState, menuButton, skeleton, toast } from "./components.js";
import * as importView from "./views/import.js";
import * as dashboard from "./views/dashboard.js";
import * as findings from "./views/findings.js";
import * as tables from "./views/tables.js";
import * as er from "./views/er.js";
import * as recommendations from "./views/recommendations.js";
import * as migration from "./views/migration.js";
import * as reference from "./views/reference.js";
import * as history from "./views/history.js";

const RUN_VIEWS = {
  dashboard: { label: "Dashboard", module: dashboard },
  findings: { label: "Findings", module: findings },
  tables: { label: "Tables", module: tables },
  er: { label: "ER diagram", module: er },
  recommendations: { label: "Recommendations", module: recommendations },
  migration: { label: "Migration review", module: migration },
  roadmap: { label: "Roadmap", module: reference },
  lineage: { label: "Lineage", module: reference },
  architecture: { label: "Architecture", module: reference },
  coverage: { label: "Coverage", module: reference },
  limitations: { label: "Limitations", module: reference },
  print: { label: "Print view", module: reference },
};
const NAV_RUN_ORDER = ["dashboard", "findings", "tables", "er", "recommendations", "migration", "roadmap", "lineage", "architecture", "coverage", "limitations"];

const state = { view: null, viewKey: null, viewCtx: null, runId: null, run: null, lastRunId: null };
const jobListeners = new Set();
let jobSnapshot = { state: "idle" };
let jobTimer = null;
let els = null;

// --- jobs -----------------------------------------------------------------

export const jobs = {
  current: () => jobSnapshot,
  subscribe(fn) { jobListeners.add(fn); return () => jobListeners.delete(fn); },
  async refresh() {
    try {
      jobSnapshot = await api("/analysis/current");
    } catch (err) { return; }
    jobListeners.forEach((fn) => fn(jobSnapshot));
    renderBusyPill();
    const active = ["starting", "running", "cancelling"].includes(jobSnapshot.state);
    if (active && !jobTimer) jobTimer = setInterval(jobs.refresh, 1000);
    if (!active && jobTimer) { clearInterval(jobTimer); jobTimer = null; }
  },
};

function renderBusyPill() {
  if (!els) return;
  const active = ["starting", "running", "cancelling"].includes(jobSnapshot.state);
  mount(els.busy, active ? h("a", { class: "busy-pill", href: "#/import" }, jobSnapshot.kind === "sandbox" ? "Sandbox test running" : "Analysis running", ` · ${fmtDuration(jobSnapshot.elapsed)}`) : null);
}

// --- theme ----------------------------------------------------------------

function storedTheme() { try { return window.localStorage.getItem("dbintel.theme") || "system"; } catch (err) { return "system"; } }
function applyTheme(value) {
  if (value === "system") document.documentElement.removeAttribute("data-theme"); else document.documentElement.setAttribute("data-theme", value);
  try { window.localStorage.setItem("dbintel.theme", value); } catch (err) { /* per-viewer convenience only */ }
}
function themeControl() {
  const select = h("select", { "aria-label": "Theme", onChange: (e) => applyTheme(e.target.value) },
    [["system", "Theme: system"], ["light", "Theme: light"], ["dark", "Theme: dark"]].map(([v, t]) => h("option", { value: v, selected: storedTheme() === v }, t)));
  return select;
}

// --- shell ----------------------------------------------------------------

function buildShell() {
  const nav = h("nav", { "aria-label": "Main" });
  const busy = h("div", {});
  const sidebar = h("aside", { class: "sidebar" },
    h("a", { class: "brand", href: "#/import" }, h("span", { class: "brand-mark", "aria-hidden": "true" }, "db"), "dbintel"),
    nav,
    h("div", { class: "sidebar-foot" }, busy, themeControl(), h("div", { class: "small muted" }, "Runs on this computer only")));
  const topbar = h("header", { class: "topbar" });
  const content = h("main", { id: "main", class: "content", tabindex: "-1" });
  mount(document.getElementById("app"), sidebar, h("div", { class: "main" }, topbar, content));
  els = { nav, topbar, content, busy };
}

function navLink(label, href, current, disabled) {
  return h("a", { class: `nav-link${disabled ? " disabled" : ""}`, href: disabled ? "#/import" : href, "aria-current": current ? "page" : null, tabindex: disabled ? "-1" : null }, label);
}

function renderNav(route) {
  const [first, runId, section] = route.segments;
  const active = first === "run" ? section || "dashboard" : first || "import";
  const id = state.runId || state.lastRunId;
  const runLinks = NAV_RUN_ORDER.map((key) => navLink(RUN_VIEWS[key].label, id ? routeHref(["run", id, key]) : "#/import", first === "run" && active === key, !id));
  mount(els.nav,
    h("div", { class: "nav-group" }, navLink("New analysis", "#/import", active === "import"), navLink("History", "#/history", active === "history" || active === "compare")),
    h("div", { class: "nav-group" }, h("div", { class: "nav-title" }, id ? "This run" : "This run (open one first)"), runLinks));
}

function renderTopbar(route) {
  const [first] = route.segments;
  const run = first === "run" ? state.run : null;
  if (!run) {
    mount(els.topbar, h("div", {}, h("div", { class: "topbar-title" }, first === "history" || first === "compare" ? "Runs" : "New analysis")));
    return;
  }
  const name = (run.source && run.source.name) || "Database";
  const id = run.id;
  const exportMenu = menuButton("Export", [
    { label: "HTML report", action: () => runExport(id, "html", "html") },
    { label: "Markdown report", action: () => runExport(id, "md", "md") },
    { label: "JSON report", action: () => runExport(id, "json", "json") },
    { label: "Print or save as PDF", action: () => navigate(["run", id, "print"]) },
    { note: "PDF is produced through your browser's print dialog." },
  ]);
  mount(els.topbar,
    h("div", {}, h("div", { class: "topbar-title" }, name), h("div", { class: "topbar-sub" }, `${(run.source && run.source.dialect) || ""} · ${run.generated_at || ""}`)),
    h("div", { class: "topbar-spacer" }), exportMenu);
}

async function runExport(id, fmt, ext) {
  try { await download(`/runs/${encodeURIComponent(id)}/export/${fmt}`, `dbintel_report.${ext}`); toast("Download started"); } catch (err) { toast(err.message); }
}

function sessionScreen(message) {
  const input = h("input", { type: "password", id: "token-input", autocomplete: "off" });
  mount(document.getElementById("app"), h("div", { class: "content" }, h("div", { class: "card stack" },
    h("h2", {}, "Open dbintel from its launch link"),
    h("p", {}, message || "This page needs the session link printed when dbintel started. Close this tab and use ui.bat, or paste the session token from that link below."),
    h("label", { class: "field", for: "token-input" }, "Session token", input),
    h("div", {}, h("button", { class: "btn btn-primary", onClick: () => { setToken(input.value.trim()); start(); } }, "Open")))));
}

// --- routing --------------------------------------------------------------

function viewFor(route) {
  const [first, runId, section, detail] = route.segments;
  if (first === "run" && runId) {
    const key = section || "dashboard";
    if (RUN_VIEWS[key]) return { key: `run:${runId}:${key}:${detail || ""}`, module: RUN_VIEWS[key].module, section: key, runId };
    return null;
  }
  if (first === "history" || first === "compare") return { key: first, module: history, section: first };
  return { key: "import", module: importView, section: "import" };
}

function makeCtx(route, target) {
  return { root: els.content, segments: route.segments, query: route.query, section: target.section, runId: target.runId || null, run: state.run,
    jobs, go: (query) => navigate(route.segments, query) };
}

async function ensureRun(runId) {
  if (state.run && state.run.id === runId) return true;
  state.run = null;
  state.runId = runId;
  mount(els.content, skeleton(8));
  try {
    state.run = await api(`/runs/${encodeURIComponent(runId)}`);
    state.lastRunId = runId;
    return true;
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) { sessionScreen(); return false; }
    mount(els.content, err.status === 404
      ? emptyState("That run does not exist", "It may have been deleted. Open another run from History.", h("a", { class: "btn", href: "#/history" }, "Go to history"))
      : errorState(err, () => dispatch()));
    return false;
  }
}

function destroyView() {
  if (state.view && state.view.destroy) state.view.destroy();
  state.view = null;
  state.viewKey = null;
}

async function dispatch() {
  const route = parseHash(window.location.hash);
  const target = viewFor(route);
  if (!target) { destroyView(); mount(els.content, emptyState("Page not found", "Choose a section from the menu.")); return; }
  renderNav(route);
  if (state.viewKey === target.key && state.view && state.view.update) {
    state.viewCtx.query = route.query;
    state.viewCtx.segments = route.segments;
    state.viewCtx.go = (query) => navigate(route.segments, query);
    state.view.update(route.query);
    return;
  }
  destroyView();
  if (target.runId) {
    const ok = await ensureRun(target.runId);
    if (!ok) { renderNav(route); renderTopbar(route); return; }
    renderNav(route);
  } else {
    state.runId = null;
    state.run = null;
  }
  renderTopbar(route);
  const ctx = makeCtx(route, target);
  mount(els.content);
  state.viewKey = target.key;
  state.viewCtx = ctx;
  state.view = target.module.mountView(ctx) || null;
  els.content.focus();
  window.scrollTo(0, 0);
}

async function start() {
  try {
    await api("/meta");
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) { sessionScreen(); return; }
    mount(document.getElementById("app"), h("div", { class: "content" }, errorState(err, start)));
    return;
  }
  buildShell();
  window.addEventListener("hashchange", dispatch);
  await jobs.refresh();
  try {
    const { runs } = await api("/runs");
    state.lastRunId = runs.length ? runs[0].id : null;
  } catch (err) { /* the import screen shows errors */ }
  if (!window.location.hash || window.location.hash === "#/") window.location.replace("#/import");
  dispatch();
}

applyTheme(storedTheme());
loadToken();
if (!getToken()) sessionScreen(); else start();
