// Import screen: choose a source, settings, and watch progress.
import { h, mount, fmtBytes, fmtDuration } from "../dom.js";
import { api, uploadFile } from "../api.js";
import { navigate } from "../router.js";
import { emptyState, notice, selectField, skeleton, toast } from "../components.js";

const SOURCE_KINDS = [["upload", "Upload files"], ["path", "Use a file path"], ["connection", "Connect read-only"]];

export function mountView(ctx) {
  const root = ctx.root;
  const state = { source: "upload", meta: null, uploads: { source: [], query_log: [], pipelines: [], profile: [] }, engine: "postgres", uploading: 0 };
  const unsub = ctx.jobs.subscribe(onJob);
  let submitBtn;
  let progressEl = h("div", {});
  let errorEl = h("div", {});
  let sourcePanel = h("div", {});

  mount(root, skeleton(8));
  load();

  async function load() {
    try {
      const meta = await api("/meta");
      state.meta = meta;
      state.uploads = meta.uploads;
      renderPage();
      onJob(ctx.jobs.current());
    } catch (err) { mount(root, emptyState("The form could not be loaded", err.message)); }
  }

  function field(id, label, input, hint) { return h("label", { class: "field", for: id }, label, input, hint ? h("span", { class: "hint" }, hint) : null); }

  function renderPage() {
    const nameInput = h("input", { type: "text", id: "db-name", placeholder: "Optional, for your report" });
    // Only values the person changes are sent, so an uploaded profile is not overwritten by form defaults.
    const defaults = { workload: "OLTP", tenancy: "none", tenant_column: "tenant_id", company_column: "company_id" };
    const settings = {};
    state.nameInput = nameInput;
    state.settings = settings;
    const o = state.meta.options;
    const sourceTabs = h("div", { class: "seg", role: "tablist" }, SOURCE_KINDS.map(([kind, label]) =>
      h("button", { role: "tab", "aria-selected": kind === state.source ? "true" : "false", onClick: (e) => { state.source = kind; renderSource(); e.currentTarget.parentElement.querySelectorAll("button").forEach((b) => b.setAttribute("aria-selected", b === e.currentTarget ? "true" : "false")); } }, label)));
    submitBtn = h("button", { class: "btn btn-primary", onClick: startRun }, "Run analysis");

    mount(root,
      h("div", { class: "page-head" }, h("div", {}, h("h1", {}, "New analysis"), h("p", {}, "Point dbintel at a dump, spreadsheet or a read-only connection. Nothing in the source is changed."))),
      progressEl,
      h("div", { class: "cols-main" },
        h("div", { class: "stack" },
          h("div", { class: "card stack" }, h("h3", {}, "Source"), sourceTabs, sourcePanel),
          h("div", { class: "card stack" }, h("h3", {}, "Optional inputs"),
            h("p", { class: "muted small" }, "These increase what can be assessed. Anything missing is reported as a limitation, not as a pass."),
            optionalFile("query_log", "Query log", "JSON or text; adds query-level checks."),
            optionalFile("pipelines", "Pipeline manifest", "YAML describing ETL jobs."),
            field("app-source", "Application source folder", (state.appSource = h("input", { type: "text", id: "app-source", placeholder: "C:\\code\\my-app" })), "Read in place to see which code touches each table. Leave empty if not available."))),
        h("div", { class: "stack" },
          h("div", { class: "card stack" }, h("h3", {}, "Settings"),
            h("div", { class: "form-grid" },
              field("db-name", "Database name", nameInput),
              selectField("workload", "Workload", o.workloads.map((w) => [w, w.replace("_", " ")]), defaults.workload, (v) => { settings.workload = v; }),
              selectField("tenancy", "Tenancy", o.tenancies.map((t) => [t, t === "none" ? "Single tenant" : `${t} model`]), defaults.tenancy, (v) => { settings.tenancy = v; }),
              field("tenant-col", "Tenant column", h("input", { type: "text", id: "tenant-col", value: defaults.tenant_column, onInput: (e) => { settings.tenant_column = e.target.value.trim(); } })),
              field("company-col", "Company column", h("input", { type: "text", id: "company-col", value: defaults.company_column, onInput: (e) => { settings.company_column = e.target.value.trim(); } })),
              selectField("target-dialect", "Proposed SQL dialect", [["", "Same as source"], ...o.dialects.map((d) => [d, d])], "", (v) => { settings.target_dialect = v; }),
              selectField("dialect", "Dump dialect", [["", "Detect automatically"], ...o.dialects.map((d) => [d, d])], "", (v) => { settings.dialect = v; })),
            h("label", { class: "check" }, h("input", { type: "checkbox", onChange: (e) => { settings.multi_company = e.target.checked; } }), "Multi-company data model"),
            uploadSlot("profile", "Profile YAML", ".yaml,.yml", "Optional. Anything you change in this form overrides the profile.")),
          errorEl,
          h("div", { class: "row" }, submitBtn, h("span", { class: "small muted" }, "A large dump can take several minutes.")))));
    renderSource();
  }

  function optionalFile(slot, label, hint) {
    const pathInput = h("input", { type: "text", id: `${slot}-path`, placeholder: "Full path on this computer (optional)" });
    state[`${slot}Path`] = pathInput;
    return h("div", { class: "stack" }, uploadSlot(slot, label, "", hint), h("label", { class: "field", for: `${slot}-path` }, "or a path on this computer", pathInput));
  }

  function renderSource() {
    if (state.source === "upload") {
      const input = h("input", { type: "file", multiple: true, hidden: true, onChange: (e) => { addFiles("source", [...e.target.files]); e.target.value = ""; } });
      const zone = h("div", { class: "dropzone", tabindex: "0", role: "button", "aria-label": "Choose files or drop them here",
        onClick: () => input.click(), onKeydown: (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); input.click(); } },
        onDragover: (e) => { e.preventDefault(); zone.classList.add("active"); },
        onDragleave: () => zone.classList.remove("active"),
        onDrop: (e) => { e.preventDefault(); zone.classList.remove("active"); addFiles("source", [...e.dataTransfer.files]); } },
      h("strong", {}, "Drop files here or choose files"), h("div", { class: "small muted" }, `SQL dump, CSV, Excel, JSON metadata or SQLite. Up to ${state.meta.max_upload_mb} MB per file.`), input);
      mount(sourcePanel, zone, fileList("source"), h("p", { class: "hint" }, "For a large dump, use a file path instead so nothing is copied."));
    } else if (state.source === "path") {
      const input = h("input", { type: "text", id: "source-path", placeholder: "C:\\exports\\database.sql or a folder of CSV files" });
      state.pathInput = input;
      mount(sourcePanel, field("source-path", "Full path", input, "The file is read in place and is not copied. Best for large dumps."));
    } else {
      const o = state.meta.options;
      const c = (state.conn = { engine: state.engine, host: "localhost", port: "", database: "", user: "", password: "", sqlite_path: "" });
      const engineSelect = selectField("engine", "Engine", o.engines.map((e) => [e, e === "postgres" ? "PostgreSQL" : e === "mysql" ? "MySQL" : "SQLite"]), state.engine, (v) => { state.engine = v; c.engine = v; renderSource(); });
      if (state.engine === "sqlite") {
        mount(sourcePanel, engineSelect, field("sqlite-path", "SQLite file path", h("input", { type: "text", id: "sqlite-path", onInput: (e) => { c.sqlite_path = e.target.value; } })), readOnlyNote());
      } else {
        mount(sourcePanel, h("div", { class: "form-grid" }, engineSelect,
          field("host", "Host", h("input", { type: "text", id: "host", value: c.host, onInput: (e) => { c.host = e.target.value; } })),
          field("port", "Port", h("input", { type: "number", id: "port", placeholder: state.engine === "mysql" ? "3306" : "5432", onInput: (e) => { c.port = e.target.value; } })),
          field("database", "Database", h("input", { type: "text", id: "database", onInput: (e) => { c.database = e.target.value; } })),
          field("user", "User", h("input", { type: "text", id: "user", autocomplete: "username", onInput: (e) => { c.user = e.target.value; } })),
          field("password", "Password", h("input", { type: "password", id: "password", autocomplete: "off", onInput: (e) => { c.password = e.target.value; } }), "Held in memory for this run only. Never saved.")),
        readOnlyNote());
      }
    }
  }

  function readOnlyNote() { return h("p", { class: "hint" }, "Connections are read-only. dbintel never changes the source database."); }

  function fileList(slot) {
    const files = state.uploads[slot] || [];
    if (!files.length) return h("ul", { class: "file-list", id: `files-${slot}` });
    return h("ul", { class: "file-list", id: `files-${slot}` }, files.map((f) =>
      h("li", {}, h("span", {}, f.name, " ", h("span", { class: "muted small" }, fmtBytes(f.bytes))),
        h("button", { class: "btn btn-small", onClick: () => clearSlot(slot) }, "Remove"))));
  }

  function uploadSlot(slot, label, accept, hint) {
    const holder = h("div", { id: `slot-${slot}` });
    state[`slot_${slot}`] = holder;
    const input = h("input", { type: "file", accept: accept || null, hidden: true, onChange: (e) => { addFiles(slot, [...e.target.files]); e.target.value = ""; } });
    const render = () => mount(holder, fileList(slot));
    render();
    state[`render_${slot}`] = render;
    return h("div", { class: "stack" }, h("div", { class: "row-spread" },
      h("div", {}, h("div", { class: "small" }, h("strong", {}, label)), hint ? h("div", { class: "hint" }, hint) : null),
      h("button", { class: "btn btn-small", onClick: () => input.click() }, "Choose file"), input), holder);
  }

  function renderFiles(slot) {
    if (slot === "source") renderSource();
    else if (state[`render_${slot}`]) state[`render_${slot}`]();
  }

  async function addFiles(slot, files) {
    for (const file of files) {
      if (file.size > state.meta.max_upload_mb * 1024 * 1024) {
        mount(errorEl, notice(`${file.name} is larger than the ${state.meta.max_upload_mb} MB limit. Use the file path option to read it in place.`, "bad"));
        continue;
      }
      try {
        state.uploading += 1;
        const res = await uploadFile(slot, file);
        state.uploads = res.uploads;
        renderFiles(slot);
      } catch (err) {
        mount(errorEl, notice(err.message, "bad"));
      } finally { state.uploading -= 1; }
    }
  }

  async function clearSlot(slot) {
    try {
      const res = await api(`/uploads/${slot}`, { method: "DELETE" });
      state.uploads = res.uploads;
      renderFiles(slot);
    } catch (err) { mount(errorEl, notice(err.message, "bad")); }
  }

  function buildRequest() {
    const body = { name: state.nameInput.value.trim() || null, settings: { ...state.settings }, inputs: {
      query_log_path: state.query_logPath.value.trim() || null,
      pipelines_path: state.pipelinesPath.value.trim() || null,
      app_source_dir: state.appSource.value.trim() || null,
    } };
    if (state.source === "upload") body.source = { kind: "upload" };
    if (state.source === "path") body.source = { kind: "path", path: state.pathInput ? state.pathInput.value : "" };
    if (state.source === "connection") body.source = { kind: "connection", connection: { ...state.conn } };
    return body;
  }

  async function startRun() {
    mount(errorEl);
    if (state.uploading) { mount(errorEl, notice("Please wait until the files have finished uploading.", "warn")); return; }
    submitBtn.disabled = true;
    try {
      const body = buildRequest();
      await api("/analysis", { method: "POST", body });
      if (state.conn) state.conn.password = "";
      await ctx.jobs.refresh();
    } catch (err) {
      mount(errorEl, notice(err.message, "bad"));
      submitBtn.disabled = false;
    }
  }

  function stageIcon(stateName) { return h("span", { class: `stage-icon ${stateName === "running" ? "running" : stateName === "done" ? "done" : stateName === "failed" || stateName === "cancelled" ? "failed" : ""}`, "aria-hidden": "true" }); }

  function onJob(job) {
    if (!state.meta) return;
    const active = job && ["starting", "running", "cancelling"].includes(job.state);
    if (active) state.sawActive = true;
    if (submitBtn) submitBtn.disabled = Boolean(active);
    if (!job || job.state === "idle" || (job.kind === "sandbox" && !active)) { mount(progressEl); return; }
    if (job.kind === "sandbox") {
      mount(progressEl, notice(h("span", {}, "A sandbox test is running. ", h("button", { class: "link-btn", onClick: cancel }, "Cancel the test"), ` ${fmtDuration(job.elapsed)}`), "info"));
      return;
    }
    const heading = job.state === "done" ? "Analysis complete" : job.state === "failed" ? "The analysis stopped" : job.state === "cancelled" ? "Analysis cancelled" : job.state === "cancelling" ? "Cancelling" : "Analysis running";
    const body = h("div", { class: "card stack", role: "group", "aria-label": "Analysis progress" },
      h("div", { class: "row-spread" },
        h("div", {}, h("h3", {}, heading), h("div", { class: "muted small" }, job.label || "")),
        h("div", { class: "row" }, h("span", { class: "tile-value nowrap", "aria-live": "off" }, fmtDuration(job.elapsed)),
          active ? h("button", { class: "btn btn-danger", disabled: job.state === "cancelling", onClick: cancel }, "Cancel") : null,
          job.state === "done" && job.run_id ? h("button", { class: "btn btn-primary", onClick: () => navigate(["run", job.run_id, "dashboard"]) }, "Open results") : null)),
      job.state === "failed" ? notice(job.error || "The analysis stopped.", "bad") : null,
      job.state === "cancelled" ? notice("No results were saved from this run.", "warn") : null,
      h("ul", { class: "progress-list", "aria-label": "Stages" }, job.stages.map((st) =>
        h("li", {}, stageIcon(st.state), h("span", {}, st.label), h("span", { class: "muted small nowrap" }, st.state === "done" ? fmtDuration(st.seconds) : st.state === "running" ? "working" : "")))));
    mount(progressEl, body);
    if (job.state === "done" && job.run_id && state.sawActive && !state.navigated) {
      state.navigated = true;
      toast("Analysis complete");
      setTimeout(() => navigate(["run", job.run_id, "dashboard"]), 700);
    }
  }

  async function cancel() {
    try { await api("/analysis/cancel", { method: "POST", body: {} }); ctx.jobs.refresh(); }
    catch (err) { mount(errorEl, notice(err.message, "bad")); }
  }

  return { destroy() { unsub(); } };
}
