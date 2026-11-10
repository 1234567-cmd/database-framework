// History of saved runs and comparison of two runs by stable finding ID.
import { h, mount, fmtNumber, fmtPct, titleCase } from "../dom.js";
import { api } from "../api.js";
import { navigate, routeHref } from "../router.js";
import { confirmDialog, dataTable, emptyState, errorState, kindBadge, notice, selectField, sevBadge, skeleton, tile, toast } from "../components.js";

export function mountView(ctx) { return ctx.section === "compare" ? compareView(ctx) : historyView(ctx); }

function historyView(ctx) {
  const root = ctx.root;
  const selected = new Set();
  let runs = [];

  async function load() {
    mount(root, skeleton(8));
    try {
      const data = await api("/runs");
      runs = data.runs;
      render();
    } catch (err) { mount(root, errorState(err, load)); }
  }

  function toggle(id, on) { if (on) selected.add(id); else selected.delete(id); renderCompareBar(); }

  let compareBar = h("div", {});
  function renderCompareBar() {
    const ids = [...selected];
    mount(compareBar, h("div", { class: "row no-print" },
      h("button", { class: "btn", disabled: ids.length !== 2, onClick: () => navigate(["compare"], { a: ids[0], b: ids[1] }) }, "Compare selected"),
      h("span", { class: "small muted" }, ids.length === 2 ? "Two runs selected." : "Select exactly two runs to compare.")));
  }

  function render() {
    mount(root, h("div", { class: "page-head" }, h("div", {}, h("h1", {}, "History"), h("p", {}, "Runs saved on this computer. Open one without re-running it, or compare two."))), compareBar,
      runs.length ? h("div", { class: "section" }, dataTable([
        { label: "", render: (r) => h("input", { type: "checkbox", "aria-label": `Select run ${r.id}`, checked: selected.has(r.id), onClick: (e) => e.stopPropagation(), onChange: (e) => toggle(r.id, e.target.checked) }) },
        { label: "Database", render: (r) => h("a", { href: routeHref(["run", r.id, "dashboard"]) }, r.name || r.id) },
        { label: "Source", render: (r) => h("span", { class: "small muted" }, r.source_label || "—") },
        { label: "Generated", render: (r) => h("span", { class: "nowrap small" }, r.generated_at || "—") },
        { label: "Score", num: true, render: (r) => (r.overall === null || r.overall === undefined ? "n/a" : fmtNumber(r.overall)) },
        { label: "Grade", render: (r) => r.grade || "—" },
        { label: "Confidence", num: true, render: (r) => fmtPct(r.confidence) },
        { label: "Findings", num: true, render: (r) => fmtNumber(r.findings_total) },
        { label: "Critical", num: true, render: (r) => fmtNumber(r.critical) },
        { label: "Tables", num: true, render: (r) => fmtNumber(r.tables) },
        { label: "", render: (r) => h("button", { class: "btn btn-small btn-danger", "aria-label": `Delete run ${r.id}`, onClick: () => remove(r) }, "Delete") },
      ], runs, { rowKey: (r) => r.id })) : emptyState("No saved runs yet", "Run an analysis and it will appear here.", h("a", { class: "btn btn-primary", href: "#/import" }, "New analysis")));
    renderCompareBar();
  }

  async function remove(run) {
    const ok = await confirmDialog({ title: "Delete this run?", message: `Its saved reports for ${run.name || run.id} are removed from this computer. This does not touch any database.`, confirmLabel: "Delete run", danger: true });
    if (!ok) return;
    try {
      await api(`/runs/${encodeURIComponent(run.id)}`, { method: "DELETE" });
      selected.delete(run.id);
      toast("Run deleted");
      load();
    } catch (err) { toast(err.message); }
  }

  load();
  return {};
}

function compareView(ctx) {
  const root = ctx.root;
  const { a, b } = ctx.query;
  async function load() {
    mount(root, skeleton(10));
    try {
      const { runs } = await api("/runs");
      if (!a || !b) { renderPicker(runs); return; }
      const data = await api(`/compare?a=${encodeURIComponent(a)}&b=${encodeURIComponent(b)}`);
      renderCompare(data);
    } catch (err) { mount(root, err.status === 404 ? emptyState("A run could not be found", err.message, h("a", { class: "btn", href: "#/history" }, "Go to history")) : errorState(err, load)); }
  }

  function renderPicker(runs) {
    if (runs.length < 2) { mount(root, emptyState("Two runs are needed to compare", "Run another analysis, then come back.", h("a", { class: "btn", href: "#/history" }, "Go to history"))); return; }
    let first = runs[1].id; let second = runs[0].id;
    const options = runs.map((r) => [r.id, `${r.name || r.id} · ${r.generated_at || ""}`]);
    mount(root, h("div", { class: "page-head" }, h("div", {}, h("h1", {}, "Compare runs"))),
      h("div", { class: "card stack" }, h("div", { class: "grid grid-2" }, selectField("cmp-a", "Baseline", options, first, (v) => { first = v; }), selectField("cmp-b", "Compare with", options, second, (v) => { second = v; })),
        h("div", {}, h("button", { class: "btn btn-primary", onClick: () => navigate(["compare"], { a: first, b: second }) }, "Compare"))));
  }

  function findingList(rows, total, emptyText, limit) {
    if (!rows.length) return h("p", { class: "muted" }, emptyText);
    return h("div", {}, dataTable([{ label: "Severity", render: (f) => sevBadge(f.severity) }, { label: "Finding", class: "title-cell", render: (f) => f.title }, { label: "Kind", render: (f) => kindBadge(f.kind) }, { label: "Table", render: (f) => h("span", { class: "mono small" }, f.table || "—") }, { label: "ID", render: (f) => h("span", { class: "mono small" }, f.id) }], rows),
      total > limit ? h("p", { class: "small muted" }, `Showing the first ${limit} of ${fmtNumber(total)}.`) : null);
  }

  function renderCompare(d) {
    const delta = d.overall_delta;
    const deltaText = delta === null ? "Not comparable" : `${delta > 0 ? "+" : ""}${delta}`;
    mount(root, h("div", { class: "page-head" }, h("div", {}, h("h1", {}, "Compare runs"), h("p", {}, `Baseline ${d.a.name} (${d.a.generated_at}) against ${d.b.name} (${d.b.generated_at}).`)), h("a", { class: "btn", href: "#/history" }, "Back to history")),
      h("div", { class: "tiles" }, tile("Score change", deltaText), tile("Baseline score", d.a.overall === null ? "n/a" : fmtNumber(d.a.overall)), tile("New score", d.b.overall === null ? "n/a" : fmtNumber(d.b.overall)), tile("New findings", fmtNumber(d.new_count)), tile("Resolved", fmtNumber(d.resolved_count)), tile("Changed severity or kind", fmtNumber(d.changed_count)), tile("Unchanged", fmtNumber(d.unchanged_count))),
      d.a.name !== d.b.name ? notice("These runs are for databases with different names, so differences may not mean change over time.", "warn") : null,
      h("div", { class: "section" }, h("h2", {}, "Categories"), dataTable([{ label: "Category", render: (c) => titleCase(c.category) }, { label: "Baseline", num: true, render: (c) => (c.before === null || c.before === undefined ? "not assessed" : fmtNumber(c.before)) }, { label: "New", num: true, render: (c) => (c.after === null || c.after === undefined ? "not assessed" : fmtNumber(c.after)) }, { label: "Change", num: true, render: (c) => (c.delta === null ? "—" : `${c.delta > 0 ? "+" : ""}${c.delta}`) }], d.category_changes)),
      h("div", { class: "section" }, h("h2", {}, `New findings (${fmtNumber(d.new_count)})`), findingList(d.new, d.new_count, "No new findings.", d.list_limit)),
      h("div", { class: "section" }, h("h2", {}, `Resolved findings (${fmtNumber(d.resolved_count)})`), findingList(d.resolved, d.resolved_count, "No findings resolved.", d.list_limit)),
      h("div", { class: "section" }, h("h2", {}, `Severity or kind changed (${fmtNumber(d.changed_count)})`), d.changed.length ? dataTable([{ label: "Finding", class: "title-cell", render: (c) => c.title }, { label: "Before", render: (c) => `${c.before.severity}, ${c.before.kind}` }, { label: "After", render: (c) => `${c.after.severity}, ${c.after.kind}` }, { label: "ID", render: (c) => h("span", { class: "mono small" }, c.id) }], d.changed) : h("p", { class: "muted" }, "None.")));
  }

  load();
  return {};
}
