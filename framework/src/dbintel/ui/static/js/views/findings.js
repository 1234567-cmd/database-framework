// Findings explorer: server-side filtering, sorting and paging, with a deep-linkable detail drawer.
import { h, mount, fmtPct, titleCase } from "../dom.js";
import { api } from "../api.js";
import { routeHref } from "../router.js";
import { chip, dataTable, emptyState, errorState, flagBadge, kindBadge, kv, notice, openDrawer, pager, selectField, sevBadge, skeleton } from "../components.js";

const FILTER_KEYS = ["severity", "kind", "category", "rule", "table", "confidence", "provisional", "q", "sort", "order"];

export function mountView(ctx) {
  const root = ctx.root;
  const runPath = `/runs/${encodeURIComponent(ctx.runId)}`;
  let query = { ...ctx.query };
  let lastListKey = null;
  let drawer = null;
  let drawerId = null;
  let requestId = 0;
  let debounce = null;

  const searchInput = h("input", { type: "search", id: "finding-search", placeholder: "Search title, table, evidence, ID",
    onInput: (e) => { clearTimeout(debounce); const value = e.target.value; debounce = setTimeout(() => go({ q: value, page: "" }), 280); } });
  const facetsEl = h("div", { class: "chip-row" });
  const selectsEl = h("div", { class: "filter-grid" });
  const listEl = h("div", {});
  mount(root,
    h("div", { class: "page-head" }, h("div", {}, h("h1", {}, "Findings"), h("p", {}, "Filtered on the server. Confirmed defects come first by default."))),
    h("div", { class: "filters" }, h("label", { class: "field", for: "finding-search" }, "Search", searchInput), facetsEl, selectsEl),
    listEl);

  function go(patch) {
    const next = { ...query, ...patch };
    Object.keys(next).forEach((k) => { if (next[k] === "" || next[k] === undefined || next[k] === null) delete next[k]; });
    ctx.go(next);
  }

  function listKey(q) { return JSON.stringify(FILTER_KEYS.concat("page", "size").map((k) => q[k] || "")); }

  function sync() {
    searchInput.value = query.q || "";
    const key = listKey(query);
    if (key !== lastListKey) { lastListKey = key; loadList(); }
    syncDrawer();
  }

  async function loadList() {
    const id = ++requestId;
    mount(listEl, skeleton(8));
    const params = new URLSearchParams();
    FILTER_KEYS.forEach((k) => { if (query[k]) params.set(k, query[k]); });
    if (query.page) params.set("page", query.page);
    params.set("size", "50");
    try {
      const data = await api(`${runPath}/findings?${params.toString()}`);
      if (id !== requestId) return;
      renderFacets(data);
      renderList(data);
    } catch (err) { if (id === requestId) mount(listEl, errorState(err, loadList)); }
  }

  function toggleFacet(name, value) {
    const current = new Set((query[name] || "").split(",").filter(Boolean));
    if (current.has(value)) current.delete(value); else current.add(value);
    go({ [name]: [...current].join(","), page: "" });
  }

  function renderFacets(data) {
    const facets = data.facets || {};
    const selected = (name) => new Set((query[name] || "").split(",").filter(Boolean));
    const facetChips = (name, order) => order.filter((value) => (facets[name] || {})[value] !== undefined || selected(name).has(value))
      .map((value) => chip(titleCase(value), (facets[name] || {})[value] || 0, selected(name).has(value), () => toggleFacet(name, value)));
    mount(facetsEl, facetChips("severity", ["critical", "high", "medium", "low", "informational"]), facetChips("kind", ["confirmed_defect", "context_dependent", "optional_improvement"]),
      h("button", { class: "chip", "aria-pressed": query.provisional === "1" ? "true" : "false", onClick: () => go({ provisional: query.provisional === "1" ? "" : "1", page: "" }) }, "Provisional standard"));
    const options = (name) => Object.keys(facets[name] || {}).sort().map((v) => [v, `${v} (${facets[name][v]})`]);
    mount(selectsEl,
      selectField("f-category", "Category", options("category").map(([v, t]) => [v, titleCase(t)]), query.category || "", (v) => go({ category: v, page: "" }), { includeAny: true }),
      selectField("f-rule", "Rule", options("rule"), query.rule || "", (v) => go({ rule: v, page: "" }), { includeAny: true }),
      selectField("f-table", "Table", options("table"), query.table || "", (v) => go({ table: v, page: "" }), { includeAny: true }),
      selectField("f-confidence", "Confidence", [["high", "High (0.8 and up)"], ["medium", "Medium (0.5 to 0.8)"], ["low", "Low (under 0.5)"]], query.confidence || "", (v) => go({ confidence: v, page: "" }), { includeAny: true }));
  }

  function renderList(data) {
    const columns = [
      { label: "Severity", sortKey: "severity", render: (f) => sevBadge(f.severity) },
      { label: "Finding", sortKey: "title", class: "title-cell", render: (f) => h("a", { class: "title", href: routeHref(ctx.segments, { ...query, f: f.id }) }, f.title) },
      { label: "Kind", sortKey: "kind", render: (f) => kindBadge(f.kind) },
      { label: "Table", sortKey: "table", render: (f) => h("span", { class: "mono" }, [f.table, f.column].filter(Boolean).join(".") || "—") },
      { label: "Rule", sortKey: "rule", render: (f) => h("span", { class: "mono small nowrap" }, f.rule_id) },
      { label: "Confidence", sortKey: "confidence", num: true, render: (f) => fmtPct(f.confidence) },
    ];
    const defaultNote = data.default_view ? notice("Showing confirmed defects first, then context-dependent items, then optional improvements.", "info") : null;
    mount(listEl, defaultNote, h("div", { class: "section" }, dataTable(columns, data.items, {
      sort: data.applied.sort === "default" ? null : data.applied.sort, order: data.applied.order, rowKey: (f) => f.id,
      onSort: (key) => go({ sort: key, order: data.applied.sort === key && data.applied.order !== "desc" ? "desc" : "", page: "" }),
      onRow: (f) => go({ f: f.id }), emptyMessage: "No findings match", emptyHint: data.total === 0 && Object.values(data.applied).every((v) => !v || v === "default" || v === "asc") ? "This run has no findings." : "Clear a filter or change the search.",
    }), pager(data, (page) => go({ page }))));
  }

  function renderDrawerBody(body, data) {
    const f = data.finding;
    const standards = (f.standards || []).map((sid) => h("div", {}, h("strong", { class: "mono" }, sid), ": ", (f.standard_statements || {})[sid] || ""));
    mount(body, h("div", { class: "stack" },
      kv([["ID", f.id], ["Rule", f.rule_id], ["Severity", sevBadge(f.severity)], ["Kind", kindBadge(f.kind)], ["Category", titleCase(f.category)], ["Database", f.database],
        ["Table", f.table], ["Column", f.column], ["Confidence", fmtPct(f.confidence)], ["Provisional standard", f.provisional_standard ? flagBadge("Provisional", "warn") : "No"], ["Complexity", f.complexity]]),
      section("Evidence", f.evidence), section("Root cause", f.root_cause), section("Business impact", f.business_impact), section("Technical impact", f.technical_impact),
      h("div", {}, h("h4", {}, "Standards"), standards.length ? standards : h("p", { class: "muted" }, "None recorded.")),
      section("Recommended solution", f.recommended_solution), section("Migration requirements", f.migration_requirements), section("Risks", f.risks), section("Validation strategy", f.validation_strategy),
      h("div", {}, h("h4", {}, "Related recommendations"), data.recommendations.length ? data.recommendations.map((r) => h("div", {}, h("a", { href: routeHref(["run", ctx.runId, "recommendations"], { r: r.id }) }, `${r.priority} ${r.title}`))) : h("p", { class: "muted" }, "None.")),
      h("div", {}, h("h4", {}, "Related migration steps"), data.steps.length ? data.steps.map((s) => h("div", {}, h("a", { href: routeHref(["run", ctx.runId, "migration"], { s: s.id }) }, `${s.id}: ${s.title}`), s.manual ? " " : null, s.manual ? flagBadge("Manual") : null)) : h("p", { class: "muted" }, "None."))));
  }

  function section(title, text) { return h("div", {}, h("h4", {}, title), h("p", {}, text || "—")); }

  async function syncDrawer() {
    const id = query.f;
    if (!id) { if (drawer) { const d = drawer; drawer = null; drawerId = null; d.close(); } return; }
    if (id === drawerId) return;
    drawerId = id;
    if (drawer) { const d = drawer; drawer = null; d.close(); }
    const head = h("div", {}, h("h3", {}, "Finding"), h("div", { class: "mono small muted" }, id));
    const opened = openDrawer({ head }, () => { if (drawer === opened) { drawer = null; drawerId = null; go({ f: "" }); } });
    drawer = opened;
    mount(opened.body, skeleton(10));
    try {
      const data = await api(`${runPath}/findings/${encodeURIComponent(id)}`);
      if (drawerId !== id) return;
      mount(head, h("h3", {}, data.finding.title), h("div", { class: "row small muted" }, h("span", { class: "mono" }, id), sevBadge(data.finding.severity), kindBadge(data.finding.kind)));
      renderDrawerBody(opened.body, data);
    } catch (err) { if (drawerId === id) mount(opened.body, err.status === 404 ? emptyState("That finding is not in this run", err.message) : errorState(err)); }
  }

  sync();
  return { update(q) { query = { ...q }; sync(); },
    destroy() { clearTimeout(debounce); requestId += 1; if (drawer) { const d = drawer; drawer = null; drawerId = null; d.close(); } } };
}
