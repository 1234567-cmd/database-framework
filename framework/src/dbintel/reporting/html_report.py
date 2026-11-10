"""Self-contained HTML report: no external scripts, stylesheets, fonts or images, and every value is escaped."""
from __future__ import annotations

import html
from typing import Any, Optional

from .content import KIND_LABELS, KINDS, SEVERITIES, build_report
from .er import SVG_CSS, current_diagrams, proposed_diagrams

_CSS = """
:root { --bg:#fbfaf7; --surface:#ffffff; --head:#efece4; --text:#22211d; --muted:#6b6a63; --line:#d9d6cc; --accent:#2a5d8f;
  --good:#1f7a4a; --warn:#946200; --serious:#b4510f; --crit:#a82a2a; --info:#55677a; }
@media (prefers-color-scheme: dark) { :root { --bg:#17181a; --surface:#212326; --head:#2c2f33; --text:#e9e7e1; --muted:#a4a29a;
  --line:#3a3d42; --accent:#7fb3e0; --good:#62c493; --warn:#e0b14f; --serious:#ee9a5a; --crit:#f08787; --info:#a3b6c9; } }
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--text); font:15px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width: 1120px; margin: 0 auto; padding: 24px 16px 64px; }
h1 { font-size: 26px; margin: 0 0 4px; } h2 { font-size: 20px; margin: 36px 0 10px; border-bottom: 1px solid var(--line); padding-bottom: 4px; }
h3 { font-size: 16px; margin: 22px 0 8px; } h4 { font-size: 14px; margin: 14px 0 4px; }
nav { margin: 12px 0 8px; font-size: 13px; } nav a { color: var(--accent); margin-right: 12px; white-space: nowrap; }
.banner { background: var(--head); border: 1px solid var(--line); padding: 8px 12px; border-radius: 4px; margin: 12px 0; }
.muted { color: var(--muted); } code, pre { font-family: ui-monospace, Consolas, monospace; font-size: 12.5px; }
pre { background: var(--surface); border: 1px solid var(--line); padding: 10px; overflow-x: auto; border-radius: 4px; white-space: pre; }
table { border-collapse: collapse; width: 100%; font-size: 13.5px; background: var(--surface); }
th, td { border: 1px solid var(--line); padding: 4px 8px; text-align: left; vertical-align: top; overflow-wrap: anywhere; }
th { background: var(--head); font-weight: 600; } td.n, th.n { text-align: right; font-variant-numeric: tabular-nums; }
.wide { overflow-x: auto; } .tiles { display:flex; flex-wrap:wrap; gap:10px; margin: 12px 0; }
.tile { background: var(--surface); border:1px solid var(--line); border-radius:4px; padding:8px 14px; min-width: 120px; }
.tile b { display:block; font-size: 24px; font-variant-numeric: tabular-nums; } .tile span { color: var(--muted); font-size: 12px; }
details { background: var(--surface); border: 1px solid var(--line); border-radius: 4px; margin: 6px 0; padding: 4px 10px; }
summary { cursor: pointer; } dl { display:grid; grid-template-columns: 180px 1fr; gap: 2px 12px; margin: 8px 0; }
dt { color: var(--muted); font-size: 13px; } dd { margin:0; white-space: pre-wrap; overflow-wrap: anywhere; }
.sev { font-weight: 600; padding: 0 4px; font-size: 12px; } .critical { color: var(--crit); } .high { color: var(--serious); } .medium { color: var(--warn); }
.low { color: var(--info); } .informational { color: var(--muted); }
.bar { height: 8px; background: var(--accent); border-radius: 0 4px 4px 0; min-width: 2px; } .barcell { width: 40%; }
@media (max-width: 640px) { dl { grid-template-columns: 1fr; } }
"""


def e(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _table(header: list[str], rows: list[list[Any]], numeric: Optional[set[int]] = None) -> str:
    numeric = numeric or set()
    head = "".join(f'<th{" class=n" if i in numeric else ""}>{e(h)}</th>' for i, h in enumerate(header))
    body = "".join("<tr>" + "".join(f'<td{" class=n" if i in numeric else ""}>{e(c)}</td>' for i, c in enumerate(row)) + "</tr>" for row in rows)
    return f'<div class="wide"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def _list(items: list, fmt: Any = e) -> str:
    return "<ul>" + "".join(f"<li>{fmt(i)}</li>" for i in items) + "</ul>" if items else '<p class="muted">None.</p>'


def _pre(text: str) -> str:
    return f"<pre>{e(text)}</pre>"


def _dep(item: Any) -> str:
    if isinstance(item, dict):
        return e(", ".join(f"{k}: {v}" for k, v in item.items() if v not in (None, "", [])))
    return e(item)


def _bar_table(title: str, values: dict[str, int], classes: bool = False) -> str:
    peak = max(list(values.values()) + [1])
    rows = []
    for name, count in values.items():
        width = 100 * count / peak
        cls = f' class="sev {e(name)}"' if classes else ""
        bar = f'<div class="bar" style="width:{width:.1f}%" title="{e(name)}: {count}"></div>' if count else ""
        rows.append(f'<tr><td><span{cls}>{e(name)}</span></td><td class="n">{count}</td><td class="barcell">{bar}</td></tr>')
    return f'<h3>{e(title)}</h3><div class="wide"><table><thead><tr><th>Value</th><th class="n">Count</th><th>Share of largest</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


def _finding(f: dict[str, Any]) -> str:
    standards = "\n".join(f"{sid}: {f['standard_statements'].get(sid, '')}" for sid in f["standards"])
    fields = [("ID", f["id"]), ("Rule", f["rule_id"]), ("Severity", f["severity"]), ("Kind", f["kind"]), ("Category", f["category"]), ("Database", f["database"]),
              ("Table", f["table"] or "(none)"), ("Column", f["column"] or "(none)"), ("Evidence", f["evidence"]), ("Root cause", f["root_cause"]),
              ("Business impact", f["business_impact"]), ("Technical impact", f["technical_impact"]), ("Standards", standards),
              ("Recommended solution", f["recommended_solution"]), ("Complexity", f["complexity"]), ("Migration requirements", f["migration_requirements"]),
              ("Risks", f["risks"]), ("Validation strategy", f["validation_strategy"]), ("Confidence", f"{f['confidence']:.2f}"),
              ("Provisional standard", "yes" if f["provisional_standard"] else "no")]
    dl = "".join(f"<dt>{e(k)}</dt><dd>{e(v)}</dd>" for k, v in fields)
    where = " . ".join(x for x in (f["table"], f["column"]) if x)
    where = f' <code>{e(where)}</code>' if where else ""
    is_open = " open" if f["severity"] == "critical" else ""
    return (f'<details{is_open} id="f-{e(f["id"])}"><summary><span class="sev {e(f["severity"])}">{e(f["severity"]).upper()}</span> {e(f["title"])}{where}'
            f' <span class="muted">{e(f["id"])}</span></summary><dl>{dl}</dl></details>')


def _recommendation(r: dict[str, Any]) -> str:
    return (f'<details id="r-{e(r["id"])}"><summary><b>{e(r["priority"])}</b> {e(r["title"])} <span class="muted">score {e(r["priority_score"])}, {e(r["id"])}</span></summary>'
            f'<h4>Findings</h4><p><code>{e(", ".join(r["finding_ids"]))}</code></p>'
            f'<h4>Priority rationale</h4>{_list(r["priority_rationale"])}'
            f'<h4>Existing structure</h4>{_pre(r["existing_structure"])}<h4>Weakness</h4>{_pre(r["weakness"])}'
            f'<h4>Recommended structure</h4>{_pre(r["recommended_structure"])}'
            f'<h4>Before</h4>{_pre(r["before_after"]["before"])}<h4>After</h4>{_pre(r["before_after"]["after"])}'
            f'<h4>Proposed SQL</h4>{_pre(r["proposed_sql"])}'
            f'<h4>Application dependencies</h4>{_list(r["application_dependencies"], _dep)}'
            f'<h4>Data dependencies</h4>{_list(r["data_dependencies"], _dep)}'
            f'<h4>Data migration</h4>{_pre(r["data_migration"])}<h4>Rollback</h4>{_pre(r["rollback"])}'
            f'<h4>Validation tests</h4>{_list(r["validation_tests"])}<h4>Business notes</h4>{_list(r["business_logic_notes"])}'
            f'<p>Requires review: {"yes" if r["requires_review"] else "no"}</p></details>')


def _er_section(title: str, diagrams: list, data: list[dict]) -> str:
    out = [f"<h3>{e(title)}</h3>"]
    for diagram, record in zip(diagrams, data):
        out.append(f'<h4>{e(diagram.title)}</h4>{diagram.svg}')
        for note in record.get("notes", []):
            out.append(f'<p class="muted">{e(note)}</p>')
        out.append(f'<details><summary>Mermaid source</summary>{_pre(record["mermaid"])}</details>')
    return "".join(out)


_NAV = [("summary", "Summary"), ("scores", "Scores"), ("distributions", "Distributions"), ("findings", "Findings"), ("causes", "Root causes"),
        ("recommendations", "Recommendations"), ("migration", "Migration"), ("lineage", "Lineage"), ("architecture", "Architecture"), ("er", "ER diagrams"),
        ("roadmap", "Roadmap"), ("coverage", "Coverage"), ("warnings", "Warnings")]


def render_html(assessment: Any, data: dict | None = None) -> str:
    d = data if data is not None else build_report(assessment)
    s, h, m, a, c, r = d["summary"], d["health"], d["migration"], d["architecture"], d["coverage"], d["roadmap"]
    p: list[str] = []
    p.append(f'<h1>Database assessment: {e(d["source"]["name"])}</h1>')
    p.append(f'<p class="muted">Generated {e(d["generated_at"])}. Source: {e(d["source"]["label"])}. Plan hash: <code>{e(s["plan_hash"])}</code></p>')
    p.append('<div class="banner"><b>This report describes proposals only. Nothing has been changed.</b></div>')
    p.append("<nav>" + "".join(f'<a href="#{k}">{e(v)}</a>' for k, v in _NAV) + "</nav>")

    p.append('<section id="summary"><h2>Executive summary</h2>')
    tiles = [("Overall", "n/a" if h["overall"] is None else h["overall"]), ("Grade", h["grade"]), ("Confidence", f"{h['confidence']:.0%}"), ("Findings", s["findings_total"]),
             ("Critical", s["critical"]), ("High", s["high"]), ("Confirmed defects", s["confirmed_defects"]), ("Plan steps", s["plan_steps"])]
    p.append('<div class="tiles">' + "".join(f'<div class="tile"><b>{e(v)}</b><span>{e(k)}</span></div>' for k, v in tiles) + "</div>")
    p.append("".join(f"<p>{e(t)}</p>" for t in s["text"]))
    if s["top_risks"]:
        p.append("<h3>Top confirmed risks</h3>")
        p.append(_list(s["top_risks"], lambda x: f'<span class="sev {e(x["severity"])}">{e(x["severity"]).upper()}</span> {e(x["title"])} <code>{e(x["id"])}</code>'))
    p.append("</section>")

    p.append('<section id="scores"><h2>Health scores</h2>')
    overall = "not assessed" if h["overall"] is None else h["overall"]
    p.append(f'<p>Overall <b>{e(overall)}</b>, grade <b>{e(h["grade"])}</b>, confidence {h["confidence"]:.0%}. Capped: {"yes" if h["capped"] else "no"}.</p>')
    p.append(f'<p class="muted"><b>Method:</b> {e(h["method"])}</p>')
    p.append(_table(["Category", "Score", "Grade", "Confidence", "Weight", "Rules run", "Rules skipped", "Deductions"],
                    [[x["category"], "not assessed" if x["score"] is None else x["score"], x["grade"], f"{x['confidence']:.0%}", h["weights"][x["category"]], x["rules_executed"],
                      x["rules_skipped"], len(x["deductions"])] for x in h["categories"]], numeric={1, 3, 4, 5, 6, 7}))
    for x in h["categories"]:
        if x["deductions"] or x["skipped_reasons"]:
            body = _table(["Rule", "Title", "Count", "Points"], [[i["rule_id"], i["title"], i["count"], i["points"]] for i in x["deductions"]], {2, 3}) if x["deductions"] else ""
            if x["skipped_reasons"]:
                body += "<h4>Skipped or failed rules</h4>" + _list(x["skipped_reasons"])
            p.append(f'<details><summary>{e(x["category"])}: {len(x["deductions"])} deduction(s)</summary>{body}</details>')
    p.append("</section>")

    p.append('<section id="distributions"><h2>Distributions</h2>')
    p.append(_bar_table("Severity", d["distribution"]["severity"], True))
    p.append(_bar_table("Kind", d["distribution"]["kind"]))
    p.append(_bar_table("Category", d["distribution"]["category"]))
    p.append("</section>")

    p.append(f'<section id="findings"><h2>Findings ({d["findings_total"]})</h2>')
    for kind in KINDS:
        items = d["findings"][kind]
        p.append(f'<h3 id="kind-{kind}">{e(KIND_LABELS[kind])} ({len(items)})</h3>')
        p.append("".join(_finding(f) for f in items) if items else '<p class="muted">None.</p>')
    p.append("</section>")

    p.append(f'<section id="causes"><h2>Root cause groups ({len(d["root_cause_groups"])})</h2>')
    p.append(_table(["Id", "Cause", "Count", "Tables", "Systemic", "Rules", "Shared fix", "Note"],
                    [[g["id"], g["cause"], g["count"], len(g["tables"]), "yes" if g["systemic"] else "no", ", ".join(g["rule_ids"]), ", ".join(g["shared_fix_ops"]), g["note"]] for g in d["root_cause_groups"]], {2, 3}))
    p.append("</section>")

    p.append(f'<section id="recommendations"><h2>Recommendations ({len(d["recommendations"])})</h2>')
    p.append("".join(_recommendation(x) for x in d["recommendations"]))
    p.append("</section>")

    p.append('<section id="migration"><h2>Migration plan summary</h2>')
    p.append(f'<p>Target {e(m["dialect"])}. Plan hash <code>{e(m["plan_hash"])}</code>. {m["total_steps"]} step(s): {m["executable_steps"]} executable, {m["manual_steps"]} manual, '
             f'{m["destructive_steps"]} destructive, {m["refused_steps"]} refused, {m["irreversible_steps"]} not reversible.</p>')
    p.append(f'<p><b>Backup first:</b> {e(m["backup_recommendation"])}</p>')
    p.append(_table(["Order", "Id", "Title", "Type", "Destructive", "Reversible", "Loss risk", "Lock risk"],
                    [[x["order"], x["id"], x["title"], "manual" if x["manual"] else "sql", x["destructive"], x["reversible"], x["data_loss_risk"], x["lock_risk"]] for x in m["steps"]], {0}))
    p.append(f'<h3>Destructive steps ({m["destructive_steps"]})</h3>')
    p.append(_list(m["destructive"], lambda x: e(f"{x['id']}: {x['title']} (table {x['table']}, loss risk {x['data_loss_risk']}, reversible {x['reversible']})")))
    p.append(f'<h3>Refused steps ({m["refused_steps"]})</h3>')
    p.append(_list(m["refused"], lambda x: e(f"{x['id']}: {x['title']}. Reason: {x['reason']}")))
    p.append(f'<p>Unaddressed findings: {len(m["unaddressed_findings"])}. Already satisfied: {len(m["satisfied_findings"])}.</p>')
    if m["notes"]:
        p.append("<h3>Plan notes</h3>" + _list(m["notes"]))
    p.append("<p>Generated SQL files are in the <code>migrations</code> folder.</p></section>")

    line = d["lineage"]
    p.append(f'<section id="lineage"><h2>Lineage ({len(line["edges"])} edges)</h2>')
    p.append(_table(["Source", "Target", "Via", "Kind"], [[x["source"], x["target"], x["via"], x["kind"]] for x in line["edges"]]) if line["edges"] else '<p class="muted">No lineage edges were found.</p>')
    p.append(_list(line["gaps"] + line["notes"]))
    p.append("</section>")

    p.append('<section id="architecture"><h2>Architecture</h2>')
    p.append(f'<h3>Tables ({len(a["tables"])})</h3>')
    p.append(_table(["Table", "Columns", "Primary key", "FKs out", "Referenced by", "Indexes", "Rows", "RLS"],
                    [[t["name"], t["columns"], ", ".join(t["primary_key"]) or "(none)", t["foreign_keys"], t["referenced_by"], t["indexes"], t["row_count"], t["rls_enabled"]] for t in a["tables"]], {1, 3, 4, 5, 6}))
    p.append(f'<h3>Relations ({len(a["relations"])})</h3>')
    p.append(_table(["From", "Columns", "To", "Ref columns", "On delete", "On update"],
                    [[x["from"], ",".join(x["columns"]), x["to"], ",".join(x["ref_columns"]), x["on_delete"], x["on_update"]] for x in a["relations"]]) if a["relations"] else '<p class="muted">None.</p>')
    p.append(f'<h3>Domains by connectivity ({len(a["domains"])})</h3>')
    p.append(_list(a["domains"], lambda x: f'<b>{e(x["name"])}</b> ({x["size"]}): <code>{e(", ".join(x["tables"]))}</code>'))
    p.append("</section>")

    db_diagrams_current = current_diagrams(assessment.db)
    db_diagrams_proposed = proposed_diagrams(assessment.db, assessment.findings, assessment.plan)
    p.append('<section id="er"><h2>ER diagrams</h2>')
    p.append('<p class="muted">Solid lines are existing foreign keys; dashed lines and highlighted columns are proposed. The Mermaid source is under each diagram.</p>')
    p.append(_er_section("Current", db_diagrams_current, d["er"]["current"]))
    p.append(_er_section("Proposed", db_diagrams_proposed, d["er"]["proposed"]))
    p.append("</section>")

    p.append('<section id="roadmap"><h2>Improvement roadmap</h2>')
    p.append(f'<p class="muted">{e(r["basis"])}</p><h3>Prerequisites</h3>{_list(r["prerequisites"])}')
    for phase in r["phases"]:
        p.append(f'<h3>Phase {phase["phase"]}: {e(phase["name"])}</h3>')
        p.append(_table(["Rec", "Title", "Priority", "Score", "Steps", "Depends on", "Moved for"],
                        [[i["recommendation"], i["title"], i["priority"], i["priority_score"], ", ".join(i["steps"]), ", ".join(i["depends_on"]), i["moved_forward_for"]] for i in phase["items"]], {3}))
    p.append("</section>")

    p.append('<section id="coverage"><h2>Coverage</h2>')
    p.append(f'<p>{c["rules_executed_count"]} rules executed, {c["skipped_count"]} skipped, {c["errors_count"]} errors. Inputs available: {e(", ".join(c["capabilities"]) or "(none)")}.</p>')
    p.append(f'<details><summary>Executed rules ({c["rules_executed_count"]})</summary><p><code>{e(", ".join(c["rules_executed"]))}</code></p></details>')
    p.append(f'<h3>Skipped ({c["skipped_count"]})</h3>')
    p.append(_table(["Rule", "Reason"], [[x["rule"], x["reason"]] for x in c["skipped"]]) if c["skipped"] else '<p class="muted">None.</p>')
    p.append(f'<h3>Errors ({c["errors_count"]})</h3>')
    p.append(_table(["Rule", "Error"], [[x["rule"], x["error"]] for x in c["errors"]]) if c["errors"] else '<p class="muted">None.</p>')
    p.append("</section>")

    p.append(f'<section id="warnings"><h2>Import warnings ({len(d["import_warnings"])})</h2>{_list(d["import_warnings"])}<h2>Limitations</h2>{_list(d["limitations"])}</section>')
    title = f"dbintel: {d['source']['name']}"
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            f"<title>{e(title)}</title><style>{_CSS}{SVG_CSS}</style></head><body><main>" + "".join(p) + "</main></body></html>\n")
