// Tables: searchable list and a detail page with columns, keys, indexes, relationships and findings.
import { h, mount, fmtNumber, titleCase } from "../dom.js";
import { api } from "../api.js";
import { navigate, routeHref } from "../router.js";
import { bullets, dataTable, emptyState, errorState, flagBadge, kindBadge, kv, notice, pager, sevBadge, skeleton } from "../components.js";

export function mountView(ctx) {
  const name = ctx.segments[3];
  return name ? tableDetail(ctx, name) : tableList(ctx);
}

function tableList(ctx) {
  const root = ctx.root;
  const runId = ctx.runId;
  let query = { ...ctx.query };
  let requestId = 0;
  let debounce = null;
  const input = h("input", { type: "search", id: "table-search", placeholder: "Filter by table name", value: query.q || "",
    onInput: (e) => { clearTimeout(debounce); const value = e.target.value; debounce = setTimeout(() => go({ q: value, page: "" }), 280); } });
  const listEl = h("div", {});
  mount(root, h("div", { class: "page-head" }, h("div", {}, h("h1", {}, "Tables"), h("p", {}, "Every table with its size, keys and open findings."))),
    h("div", { class: "filters" }, h("label", { class: "field", for: "table-search" }, "Search", input)), listEl);

  function go(patch) {
    const next = { ...query, ...patch };
    Object.keys(next).forEach((k) => { if (next[k] === "" || next[k] === undefined) delete next[k]; });
    ctx.go(next);
  }

  async function load() {
    const id = ++requestId;
    mount(listEl, skeleton(10));
    const params = new URLSearchParams();
    ["q", "sort", "order", "page"].forEach((k) => { if (query[k]) params.set(k, query[k]); });
    params.set("size", "50");
    try {
      const data = await api(`/runs/${encodeURIComponent(runId)}/tables?${params.toString()}`);
      if (id !== requestId) return;
      const columns = [
        { label: "Table", sortKey: "name", render: (t) => h("a", { class: "mono", href: routeHref(["run", runId, "tables", t.name]) }, t.name) },
        { label: "Columns", sortKey: "columns", num: true, render: (t) => fmtNumber(t.columns) },
        { label: "Primary key", render: (t) => (t.primary_key.length ? h("span", { class: "mono small" }, t.primary_key.join(", ")) : flagBadge("None", "bad")) },
        { label: "FKs out", sortKey: "foreign_keys", num: true, render: (t) => fmtNumber(t.foreign_keys) },
        { label: "Referenced by", sortKey: "referenced_by", num: true, render: (t) => fmtNumber(t.referenced_by) },
        { label: "Indexes", sortKey: "indexes", num: true, render: (t) => fmtNumber(t.indexes) },
        { label: "Rows", sortKey: "rows", num: true, render: (t) => fmtNumber(t.row_count) },
        { label: "Findings", sortKey: "findings", num: true, render: (t) => h("a", { href: routeHref(["run", runId, "findings"], { table: t.name }) }, fmtNumber(t.findings)) },
        { label: "Worst", render: (t) => worst(t.severity_counts) },
      ];
      mount(listEl, dataTable(columns, data.items, { sort: query.sort || "name", order: query.order || "asc", rowKey: (t) => t.name,
        onSort: (key) => go({ sort: key, order: (query.sort || "name") === key && query.order !== "desc" ? "desc" : "", page: "" }),
        onRow: (t) => navigate(["run", runId, "tables", t.name]), emptyMessage: "No tables match", emptyHint: "Change the search." }),
      pager(data, (page) => go({ page })));
    } catch (err) { if (id === requestId) mount(listEl, errorState(err, load)); }
  }
  load();
  return { update(q) { query = { ...q }; load(); }, destroy() { clearTimeout(debounce); requestId += 1; } };
}

function worst(counts) {
  for (const sev of ["critical", "high", "medium", "low", "informational"]) if (counts && counts[sev]) return sevBadge(sev);
  return h("span", { class: "muted" }, "—");
}

function tableDetail(ctx, name) {
  const root = ctx.root;
  const runId = ctx.runId;
  mount(root, skeleton(12));
  load();
  async function load() {
    try {
      const t = await api(`/runs/${encodeURIComponent(runId)}/tables/${encodeURIComponent(name)}`);
      render(t);
    } catch (err) {
      mount(root, err.status === 404
        ? emptyState("That table is not in this run", err.message, h("a", { class: "btn", href: routeHref(["run", runId, "tables"]) }, "Back to tables"))
        : errorState(err, load));
    }
  }
  function tableLink(target) { return target ? h("a", { class: "mono", href: routeHref(["run", runId, "tables", target]) }, target) : h("span", { class: "muted" }, "outside this schema"); }

  function render(t) {
    const columns = [
      { label: "Column", render: (c) => h("span", { class: "mono" }, c.name) },
      { label: "Type", render: (c) => h("span", { class: "mono small" }, c.type) },
      { label: "Null", render: (c) => (c.nullable ? "yes" : "no") },
      { label: "Key", render: (c) => h("span", { class: "badges" }, c.pk ? flagBadge("PK") : null, c.fk_to ? flagBadge(`FK to ${c.fk_to}`) : null, c.identity ? flagBadge("Identity") : null, c.generated ? flagBadge("Generated") : null) },
      { label: "Default", render: (c) => h("span", { class: "mono small" }, c.default === null || c.default === undefined ? "—" : c.default) },
      { label: "Comment", render: (c) => c.comment || "—" },
      { label: "Findings", num: true, render: (c) => (c.findings ? h("a", { href: routeHref(["run", runId, "findings"], { table: t.name, q: c.name }) }, fmtNumber(c.findings)) : "0") },
    ];
    const relationTable = (rows, direction) => (rows.length ? dataTable([
      { label: direction === "out" ? "References table" : "Referencing table", render: (r) => tableLink(direction === "out" ? r.to_resolved || r.to : r.from_resolved) },
      { label: "Columns", render: (r) => h("span", { class: "mono small" }, direction === "out" ? r.columns.join(", ") : `${r.columns.join(", ")} → ${r.ref_columns.join(", ")}`) },
      { label: "Ref columns", render: (r) => h("span", { class: "mono small" }, r.ref_columns.join(", ")) },
      { label: "On delete", render: (r) => r.on_delete || "—" },
      { label: "On update", render: (r) => r.on_update || "—" },
    ], rows) : h("p", { class: "muted" }, "None."));
    const findingRows = t.findings.slice(0, 100);
    mount(root,
      h("div", { class: "page-head" }, h("div", {}, h("h1", { class: "mono" }, t.name), h("p", {}, t.comment || "No description in the schema."))),
      t.financial ? notice("Financial table protection applies: destructive proposals for this table are refused.", "warn") : null,
      h("div", { class: "tiles" }, kvTile("Rows", fmtNumber(t.row_count)), kvTile("Columns", fmtNumber(t.columns.length)), kvTile("Foreign keys", fmtNumber(t.relations_out.length)), kvTile("Referenced by", fmtNumber(t.relations_in.length)), kvTile("Findings", fmtNumber(t.findings.length))),
      h("div", { class: "section" }, h("h2", {}, "Columns"), dataTable(columns, t.columns, { emptyMessage: "No columns recorded" })),
      h("div", { class: "section grid grid-2" },
        h("div", { class: "card" }, h("h3", {}, "Keys"), kv([["Primary key", t.primary_key.length ? t.primary_key.join(", ") : "None"], ["Constraint name", t.primary_key_name]]), t.unique_keys.length ? h("div", { class: "section" }, h("h4", {}, "Unique keys"), bullets(t.unique_keys.map((u) => `${u.name || "(unnamed)"}: ${u.columns.join(", ")}`))) : null),
        h("div", { class: "card" }, h("h3", {}, "Indexes"), t.indexes_available
          ? (t.indexes.length ? bullets(t.indexes.map((i) => `${i.name || "(unnamed)"}: ${i.columns.join(", ")}${i.unique ? " (unique)" : ""}${i.where ? ` where ${i.where}` : ""}`)) : h("p", { class: "muted" }, "None."))
          : h("p", { class: "muted" }, "Index details are not in this report."))),
      h("div", { class: "section grid grid-2" },
        h("div", { class: "card" }, h("h3", {}, `References out (${t.relations_out.length})`), relationTable(t.relations_out, "out")),
        h("div", { class: "card" }, h("h3", {}, `Referenced by (${t.relations_in.length})`), relationTable(t.relations_in, "in"))),
      t.checks.length ? h("div", { class: "card section" }, h("h3", {}, "Check constraints"), bullets(t.checks.map((c) => `${c.name || "(unnamed)"}: ${c.expression}`))) : null,
      h("div", { class: "card section" }, h("h3", {}, `Dependencies (${t.dependencies.length})`), t.dependencies.length
        ? dataTable([{ label: "Direction", render: (d) => d.direction }, { label: "Object", render: (d) => h("span", { class: "mono" }, d.object) }, { label: "Via", render: (d) => d.via }, { label: "Kind", render: (d) => titleCase(d.kind) }], t.dependencies)
        : h("p", { class: "muted" }, "No views, routines, triggers or pipelines reference this table in the inputs given.")),
      h("div", { class: "section" }, h("div", { class: "row-spread" }, h("h2", {}, `Findings (${t.findings.length})`), h("a", { href: routeHref(["run", runId, "findings"], { table: t.name }), class: "small" }, "Open in Findings")),
        dataTable([{ label: "Severity", render: (f) => sevBadge(f.severity) }, { label: "Finding", class: "title-cell", render: (f) => h("a", { href: routeHref(["run", runId, "findings"], { f: f.id }) }, f.title) }, { label: "Kind", render: (f) => kindBadge(f.kind) }, { label: "Column", render: (f) => h("span", { class: "mono" }, f.column || "—") }], findingRows, { emptyMessage: "No findings on this table" }),
        t.findings.length > 100 ? h("p", { class: "small muted" }, `Showing 100 of ${t.findings.length}.`) : null));
  }
  function kvTile(label, value) { return h("div", { class: "tile" }, h("div", { class: "tile-value" }, value), h("div", { class: "tile-label" }, label)); }
}
