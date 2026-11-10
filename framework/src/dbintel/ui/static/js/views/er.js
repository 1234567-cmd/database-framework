// Interactive ER diagram. Shows one domain or a focused neighbourhood; the whole schema is never drawn at once.
import { h, s, mount, clear, fmtNumber } from "../dom.js";
import { api, download } from "../api.js";
import { routeHref } from "../router.js";
import { errorState, notice, selectField, skeleton, toast } from "../components.js";
import { edgePath, layoutGraph, HEADER_HEIGHT, NODE_WIDTH, ROW_HEIGHT, shownColumns } from "../layout.js";

export function mountView(ctx) {
  const root = ctx.root;
  const runPath = `/runs/${encodeURIComponent(ctx.runId)}`;
  let query = { ...ctx.query };
  let requestId = 0;
  let view = null;
  let names = [];
  let selectedNode = null;

  const controls = h("div", { class: "filters no-print" });
  const canvasEl = h("div", { class: "er-canvas" });
  const sideEl = h("div", { class: "er-side" });
  const noteEl = h("div", { class: "stack" });
  mount(root, h("div", { class: "page-head" }, h("div", {}, h("h1", {}, "ER diagram"), h("p", {}, "Drag to pan, scroll to zoom, click a table to focus on it and its neighbours."))),
    controls, noteEl, h("div", { class: "er-layout section" }, canvasEl, sideEl));

  function go(patch) {
    const next = { ...query, ...patch };
    Object.keys(next).forEach((k) => { if (next[k] === "" || next[k] === undefined || next[k] === null) delete next[k]; });
    ctx.go(next);
  }

  async function load() {
    const id = ++requestId;
    mount(canvasEl, h("div", { class: "state" }, skeleton(6)));
    const params = new URLSearchParams();
    ["mode", "diagram", "focus", "hops"].forEach((k) => { if (query[k]) params.set(k, query[k]); });
    try {
      if (!names.length) names = (await api(`${runPath}/table-names`)).names;
      view = await api(`${runPath}/er?${params.toString()}`);
      if (id !== requestId) return;
      selectedNode = view.focus ? view.nodes.find((n) => n.name === view.focus) || null : null;
      renderControls();
      renderNotes();
      renderCanvas();
      renderSide();
    } catch (err) { if (id === requestId) mount(canvasEl, errorState(err, load)); }
  }

  function renderControls() {
    const searchInput = h("input", { type: "search", id: "er-search", list: "er-tables", placeholder: "Table name, press Enter", value: query.highlight || "",
      onKeydown: (e) => { if (e.key === "Enter") { e.preventDefault(); runSearch(searchInput.value); } },
      onChange: (e) => runSearch(e.target.value) });
    const datalist = h("datalist", { id: "er-tables" }, names.slice(0, 400).map((n) => h("option", { value: n })));
    const modeButtons = h("div", { class: "seg", role: "group", "aria-label": "Schema shown" }, [["current", "Current"], ["proposed", "Proposed"]].map(([m, label]) =>
      h("button", { "aria-pressed": (query.mode || "current") === m ? "true" : "false", disabled: m === "proposed" && !view.proposed_available, onClick: () => go({ mode: m === "current" ? "" : m }) }, label)));
    const domainOptions = view.diagrams.map((d) => {
      const around = (d.title || "").match(/\(\d+ of \d+: around (.+)\)$/);
      return [String(d.index), around ? `${around[1]} (${d.size} tables)` : `${d.title} (${d.size} tables)`];
    });
    const hops = selectField("er-hops", "Neighbours", [["1", "1 step"], ["2", "2 steps"]], query.hops || "1", (v) => go({ hops: v === "1" ? "" : v }));
    mount(controls,
      h("div", { class: "row-spread" },
        h("div", { class: "row" }, modeButtons,
          h("button", { class: "btn", disabled: !view.focus && query.diagram === undefined, onClick: () => go({ focus: "", highlight: "", diagram: query.diagram }) }, "Show domain view")),
        h("div", { class: "row" },
          h("button", { class: "btn", onClick: downloadMermaid }, "Download Mermaid"),
          h("span", { class: "small muted" }, `${fmtNumber(view.nodes.length)} of ${fmtNumber(view.total_tables)} tables shown`))),
      h("div", { class: "filter-grid" },
        h("label", { class: "field", for: "er-search" }, "Find a table", searchInput, datalist),
        selectField("er-domain", "Domain", domainOptions, view.selected_diagram === null || view.selected_diagram === undefined ? "" : String(view.selected_diagram), (v) => go({ diagram: v, focus: "", highlight: "" }), { includeAny: !view.diagrams.length || view.selected_diagram === null, anyLabel: view.focus ? "Focused view" : "All tables" }),
        hops));
  }

  function renderNotes() {
    const notes = [...view.notes];
    if (view.truncated) notes.push(`Only the first ${view.node_limit} tables are drawn in this view. Use focus or a smaller domain.`);
    mount(noteEl, notes.map((n) => notice(n, "warn")),
      h("div", { class: "legend" }, h("span", {}, h("span", { class: "legend-line" }), "existing foreign key"), h("span", {}, h("span", { class: "legend-line proposed" }), "proposed"), h("span", {}, "dashed box: table outside this view")));
  }

  function runSearch(text) {
    const value = (text || "").trim();
    if (!value) { go({ highlight: "" }); return; }
    const lower = value.toLowerCase();
    const exact = names.find((n) => n.toLowerCase() === lower);
    const partial = exact || names.find((n) => n.toLowerCase().includes(lower));
    if (partial) go({ focus: partial, highlight: "", diagram: "" });
    else toast(`No table matches ${value}`);
  }

  async function downloadMermaid() {
    const params = new URLSearchParams();
    ["mode", "diagram", "focus", "hops"].forEach((k) => { if (query[k]) params.set(k, query[k]); });
    if (view.selected_diagram !== null && view.selected_diagram !== undefined && !query.focus) params.set("diagram", view.selected_diagram);
    try { await download(`${runPath}/er/mermaid?${params.toString()}`, "er_diagram.mmd"); }
    catch (err) { toast(err.message); }
  }

  function renderCanvas() {
    if (!view.nodes.length) {
      mount(canvasEl, h("div", { class: "state" }, h("h3", {}, "Nothing to draw"), h("p", {}, "This selection has no tables.")));
      return;
    }
    const nodes = view.nodes;
    const layout = layoutGraph(nodes, view.edges, view.focus);
    const svg = s("svg", { class: "er-svg", role: "img", "aria-label": `ER diagram with ${nodes.length} tables` });
    const defs = s("defs", {}, marker("er-arrow", ""), marker("er-arrow-p", "proposed"));
    const viewport = s("g", {});
    svg.appendChild(defs);
    svg.appendChild(viewport);
    view.edges.forEach((e) => {
      const from = layout.boxes.get(e.source); const to = layout.boxes.get(e.target);
      if (!from || !to) return;
      viewport.appendChild(s("path", { d: edgePath(from, to), class: `er-edge${e.proposed ? " proposed" : ""}`, "marker-end": `url(#${e.proposed ? "er-arrow-p" : "er-arrow"})` },
        s("title", {}, `${e.source}(${e.columns.join(", ")}) references ${e.target}(${e.ref_columns.join(", ")})${e.proposed ? " (proposed)" : ""}`)));
    });
    nodes.forEach((n) => viewport.appendChild(nodeElement(n, layout.boxes.get(n.name))));
    const toolbar = h("div", { class: "er-toolbar no-print" },
      h("button", { class: "btn btn-small", "aria-label": "Zoom in", onClick: () => zoom(1.25) }, "+"),
      h("button", { class: "btn btn-small", "aria-label": "Zoom out", onClick: () => zoom(0.8) }, "−"),
      h("button", { class: "btn btn-small", onClick: fit }, "Fit"));
    mount(canvasEl, svg, toolbar);

    let scale = 1; let tx = 0; let ty = 0;
    function apply() { viewport.setAttribute("transform", `translate(${tx} ${ty}) scale(${scale})`); }
    function zoom(factor, cx, cy) {
      const rect = svg.getBoundingClientRect();
      const px = cx === undefined ? rect.width / 2 : cx - rect.left;
      const py = cy === undefined ? rect.height / 2 : cy - rect.top;
      const next = Math.max(0.15, Math.min(3, scale * factor));
      tx = px - ((px - tx) * next) / scale;
      ty = py - ((py - ty) * next) / scale;
      scale = next;
      apply();
    }
    function fit() {
      const rect = svg.getBoundingClientRect();
      const margin = 24;
      scale = Math.max(0.15, Math.min(1.2, Math.min((rect.width - margin) / layout.width, (rect.height - margin) / layout.height)));
      tx = (rect.width - layout.width * scale) / 2;
      ty = (rect.height - layout.height * scale) / 2;
      apply();
    }
    let drag = null;
    svg.addEventListener("pointerdown", (e) => {
      if (e.target.closest(".er-node") || e.button !== 0) return;
      drag = { x: e.clientX, y: e.clientY, tx, ty };
      svg.classList.add("panning");
      svg.setPointerCapture(e.pointerId);
    });
    svg.addEventListener("pointermove", (e) => { if (drag) { tx = drag.tx + e.clientX - drag.x; ty = drag.ty + e.clientY - drag.y; apply(); } });
    const endDrag = () => { drag = null; svg.classList.remove("panning"); };
    svg.addEventListener("pointerup", endDrag);
    svg.addEventListener("pointercancel", endDrag);
    svg.addEventListener("wheel", (e) => { e.preventDefault(); zoom(e.deltaY < 0 ? 1.12 : 0.89, e.clientX, e.clientY); }, { passive: false });
    window.requestAnimationFrame(fit);
  }

  function marker(id, cls) {
    return s("marker", { id, viewBox: "0 0 8 8", refX: "7", refY: "4", markerWidth: "8", markerHeight: "8", orient: "auto-start-reverse" },
      s("path", { d: "M0 0 L8 4 L0 8 z", class: `er-arrow${cls ? " " + cls : ""}` }));
  }

  function nodeElement(n, box) {
    const highlight = (query.highlight || "").toLowerCase();
    const classes = ["er-node"]; if (n.external) classes.push("external"); if (n.focus) classes.push("focused"); if (n.changed) classes.push("changed");
    if (highlight && n.name.toLowerCase().includes(highlight)) classes.push("match");
    const g = s("g", { class: classes.join(" "), transform: `translate(${box.x} ${box.y})`, tabindex: "0", role: "button", "aria-label": `Table ${n.name}${n.external ? ", outside this view" : ""}`,
      onClick: () => focusOn(n), onKeydown: (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); focusOn(n); } } });
    g.appendChild(s("rect", { class: "er-node-box", width: box.width, height: box.height, rx: "4" }));
    g.appendChild(s("rect", { class: "er-node-head", width: box.width, height: HEADER_HEIGHT, rx: "4" }));
    g.appendChild(s("text", { class: "er-title", x: "10", y: "17" }, clip(n.name, 34)));
    g.appendChild(s("title", {}, n.name));
    if (n.external) { g.appendChild(s("text", { class: "er-col muted", x: "10", y: String(HEADER_HEIGHT + 14) }, "outside this view")); return g; }
    const { shown, hidden } = shownColumns(n);
    shown.forEach((c, i) => {
      const marks = [c.pk ? "PK" : "", c.fk ? "FK" : ""].filter(Boolean).join(" ");
      const text = clip(`${marks ? marks + " " : ""}${c.name}  ${c.type}`, 37);
      const cls = c.state ? `er-col state-${c.state}` : "er-col";
      g.appendChild(s("text", { class: cls, x: "10", y: String(HEADER_HEIGHT + 14 + i * ROW_HEIGHT) }, text, s("title", {}, `${c.name} ${c.type}${c.state ? ` (proposed: ${c.state})` : ""}`)));
    });
    if (hidden) g.appendChild(s("text", { class: "er-col muted", x: "10", y: String(HEADER_HEIGHT + 14 + shown.length * ROW_HEIGHT) }, `+${hidden} more columns`));
    return g;
  }

  function clip(text, limit) { return text.length <= limit ? text : `${text.slice(0, limit - 1)}…`; }

  function focusOn(n) {
    if (n.external || n.focus) { selectedNode = n; renderSide(); return; }
    go({ focus: n.name, highlight: "", diagram: "" });
  }

  function renderSide() {
    if (!selectedNode) {
      mount(sideEl, h("div", { class: "card card-tight" }, h("h3", {}, "Select a table"), h("p", { class: "muted small" }, "Click a table to focus on it. Its columns and links appear here.")),
        h("div", { class: "card card-tight" }, h("h3", {}, "Domains"), h("p", { class: "small muted" }, `${fmtNumber(view.diagrams.length)} neighbourhoods of up to 20 tables, built from foreign key connections.`)));
      return;
    }
    const n = selectedNode;
    const outEdges = view.edges.filter((e) => e.source === n.name);
    const inEdges = view.edges.filter((e) => e.target === n.name);
    const columnList = n.columns.length ? h("ul", { class: "small mono" }, n.columns.slice(0, 200).map((c) => h("li", {}, `${c.pk ? "PK " : ""}${c.fk ? "FK " : ""}${c.name} ${c.type}${c.state ? ` (proposed: ${c.state})` : ""}`))) : h("p", { class: "muted small" }, "Column details are in the diagram that owns this table.");
    mount(sideEl, h("div", { class: "card card-tight stack" },
      h("h3", { class: "mono" }, n.name),
      n.external ? null : h("div", { class: "row" }, h("a", { class: "btn btn-small", href: routeHref(["run", ctx.runId, "tables", n.name]) }, "Table details"), h("a", { class: "btn btn-small", href: routeHref(["run", ctx.runId, "findings"], { table: n.name }) }, `Findings (${fmtNumber(n.findings)})`)),
      h("div", {}, h("h4", {}, "Columns"), columnList),
      linkSection("References", outEdges.map((e) => e.target)), linkSection("Referenced by", inEdges.map((e) => e.source))));
  }

  function linkSection(title, names_) {
    return h("div", {}, h("h4", {}, title), names_.length ? h("ul", { class: "small" }, names_.map((name) => h("li", {}, h("button", { class: "link-btn mono", onClick: () => go({ focus: name, highlight: "", diagram: "" }) }, name)))) : h("p", { class: "muted small" }, "None shown."));
  }

  load();
  return { update(q) { query = { ...q }; load(); }, destroy() { requestId += 1; clear(root); } };
}
