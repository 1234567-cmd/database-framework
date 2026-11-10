"""Data engineering readiness, governance and reliability checks."""
from __future__ import annotations

import re
from typing import Any, Iterable, Optional

import sqlglot
from sqlglot import exp

from ..findings import Fix
from ..model import Database, PipelineJob, PipelineStep, Table
from ..rules.engine import Hit, check, iter_tables
from .security import compile_any, manual, matches

_DIALECTS = {"postgres": "postgres", "mysql": "mysql", "sqlite": "sqlite"}
_FLOAT_TYPES = {exp.DataType.Type.FLOAT, exp.DataType.Type.DOUBLE}


# ---- SQL parsing and lineage ----

def _parse(sql: str, dialect: str) -> Optional[list[exp.Expression]]:
    """Parsed statements, or None when the SQL cannot be parsed (for example templated SQL)."""
    if not (sql or "").strip():
        return []
    try:
        return [s for s in sqlglot.parse(sql, read=_DIALECTS.get(dialect)) if s is not None]
    except Exception:  # sqlglot raises several error types for unsupported syntax
        return None


def _table_name(table: exp.Table) -> str:
    return (f"{table.db}.{table.name}" if table.db else table.name).lower()


def _write_target(stmt: exp.Expression) -> Optional[str]:
    if isinstance(stmt, exp.Create):
        if str(stmt.args.get("kind", "")).upper() not in ("TABLE", "VIEW") or stmt.expression is None:
            return None
        node = stmt.this
    elif isinstance(stmt, (exp.Insert, exp.Merge, exp.Update)):
        node = stmt.this
    else:
        return None
    table = node if isinstance(node, exp.Table) else node.find(exp.Table)
    return _table_name(table) if table is not None else None


def statement_edges(stmt: exp.Expression) -> list[tuple[str, str]]:
    target = _write_target(stmt)
    if not target:
        return []
    cte_names = {c.alias.lower() for c in stmt.find_all(exp.CTE)}
    sources = {_table_name(t) for t in stmt.find_all(exp.Table)} - cte_names - {target}
    return [(s, target) for s in sorted(sources)]


def build_lineage(db: Database) -> list[dict[str, str]]:
    """Table-level lineage from pipeline steps and view definitions.

    Each edge is ``{"source", "target", "via", "origin"}``; origin is ``sql`` or ``declared``.
    """
    edges: dict[tuple[str, str, str], dict[str, str]] = {}

    def add(source: str, target: str, via: str, origin: str) -> None:
        key = (source.lower(), target.lower(), via)
        if key[0] != key[1] and (key not in edges or origin == "sql"):
            edges[key] = {"source": key[0], "target": key[1], "via": via, "origin": origin}

    for job in db.pipelines:
        for step in job.steps:
            via = f"{job.name}.{step.name}"
            for stmt in _parse(step.sql, db.dialect) or []:
                for source, target in statement_edges(stmt):
                    add(source, target, via, "sql")
            for source in step.sources:
                for target in step.targets:
                    add(source, target, via, "declared")
    for view in db.views:
        stmts = _parse(view.definition, db.dialect) or []
        found = False
        for stmt in stmts:
            cte_names = {c.alias.lower() for c in stmt.find_all(exp.CTE)}
            for table in stmt.find_all(exp.Table):
                name = _table_name(table)
                if name not in cte_names:
                    add(name, view.name, f"view {view.name}", "sql")
                    found = True
        if not found:
            for ref in view.references:
                add(ref, view.name, f"view {view.name}", "declared")
    return [edges[k] for k in sorted(edges)]


# ---- scope helper: pipeline rules whose standard names analytical scopes ----

def _scope_note(profile, params: dict, kind: Optional[str] = None) -> tuple[Optional[str], str]:
    """A step of a supplied pipeline is in scope of the standard, but the profile may describe an OLTP source."""
    scope = params.get("standard_workloads")
    if scope and profile.workload not in scope:
        return "context_dependent", f" The profile workload is {profile.workload}; the standard is scoped to {', '.join(scope)}."
    return kind, ""


def _steps(db: Database) -> Iterable[tuple[PipelineJob, PipelineStep]]:
    return ((j, s) for j in db.pipelines for s in j.steps)


def _step_target(step: PipelineStep) -> Optional[str]:
    return step.targets[0] if step.targets else None


def _step_fix(job: PipelineJob, step: PipelineStep, description: str):
    return manual(_step_target(step), None, f"Pipeline {job.name}, step {step.name}: {description}")


def _job_fix(job: PipelineJob, description: str):
    return manual(None, None, f"Pipeline {job.name}: {description}")


def _flat(sql: str) -> str:
    return " ".join((sql or "").split())


# ---- pipeline checks ----

_DEDUPE_TEXT = re.compile(r"\bon\s+conflict\b|\bon\s+duplicate\s+key\b|\bmerge\s+into\b|\bnot\s+exists\b|\bnot\s+in\b|"
                          r"\binsert\s+ignore\b|\bis\s+null\b.*\bleft\s+join\b|\bleft\s+join\b.*\bis\s+null\b", re.I)


def _plain_insert_select(sql: str, stmts: Optional[list[exp.Expression]]) -> bool:
    if stmts is None:
        flat = _flat(sql)
        return bool(re.search(r"\binsert\s+into\b", flat, re.I) and re.search(r"\bselect\b", flat, re.I))
    return any(isinstance(s, exp.Insert) and not isinstance(s.expression, exp.Values) for s in stmts)


def _has_prior_delete(job: PipelineJob, step: PipelineStep, stmts: Optional[list[exp.Expression]], dialect: str) -> bool:
    targets = {t.lower() for t in step.targets}
    for other in job.steps:
        for stmt in _parse(other.sql, dialect) or []:
            if isinstance(stmt, exp.Delete):
                table = stmt.find(exp.Table)
                if table is not None and (not targets or _table_name(table) in targets):
                    return True
        if other is step:
            break
    return False


@check("data_engineering.non_idempotent_steps")
def non_idempotent_steps(db, profile, params):
    for job, step in _steps(db):
        if job.idempotent is True or step.write_mode in ("overwrite", "merge") or step.merge_keys:
            continue
        stmts = _parse(step.sql, db.dialect)
        insert = _plain_insert_select(step.sql, stmts)
        if not insert and not (step.write_mode == "append" and not step.sql):
            continue
        if _DEDUPE_TEXT.search(_flat(step.sql)) or _has_prior_delete(job, step, stmts, db.dialect):
            continue
        kind, note = _scope_note(profile, params)
        if not step.sql:
            kind, note = "context_dependent", " No SQL was supplied, so a guard in the code cannot be ruled out."
        yield Hit(table=_step_target(step), vars={"job": job.name, "step": step.name}, kind=kind,
                  evidence=f"Step {step.name} of {job.name} appends with no merge key, dedupe guard or prior delete.{note}",
                  fix=_step_fix(job, step, "declare a merge key or delete the interval before insert so a rerun leaves one copy."))


@check("data_engineering.non_atomic_overwrite")
def non_atomic_overwrite(db, profile, params):
    atomic = compile_any(params.get("atomic_patterns", []))
    for job, step in _steps(db):
        flat = _flat(step.sql)
        truncates = re.search(r"\btruncate\b", flat, re.I) and re.search(r"\binsert\b", flat, re.I)
        delete_all = re.search(r"\bdelete\s+from\s+[\w.\"`]+\s*;", flat, re.I) and re.search(r"\binsert\b", flat, re.I)
        if not (step.write_mode == "overwrite" or truncates or delete_all) or matches(atomic, flat):
            continue
        kind, note = _scope_note(profile, params)
        if not step.sql:
            kind, note = "context_dependent", " No SQL was supplied, so atomicity cannot be confirmed."
        yield Hit(table=_step_target(step), vars={"job": job.name, "step": step.name}, kind=kind,
                  evidence=f"Step {step.name} of {job.name} replaces the target without a swap or transaction.{note}",
                  fix=_step_fix(job, step, "build into a staging table and swap, or wrap the replace in one transaction."))


@check("data_engineering.missing_merge_keys")
def missing_merge_keys(db, profile, params):
    for job, step in _steps(db):
        if step.write_mode != "merge" or step.merge_keys:
            continue
        stmts = _parse(step.sql, db.dialect) or []
        if any(isinstance(s, exp.Merge) for s in stmts):
            continue
        kind, note = _scope_note(profile, params)
        yield Hit(table=_step_target(step), vars={"job": job.name, "step": step.name}, kind=kind,
                  evidence=f"Step {step.name} of {job.name} merges with no declared key.{note}",
                  fix=_step_fix(job, step, "declare the business key the merge uses."))


@check("data_engineering.no_incremental_column")
def no_incremental_column(db, profile, params):
    filter_rx = compile_any(params.get("incremental_filter_patterns", []))
    for job, step in _steps(db):
        if step.kind != "extract" or step.write_mode == "overwrite" or step.incremental_column:
            continue
        if matches(filter_rx, _flat(step.sql)):
            continue
        yield Hit(table=step.sources[0] if step.sources else None, vars={"job": job.name, "step": step.name},
                  evidence=f"Extract step {step.name} of {job.name} declares no incremental column.",
                  fix=_step_fix(job, step, "declare the change column, or use log-based capture."))


@check("data_engineering.no_change_column")
def no_change_column(db, profile, params):
    change = compile_any(params.get("change_column_patterns", []))
    ctype = params.get("change_column_type", "timestamp")
    for t in iter_tables(db, profile):
        if profile.is_audit_exempt(t.name) or any(matches(change, c.name) for c in t.columns):
            continue
        yield Hit(table=t.fqname, column=params.get("change_column_name", "updated_at"),
                  evidence=f"Table {t.fqname} has no reliable change column.",
                  fix=Fix("add_column", t.fqname, params.get("change_column_name", "updated_at"),
                          {"type": ctype, "nullable": True, "default": None}))


def _cdc_tables(db: Database, params: dict) -> set[str]:
    rx = compile_any(params.get("cdc_step_patterns", []))
    found: set[str] = set()
    for job, step in _steps(db):
        if matches(rx, step.name) or matches(rx, job.name) or matches(rx, step.kind):
            found |= {s.lower().split(".")[-1] for s in step.sources}
    return found


def _settings_suggest_cdc(db: Database, params: dict) -> bool:
    current = {str(k).lower(): str(v).lower() for k, v in db.settings.items()}
    return any(current.get(i["setting"].lower()) in {str(v).lower() for v in i["values"]} for i in params.get("cdc_settings", []))


def _has_key(t: Table) -> bool:
    if t.primary_key:
        return True
    for idx in t.indexes:
        if idx.unique and not idx.where and all((t.column(c) is not None and not t.column(c).nullable) for c in idx.columns):
            return True
    return False


@check("data_engineering.no_pk_under_cdc")
def no_pk_under_cdc(db, profile, params):
    cdc = _cdc_tables(db, params)
    signal = _settings_suggest_cdc(db, params)
    for t in iter_tables(db, profile):
        if _has_key(t):
            continue
        fix = manual(t.fqname, None, "Choose a primary key or an equivalent replica identity before capture.")
        if t.name.lower() in cdc:
            yield Hit(table=t.fqname, evidence=f"Table {t.fqname} is captured by a CDC step and has no key.",
                      confidence=0.95, fix=fix)
        elif signal or (params.get("assume_readiness", True) and not cdc):
            basis = "logical change capture appears enabled" if signal else "no change-capture step was declared, so this is readiness only"
            yield Hit(table=t.fqname, kind="context_dependent", confidence=0.5, severity="medium",
                      evidence=f"Table {t.fqname} has no key; {basis}.", fix=fix)


def _job_flag(profile, params, job: PipelineJob, value: Optional[bool], absent: str):
    kind, note = _scope_note(profile, params)
    if value is None:
        kind, note = "context_dependent", " The manifest does not state this, so it is treated as unknown."
    return kind, f"{absent}{note}"


@check("data_engineering.no_run_metadata")
def no_run_metadata(db, profile, params):
    for job in db.pipelines:
        if job.records_run_metadata is not True:
            kind, evidence = _job_flag(profile, params, job, job.records_run_metadata, f"Job {job.name} does not record run metadata.")
            yield Hit(vars={"job": job.name}, kind=kind, evidence=evidence,
                      fix=_job_fix(job, "record run identity, source position, code version and result per run."))


@check("data_engineering.no_lineage")
def no_lineage(db, profile, params):
    for job in db.pipelines:
        if job.emits_lineage is not True:
            kind, evidence = _job_flag(profile, params, job, job.emits_lineage, f"Job {job.name} does not emit lineage.")
            yield Hit(vars={"job": job.name}, kind=kind, evidence=evidence, fix=_job_fix(job, "emit run-level lineage."))


@check("data_engineering.no_quality_gates")
def no_quality_gates(db, profile, params):
    for job in db.pipelines:
        if not job.quality_checks:
            kind, note = _scope_note(profile, params)
            yield Hit(vars={"job": job.name}, kind=kind, evidence=f"Job {job.name} declares no quality checks.{note}",
                      fix=_job_fix(job, "add quality gates that run before the output is published."))


@check("data_engineering.no_owner")
def no_owner(db, profile, params):
    for job in db.pipelines:
        if not (job.owner or "").strip():
            yield Hit(vars={"job": job.name}, evidence=f"Job {job.name} has no owner.",
                      fix=_job_fix(job, "name an accountable owner."))


@check("data_engineering.no_retries")
def no_retries(db, profile, params):
    for job in db.pipelines:
        if not job.retries:
            state = "unset" if job.retries is None else "0"
            kind, note = _scope_note(profile, params)
            yield Hit(vars={"job": job.name}, kind=kind, evidence=f"Job {job.name} has retries {state}.{note}",
                      fix=_job_fix(job, "configure bounded retries once its steps are idempotent."))


def _money(name: str, profile) -> bool:
    low = name.lower()
    return any(p.lower() in low for p in profile.money_name_patterns)


@check("data_engineering.float_money_typed_layer")
def float_money_typed_layer(db, profile, params):
    for t in iter_tables(db, profile):
        for c in t.columns:
            if c.type.family == "float" and _money(c.name, profile):
                yield Hit(table=t.fqname, column=c.name, evidence=f"{t.fqname}.{c.name} is {c.data_type}.",
                          vars={"where_found": "schema"},
                          fix=manual(t.fqname, c.name, "Change the type to exact decimal or integer minor units, and reconcile totals."))
    for job, step in _steps(db):
        for stmt in _parse(step.sql, db.dialect) or []:
            for cast in stmt.find_all(exp.Cast):
                if cast.to is None or cast.to.this not in _FLOAT_TYPES:
                    continue
                parent = cast.parent
                name = parent.alias if isinstance(parent, exp.Alias) else (cast.this.name if isinstance(cast.this, exp.Column) else "")
                if name and _money(name, profile):
                    yield Hit(table=_step_target(step), column=name, vars={"where_found": f"{job.name}.{step.name}"},
                              evidence=f"Step {step.name} of {job.name} casts {name} to floating point.",
                              fix=_step_fix(job, step, f"cast {name} to exact decimal."))


@check("data_engineering.lineage_gaps")
def lineage_gaps(db, profile, params):
    for job, step in _steps(db):
        stmts = _parse(step.sql, db.dialect)
        issue = None
        if not step.sql and not step.sources and not step.targets:
            issue = "has no SQL and declares no sources or targets"
        elif stmts is None and not step.sources:
            issue = "has SQL that cannot be parsed and declares no sources"
        elif stmts and step.sources:
            declared = {s.lower() for s in step.sources}
            found = {s for stmt in stmts for s, _ in statement_edges(stmt)}
            missing = sorted(s for s in found if s not in declared and s.split(".")[-1] not in declared)
            if missing:
                issue = f"reads {', '.join(missing)}, which it does not declare"
        if issue:
            kind, note = _scope_note(profile, params)
            yield Hit(table=_step_target(step), vars={"job": job.name, "step": step.name}, kind=kind,
                      evidence=f"Step {step.name} of {job.name} {issue}.{note}",
                      fix=_step_fix(job, step, "declare its sources and targets so lineage can be computed."))


def _has_select_star(stmts: Optional[list[exp.Expression]]) -> bool:
    for stmt in stmts or []:
        for select in stmt.find_all(exp.Select):
            for item in select.expressions:
                if isinstance(item, exp.Star) or (isinstance(item, exp.Column) and isinstance(item.this, exp.Star)):
                    return True
    return False


@check("data_engineering.select_star")
def select_star(db, profile, params):
    kind, note = _scope_note(profile, params)
    for job, step in _steps(db):
        if _has_select_star(_parse(step.sql, db.dialect)):
            yield Hit(table=_step_target(step), vars={"job": job.name, "step": step.name}, kind=kind,
                      evidence=f"Step {step.name} of {job.name} uses SELECT *.{note}",
                      fix=_step_fix(job, step, "list the columns explicitly."))
    for view in db.views:
        if _has_select_star(_parse(view.definition, db.dialect)):
            yield Hit(table=view.fqname, vars={"job": "(view)", "step": view.name}, kind=kind,
                      evidence=f"View {view.fqname} uses SELECT *.{note}",
                      fix=manual(view.fqname, None, "List the columns explicitly in the view."))


@check("data_engineering.view_dependencies")
def view_dependencies(db, profile, params):
    names = {v.name.lower() for v in db.views} | {v.fqname.lower() for v in db.views}
    kind, note = _scope_note(profile, params)
    for job, step in _steps(db):
        for source in step.sources:
            if source.lower() in names:
                yield Hit(table=source, vars={"consumer": f"{job.name}.{step.name}"}, kind=kind,
                          evidence=f"Step {step.name} of {job.name} reads view {source}.{note}",
                          fix=_step_fix(job, step, "depend on a governed table or a versioned contract."))
    for view in db.views:
        refs = [e["source"] for e in build_lineage_for_view(db, view.name)]
        for ref in refs:
            if ref in names:
                yield Hit(table=ref, vars={"consumer": f"view {view.name}"}, kind=kind,
                          evidence=f"View {view.name} depends on view {ref}.{note}",
                          fix=manual(view.fqname, None, "Flatten the view chain or document the dependency."))


def build_lineage_for_view(db: Database, name: str) -> list[dict[str, str]]:
    return [e for e in build_lineage(db) if e["target"] == name.lower() and e["via"].startswith("view ")]


# ---- governance ----

def _meta_text(db: Database) -> Iterable[str]:
    for t in db.tables:
        if t.comment:
            yield t.comment
        for c in t.columns:
            if c.comment:
                yield c.comment


def _comments_supported(db: Database, params: dict) -> bool:
    return db.dialect not in params.get("unsupported_dialects", []) and db.source not in params.get("unsupported_sources", [])


@check("governance.missing_table_comments")
def missing_table_comments(db, profile, params):
    if not _comments_supported(db, params):
        return
    for t in iter_tables(db, profile):
        if not (t.comment or "").strip():
            yield Hit(table=t.fqname, evidence=f"Table {t.fqname} has no description.",
                      fix=manual(t.fqname, None, "Add a description to the table, with no sensitive values."))


@check("governance.missing_column_comments")
def missing_column_comments(db, profile, params):
    if not _comments_supported(db, params):
        return
    for t in iter_tables(db, profile):
        missing = [c.name for c in t.columns if not (c.comment or "").strip()]
        if t.columns and len(missing) / len(t.columns) >= float(params.get("min_missing_ratio", 0.5)):
            yield Hit(table=t.fqname, vars={"missing_count": len(missing)},
                      evidence=f"{len(missing)} of {len(t.columns)} columns have no description.",
                      fix=manual(t.fqname, None, "Describe the columns, with no sensitive values."))


def _any_marker(db: Database, comment_rx, table_rx) -> bool:
    return any(matches(comment_rx, c) for c in _meta_text(db)) or any(matches(table_rx, t.name) for t in db.tables)


@check("governance.no_owner_metadata")
def no_owner_metadata(db, profile, params):
    if db.tables and not _any_marker(db, compile_any(params.get("comment_patterns", [])), compile_any(params.get("table_patterns", []))):
        yield Hit(evidence="No owner marker in table or column descriptions and no ownership catalog table.",
                  fix=manual(None, None, "Record an accountable owner per table or dataset."))


@check("governance.no_classification")
def no_classification(db, profile, params):
    if not db.tables or _any_marker(db, compile_any(params.get("comment_patterns", [])), compile_any(params.get("table_patterns", []))):
        return
    if any(matches(compile_any(params.get("column_patterns", [])), c.name) for t in db.tables for c in t.columns):
        return
    yield Hit(evidence="No classification marker in descriptions, columns or catalog tables.",
              fix=manual(None, None, "Add a classification attribute per column that drives masking and retention."))


@check("governance.no_audit_history")
def no_audit_history(db, profile, params):
    if not profile.system_of_record or not db.tables:
        return
    rx = compile_any(params.get("table_patterns", []))
    if not any(matches(rx, t.name) for t in db.tables):
        yield Hit(evidence="No audit or history table was found.",
                  fix=manual(None, None, "Decide which record classes need audit history and how long it is retained."))


@check("governance.no_retention_structures")
def no_retention_structures(db, profile, params):
    if not profile.system_of_record or not db.tables:
        return
    rx = compile_any(params.get("table_patterns", []))
    if not any(matches(rx, t.name) for t in db.tables):
        yield Hit(evidence="No retention schedule or legal hold table was found; this may be held outside the database.",
                  fix=manual(None, None, "Requires legal review: define retention by record class, jurisdiction, start event and hold."))


@check("governance.no_migration_history")
def no_migration_history(db, profile, params):
    if db.tables and not any(t.name.lower() in {n.lower() for n in params.get("history_tables", [])} for t in db.tables):
        yield Hit(evidence="No known migration history table was found.",
                  fix=manual(None, None, "Adopt a versioned migration tool that records what was applied."))


# ---- reliability ----

def _setting(db: Database, name: str) -> Any:
    low = name.lower()
    return next((v for k, v in db.settings.items() if str(k).lower() == low), None)


@check("reliability.recovery_settings_off")
def recovery_settings_off(db, profile, params):
    for item in params.get("recovery_settings", []):
        if item.get("dialects") and db.dialect not in item["dialects"]:
            continue
        value = _setting(db, item["setting"])
        if value is not None and str(value).strip().lower() in {str(v).lower() for v in item["bad_values"]}:
            yield Hit(evidence=f"Setting {item['setting']} is {value}.", vars={"setting": item["setting"]},
                      fix=manual(None, None, "Confirm the backup design and enable log archiving if point-in-time recovery is required."))


@check("reliability.recovery_settings_on")
def recovery_settings_on(db, profile, params):
    seen = []
    for item in params.get("recovery_settings", []):
        if item.get("dialects") and db.dialect not in item["dialects"]:
            continue
        value = _setting(db, item["setting"])
        if value is not None and str(value).strip().lower() not in {str(v).lower() for v in item["bad_values"]}:
            seen.append(f"{item['setting']}={value}")
    if seen:
        yield Hit(evidence="Recovery-related settings: " + ", ".join(seen) + ". A setting cannot prove that a backup exists.")


@check("reliability.not_backup_substitutes")
def not_backup_substitutes(db, profile, params):
    setting_rx = compile_any(params.get("replica_setting_patterns", []))
    history_rx = compile_any(params.get("history_table_patterns", []))
    signals = [k for k, v in db.settings.items() if matches(setting_rx, str(k)) and str(v).strip().lower() not in ("", "0", "off", "false", "none")]
    tables = [t.name for t in db.tables if matches(history_rx, t.name)]
    if signals or tables:
        parts = []
        if signals:
            parts.append("replication settings: " + ", ".join(sorted(signals)[:5]))
        if tables:
            parts.append("history tables: " + ", ".join(sorted(tables)[:5]))
        yield Hit(evidence="; ".join(parts) + ".")
