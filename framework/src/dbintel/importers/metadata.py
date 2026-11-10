"""JSON metadata, query logs and pipeline manifests.

Metadata form, written by ``export_metadata`` and read by ``import_metadata``::

    {
      "format": "dbintel-metadata", "version": 1,
      "name": "shop", "dialect": "postgres", "source": "metadata",
      "tables": [{"name": "orders", "schema": "public",
                  "columns": [{"name": "id", "data_type": "integer", "nullable": false}],
                  "primary_key": ["id"], "indexes": [{"name": "ix", "columns": ["a"]}],
                  "foreign_keys": [{"name": "fk", "columns": ["c"], "ref_table": "t", "ref_columns": ["id"]}],
                  "checks": [{"name": "ck", "expression": "a > 0"}]}],
      "views": [], "routines": [], "roles": [], "grants": [], "policies": [], "query_stats": [], "pipelines": [],
      "settings": {}, "security_metadata": false, "import_warnings": []
    }

Field names are those of the dataclasses in ``dbintel.model``; only ``name`` is required on most objects. Unknown fields
produce warnings and are ignored. ``format`` and ``version`` are optional on input. Row data is never included.

Pipeline manifests are YAML: a list of jobs, a mapping with ``pipelines:``, or one job. Each job takes the PipelineJob fields,
with ``steps`` taking the PipelineStep fields.
"""
from __future__ import annotations

import dataclasses
import json
import os
from pathlib import Path
from typing import Any, Optional, Union

from ..model import (CheckConstraint, Column, Database, ForeignKey, Grant, Index, PipelineJob, PipelineStep, QueryStat, RlsPolicy,
                     Role, Routine, Table, View)
from ._common import read_text

FORMAT = "dbintel-metadata"
VERSION = 1
PathArg = Union[str, "os.PathLike[str]"]

_NESTED: dict[type, dict[str, type]] = {
    Table: {"columns": Column, "indexes": Index, "foreign_keys": ForeignKey, "checks": CheckConstraint},
    PipelineJob: {"steps": PipelineStep},
}
_DATABASE_LISTS: dict[str, type] = {
    "tables": Table, "views": View, "routines": Routine, "roles": Role, "grants": Grant, "policies": RlsPolicy,
    "query_stats": QueryStat, "pipelines": PipelineJob,
}


def _build(cls: type, data: Any, warnings: list[str], where: str) -> Optional[Any]:
    if not isinstance(data, dict):
        warnings.append(f"{where}: expected an object, found {type(data).__name__}; skipped")
        return None
    known = {f.name: f for f in dataclasses.fields(cls)}
    kwargs: dict[str, Any] = {}
    for key, value in data.items():
        if key not in known:
            warnings.append(f"{where}: unknown field {key!r} ignored")
            continue
        nested = _NESTED.get(cls, {}).get(key)
        if nested is not None:
            items = value if isinstance(value, list) else []
            kwargs[key] = [obj for i, item in enumerate(items)
                           if (obj := _build(nested, item, warnings, f"{where}.{key}[{i}]")) is not None]
        else:
            kwargs[key] = value
    missing = [f.name for f in known.values()
               if f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING and f.name not in kwargs]
    if missing:
        warnings.append(f"{where}: missing required field {missing[0]!r}; skipped")
        return None
    return cls(**kwargs)


def import_metadata(path: PathArg) -> Database:
    """Read a metadata JSON file. The result has no ``data`` access, so rules needing row data are skipped."""
    raw = json.loads(read_text(path))
    if not isinstance(raw, dict):
        raise ValueError("metadata file must contain a JSON object")
    if raw.get("format", FORMAT) != FORMAT:
        raise ValueError(f"not a {FORMAT} file")
    warnings: list[str] = []
    db = Database(name=str(raw.get("name") or Path(path).stem), dialect=str(raw.get("dialect") or "generic"),
                  source=str(raw.get("source") or "metadata"))
    for key, cls in _DATABASE_LISTS.items():
        items = raw.get(key) or []
        if not isinstance(items, list):
            warnings.append(f"{key}: expected a list; skipped")
            continue
        setattr(db, key, [obj for i, item in enumerate(items) if (obj := _build(cls, item, warnings, f"{key}[{i}]")) is not None])
    settings = raw.get("settings") or {}
    db.settings = settings if isinstance(settings, dict) else {}
    db.security_metadata = bool(raw.get("security_metadata", False))
    db.import_warnings = [str(w) for w in raw.get("import_warnings") or []] + warnings
    return db


def export_metadata(db: Database, path: PathArg) -> Path:
    """Write the model, without row data or any connection details, as JSON."""
    payload: dict[str, Any] = {"format": FORMAT, "version": VERSION, "name": db.name, "dialect": db.dialect, "source": db.source}
    for key in _DATABASE_LISTS:
        payload[key] = [dataclasses.asdict(o) for o in getattr(db, key)]
    payload.update(settings=db.settings, security_metadata=db.security_metadata, import_warnings=db.import_warnings)
    target = Path(path)
    target.write_text(json.dumps(payload, indent=2, default=str, sort_keys=False), encoding="utf-8")
    return target


def load_query_log(db: Database, path: PathArg) -> Database:
    """Add QueryStat entries from semicolon-separated SQL, or a JSON list of objects with sql, calls, mean_ms and plan."""
    text = read_text(path)
    stripped = text.lstrip()
    if Path(path).suffix.lower() == ".json" or stripped.startswith("["):
        _load_json_log(db, text, Path(path).name)
        return db
    from .sql_dump import split_statements
    counts: dict[str, int] = {}
    for statement in split_statements(text, db.dialect if db.dialect in {"mysql", "postgres", "sqlite"} else "generic"):
        counts[statement.text] = counts.get(statement.text, 0) + 1
    db.query_stats.extend(QueryStat(sql=sql, calls=calls) for sql, calls in counts.items())
    return db


def _load_json_log(db: Database, text: str, label: str) -> None:
    try:
        entries = json.loads(text)
    except ValueError as exc:
        db.import_warnings.append(f"{label}: invalid JSON query log: {exc}")
        return
    if not isinstance(entries, list):
        db.import_warnings.append(f"{label}: expected a JSON list")
        return
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict) or not isinstance(entry.get("sql"), str) or not entry["sql"].strip():
            db.import_warnings.append(f"{label}[{i}]: no sql; skipped")
            continue
        try:
            calls = int(entry.get("calls", 1))
            mean_ms = float(entry.get("mean_ms", 0.0))
            total_ms = float(entry.get("total_ms", calls * mean_ms))
            rows = entry.get("rows")
            rows = None if rows is None else int(rows)
        except (TypeError, ValueError):
            db.import_warnings.append(f"{label}[{i}]: non-numeric calls, mean_ms, total_ms or rows; skipped")
            continue
        plan = entry.get("plan")
        if plan is not None and not isinstance(plan, str):
            plan = json.dumps(plan)
        db.query_stats.append(QueryStat(sql=entry["sql"], calls=calls, total_ms=total_ms, mean_ms=mean_ms, rows=rows, plan=plan))


def load_pipelines(db: Database, path: PathArg) -> Database:
    """Add PipelineJob entries from a YAML manifest."""
    import yaml
    label = Path(path).name
    try:
        doc = yaml.safe_load(read_text(path))
    except yaml.YAMLError as exc:
        db.import_warnings.append(f"{label}: invalid YAML: {str(exc).splitlines()[0]}")
        return db
    if isinstance(doc, dict) and "pipelines" in doc:
        jobs = doc["pipelines"]
    elif isinstance(doc, dict):
        jobs = [doc]
    else:
        jobs = doc
    if not isinstance(jobs, list):
        db.import_warnings.append(f"{label}: expected a list of pipelines")
        return db
    for i, item in enumerate(jobs):
        job = _build(PipelineJob, item, db.import_warnings, f"{label}[{i}]")
        if job is not None:
            job.source_file = str(path)
            db.pipelines.append(job)
    return db
