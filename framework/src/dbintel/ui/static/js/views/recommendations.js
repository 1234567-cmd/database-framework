// Recommendations: list with priority rationale, and a detail pane comparing the existing and recommended design.
import { h, mount, fmtNumber } from "../dom.js";
import { api } from "../api.js";
import { routeHref } from "../router.js";
import { bullets, chip, codeBlock, emptyState, errorState, kindBadge, notice, pager, sevBadge, skeleton } from "../components.js";

export function mountView(ctx) {
  const root = ctx.root;
  const runPath = `/runs/${encodeURIComponent(ctx.runId)}`;
  let query = { ...ctx.query };
  let requestId = 0;
  let detailId = null;
  let debounce = null;
  const listEl = h("div", {});
  const detailEl = h("div", {});
  const input = h("input", { type: "search", id: "rec-search", placeholder: "Search title or table", value: query.q || "",
    onInput: (e) => { clearTimeout(debounce); const value = e.target.value; debounce = setTimeout(() => go({ q: value, page: "" }), 280); } });
  const priorityEl = h("div", { class: "chip-row" });
  mount(root, h("div", { class: "page-head" }, h("div", {}, h("h1", {}, "Recommendations"), h("p", {}, "What to change, why it ranks where it does, and what depends on it."))),
    h("div", { class: "filters" }, h("label", { class: "field", for: "rec-search" }, "Search", input), priorityEl),
    h("div", { class: "split" }, listEl, detailEl));

  function go(patch) {
    const next = { ...query, ...patch };
    Object.keys(next).forEach((k) => { if (next[k] === "" || next[k] === undefined) delete next[k]; });
    ctx.go(next);
  }

  async function loadList() {
    const id = ++requestId;
    mount(listEl, skeleton(8));
    const params = new URLSearchParams();
    ["q", "priority", "page"].forEach((k) => { if (query[k]) params.set(k, query[k]); });
    params.set("size", "40");
    try {
      const data = await api(`${runPath}/recommendations?${params.toString()}`);
      if (id !== requestId) return;
      const selected = new Set((query.priority || "").split(",").filter(Boolean));
      mount(priorityEl, Object.entries(data.priorities).map(([p, count]) => chip(p, count, selected.has(p), () => {
        if (selected.has(p)) selected.delete(p); else selected.add(p);
        go({ priority: [...selected].join(","), page: "" });
      })));
      mount(listEl, data.items.length ? h("div", { class: "stack" }, data.items.map((r) => h("button", { class: `card card-tight left rec-item`, onClick: () => go({ r: r.id }) },
        h("div", { class: "row small muted" }, h("span", { class: "badge badge-outline" }, r.priority), h("span", {}, `score ${r.priority_score}`), h("span", {}, `${fmtNumber(r.findings)} finding(s)`)), h("div", {}, r.title), r.table ? h("div", { class: "mono small muted" }, r.table) : null)),
      pager(data, (page) => go({ page }))) : emptyState("No recommendations match", "Clear a filter or change the search."));
    } catch (err) { if (id === requestId) mount(listEl, errorState(err, loadList)); }
  }

  async function loadDetail() {
    const id = query.r;
    if (id === detailId) return;
    detailId = id;
    if (!id) { mount(detailEl, h("div", { class: "card state" }, h("h3", {}, "Choose a recommendation"), h("p", {}, "Its before and after, SQL and dependencies appear here."))); return; }
    mount(detailEl, h("div", { class: "card" }, skeleton(10)));
    try {
      const data = await api(`${runPath}/recommendations/${encodeURIComponent(id)}`);
      if (id !== detailId) return;
      renderDetail(data);
    } catch (err) { if (id === detailId) mount(detailEl, h("div", { class: "card" }, err.status === 404 ? emptyState("Not in this run", err.message) : errorState(err))); }
  }

  function renderDetail(data) {
    const r = data.recommendation;
    const before = (r.before_after || {}).before; const after = (r.before_after || {}).after;
    mount(detailEl, h("div", { class: "card stack" },
      h("div", {}, h("div", { class: "row small muted" }, h("span", { class: "badge badge-outline" }, r.priority), h("span", { class: "mono" }, r.id), r.requires_review ? h("span", { class: "badge badge-warn" }, "Needs review") : null),
        h("h2", {}, r.title), h("h4", {}, "Priority rationale"), bullets(r.priority_rationale)),
      r.application_impact_evaluated ? null : notice("Application impact was not evaluated. No application source folder was given, so other code that uses this data was not checked.", "warn"),
      h("div", {}, h("h4", {}, "Weakness"), h("p", {}, r.weakness)),
      h("div", {}, h("h4", {}, "Existing and recommended"), h("div", { class: "compare-panes" }, h("div", {}, h("h4", {}, "Existing"), codeBlock(r.existing_structure)), h("div", {}, h("h4", {}, "Recommended"), codeBlock(r.recommended_structure)))),
      h("div", {}, h("h4", {}, "Before and after"), h("div", { class: "compare-panes" }, h("div", {}, h("h4", {}, "Before"), codeBlock(before)), h("div", {}, h("h4", {}, "After"), codeBlock(after)))),
      h("div", {}, h("h4", {}, "Proposed SQL"), codeBlock(r.proposed_sql, { placeholder: "No SQL for this recommendation." })),
      h("div", { class: "grid grid-2" }, h("div", {}, h("h4", {}, "Application dependencies"), bullets(r.application_dependencies)), h("div", {}, h("h4", {}, "Data dependencies"), bullets(r.data_dependencies))),
      h("div", { class: "grid grid-2" }, h("div", {}, h("h4", {}, "Data migration"), h("p", {}, r.data_migration)), h("div", {}, h("h4", {}, "Rollback"), h("p", { class: "mono small" }, r.rollback))),
      h("div", {}, h("h4", {}, "Validation tests"), bullets(r.validation_tests)),
      h("div", {}, h("h4", {}, "Business notes"), bullets(r.business_logic_notes)),
      h("div", {}, h("h4", {}, `Findings (${data.findings.length})`), data.findings.slice(0, 30).map((f) => h("div", { class: "row" }, sevBadge(f.severity), kindBadge(f.kind), h("a", { href: routeHref(["run", ctx.runId, "findings"], { f: f.id }) }, f.title)))),
      h("div", {}, h("h4", {}, `Migration steps (${data.steps.length})`), data.steps.length ? data.steps.slice(0, 40).map((s) => h("div", {}, h("a", { href: routeHref(["run", ctx.runId, "migration"], { s: s.id }) }, `${s.id}: ${s.title}`))) : h("p", { class: "muted" }, "None."))));
  }

  let lastListKey = null;
  function sync() {
    const key = JSON.stringify([query.q || "", query.priority || "", query.page || ""]);
    if (key !== lastListKey) { lastListKey = key; loadList(); }
    loadDetail();
  }
  sync();
  return { update(q) { query = { ...q }; sync(); }, destroy() { clearTimeout(debounce); requestId += 1; detailId = "__closed__"; } };
}
