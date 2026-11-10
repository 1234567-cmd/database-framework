// Migration review: filterable steps, SQL with copy, and a sandbox test. This tool has no way to apply a plan to a source database.
import { h, mount, fmtNumber } from "../dom.js";
import { api, download } from "../api.js";
import { routeHref } from "../router.js";
import { bullets, codeBlock, copyButton, dataTable, emptyState, errorState, flagBadge, kv, notice, openDrawer, pager, sevBadge, skeleton, statusBadge, tile, toast } from "../components.js";

const FLAGS = [["destructive", "Destructive"], ["irreversible", "Irreversible"], ["refused", "Refused"], ["data_repair", "Data repair required"], ["manual", "Manual"], ["breaking", "Breaking"]];

function stepBadges(step) {
  return h("span", { class: "badges" },
    step.manual ? flagBadge("Manual") : null, step.destructive ? flagBadge("Destructive", "bad") : null,
    !step.manual && !step.reversible ? flagBadge("Irreversible", "warn") : null, step.refused_reason ? flagBadge("Refused", "bad") : null,
    step.requires_data_repair ? flagBadge("Data repair required", "warn") : null, step.breaking ? flagBadge("Breaking", "warn") : null);
}

export function mountView(ctx) {
  const root = ctx.root;
  const runPath = `/runs/${encodeURIComponent(ctx.runId)}`;
  const run = ctx.run;
  const migration = run.migration || {};
  let query = { ...ctx.query };
  let requestId = 0;
  let drawer = null;
  let drawerId = null;
  let debounce = null;
  const filtersEl = h("div", { class: "chip-row" });
  const listEl = h("div", {});
  const sandboxEl = h("div", {});
  const search = h("input", { type: "search", id: "step-search", placeholder: "Search step, table or column", value: query.q || "",
    onInput: (e) => { clearTimeout(debounce); const value = e.target.value; debounce = setTimeout(() => go({ q: value, page: "" }), 280); } });
  const tableFilter = h("input", { type: "search", id: "step-table", placeholder: "Filter by table", value: query.table || "",
    onInput: (e) => { clearTimeout(debounce); const value = e.target.value; debounce = setTimeout(() => go({ table: value, page: "" }), 280); } });

  mount(root,
    h("div", { class: "page-head" }, h("div", {}, h("h1", {}, "Migration review"), h("p", {}, "Proposed changes only. This tool never applies them to your database.")),
      h("div", { class: "row no-print" }, h("button", { class: "btn", onClick: downloadZip }, "Download plan as zip"))),
    notice(h("span", {}, h("strong", {}, "Proposals, not actions. "), "There is no apply function in dbintel. Review the SQL, test it on a copy, and run it through your own change process."), "info"),
    h("div", { class: "tiles section" }, tile("Steps", fmtNumber(migration.total_steps)), tile("With SQL", fmtNumber(migration.executable_steps)), tile("Manual", fmtNumber(migration.manual_steps)),
      tile("Destructive", fmtNumber(migration.destructive_steps)), tile("Refused", fmtNumber(migration.refused_steps)), tile("Irreversible", fmtNumber(migration.irreversible_steps))),
    h("div", { class: "grid grid-2 section" },
      h("div", { class: "card" }, h("h3", {}, "Back up first"), h("p", {}, migration.backup_recommendation || "—")),
      h("div", { class: "card" }, h("h3", {}, "Plan hash"), h("div", { class: "row" }, h("code", {}, migration.plan_hash || "—"), migration.plan_hash ? copyButton(migration.plan_hash, "Copy") : null), h("p", { class: "muted small" }, "Target dialect: ", migration.dialect || "—", ". Unaddressed findings: ", fmtNumber(migration.unaddressed_count), "."))),
    (migration.notes || []).length ? h("div", { class: "card section" }, h("h3", {}, "Plan notes"), bullets(migration.notes)) : null,
    h("div", { class: "section" }, h("h2", {}, "Sandbox test"), sandboxEl),
    h("div", { class: "section" }, h("h2", {}, "Steps"),
      h("div", { class: "filters" }, h("div", { class: "grid grid-2" }, h("label", { class: "field", for: "step-search" }, "Search", search), h("label", { class: "field", for: "step-table" }, "Table", tableFilter)), filtersEl), listEl));

  function go(patch) {
    const next = { ...query, ...patch };
    Object.keys(next).forEach((k) => { if (next[k] === "" || next[k] === undefined || next[k] === null) delete next[k]; });
    ctx.go(next);
  }

  async function downloadZip() {
    try { await download(`${runPath}/migration/zip`, `migrations_${ctx.runId}.zip`); toast("Download started"); } catch (err) { toast(err.message); }
  }

  async function loadList() {
    const id = ++requestId;
    mount(listEl, skeleton(8));
    const params = new URLSearchParams();
    ["q", "table", "flags", "page"].forEach((k) => { if (query[k]) params.set(k, query[k]); });
    params.set("size", "50");
    try {
      const data = await api(`${runPath}/migration/steps?${params.toString()}`);
      if (id !== requestId) return;
      const selected = new Set((query.flags || "").split(",").filter(Boolean));
      mount(filtersEl, FLAGS.map(([flag, label]) => h("button", { class: "chip", "aria-pressed": selected.has(flag) ? "true" : "false", onClick: () => {
        if (selected.has(flag)) selected.delete(flag); else selected.add(flag);
        go({ flags: [...selected].join(","), page: "" });
      } }, label, h("span", { class: "count" }, fmtNumber(data.flag_counts[flag])))));
      const columns = [
        { label: "#", num: true, render: (s) => s.order },
        { label: "Step", class: "title-cell", render: (s) => h("a", { href: routeHref(ctx.segments, { ...query, s: s.id }) }, h("span", { class: "mono small" }, s.id), " ", s.title) },
        { label: "Table", render: (s) => h("span", { class: "mono small" }, s.table || "—") },
        { label: "Flags", render: (s) => stepBadges(s) },
        { label: "Loss risk", render: (s) => s.data_loss_risk },
        { label: "Lock risk", render: (s) => s.lock_risk },
      ];
      mount(listEl, dataTable(columns, data.items, { rowKey: (s) => s.id, onRow: (s) => go({ s: s.id }), emptyMessage: "No steps match", emptyHint: "Clear a filter or change the search." }), pager(data, (page) => go({ page })));
    } catch (err) { if (id === requestId) mount(listEl, errorState(err, loadList)); }
  }

  async function syncDrawer() {
    const id = query.s;
    if (!id) { if (drawer) { const d = drawer; drawer = null; drawerId = null; d.close(); } return; }
    if (id === drawerId) return;
    drawerId = id;
    if (drawer) { const d = drawer; drawer = null; d.close(); }
    const head = h("div", {}, h("h3", {}, "Migration step"), h("div", { class: "mono small muted" }, id));
    const opened = openDrawer({ head }, () => { if (drawer === opened) { drawer = null; drawerId = null; go({ s: "" }); } });
    drawer = opened;
    mount(opened.body, skeleton(10));
    try {
      const data = await api(`${runPath}/migration/steps/${encodeURIComponent(id)}`);
      if (drawerId !== id) return;
      renderStep(head, opened.body, data);
    } catch (err) { if (drawerId === id) mount(opened.body, err.status === 404 ? emptyState("That step is not in this run", err.message) : errorState(err)); }
  }

  function renderStep(head, body, data) {
    const s = data.step;
    mount(head, h("h3", {}, s.title), h("div", { class: "row small" }, h("span", { class: "mono muted" }, s.id), stepBadges(s)));
    const checksTable = (checks) => (checks.length ? h("div", { class: "stack" }, checks.map((c) => h("div", {}, h("div", {}, c.description, " ", h("span", { class: "small muted" }, `Expect ${c.expected}.`)), c.sql ? codeBlock(c.sql) : null))) : h("p", { class: "muted small" }, "None."));
    mount(body, h("div", { class: "stack" },
      s.refused_reason ? notice(h("span", {}, h("strong", {}, "Refused. "), s.refused_reason), "bad") : null,
      s.requires_data_repair ? notice(h("span", {}, h("strong", {}, "Data repair required first. "), (s.data_repair_notes || []).join(" ")), "warn") : null,
      s.irreversible_reason ? notice(h("span", {}, h("strong", {}, "Cannot be reversed. "), s.irreversible_reason), "warn") : null,
      kv([["Operation", s.op], ["Table", s.table], ["Column", s.column], ["Order", s.order], ["Destructive", s.destructive ? "Yes" : "No"], ["Reversible", s.reversible ? "Yes" : "No"],
        ["Data loss risk", s.data_loss_risk], ["Lock risk", s.lock_risk], ["Backup needed", s.requires_backup ? "Yes" : "No"], ["Transactional", s.transactional === false ? "No, run statements individually" : "Yes"], ["Phase", s.phase_label], ["Depends on", (s.depends_on || []).join(", ")]]),
      s.manual ? h("div", {}, h("h4", {}, "Manual step"), h("p", {}, s.manual_description || "—")) : h("div", {}, h("h4", {}, "Up SQL"), codeBlock(s.up_script, { placeholder: "No SQL." })),
      s.manual ? null : h("div", {}, h("h4", {}, "Down SQL"), codeBlock(s.down_script, { placeholder: "No rollback is defined for this step." })),
      h("div", {}, h("h4", {}, "Prechecks"), checksTable(s.prechecks || [])),
      h("div", {}, h("h4", {}, "Postchecks"), checksTable(s.postchecks || [])),
      (s.online_notes || []).length ? h("div", {}, h("h4", {}, "Online change notes"), bullets(s.online_notes)) : null,
      (s.dependency_risks || []).length ? h("div", {}, h("h4", {}, "Dependency risks"), bullets(s.dependency_risks)) : null,
      h("div", {}, h("h4", {}, `Findings (${data.findings.length})`), data.findings.length ? data.findings.map((f) => h("div", { class: "row" }, sevBadge(f.severity), h("a", { href: routeHref(["run", ctx.runId, "findings"], { f: f.id }) }, f.title))) : h("p", { class: "muted" }, "None.")),
      h("div", {}, h("h4", {}, "Recommendations"), data.recommendations.length ? data.recommendations.map((r) => h("div", {}, h("a", { href: routeHref(["run", ctx.runId, "recommendations"], { r: r.id }) }, `${r.priority} ${r.title}`))) : h("p", { class: "muted" }, "None."))));
  }

  // --- sandbox ----------------------------------------------------------

  async function loadSandbox() {
    try {
      const status = await api(`${runPath}/sandbox`);
      renderSandbox(status);
    } catch (err) { mount(sandboxEl, errorState(err, loadSandbox)); }
  }

  function renderSandbox(status) {
    const lastResult = status.last_result;
    if (!status.available) {
      mount(sandboxEl, h("div", { class: "card stack" }, h("div", { class: "row" }, h("span", { class: "badge badge-outline" }, "Sandbox unavailable")), h("p", {}, status.reason || "This run cannot be tested."), lastResult ? resultView(lastResult) : null));
      return;
    }
    const input = h("input", { type: "text", id: "plan-hash", autocomplete: "off", spellcheck: "false", placeholder: "Type or paste the plan hash", value: "" });
    const understand = h("input", { type: "checkbox" });
    const errorEl = h("div", {});
    const button = h("button", { class: "btn btn-primary", disabled: true, onClick: start }, "Run sandbox test");
    const refresh = () => { button.disabled = status.busy || status.running_here || input.value.trim() !== status.plan_hash || !understand.checked; };
    input.addEventListener("input", refresh);
    understand.addEventListener("change", refresh);

    async function start() {
      mount(errorEl);
      button.disabled = true;
      try {
        await api(`${runPath}/sandbox`, { method: "POST", body: { plan_hash: input.value.trim() } });
        await ctx.jobs.refresh();
        loadSandbox();
      } catch (err) { mount(errorEl, notice(err.message, "bad")); refresh(); }
    }

    mount(sandboxEl, h("div", { class: "card stack" },
      h("p", {}, "This builds a private temporary SQLite copy on this computer, runs each step and its rollback there, and throws the copy away. It never connects to your source database."),
      notice(status.note, status.has_sample_rows ? "info" : "warn"),
      status.running_here ? notice(h("span", {}, "A sandbox test is running. ", h("button", { class: "link-btn", onClick: cancel }, "Cancel"), " Cancelling ends the process that holds the sample rows."), "info") : null,
      status.busy && !status.running_here ? notice("Another analysis or test is running. Try again when it finishes.", "warn") : null,
      h("div", { class: "row" }, h("label", { class: "field grow", for: "plan-hash" }, "Confirm the exact plan hash", input), status.plan_hash ? copyButton(status.plan_hash, "Copy plan hash") : null),
      h("label", { class: "check" }, understand, "I understand this runs only in a throwaway copy and proves nothing about production data."),
      errorEl,
      h("div", {}, button),
      lastResult ? resultView(lastResult) : null));

    const onJobDone = ctx.jobs.subscribe((job) => {
      if (job.kind === "sandbox" && !["starting", "running", "cancelling"].includes(job.state)) { onJobDone(); loadSandbox(); }
    });
    jobCleanups.push(onJobDone);
  }

  function resultView(result) {
    const counts = {};
    (result.results || []).forEach((r) => { counts[r.status] = (counts[r.status] || 0) + 1; });
    const columns = [
      { label: "Step", render: (r) => h("span", { class: "mono small" }, r.step_id) },
      { label: "Result", render: (r) => statusBadge(r.status) },
      { label: "Title", class: "title-cell", render: (r) => r.title },
      { label: "Rollback", render: (r) => r.rollback },
      { label: "Reason", render: (r) => h("span", { class: "small" }, r.reason || "—") },
    ];
    return h("div", { class: "stack" },
      h("h3", {}, "Latest result"),
      h("div", { class: "row" }, statusBadge(result.overall), h("span", { class: "small muted" }, `${result.engine}, ${result.mode === "live" ? "this run" : "saved run"}, finished ${result.finished_at || ""}`)),
      h("div", { class: "tiles" }, tile("Passed", fmtNumber(counts.passed || 0)), tile("Failed", fmtNumber(counts.failed || 0)), tile("Not testable", fmtNumber(counts.not_testable || 0))),
      result.schema_restored === null || result.schema_restored === undefined ? null : h("p", { class: "small" }, `Full rollback restored the schema: ${result.schema_restored ? "yes" : "no"}. ${result.schema_restored_reason || ""}`),
      (result.warnings || []).length ? h("div", {}, h("h4", {}, "Warnings"), bullets(result.warnings)) : null,
      dataTable(columns, (result.results || []).slice(0, 300), { emptyMessage: "No steps were tested" }),
      (result.results || []).length > 300 ? h("p", { class: "small muted" }, "Showing the first 300 steps.") : null);
  }

  async function cancel() {
    try { await api("/analysis/cancel", { method: "POST", body: {} }); ctx.jobs.refresh(); } catch (err) { toast(err.message); }
  }

  let lastKey = null;
  const jobCleanups = [];
  function sync() {
    const key = JSON.stringify(["q", "table", "flags", "page"].map((k) => query[k] || ""));
    if (key !== lastKey) { lastKey = key; loadList(); }
    syncDrawer();
  }
  sync();
  loadSandbox();
  return { update(q) { query = { ...q }; sync(); },
    destroy() { clearTimeout(debounce); requestId += 1; jobCleanups.forEach((fn) => fn()); if (drawer) { const d = drawer; drawer = null; drawerId = null; d.close(); } } };
}
