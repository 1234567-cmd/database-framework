"""Group findings into recommendations with before/after design, real dependency analysis and explained priorities."""
from __future__ import annotations

import copy
import hashlib
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Sequence

import sqlglot
from sqlglot import exp

from ..findings import Finding, FindingKind, Severity
from ..migrate._sql import apply_fix_effect, render_table_ddl
from ..migrate.generator import MigrationPlan, MigrationStep
from ..migrate._sql import quiet_sqlglot
from ..migrate.safety import _strip_comments, financial_patterns_from, is_financial_table
from ..model import Database, Table

_SEVERITY_POINTS = {Severity.CRITICAL: 40, Severity.HIGH: 30, Severity.MEDIUM: 20, Severity.LOW: 10, Severity.INFO: 3}
_KIND_POINTS = {FindingKind.CONFIRMED_DEFECT: 20, FindingKind.CONTEXT_DEPENDENT: 0, FindingKind.OPTIONAL_IMPROVEMENT: -5}
_COMPLEXITY_POINTS = {"low": 5, "medium": 0, "high": -5}
_BANDS = ((50, "P1"), (35, "P2"), (20, "P3"), (0, "P4"))
_READ_NOT_EVALUATED = "Application impact was not evaluated: no application source directory was supplied."
SKIP_DIRS = {".git", ".hg", ".svn", "node_modules", "bower_components", "vendor", ".venv", "venv", "env", "__pycache__",
             ".tox", ".mypy_cache", ".pytest_cache", "dist", "build", "target", ".idea", ".vscode", ".next", "coverage"}
_BINARY_EXT = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".gz", ".tar", ".tgz", ".7z", ".rar", ".exe", ".dll", ".so",
               ".dylib", ".class", ".jar", ".war", ".pyc", ".pyd", ".o", ".a", ".lib", ".woff", ".woff2", ".ttf", ".mp3", ".mp4",
               ".mov", ".avi", ".webm", ".parquet", ".db", ".sqlite", ".bin"}
MAX_FILE_BYTES = 1_048_576
MAX_FILES = 20_000
MAX_HITS_PER_NAME = 200


@dataclass
class Recommendation:
    id: str
    finding_ids: list[str]
    title: str
    priority: str
    existing_structure: str
    weakness: str
    recommended_structure: str
    before_after: dict[str, str]
    proposed_sql: str
    application_dependencies: list[dict[str, Any]]
    data_dependencies: list[dict[str, Any]]
    data_migration: str
    rollback: str
    validation_tests: list[str]
    business_logic_notes: list[str]
    requires_review: bool
    priority_score: float = 0.0
    priority_rationale: list[str] = field(default_factory=list)
    application_impact_evaluated: bool = False
    application_scan: dict[str, Any] = field(default_factory=dict)
    table: Optional[str] = None


@dataclass
class RootCauseGroup:
    id: str
    cause: str
    rule_ids: list[str]
    finding_ids: list[str]
    tables: list[str]
    count: int
    systemic: bool
    shared_fix_ops: list[str]
    note: str


# --- application source scan ------------------------------------------------

class _Scan:
    def __init__(self) -> None:
        self.hits: dict[str, list[tuple[str, int, str]]] = defaultdict(list)
        self.truncated: set[str] = set()
        self.files_scanned = 0
        self.skipped: Counter = Counter()
        self.stopped_at_limit = False

    def summary(self, directory: str) -> dict[str, Any]:
        return {"evaluated": True, "directory": directory, "files_scanned": self.files_scanned,
                "files_skipped": dict(self.skipped), "stopped_at_file_limit": self.stopped_at_limit,
                "limits": f"Files over {MAX_FILE_BYTES} bytes, binary files and vendor or build directories are skipped. "
                          "A text search finds names, not meaning: dynamically built SQL or renamed mappings may be missed."}


def _scan_source(directory: str, names: set[str]) -> _Scan:
    scan = _Scan()
    if not names:
        return scan
    pattern = re.compile(r"\b(?:" + "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True)) + r")\b", re.I)
    lowered = {n.lower(): n for n in names}
    for root, dirs, files in os.walk(directory, followlinks=False):
        kept = []
        for d in dirs:
            if d.lower() in SKIP_DIRS or d.startswith(".git"):
                scan.skipped["vendor_or_build_directory"] += 1
            else:
                kept.append(d)
        dirs[:] = kept
        for name in files:
            if scan.files_scanned >= MAX_FILES:
                scan.stopped_at_limit = True
                return scan
            path = Path(root) / name
            if path.suffix.lower() in _BINARY_EXT:
                scan.skipped["binary_extension"] += 1
                continue
            try:
                if path.stat().st_size > MAX_FILE_BYTES:
                    scan.skipped["over_size_limit"] += 1
                    continue
                raw = path.read_bytes()
            except OSError:
                scan.skipped["unreadable"] += 1
                continue
            if b"\x00" in raw[:8192]:
                scan.skipped["binary_content"] += 1
                continue
            scan.files_scanned += 1
            text = raw.decode("utf-8", errors="replace")
            relative = str(path.relative_to(directory))
            for lineno, line in enumerate(text.splitlines(), start=1):
                for match in pattern.finditer(line):
                    key = lowered.get(match.group(0).lower(), match.group(0).lower())
                    if len(scan.hits[key]) >= MAX_HITS_PER_NAME:
                        scan.truncated.add(key)
                        continue
                    scan.hits[key].append((relative, lineno, line.strip()[:160]))
    return scan


def _app_dependencies(scan: _Scan, table: str, columns: list[str]) -> list[dict[str, Any]]:
    table_hits = scan.hits.get(table, [])
    files_with_table = {h[0] for h in table_hits}
    out: list[dict[str, Any]] = [{"file": f, "line": ln, "match": table, "kind": "table", "text": text} for f, ln, text in table_hits]
    for col in columns:
        for f, ln, text in scan.hits.get(col, []):
            if f in files_with_table:  # a bare column name alone is too common to attribute to this table
                out.append({"file": f, "line": ln, "match": col, "kind": "column", "text": text})
    return out


# --- object dependency analysis --------------------------------------------

def _word_re(name: str) -> re.Pattern:
    return re.compile(rf"\b{re.escape(name)}\b", re.I)


def _parse_view(definition: str, dialect: str) -> Optional[exp.Expression]:
    read = dialect if dialect in ("postgres", "mysql", "sqlite") else None
    try:
        with quiet_sqlglot():
            parsed = sqlglot.parse_one(definition, read=read)
    except Exception:
        return None
    if isinstance(parsed, exp.Command):
        return None
    if isinstance(parsed, exp.Create) and parsed.expression is not None:
        return parsed.expression
    return parsed


def _analyze_view(view, table: Table, columns: list[str], dialect: str) -> Optional[dict[str, Any]]:
    body = view.definition or ""
    target = table.name.lower()
    tree = _parse_view(body, dialect) if body else None
    if tree is None:
        if any(r.split(".")[-1].lower() == target for r in view.references) or (body and _word_re(table.name).search(body)):
            used = [c for c in columns if _word_re(c).search(body)]
            return {"kind": "view", "object": view.fqname, "method": "text_search", "columns": used,
                    "detail": "The definition could not be parsed; a name search found this table."}
        return None
    tables = [t for t in tree.find_all(exp.Table)]
    aliases = {(t.alias or t.name).lower(): t.name.lower() for t in tables}
    if target not in {t.name.lower() for t in tables}:
        return None
    hit: list[str] = []
    possible: list[str] = []
    distinct_tables = {t.name.lower() for t in tables}
    wanted = {c.lower() for c in columns}
    star = False
    for node in tree.find_all(exp.Column):
        if isinstance(node.this, exp.Star):
            qualifier = node.table.lower() if node.table else ""
            if not qualifier or aliases.get(qualifier) == target:
                star = True
            continue
        name = node.name.lower()
        if name not in wanted:
            continue
        qualifier = node.table.lower() if node.table else ""
        if qualifier:
            if aliases.get(qualifier) == target:
                hit.append(name)
        elif len(distinct_tables) == 1:
            hit.append(name)
        else:
            possible.append(name)
    if any(True for _ in tree.find_all(exp.Star)) and not any(isinstance(c.this, exp.Star) for c in tree.find_all(exp.Column)):
        star = True
    detail = "SELECT * depends on all columns of the table." if star else ""
    if possible:
        detail += f" Unqualified use of {', '.join(sorted(set(possible)))} across a join may refer to this table."
    return {"kind": "view", "object": view.fqname, "method": "sqlglot", "columns": sorted(set(hit)),
            "possible_columns": sorted(set(possible)), "select_star": star, "detail": detail.strip()}


def _analyze_routine(routine, table: Table, columns: list[str]) -> Optional[dict[str, Any]]:
    body = _strip_comments(routine.definition or "")
    tied = (routine.table or "").split(".")[-1].lower() == table.name.lower()
    if not tied and not _word_re(table.name).search(body) and not any(r.split(".")[-1].lower() == table.name.lower() for r in routine.references):
        return None
    return {"kind": routine.kind, "object": routine.name, "method": "text_search",
            "columns": [c for c in columns if _word_re(c).search(body)],
            "detail": "Procedural bodies are searched by name, so a match may be incidental and dynamic SQL may be missed."}


def _pipelines(db: Database, table: Table) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    word = _word_re(table.name)
    for job in db.pipelines:
        for step in job.steps:
            sides = [s.split(".")[-1].lower() for s in step.sources + step.targets]
            if table.name.lower() in sides or word.search(step.sql or ""):
                out.append({"kind": "pipeline", "object": f"{job.name}.{step.name}", "method": "metadata", "columns": [], "detail": f"Step type {step.kind}."})
    return out


def _dependencies(db: Database, table: Table, columns: list[str]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for owner, fk in db.referencing(table):
        out.append({"kind": "foreign_key_in", "object": f"{owner.fqname}.{fk.name or ','.join(fk.columns)}", "method": "metadata",
                    "columns": list(fk.ref_columns), "detail": f"{owner.fqname} ({', '.join(fk.columns)}) references this table."})
    for fk in table.foreign_keys:
        out.append({"kind": "foreign_key_out", "object": fk.name or ",".join(fk.columns), "method": "metadata", "columns": list(fk.columns),
                    "detail": f"This table references {fk.ref_table}."})
    for view in db.views:
        found = _analyze_view(view, table, columns, db.dialect)
        if found:
            out.append(found)
    for routine in db.routines:
        found = _analyze_routine(routine, table, columns)
        if found:
            out.append(found)
    out.extend(_pipelines(db, table))
    return out


# --- recommendation building -----------------------------------------------

def _worst(findings: Sequence[Finding]) -> Finding:
    return min(findings, key=lambda f: (f.severity.rank, -f.confidence))


def _priority(findings: Sequence[Finding], data_deps: list[dict], steps: list[MigrationStep]) -> tuple[str, float, list[str]]:
    worst = _worst(findings)
    rationale: list[str] = []
    score = float(_SEVERITY_POINTS[worst.severity])
    rationale.append(f"Worst severity is {worst.severity.value} ({_SEVERITY_POINTS[worst.severity]} points).")
    kinds = {f.kind for f in findings}
    kind = FindingKind.CONFIRMED_DEFECT if FindingKind.CONFIRMED_DEFECT in kinds else (
        FindingKind.CONTEXT_DEPENDENT if FindingKind.CONTEXT_DEPENDENT in kinds else FindingKind.OPTIONAL_IMPROVEMENT)
    score += _KIND_POINTS[kind]
    rationale.append(f"Strongest finding kind is {kind.value} ({_KIND_POINTS[kind]:+d}).")
    confidence = max(f.confidence for f in findings)
    factor = 0.5 + 0.5 * confidence
    score *= factor
    rationale.append(f"Confidence {confidence:.2f} scales the score by {factor:.2f}.")
    complexity = (worst.complexity or "").strip().lower()
    points = _COMPLEXITY_POINTS.get(complexity, 0)
    score += points
    rationale.append(f"Complexity {worst.complexity or 'unknown'} ({points:+d}).")
    count = len(data_deps)
    dep_points = 3 if count == 0 else (-5 if count >= 5 else (-2 if count >= 2 else 0))
    score += dep_points
    rationale.append(f"{count} database objects depend on this structure ({dep_points:+d}).")
    if any(s.manual or s.requires_data_repair for s in steps):
        score -= 3
        rationale.append("Manual work or data repair is needed (-3).")
    score = round(max(score, 0.0), 1)
    band = next(name for threshold, name in _BANDS if score >= threshold)
    return band, score, rationale


def _weakness(findings: Sequence[Finding]) -> str:
    return "\n".join(f"- [{f.severity.value}] {f.title}: {f.evidence or f.root_cause}" for f in findings)


def _proposed_sql(steps: list[MigrationStep]) -> str:
    parts: list[str] = []
    for step in sorted(steps, key=lambda s: s.order):
        if step.manual:
            parts.append(f"-- {step.id} MANUAL: {step.manual_description}")
        else:
            parts.append(f"-- {step.id}: {step.title}\n{step.up_script}")
    return "\n\n".join(parts) if parts else "-- No SQL proposed for these findings."


def _rollback_text(steps: list[MigrationStep]) -> str:
    if not steps:
        return "No SQL is proposed, so no rollback is needed."
    lines: list[str] = []
    for step in steps:
        if step.manual:
            lines.append(f"{step.id}: manual step; define the rollback during its review.")
        elif step.reversible and step.down_sql:
            lines.append(f"{step.id}: rollback SQL is provided; test it in a sandbox before relying on it.")
        else:
            lines.append(f"{step.id}: NOT reversible without loss. {step.irreversible_reason}")
    return "\n".join(lines)


def _data_migration(steps: list[MigrationStep]) -> str:
    lines: list[str] = []
    for step in steps:
        if step.phase_label in ("expand", "swap", "contract"):
            lines.append(f"{step.id} ({step.phase_label}): {step.title}.")
        if step.requires_data_repair:
            lines.append(f"{step.id}: repair data if needed before this step: {'; '.join(step.data_repair_notes)}.")
    return "\n".join(lines) or "The proposed SQL does not change existing data. Confirm that against your own requirements."


def _validation(findings: Sequence[Finding], steps: list[MigrationStep]) -> list[str]:
    tests = list(dict.fromkeys(f.validation_strategy for f in findings if f.validation_strategy))
    for step in steps:
        tests += [f"{step.id} precheck: {c.description} (expect {c.expected})" for c in step.prechecks]
        tests += [f"{step.id} postcheck: {c.description} (expect {c.expected})" for c in step.postchecks]
    return tests


def _business_notes(findings: Sequence[Finding], steps: list[MigrationStep], table: Optional[Table], patterns: Sequence[str]) -> list[str]:
    notes = ["No business rule was inferred. Confirm each change against how the business uses this data."]
    for f in findings:
        if f.kind == FindingKind.CONTEXT_DEPENDENT:
            notes.append(f"{f.id}: context dependent; a data owner must decide whether it applies.")
    if table is not None and is_financial_table(table.name, patterns):
        notes.append(f"{table.name} matches financial table protection; destructive changes are refused and left as manual steps.")
    for step in steps:
        if step.refused_reason:
            notes.append(f"{step.id}: {step.refused_reason}")
    return notes


def _after_table(table: Table, findings: Sequence[Finding], by_finding: dict[str, list[MigrationStep]]) -> tuple[Table, list[str]]:
    after = copy.deepcopy(table)
    deferred: list[str] = []
    for f in findings:
        steps = by_finding.get(f.id, [])
        if f.fix is None:
            continue
        if not steps or any(s.manual for s in steps):
            deferred.append(f"{f.id} ({f.fix.op}) is left as a manual decision and is not shown.")
            continue
        apply_fix_effect(after, f.fix.op, f.fix.column or f.column, dict(f.fix.params or {}))
    return after, deferred


def _group_key(f: Finding) -> str:
    return f"table:{f.table}" if f.table else f"concern:{f.category}"


def build_recommendations(db: Database, findings: Sequence[Finding], plan: MigrationPlan,
                          app_source_dir: Optional[str] = None, *, profile: Any = None,
                          financial_patterns: Optional[Sequence[str]] = None) -> list[Recommendation]:
    """One recommendation per table, or per concern for findings that are not about one table."""
    patterns = financial_patterns_from(profile, financial_patterns)
    groups: dict[str, list[Finding]] = defaultdict(list)
    for f in findings:
        groups[_group_key(f)].append(f)
    by_finding: dict[str, list[MigrationStep]] = defaultdict(list)
    for step in plan.steps:
        for fid in step.finding_ids:
            by_finding[fid].append(step)
    scan, scan_summary = _prepare_scan(db, findings, app_source_dir)
    recs: list[Recommendation] = []
    for key, items in sorted(groups.items()):
        recs.append(_build_one(db, key, items, by_finding, scan, scan_summary, patterns))
    recs.sort(key=lambda r: (-r.priority_score, r.id))
    return recs


def _prepare_scan(db: Database, findings: Sequence[Finding], app_source_dir: Optional[str]) -> tuple[Optional[_Scan], dict[str, Any]]:
    if not app_source_dir or not Path(app_source_dir).is_dir():
        reason = _READ_NOT_EVALUATED if not app_source_dir else f"Application impact was not evaluated: {app_source_dir!r} is not a directory."
        return None, {"evaluated": False, "message": reason}
    names: set[str] = set()
    for f in findings:
        if f.table:
            names.add(f.table.split(".")[-1])
        if f.column:
            names.add(f.column)
        if f.fix is not None:
            names.update(str(c) for c in (f.fix.params.get("columns") or []) if c)
            if f.fix.column:
                names.add(f.fix.column)
    scan = _scan_source(app_source_dir, names)
    return scan, scan.summary(app_source_dir)


def _build_one(db: Database, key: str, items: list[Finding], by_finding: dict[str, list[MigrationStep]], scan: Optional[_Scan],
               scan_summary: dict[str, Any], patterns: Sequence[str]) -> Recommendation:
    is_table = key.startswith("table:")
    table_name = key.split(":", 1)[1].split(".")[-1] if is_table else None
    table = db.table(table_name) if table_name else None
    steps = sorted({id(s): s for f in items for s in by_finding.get(f.id, [])}.values(), key=lambda s: s.order)
    columns = sorted({c for f in items for c in ([f.column] if f.column else []) + ([f.fix.column] if f.fix and f.fix.column else []) + (list(f.fix.params.get("columns") or []) if f.fix else []) if c})
    deps = _dependencies(db, table, columns) if table is not None else []
    if table is not None:
        before = render_table_ddl(table)
        after_table, deferred = _after_table(table, items, by_finding)
        after = render_table_ddl(after_table)
    else:
        before = after = f"Concern: {key.split(':', 1)[1]}. Not specific to one table."
        deferred = []
    if scan is not None and table_name:
        app_deps = _app_dependencies(scan, table_name, columns)
        evaluated = True
        if not app_deps:
            app_deps = [{"status": "scanned_no_match", "message": f"Scanned {scan.files_scanned} files; no reference to {table_name} was found. This does not rule out dynamically built SQL."}]
    elif scan is not None:
        app_deps = [{"status": "not_applicable", "message": "This concern is not tied to one table, so the source scan was not applied to it."}]
        evaluated = True
    else:
        app_deps = [{"status": "not_evaluated", "message": scan_summary.get("message", _READ_NOT_EVALUATED)}]
        evaluated = False
    priority, score, rationale = _priority(items, deps, steps)
    deferred_text = ("\n\nDeferred:\n" + "\n".join(f"- {d}" for d in deferred)) if deferred else ""
    review = (not evaluated or bool(deps) or any(s.manual or s.breaking or s.destructive or s.requires_data_repair for s in steps)
              or any(f.kind != FindingKind.CONFIRMED_DEFECT or f.confidence < 0.7 for f in items)
              or (table is not None and is_financial_table(table.name, patterns))
              or any(a.get("kind") for a in app_deps))
    digest = hashlib.sha256(f"{db.name}|{key}".encode("utf-8")).hexdigest()[:10]
    subject = table.fqname if table is not None else key.split(":", 1)[1]
    return Recommendation(
        id=f"REC-{digest}", finding_ids=sorted(f.id for f in items), title=f"Address {len(items)} finding(s) on {subject}",
        priority=priority, existing_structure=before, weakness=_weakness(items), recommended_structure=after + deferred_text,
        before_after={"before": before, "after": after}, proposed_sql=_proposed_sql(steps), application_dependencies=app_deps,
        data_dependencies=deps, data_migration=_data_migration(steps), rollback=_rollback_text(steps),
        validation_tests=_validation(items, steps), business_logic_notes=_business_notes(items, steps, table, patterns),
        requires_review=review, priority_score=score, priority_rationale=rationale, application_impact_evaluated=evaluated,
        application_scan=scan_summary, table=table.fqname if table is not None else None)


# --- root causes -----------------------------------------------------------

def _mask_names(f: Finding) -> str:
    text = f.root_cause or f.rule_id
    for name in filter(None, [f.column, f.table, (f.table or "").split(".")[-1]]):
        text = re.sub(rf"\b{re.escape(name)}\b", "#", text, flags=re.I)
    return re.sub(r"\s+", " ", text).strip().lower()


def root_cause_groups(findings: Sequence[Finding]) -> list[RootCauseGroup]:
    """Cluster findings under a shared cause; table and column names are masked so that a repeated gap groups together."""
    clusters: dict[tuple, list[Finding]] = defaultdict(list)
    for f in findings:
        clusters[(f.category, _mask_names(f))].append(f)
    out: list[RootCauseGroup] = []
    for (category, cause), items in clusters.items():
        tables = sorted({f.table for f in items if f.table})
        systemic = len(tables) >= 2
        digest = hashlib.sha256(f"{category}|{cause}".encode("utf-8")).hexdigest()[:10]
        note = (f"The same gap appears on {len(tables)} tables, which points to a missing convention rather than isolated defects. "
                "Fix the convention and apply it across the group." if systemic else "Limited to one object.")
        out.append(RootCauseGroup(id=f"RC-{digest}", cause=items[0].root_cause or cause, rule_ids=sorted({f.rule_id for f in items}),
                                  finding_ids=sorted(f.id for f in items), tables=tables, count=len(items), systemic=systemic,
                                  shared_fix_ops=sorted({f.fix.op for f in items if f.fix}), note=note))
    out.sort(key=lambda g: (-g.count, g.id))
    return out
