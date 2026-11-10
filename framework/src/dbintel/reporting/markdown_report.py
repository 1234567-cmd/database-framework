"""Markdown report. Identifiers are in code spans, SQL in fenced blocks and table cells are escaped."""
from __future__ import annotations

import re
from typing import Any

from .content import KIND_LABELS, KINDS, SEVERITIES, build_report


def _cell(value: Any) -> str:
    text = "" if value is None else str(value)
    return re.sub(r"\s+", " ", text.replace("\\", "\\\\").replace("|", "\\|").replace("<", "&lt;")).strip()


def _text(value: Any) -> str:
    return "" if value is None else str(value).replace("<", "&lt;").strip()


def _code(value: Any) -> str:
    text = str(value if value is not None else "")
    fence = "``" if "`" in text else "`"
    pad = " " if text.startswith("`") or text.endswith("`") else ""
    return f"{fence}{pad}{text}{pad}{fence}"


def _fence(body: str, lang: str = "sql") -> str:
    ticks = max([len(m) for m in re.findall(r"`+", body)] + [2]) + 1
    bar = "`" * ticks
    return f"{bar}{lang}\n{body.rstrip()}\n{bar}"


def _table(header: list[str], rows: list[list[Any]]) -> str:
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(_cell(c) for c in row) + " |" for row in rows]
    return "\n".join(out)


def _finding(f: dict[str, Any]) -> str:
    standards = "; ".join(f"{sid}: {f['standard_statements'].get(sid, '')}" for sid in f["standards"])
    fields = [("ID", _code(f["id"])), ("Rule", _code(f["rule_id"])), ("Severity", f["severity"]), ("Kind", f["kind"]),
              ("Category", f["category"]), ("Database", _code(f["database"])), ("Table", _code(f["table"]) if f["table"] else "(none)"),
              ("Column", _code(f["column"]) if f["column"] else "(none)"), ("Evidence", _text(f["evidence"])), ("Root cause", _text(f["root_cause"])),
              ("Business impact", _text(f["business_impact"])), ("Technical impact", _text(f["technical_impact"])),
              ("Standards", _text(standards)), ("Recommended solution", _text(f["recommended_solution"])), ("Complexity", _text(f["complexity"])),
              ("Migration requirements", _text(f["migration_requirements"])), ("Risks", _text(f["risks"])),
              ("Validation strategy", _text(f["validation_strategy"])), ("Confidence", f"{f['confidence']:.2f}"),
              ("Provisional standard", "yes" if f["provisional_standard"] else "no")]
    body = "\n".join(f"- **{label}:** {value}" for label, value in fields)
    return f"#### {_cell(f['severity']).upper()}: {_text(f['title'])}\n\n{body}\n"


def _recommendation(r: dict[str, Any]) -> str:
    parts = [f"### {_text(r['id'])} [{r['priority']}] {_text(r['title'])}", f"Priority score {r['priority_score']}. Findings: {', '.join(_code(x) for x in r['finding_ids'])}.",
             "**Priority rationale:** " + _text(" ".join(r["priority_rationale"])), "**Existing structure:**", _fence(r["existing_structure"]), "**Weakness:**", _text(r["weakness"]),
             "**Recommended structure:**", _fence(r["recommended_structure"]), "**Before:**", _fence(r["before_after"]["before"]), "**After:**", _fence(r["before_after"]["after"]),
             "**Proposed SQL:**", _fence(r["proposed_sql"]), "**Application dependencies:**"]
    parts += [_list(r["application_dependencies"], _dep), "**Data dependencies:**", _list(r["data_dependencies"], _dep),
              "**Data migration:** " + _text(r["data_migration"]), "**Rollback:** " + _text(r["rollback"]), "**Validation tests:**", _list(r["validation_tests"], _text),
              "**Business notes:**", _list(r["business_logic_notes"], _text), f"**Requires review:** {'yes' if r['requires_review'] else 'no'}"]
    return "\n\n".join(parts) + "\n"


def _dep(item: Any) -> str:
    if isinstance(item, dict):
        return _text(", ".join(f"{k}: {v}" for k, v in item.items() if v not in (None, "", [])))
    return _text(item)


def _list(items: list, fmt: Any) -> str:
    return "\n".join(f"- {fmt(i)}" for i in items) if items else "- None."


def render_markdown(assessment: Any, data: dict | None = None) -> str:
    d = data if data is not None else build_report(assessment)
    s = d["summary"]
    h = d["health"]
    out: list[str] = [f"# Database assessment: {_cell(d['source']['name'])}", f"Generated {d['generated_at']}. Plan hash `{s['plan_hash']}`.",
                      "**This report describes proposals only. Nothing has been changed.**", "## Executive summary", "\n\n".join(_text(t) for t in s["text"])]
    if s["top_risks"]:
        out.append("Top confirmed risks:\n\n" + "\n".join(f"- [{r['severity']}] {_text(r['title'])} ({_code(r['id'])})" for r in s["top_risks"]))

    out.append("## Health scores")
    overall = "not assessed" if h["overall"] is None else h["overall"]
    out.append(f"Overall **{overall}**, grade **{h['grade']}**, confidence {h['confidence']:.0%}. Capped: {'yes' if h['capped'] else 'no'}.")
    out.append("**Method:** " + _text(h["method"]))
    out.append(_table(["Category", "Score", "Grade", "Confidence", "Weight", "Rules run", "Rules skipped", "Deductions"],
                      [[c["category"], "not assessed" if c["score"] is None else c["score"], c["grade"], f"{c['confidence']:.0%}", h["weights"][c["category"]], c["rules_executed"],
                        c["rules_skipped"], len(c["deductions"])] for c in h["categories"]]))
    for c in h["categories"]:
        if c["deductions"] or c["skipped_reasons"]:
            out.append(f"### Deductions: {c['category']}")
            if c["deductions"]:
                out.append(_table(["Rule", "Title", "Count", "Points"], [[x["rule_id"], x["title"], x["count"], x["points"]] for x in c["deductions"]]))
            if c["skipped_reasons"]:
                out.append(_list(c["skipped_reasons"], _text))

    out.append("## Distributions")
    out.append(_table(["Severity", "Count"], [[k, d["distribution"]["severity"][k]] for k in SEVERITIES]))
    out.append(_table(["Kind", "Count"], [[k, d["distribution"]["kind"][k]] for k in KINDS]))
    out.append(_table(["Category", "Count"], [[k, v] for k, v in d["distribution"]["category"].items()]))

    out.append(f"## Findings ({d['findings_total']})")
    for kind in KINDS:
        items = d["findings"][kind]
        out.append(f"### {KIND_LABELS[kind]} ({len(items)})")
        out.append("\n".join(_finding(f) for f in items) if items else "None.")

    out.append(f"## Root cause groups ({len(d['root_cause_groups'])})")
    out.append(_table(["Id", "Cause", "Count", "Tables", "Systemic", "Rules", "Shared fix"],
                      [[g["id"], g["cause"], g["count"], len(g["tables"]), "yes" if g["systemic"] else "no", ", ".join(g["rule_ids"]), ", ".join(g["shared_fix_ops"])] for g in d["root_cause_groups"]]))

    out.append(f"## Recommendations ({len(d['recommendations'])})")
    out += [_recommendation(r) for r in d["recommendations"]]

    m = d["migration"]
    out.append("## Migration plan summary")
    out.append(f"Target dialect {m['dialect']}. Plan hash `{m['plan_hash']}`. {m['total_steps']} step(s): {m['executable_steps']} executable, {m['manual_steps']} manual, "
               f"{m['destructive_steps']} destructive, {m['refused_steps']} refused, {m['irreversible_steps']} not reversible.")
    out.append("**Backup first:** " + _text(m["backup_recommendation"]))
    out.append(_table(["Order", "Id", "Title", "Type", "Destructive", "Reversible", "Loss risk", "Lock risk"],
                      [[s2["order"], s2["id"], s2["title"], "manual" if s2["manual"] else "sql", s2["destructive"], s2["reversible"], s2["data_loss_risk"], s2["lock_risk"]] for s2 in m["steps"]]))
    out.append(f"### Destructive steps ({m['destructive_steps']})")
    out.append(_list(m["destructive"], lambda x: f"{x['id']}: {_text(x['title'])} (table {x['table']}, loss risk {x['data_loss_risk']}, reversible {x['reversible']})"))
    out.append(f"### Refused steps ({m['refused_steps']})")
    out.append(_list(m["refused"], lambda x: f"{x['id']}: {_text(x['title'])}. Reason: {_text(x['reason'])}"))
    out.append(f"Unaddressed findings: {len(m['unaddressed_findings'])}. Already satisfied: {len(m['satisfied_findings'])}.")
    if m["notes"]:
        out.append("### Plan notes\n\n" + _list(m["notes"], _text))
    out.append("Generated SQL files are in the `migrations` folder.")

    line = d["lineage"]
    out.append(f"## Lineage ({len(line['edges'])} edges)")
    out.append(_table(["Source", "Target", "Via", "Kind"], [[e["source"], e["target"], e["via"], e["kind"]] for e in line["edges"]]) if line["edges"] else "No lineage edges were found.")
    out.append(_list(line["gaps"] + line["notes"], _text))

    a = d["architecture"]
    out.append("## Architecture")
    out.append(f"### Tables ({len(a['tables'])})")
    out.append(_table(["Table", "Columns", "Primary key", "FKs out", "Referenced by", "Indexes", "Rows", "RLS"],
                      [[t["name"], t["columns"], ", ".join(t["primary_key"]) or "(none)", t["foreign_keys"], t["referenced_by"], t["indexes"], t["row_count"], t["rls_enabled"]] for t in a["tables"]]))
    out.append(f"### Relations ({len(a['relations'])})")
    out.append(_table(["From", "Columns", "To", "Ref columns", "On delete", "On update"],
                      [[r["from"], ",".join(r["columns"]), r["to"], ",".join(r["ref_columns"]), r["on_delete"], r["on_update"]] for r in a["relations"]]) if a["relations"] else "None.")
    out.append(f"### Domains by connectivity ({len(a['domains'])})")
    out.append(_list(a["domains"], lambda x: f"**{_text(x['name'])}** ({x['size']}): {', '.join(_code(n) for n in x['tables'])}"))

    out.append("### ER diagrams")
    for label, diagrams in (("Current", d["er"]["current"]), ("Proposed", d["er"]["proposed"])):
        for diagram in diagrams:
            out.append(f"#### {label}: {_text(diagram['title'])}")
            out.append(_fence(diagram["mermaid"], "mermaid"))

    r = d["roadmap"]
    out.append("## Improvement roadmap")
    out.append(_text(r["basis"]))
    out.append("Prerequisites:\n\n" + _list(r["prerequisites"], _text))
    for phase in r["phases"]:
        out.append(f"### Phase {phase['phase']}: {_text(phase['name'])}")
        out.append(_table(["Rec", "Title", "Priority", "Score", "Steps", "Depends on", "Moved for"],
                          [[i["recommendation"], i["title"], i["priority"], i["priority_score"], ", ".join(i["steps"]), ", ".join(i["depends_on"]), i["moved_forward_for"]] for i in phase["items"]]))

    c = d["coverage"]
    out.append("## Coverage")
    out.append(f"{c['rules_executed_count']} rules executed, {c['skipped_count']} skipped, {c['errors_count']} errors. Inputs available: {', '.join(c['capabilities']) or '(none)'}.")
    out.append("### Executed\n\n" + (", ".join(_code(x) for x in c["rules_executed"]) or "None."))
    out.append("### Skipped")
    out.append(_table(["Rule", "Reason"], [[x["rule"], x["reason"]] for x in c["skipped"]]) if c["skipped"] else "None.")
    out.append("### Errors")
    out.append(_table(["Rule", "Error"], [[x["rule"], x["error"]] for x in c["errors"]]) if c["errors"] else "None.")

    out.append(f"## Import warnings ({len(d['import_warnings'])})")
    out.append(_list(d["import_warnings"], _text))
    out.append("## Limitations")
    out.append(_list(d["limitations"], _text))
    return "\n\n".join(out) + "\n"
