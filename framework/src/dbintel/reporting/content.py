"""One plain data structure holds everything a report says. JSON, Markdown and HTML all render from it, so they agree."""
from __future__ import annotations

import dataclasses
import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Optional

from ..analyzers.security import looks_like_pan
from ..findings import CATEGORIES, FindingKind, Severity
from ..migrate.safety import is_financial_table
from ..model import Table
from ..scoring import CATEGORY_WEIGHTS
from .er import components, current_diagrams, proposed_database, proposed_diagrams

REPORT_FORMAT = "dbintel-report"
REPORT_VERSION = 1
SEVERITIES = [s.value for s in Severity]
KINDS = [k.value for k in FindingKind]
KIND_LABELS = {"confirmed_defect": "Confirmed defects", "optional_improvement": "Optional improvements",
               "context_dependent": "Context-dependent items"}
PHASE_OF_PRIORITY = {"P1": 1, "P2": 2, "P3": 3, "P4": 4}
PHASE_NAMES = {1: "Stabilize: critical and high-priority fixes", 2: "Strengthen: integrity and security",
               3: "Improve: design and maintainability", 4: "Refine: conventions and polish"}
_PAN_RUN = re.compile(r"(?<![\w.])\d(?:[ -]?\d){12,18}(?![\w.])")


def _mask_pan(match: re.Match) -> str:
    text = match.group(0)
    return "***" + re.sub(r"\D", "", text)[-2:] if looks_like_pan(text) else text


def scrub(value: Any) -> Any:
    """A safety net applied to the whole report: any card-like number that slipped through is masked."""
    if isinstance(value, str):
        return _PAN_RUN.sub(_mask_pan, value)
    if isinstance(value, dict):
        return {k: scrub(v) for k, v in value.items()}
    if isinstance(value, list):
        return [scrub(v) for v in value]
    return value


def distribution(findings: list[Any]) -> dict[str, dict[str, int]]:
    severity = Counter(f.severity.value for f in findings)
    kind = Counter(f.kind.value for f in findings)
    category = Counter(f.category for f in findings)
    return {"severity": {s: severity.get(s, 0) for s in SEVERITIES}, "kind": {k: kind.get(k, 0) for k in KINDS},
            "category": {c: category.get(c, 0) for c in CATEGORIES}}


def _executive_summary(a: Any, dist: dict[str, dict[str, int]]) -> dict[str, Any]:
    health = a.health
    db = a.db
    confirmed = [f for f in a.findings if f.kind is FindingKind.CONFIRMED_DEFECT]
    top = sorted(confirmed, key=lambda f: (f.severity.rank, -f.confidence, f.rule_id, f.table or ""))[:5]
    overall = "not assessed" if health.overall is None else f"{health.overall} ({health.grade})"
    text = [
        f"Database {db.name} ({db.dialect}, imported from {db.source or 'unknown'}) has {len(db.tables)} table(s) and {len(db.views)} view(s).",
        f"Overall health is {overall} with {health.confidence:.0%} confidence.",
        f"{len(a.findings)} finding(s): {dist['kind']['confirmed_defect']} confirmed defect(s), {dist['kind']['optional_improvement']} "
        f"optional improvement(s) and {dist['kind']['context_dependent']} context-dependent item(s). "
        f"{dist['severity']['critical']} are critical and {dist['severity']['high']} are high severity.",
    ]
    if health.capped:
        text.append("The overall score is capped because at least one confirmed critical defect exists.")
    if len(a.coverage.skipped) or len(a.coverage.errors):
        text.append(f"{len(a.coverage.executed)} rule(s) ran; {len(a.coverage.skipped)} were skipped and {len(a.coverage.errors)} failed. See coverage.")
    plan = a.plan
    text.append(f"The migration plan has {len(plan.steps)} step(s): {len(plan.executable_steps)} with SQL and {len(plan.manual_steps)} manual. Nothing has been applied.")
    return {"text": text, "database": db.name, "dialect": db.dialect, "tables": len(db.tables), "views": len(db.views),
            "findings_total": len(a.findings), "critical": dist["severity"]["critical"], "high": dist["severity"]["high"],
            "confirmed_defects": dist["kind"]["confirmed_defect"], "optional_improvements": dist["kind"]["optional_improvement"],
            "context_dependent": dist["kind"]["context_dependent"], "overall_score": health.overall, "grade": health.grade,
            "confidence": health.confidence, "capped": health.capped, "plan_hash": a.plan_hash, "plan_steps": len(plan.steps),
            "top_risks": [{"id": f.id, "severity": f.severity.value, "title": f.title, "table": f.table, "column": f.column} for f in top]}


def _finding_dict(f: Any) -> dict[str, Any]:
    return dataclasses.asdict(f) | {"severity": f.severity.value, "kind": f.kind.value}


def _migration_section(a: Any) -> dict[str, Any]:
    plan = a.plan
    destructive = [s for s in plan.steps if s.destructive]
    refused = [s for s in plan.steps if s.refused_reason]
    irreversible = [s for s in plan.executable_steps if not s.reversible]
    rows = []
    for step in plan.steps:
        rows.append({"id": step.id, "order": step.order, "title": step.title, "op": step.op, "table": step.table, "column": step.column,
                     "manual": step.manual, "destructive": step.destructive, "reversible": step.reversible, "data_loss_risk": step.data_loss_risk,
                     "lock_risk": step.lock_risk, "requires_backup": step.requires_backup, "requires_data_repair": step.requires_data_repair,
                     "data_repair_notes": step.data_repair_notes, "refused_reason": step.refused_reason,
                     "irreversible_reason": step.irreversible_reason, "manual_description": step.manual_description, "breaking": step.breaking,
                     "depends_on": step.depends_on, "finding_ids": step.finding_ids, "phase_label": step.phase_label,
                     "up_script": step.up_script, "down_script": step.down_script,
                     "transactional": step.transactional, "online_notes": list(step.online_notes), "dependency_risks": list(step.dependency_risks),
                     "destructive_hits": list(step.destructive_hits),
                     "prechecks": [{"description": c.description, "expected": c.expected, "status": c.status, "observed": c.observed, "kind": c.kind, "sql": c.sql} for c in step.prechecks],
                     "postchecks": [{"description": c.description, "expected": c.expected, "kind": c.kind, "sql": c.sql} for c in step.postchecks]})
    return {"plan_hash": a.plan_hash, "dialect": plan.dialect, "source_dialect": plan.source_dialect, "total_steps": len(plan.steps),
            "executable_steps": len(plan.executable_steps), "manual_steps": len(plan.manual_steps), "destructive_steps": len(destructive),
            "refused_steps": len(refused), "irreversible_steps": len(irreversible), "backup_recommendation": plan.backup_recommendation,
            "destructive": [{"id": s.id, "title": s.title, "table": s.table, "data_loss_risk": s.data_loss_risk, "reversible": s.reversible} for s in destructive],
            "refused": [{"id": s.id, "title": s.title, "table": s.table, "reason": s.refused_reason} for s in refused],
            "unaddressed_findings": list(plan.unaddressed_findings), "satisfied_findings": list(plan.satisfied_findings),
            "notes": list(plan.notes), "steps": rows}


def _column_entry(c: Any) -> dict[str, Any]:
    return {"name": c.name, "type": c.data_type, "nullable": c.nullable, "default": c.default, "comment": c.comment,
            "identity": c.is_identity, "generated": c.is_generated, "ordinal": c.ordinal}


def _table_entry(table: Table, db: Any, patterns: Any) -> dict[str, Any]:
    return {"name": table.fqname, "short_name": table.name, "schema": table.schema, "columns": len(table.columns), "primary_key": list(table.primary_key),
            "primary_key_name": table.primary_key_name, "foreign_keys": len(table.foreign_keys), "indexes": len(table.indexes),
            "referenced_by": len(db.referencing(table)), "row_count": table.row_count, "rls_enabled": table.rls_enabled, "comment": table.comment,
            "financial": is_financial_table(table.name, patterns),
            "column_list": [_column_entry(c) for c in table.columns],
            "index_list": [{"name": i.name, "columns": list(i.columns), "unique": i.unique, "primary": i.primary, "method": i.method,
                            "where": i.where, "include": list(i.include), "is_constraint": i.is_constraint} for i in table.indexes],
            "check_list": [{"name": k.name, "expression": k.expression, "columns": list(k.columns)} for k in table.checks]}


def _architecture(a: Any) -> dict[str, Any]:
    from ..migrate.safety import financial_patterns_from

    db = a.db
    patterns = financial_patterns_from(a.profile)
    tables = [_table_entry(t, db, patterns) for t in db.tables]
    relations = [{"from": t.fqname, "columns": list(fk.columns), "to": fk.ref_table, "ref_columns": list(fk.ref_columns), "ref_schema": fk.ref_schema,
                  "on_delete": fk.on_delete, "on_update": fk.on_update, "name": fk.name} for t in db.tables for fk in t.foreign_keys]
    domains = []
    isolated = []
    for group in components(db.tables):
        names = sorted(t.fqname for t in group)
        if len(group) == 1:
            isolated.extend(names)
            continue
        hub = max(sorted(group, key=lambda t: t.name.lower()),
                  key=lambda t: len(t.foreign_keys) + len(db.referencing(t)))
        domains.append({"name": f"{hub.name} domain", "hub": hub.fqname, "tables": names, "size": len(names)})
    if isolated:
        domains.append({"name": "Unconnected tables", "hub": None, "tables": sorted(isolated), "size": len(isolated)})
    return {"tables": tables, "relations": relations, "domains": domains,
            "views": [{"name": v.fqname, "materialized": v.materialized, "references": list(v.references)} for v in db.views],
            "routines": [{"name": r.name, "kind": r.kind, "table": r.table} for r in db.routines],
            "proposed": _proposed_schema(a)}


def _proposed_schema(a: Any) -> dict[str, Any]:
    """The schema with the plan's executable steps applied, for the interactive ER view: changed tables, new foreign keys and notes."""
    tables, keys, changed, notes = proposed_database(a.db, a.findings, a.plan)
    return {"columns_changed": changed,
            "tables": [{"name": t.fqname, "short_name": t.name, "column_list": [_column_entry(c) for c in t.columns]}
                       for t in tables if t.name.lower() in changed],
            "relations": [{"from": t.fqname, "columns": list(fk.columns), "to": fk.ref_table, "ref_columns": list(fk.ref_columns), "name": fk.name}
                          for t in tables for fk in t.foreign_keys
                          if (t.name.lower(), tuple(c.lower() for c in fk.columns), fk.ref_table.lower()) in keys],
            "notes": notes}


def build_roadmap(a: Any) -> dict[str, Any]:
    """Phases come from recommendation priority. A recommendation that another depends on is pulled to the earlier phase."""
    recs = {r.id: r for r in a.recommendations}
    finding_rec = {fid: r.id for r in a.recommendations for fid in r.finding_ids}
    step_rec: dict[str, set[str]] = {}
    for step in a.plan.steps:
        step_rec[step.id] = {finding_rec[f] for f in step.finding_ids if f in finding_rec}
    depends: dict[str, set[str]] = {r: set() for r in recs}
    for step in a.plan.steps:
        for need in step.depends_on:
            for rid in step_rec.get(step.id, set()):
                depends[rid] |= step_rec.get(need, set()) - {rid}
    phase = {rid: PHASE_OF_PRIORITY.get(r.priority, 4) for rid, r in recs.items()}
    original = dict(phase)
    moved_because: dict[str, str] = {}
    for _ in range(len(recs) + 1):
        changed = False
        for rid, needs in depends.items():
            for need in needs:
                if phase[need] > phase[rid]:
                    phase[need] = phase[rid]
                    moved_because[need] = rid
                    changed = True
        if not changed:
            break
    ordered = sorted(recs, key=lambda r: (phase[r], -recs[r].priority_score, r))
    placed: list[str] = []
    seen: set[str] = set()

    def place(rid: str, trail: tuple[str, ...]) -> None:
        if rid in seen or rid in trail:
            return
        for need in sorted(depends[rid], key=lambda d: (phase[d], -recs[d].priority_score, d)):
            if phase[need] == phase[rid]:
                place(need, trail + (rid,))
        seen.add(rid)
        placed.append(rid)

    for rid in ordered:
        place(rid, ())
    rec_step_ids: dict[str, list[str]] = {rid: [] for rid in recs}
    for step in a.plan.steps:
        for rid in step_rec.get(step.id, set()):
            rec_step_ids[rid].append(step.id)
    phases: list[dict[str, Any]] = []
    for number in sorted(set(phase.values())):
        items = []
        for rid in placed:
            if phase[rid] != number:
                continue
            rec = recs[rid]
            items.append({"recommendation": rid, "title": rec.title, "priority": rec.priority, "priority_score": rec.priority_score,
                          "table": rec.table, "findings": len(rec.finding_ids), "steps": rec_step_ids[rid], "depends_on": sorted(depends[rid]),
                          "moved_forward_for": moved_because.get(rid) if original[rid] != number else None})
        phases.append({"phase": number, "name": PHASE_NAMES.get(number, f"Phase {number}"), "items": items})
    prereq = ["Confirm a verified backup exists and has been restored in a test.", "Review every proposal with the people who own the data."]
    repair = [s.id for s in a.plan.steps if s.requires_data_repair]
    if repair:
        prereq.append(f"Repair data before these steps: {', '.join(repair)}.")
    if a.plan.manual_steps:
        prereq.append(f"Decide the {len(a.plan.manual_steps)} manual step(s); they carry no SQL.")
    return {"prerequisites": prereq, "phases": phases, "recommendation_count": len(recs),
            "basis": "Phases follow recommendation priority (P1 to P4). A recommendation that another depends on is moved up to the phase of its dependent."}


def _coverage(a: Any) -> dict[str, Any]:
    return {"rules_executed": sorted(a.coverage.executed), "rules_executed_count": len(a.coverage.executed),
            "skipped": [{"rule": r, "reason": a.coverage.skipped[r]} for r in sorted(a.coverage.skipped)],
            "skipped_count": len(a.coverage.skipped),
            "errors": [{"rule": r, "error": a.coverage.errors[r]} for r in sorted(a.coverage.errors)],
            "errors_count": len(a.coverage.errors), "capabilities": list(a.capabilities)}


def build_report(a: Any, generated_at: Optional[str] = None) -> dict[str, Any]:
    findings = list(a.findings)
    dist = distribution(findings)
    health = a.health.to_dict()
    health["weights"] = dict(CATEGORY_WEIGHTS)
    grouped = {k: [_finding_dict(f) for f in findings if f.kind.value == k] for k in KINDS}
    data = {
        "format": REPORT_FORMAT,
        "version": REPORT_VERSION,
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": {"name": a.db.name, "dialect": a.db.dialect, "kind": a.db.source, "label": a.source_label},
        "profile": {"workload": a.profile.workload, "tenancy": a.profile.tenancy, "multi_company": a.profile.multi_company},
        "summary": _executive_summary(a, dist),
        "health": health,
        "distribution": dist,
        "findings": grouped,
        "findings_total": len(findings),
        "root_cause_groups": [dataclasses.asdict(g) for g in a.root_cause_groups],
        "recommendations": [dataclasses.asdict(r) for r in a.recommendations],
        "migration": _migration_section(a),
        "lineage": a.lineage,
        "architecture": _architecture(a),
        "roadmap": build_roadmap(a),
        "coverage": _coverage(a),
        "import_warnings": list(a.db.import_warnings),
        "limitations": list(a.limitations),
        "er": {"current": [d.to_dict() for d in current_diagrams(a.db)],
               "proposed": [d.to_dict() for d in proposed_diagrams(a.db, findings, a.plan)]},
        "timing": dict(a.timing),
    }
    return scrub(data)
