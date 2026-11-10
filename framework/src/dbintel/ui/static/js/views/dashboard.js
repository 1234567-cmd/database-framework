// Dashboard: score, categories, distributions, priorities and warnings.
import { h, mount, fmtNumber, fmtPct, titleCase } from "../dom.js";
import { api } from "../api.js";
import { routeHref } from "../router.js";
import { bullets, errorState, kindBadge, kv, notice, sevBadge, setBar, skeleton, tile } from "../components.js";

export function renderDashboard(root, run, topRecs) {
  const summary = run.summary || {};
  const health = run.health || {};
  const dist = run.distribution || {};
  const id = run.id;
  const score = health.overall;
  const confidencePct = fmtPct(health.confidence);
  const lowConfidence = (health.confidence || 0) < 0.6;
  const capText = health.capped
    ? `The overall score is capped at 59 because at least one confirmed critical defect exists. Fixing it can raise the score above the cap.`
    : "The score is not capped. A cap applies when a confirmed critical defect exists.";
  const heroScore = h("div", {},
    score === null || score === undefined ? h("div", { class: "score-num muted" }, "n/a") : h("div", { class: "score-num" }, fmtNumber(score)),
    h("div", { class: "score-grade" }, score === null || score === undefined ? "Not assessed" : `Grade ${health.grade}`),
    h("div", { class: "small muted" }, `Confidence ${confidencePct}`),
    h("div", { class: "badges" }, health.capped ? h("span", { class: "badge badge-bad" }, "Capped") : null, lowConfidence ? h("span", { class: "badge badge-warn" }, "Low confidence") : null));
  const skipped = (run.import_warnings || []).length || (run.coverage || {}).skipped_count || (run.coverage || {}).errors_count;
  const sections = [
    h("div", { class: "card hero" }, heroScore,
      h("div", { class: "prose" },
        (summary.text || []).map((t) => h("p", {}, t)),
        h("p", { class: "muted small" }, capText),
        lowConfidence ? notice("Many rules could not run with the inputs given. Treat the score as a partial view; see Coverage.", "warn") : null)),
    skipped ? h("div", { class: "card stack" }, h("h3", {}, "What was skipped"),
      (run.import_warnings || []).length ? h("div", {}, h("h4", {}, "Input warnings"), bullets(run.import_warnings)) : null,
      h("p", { class: "small" }, `${fmtNumber((run.coverage || {}).skipped_count || 0)} rule(s) were skipped and ${fmtNumber((run.coverage || {}).errors_count || 0)} failed to run. `,
        h("a", { href: routeHref(["run", id, "coverage"]) }, "See coverage"))) : null,
    h("div", {},
      h("h2", {}, "Categories"),
      h("p", { class: "muted small" }, "Dashed cards are low confidence or not assessed. A category that could not be assessed is never counted as healthy."),
      h("div", { class: "cat-grid" }, (health.categories || []).map(categoryCard))),
    h("div", { class: "grid grid-2" },
      h("div", { class: "card" }, h("h3", {}, "Findings by severity"), distRows(dist.severity, (k) => sevBadge(k), id, "severity")),
      h("div", { class: "card" }, h("h3", {}, "Findings by kind"), distRows(dist.kind, (k) => kindBadge(k), id, "kind"))),
    h("div", { class: "card" }, h("div", { class: "row-spread" }, h("h3", {}, "Top priorities"), h("a", { href: routeHref(["run", id, "findings"]), class: "small" }, "All findings")),
      (summary.top_risks || []).length ? h("div", { class: "stack" }, summary.top_risks.map((r) =>
        h("div", { class: "row" }, sevBadge(r.severity), h("a", { href: routeHref(["run", id, "findings"], { f: r.id }) }, r.title), h("span", { class: "mono muted small" }, [r.table, r.column].filter(Boolean).join(".")))))
        : h("p", { class: "muted" }, "No confirmed defects were found.")),
    topRecs.length ? h("div", { class: "card" }, h("div", { class: "row-spread" }, h("h3", {}, "Top recommendations"), h("a", { href: routeHref(["run", id, "recommendations"]), class: "small" }, "All recommendations")),
      h("div", { class: "stack" }, topRecs.map((r) => h("div", { class: "row" }, h("span", { class: "badge badge-outline" }, r.priority), h("a", { href: routeHref(["run", id, "recommendations"], { r: r.id }) }, r.title), h("span", { class: "small muted" }, `score ${r.priority_score}`))))) : null,
    h("div", { class: "card" }, h("h3", {}, "Run details"), kv([
      ["Source", (run.source || {}).label], ["Dialect", (run.source || {}).dialect], ["Generated", run.generated_at],
      ["Tables", fmtNumber(run.table_count)], ["Findings", fmtNumber(run.findings_total)],
      ["Migration steps", fmtNumber((run.migration || {}).total_steps)], ["Profile", `${(run.profile || {}).workload || ""}, tenancy ${(run.profile || {}).tenancy || ""}, multi-company ${(run.profile || {}).multi_company ? "yes" : "no"}`]])),
  ];
  mount(root, h("div", { class: "stack" }, sections));
}

function scoreTone(score) { return score >= 75 ? "good" : score >= 50 ? "warn" : "bad"; }

function categoryCard(cat) {
  const notAssessed = cat.score === null || cat.score === undefined;
  const lowConfidence = !notAssessed && cat.confidence < 0.6;
  const classes = `cat-card${notAssessed ? " cat-na" : lowConfidence ? " cat-low" : ""}`;
  const meter = h("div", { class: `meter ${notAssessed || lowConfidence ? "" : scoreTone(cat.score)}` }, setBar(h("span", {}), notAssessed ? 0 : cat.score));
  return h("div", { class: classes },
    h("div", { class: "cat-head" }, h("span", { class: "cat-name" }, titleCase(cat.category)),
      h("span", { class: "cat-score" }, notAssessed ? "—" : fmtNumber(cat.score))),
    meter,
    notAssessed ? h("span", { class: "badge badge-outline" }, "Not assessed") : h("div", { class: "row small muted" },
      h("span", {}, `Grade ${cat.grade}`), h("span", {}, `Confidence ${fmtPct(cat.confidence)}`), lowConfidence ? h("span", { class: "badge badge-warn" }, "Low confidence") : null),
    h("div", { class: "small muted" }, notAssessed ? `${cat.rules_skipped} rule(s) could not run with the inputs given.` : `${cat.rules_executed} rule(s) ran, ${cat.rules_skipped} skipped.`));
}

function distRows(values, label, runId, facet) {
  const entries = Object.entries(values || {});
  const peak = Math.max(1, ...entries.map(([, v]) => v));
  if (!entries.length) return h("p", { class: "muted" }, "No data.");
  return h("div", {}, entries.map(([key, value]) => {
    const bar = setBar(h("span", { class: facet === "severity" ? `sev-${key}` : "" }), value ? (100 * value) / peak : 0);
    return h("div", { class: "dist-row" }, h("a", { href: routeHref(["run", runId, "findings"], { [facet]: key }) }, label(key)), h("span", { class: "right" }, fmtNumber(value)), h("div", { class: "dist-bar" }, bar));
  }));
}

export function mountView(ctx) {
  const root = ctx.root;
  async function load() {
    mount(root, skeleton(10));
    try {
      const recs = await api(`/runs/${encodeURIComponent(ctx.runId)}/recommendations?size=5`);
      renderDashboard(root, ctx.run, recs.items || []);
    } catch (err) { mount(root, errorState(err, load)); }
  }
  load();
}
