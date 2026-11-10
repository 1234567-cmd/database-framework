"""Rebuild plan and schema objects from a saved run so that it can be tested after the original analysis process has ended.

Only the report and ``plan.json`` written for that run are read. Row data is never stored, so a rebuilt model has no rows.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from ..migrate.generator import Check, MigrationPlan, MigrationStep
from ..migrate.safety import plan_hash
from ..model import CheckConstraint, Column, Database, ForeignKey, Index, Table


class RebuildError(Exception):
    """The saved run does not hold enough to rebuild the plan. The message is shown to the person."""


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise RebuildError(f"The saved run has no {path.name}.") from None
    except (OSError, ValueError):
        raise RebuildError(f"The saved run's {path.name} could not be read.") from None


def rebuild_plan(run_dir: Path, expected_hash: Optional[str] = None) -> MigrationPlan:
    raw = _read_json(Path(run_dir) / "migrations" / "plan.json")
    stored = raw.pop("plan_hash", None) if isinstance(raw, dict) else None
    try:
        steps = [MigrationStep(**{**s, "prechecks": [Check(**c) for c in s.get("prechecks") or []],
                                  "postchecks": [Check(**c) for c in s.get("postchecks") or []]}) for s in raw.get("steps") or []]
        plan = MigrationPlan(database=raw["database"], source_dialect=raw["source_dialect"], dialect=raw["dialect"], steps=steps,
                             notes=list(raw.get("notes") or []), unaddressed_findings=list(raw.get("unaddressed_findings") or []),
                             satisfied_findings=list(raw.get("satisfied_findings") or []), backup_recommendation=raw.get("backup_recommendation") or "")
    except (KeyError, TypeError, ValueError) as exc:
        raise RebuildError(f"The saved plan is not in the expected form ({type(exc).__name__}).") from None
    computed = plan_hash(plan)
    if expected_hash is not None and computed != expected_hash:
        raise RebuildError("The saved plan no longer matches the plan hash in the report, so it cannot be trusted.")
    if stored is not None and computed != stored:
        raise RebuildError("The saved plan no longer matches the hash stored with it, so it cannot be trusted.")
    return plan


def rebuild_database(report: dict[str, Any]) -> Database:
    """Build a schema-only ``Database`` from the additive fields of ``report.json``. Reports without them are refused."""
    arch = report.get("architecture") or {}
    tables_raw = arch.get("tables") or []
    source = report.get("source") or {}
    if not tables_raw:
        raise RebuildError("The saved report has no table definitions.")
    if any("index_list" not in t or "short_name" not in t for t in tables_raw):
        raise RebuildError("This run was saved by an earlier version without index and key details, so its schema cannot be rebuilt. Re-run the analysis to test it.")
    tables: list[Table] = []
    by_name: dict[str, Table] = {}
    for raw in tables_raw:
        columns = [Column(name=c["name"], data_type=c["type"], nullable=bool(c.get("nullable", True)), default=c.get("default"), comment=c.get("comment"),
                          is_identity=bool(c.get("identity")), is_generated=bool(c.get("generated")), ordinal=c.get("ordinal") or 0)
                   for c in raw.get("column_list") or []]
        table = Table(name=raw["short_name"], schema=raw.get("schema"), columns=columns, primary_key=list(raw.get("primary_key") or []),
                      primary_key_name=raw.get("primary_key_name"), comment=raw.get("comment"), row_count=raw.get("row_count"), rls_enabled=raw.get("rls_enabled"),
                      indexes=[Index(name=i.get("name"), columns=list(i.get("columns") or []), unique=bool(i.get("unique")), primary=bool(i.get("primary")),
                                     method=i.get("method"), where=i.get("where"), include=list(i.get("include") or []), is_constraint=bool(i.get("is_constraint")))
                               for i in raw.get("index_list") or []],
                      checks=[CheckConstraint(name=c.get("name"), expression=c.get("expression") or "", columns=list(c.get("columns") or []))
                              for c in raw.get("check_list") or []])
        tables.append(table)
        by_name[raw["name"].lower()] = table
        by_name.setdefault(raw["short_name"].lower(), table)
    for rel in arch.get("relations") or []:
        table = by_name.get(str(rel.get("from", "")).lower())
        if table is None:
            continue
        table.foreign_keys.append(ForeignKey(name=rel.get("name"), columns=list(rel.get("columns") or []), ref_table=rel.get("to"),
                                             ref_columns=list(rel.get("ref_columns") or []), ref_schema=rel.get("ref_schema"),
                                             on_delete=rel.get("on_delete"), on_update=rel.get("on_update")))
    return Database(name=source.get("name") or "saved", dialect=source.get("dialect") or "generic", source="saved_report", tables=tables)


def rebuild(run_dir: Path) -> tuple[MigrationPlan, Database]:
    report = _read_json(Path(run_dir) / "report.json")
    plan = rebuild_plan(run_dir, (report.get("migration") or {}).get("plan_hash"))
    return plan, rebuild_database(report)
