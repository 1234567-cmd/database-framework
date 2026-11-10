// Roadmap, lineage, architecture, coverage, limitations and the print view.
import { h, mount, fmtNumber, fmtDuration, titleCase } from "../dom.js";
import { api } from "../api.js";
import { routeHref } from "../router.js";
import { bullets, dataTable, emptyState, errorState, kindBadge, kv, sevBadge, skeleton, tile } from "../components.js";
import { renderDashboard } from "./dashboard.js";

export function mountView(ctx) {
  const root = ctx.root;
  const runPath = `/runs/${encodeURIComponent(ctx.runId)}`;
  const section = ctx.section;
  let requestId = 0;

  if (section === "print") {
    renderPrint(root, ctx, runPath);
    return { destroy() {} };
  }
  async function load() {
    const id = ++requestId;
    mount(root, skeleton(10));
    try {
      const { data } = await api(`${runPath}/section/${section}`);
      if (id !== requestId) return;
      ({ roadmap: renderRoadmap, lineage: renderLineage, architecture: renderArchitecture, coverage: renderCoverage, limitations: renderLimitations }[section])(root, data, ctx);
    } catch (err) { if (id === requestId) mount(root, errorState(err, load)); }
  }
  load();
  return { destroy() { requestId += 1; } };
}

function head(title, text) { return h("div", { class: "page-head" }, h("div", {}, h("h1", {}, title), text ? h("p", {}, text) : null)); }

function renderRoadmap(root, data, ctx) {
  const phases = data.phases || [];
  mount(root, head("Roadmap", data.basis),
    h("div", { class: "card" }, h("h3", {}, "Before you start"), bullets(data.prerequisites)),
    phases.length ? phases.map((phase) => h("div", { class: "section" }, h("h2", {}, `Phase ${phase.phase}: ${phase.name}`),
      dataTable([
        { label: "Recommendation", render: (i) => h("a", { href: routeHref(["run", ctx.runId, "recommendations"], { r: i.recommendation }) }, i.title) },
        { label: "Priority", render: (i) => i.priority },
        { label: "Score", num: true, render: (i) => i.priority_score },
        { label: "Findings", num: true, render: (i) => fmtNumber(i.findings) },
        { label: "Steps", num: true, render: (i) => fmtNumber((i.steps || []).length) },
        { label: "Depends on", render: (i) => (i.depends_on || []).join(", ") || "—" },
        { label: "Moved up for", render: (i) => i.moved_forward_for || "—" },
      ], phase.items))) : emptyState("No phases", "This run has no recommendations to order."));
}

function renderLineage(root, data) {
  const edges = data.edges || [];
  mount(root, head("Lineage", `${fmtNumber(edges.length)} data flow edges, at object level.`),
    (data.notes || []).length ? h("div", { class: "card" }, h("h3", {}, "Notes"), bullets(data.notes)) : null,
    (data.gaps || []).length ? h("div", { class: "card section" }, h("h3", {}, "Gaps"), bullets(data.gaps)) : null,
    h("div", { class: "section" }, edges.length
      ? dataTable([{ label: "Source", render: (e) => h("span", { class: "mono small" }, e.source) }, { label: "Target", render: (e) => h("span", { class: "mono small" }, e.target) }, { label: "Via", render: (e) => e.via }, { label: "Kind", render: (e) => titleCase(e.kind) }], edges.slice(0, 500))
      : emptyState("No lineage edges", "Lineage comes from views, routines, triggers and pipeline manifests.")),
    edges.length > 500 ? h("p", { class: "small muted" }, "Showing the first 500 edges.") : null);
}

function renderArchitecture(root, data) {
  const domains = data.domains || [];
  mount(root, head("Architecture", "Domains by foreign key connectivity, with views, routines and other objects."),
    h("div", { class: "tiles" }, tile("Tables", fmtNumber((data.tables || []).length)), tile("Relations", fmtNumber((data.relations || []).length)), tile("Views", fmtNumber((data.views || []).length)), tile("Routines", fmtNumber((data.routines || []).length)), tile("Domains", fmtNumber(domains.length))),
    h("div", { class: "section" }, h("h2", {}, "Domains"), domains.length ? h("div", { class: "stack" }, domains.map((d) => h("div", { class: "card" }, h("h3", {}, `${d.name} (${fmtNumber(d.size)})`), h("p", { class: "mono small muted" }, d.tables.slice(0, 60).join(", "), d.tables.length > 60 ? ` and ${d.tables.length - 60} more` : "")))) : emptyState("No domains", "No foreign keys were found.")),
    h("div", { class: "section" }, h("h2", {}, "Views"), (data.views || []).length ? dataTable([{ label: "View", render: (v) => h("span", { class: "mono" }, v.name) }, { label: "Materialized", render: (v) => (v.materialized ? "Yes" : "No") }, { label: "References", render: (v) => h("span", { class: "mono small" }, v.references.join(", ") || "—") }], data.views) : h("p", { class: "muted" }, "None.")),
    h("div", { class: "section" }, h("h2", {}, "Routines and triggers"), (data.routines || []).length ? dataTable([{ label: "Name", render: (r) => h("span", { class: "mono" }, r.name) }, { label: "Kind", render: (r) => r.kind }, { label: "Table", render: (r) => r.table || "—" }], data.routines) : h("p", { class: "muted" }, "None.")));
}

function renderCoverage(root, data) {
  mount(root, head("Coverage", "Which rules ran, which were skipped and why, and which failed."),
    h("div", { class: "tiles" }, tile("Executed", fmtNumber(data.rules_executed_count)), tile("Skipped", fmtNumber(data.skipped_count)), tile("Errors", fmtNumber(data.errors_count))),
    h("div", { class: "card section" }, h("h3", {}, "Inputs available"), h("p", {}, (data.capabilities || []).join(", ") || "None recorded.")),
    h("div", { class: "section" }, h("h2", {}, `Errors (${fmtNumber(data.errors_count)})`), data.errors_count ? dataTable([{ label: "Rule", render: (r) => h("span", { class: "mono" }, r.rule) }, { label: "Error", render: (r) => r.error }], data.errors) : h("p", { class: "muted" }, "None.")),
    h("div", { class: "section" }, h("h2", {}, `Skipped (${fmtNumber(data.skipped_count)})`), data.skipped_count ? dataTable([{ label: "Rule", render: (r) => h("span", { class: "mono" }, r.rule) }, { label: "Reason", render: (r) => r.reason }], data.skipped) : h("p", { class: "muted" }, "None.")),
    h("div", { class: "section" }, h("h2", {}, `Executed (${fmtNumber(data.rules_executed_count)})`), h("p", { class: "mono small muted" }, (data.rules_executed || []).join(", "))));
}

function renderLimitations(root, data) {
  const timing = Object.entries(data.timing || {});
  mount(root, head("Limitations", "What this assessment could not see. Absence of a finding is not proof of health."),
    h("div", { class: "card" }, h("h3", {}, "Limitations of this run"), bullets(data.limitations)),
    h("div", { class: "card section" }, h("h3", {}, "Import warnings"), bullets(data.import_warnings)),
    h("div", { class: "card section" }, h("h3", {}, "Run details"), kv([["Source", (data.source || {}).label], ["Generated", data.generated_at], ["Workload", (data.profile || {}).workload], ["Tenancy", (data.profile || {}).tenancy]])),
    timing.length ? h("div", { class: "card section" }, h("h3", {}, "Stage timing"), h("ul", {}, timing.map(([k, v]) => h("li", {}, `${titleCase(k)}: ${fmtDuration(v)}`)))) : null);
}

async function renderPrint(root, ctx, runPath) {
  mount(root, skeleton(10));
  try {
    const [recs, findings, roadmap, limitations] = await Promise.all([
      api(`${runPath}/recommendations?size=20`), api(`${runPath}/findings?size=200`),
      api(`${runPath}/section/roadmap`), api(`${runPath}/section/limitations`)]);
    const dash = h("div", {});
    renderDashboard(dash, ctx.run, recs.items);
    mount(root,
      h("div", { class: "no-print card stack" }, h("h2", {}, "Print or save as PDF"), h("p", {}, "PDF is made through your browser's print dialog: choose Save as PDF as the printer. This view shows the first 200 findings; the HTML report has everything."),
        h("div", {}, h("button", { class: "btn btn-primary", onClick: () => window.print() }, "Open print dialog"))),
      h("h1", {}, `Assessment: ${(ctx.run.source || {}).name || ""}`),
      h("p", { class: "muted" }, `Generated ${ctx.run.generated_at || ""}. Proposals only; nothing has been changed.`),
      dash,
      h("section", { class: "print-section" }, h("h2", {}, `Findings (${fmtNumber(findings.total)})`), findings.items.map((f) => h("div", { class: "print-finding card card-tight" }, h("div", { class: "row" }, sevBadge(f.severity), kindBadge(f.kind), h("span", { class: "mono small" }, f.id)), h("div", {}, f.title), h("div", { class: "mono small muted" }, [f.table, f.column].filter(Boolean).join("."))))),
      h("section", { class: "print-section" }, h("h2", {}, "Roadmap"), (roadmap.data.phases || []).map((p) => h("div", {}, h("h3", {}, `Phase ${p.phase}: ${p.name}`), bullets(p.items.slice(0, 30).map((i) => `${i.priority} ${i.title}`))))),
      h("section", { class: "print-section" }, h("h2", {}, "Limitations"), bullets(limitations.data.limitations), h("h3", {}, "Import warnings"), bullets(limitations.data.import_warnings)));
  } catch (err) { mount(root, errorState(err)); }
}
