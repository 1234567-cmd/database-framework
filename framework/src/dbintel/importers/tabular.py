"""Turn rows of headers and cells into a typed Table, conservatively. Shared by the CSV and Excel importers."""
from __future__ import annotations

import datetime as dt
import re
from typing import Any, Optional, Sequence

from ..model import Column, Database, Table
from ._common import Sandbox, clean_identifier, unique_name

_INT_RE = re.compile(r"^[+-]?(?:0|[1-9]\d*)$")  # a leading zero means an identifier such as a postal code
_REAL_RE = re.compile(r"^[+-]?(?:0|[1-9]\d*)\.\d+(?:[eE][+-]?\d+)?$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?$")
_NULL_TOKENS = {"", "null", "\\n"}
_INT8_LIMIT = 2 ** 63 - 1


def is_null(value: Any) -> bool:
    if value is None:
        return True
    return isinstance(value, str) and value.strip().lower() in _NULL_TOKENS


def _is_int(text: str) -> bool:
    return bool(_INT_RE.match(text)) and abs(int(text)) <= _INT8_LIMIT


def _is_date(text: str) -> bool:
    if not _DATE_RE.match(text):
        return False
    try:
        dt.date.fromisoformat(text)
    except ValueError:
        return False
    return True


def _is_datetime(text: str) -> bool:
    if not _DATETIME_RE.match(text):
        return False
    try:
        dt.datetime.fromisoformat(text)
    except ValueError:
        return False
    return True


def infer_type(values: Sequence[Any]) -> str:
    """Pick the narrowest type every non-null value fits, and text whenever there is any doubt."""
    present = [v for v in values if not is_null(v)]
    if not present:
        return "text"
    if all(isinstance(v, bool) for v in present):
        return "boolean"
    if any(isinstance(v, bool) for v in present):
        return "text"
    if all(isinstance(v, int) for v in present):
        return "bigint"
    if all(isinstance(v, (int, float)) for v in present):
        return "double precision"
    if all(isinstance(v, dt.datetime) for v in present):
        return "timestamp"
    if all(isinstance(v, dt.date) and not isinstance(v, dt.datetime) for v in present):
        return "date"
    if not all(isinstance(v, str) for v in present):
        return "text"
    texts = [v.strip() for v in present]
    if all(_is_int(t) for t in texts):
        return "bigint"
    if all(_is_int(t) or _REAL_RE.match(t) for t in texts) and any(_REAL_RE.match(t) for t in texts):
        return "double precision"
    if all(t.lower() in {"true", "false"} for t in texts):
        return "boolean"
    if all(_is_date(t) for t in texts):
        return "date"
    if all(_is_datetime(t) for t in texts):
        return "timestamp"
    return "text"


def _convert(value: Any, data_type: str) -> Any:
    if is_null(value):
        return None
    if isinstance(value, str):
        text = value.strip()
        if data_type == "bigint":
            return int(text)
        if data_type == "double precision":
            return float(text)
        if data_type == "boolean":
            return 1 if text.lower() == "true" else 0
    return value


def normalize_headers(header: Sequence[Any], width: int, label: str, db: Database) -> list[str]:
    used: set[str] = set()
    names: list[str] = []
    blanks = 0
    duplicates = 0
    for i in range(width):
        raw = header[i] if i < len(header) else None
        text = "" if raw is None else str(raw).strip()
        if not text:
            blanks += 1
            text = f"column_{i + 1}"
        before = text.lower() in used
        names.append(unique_name(text, used))
        duplicates += int(before)
    if blanks:
        db.import_warnings.append(f"{label}: {blanks} blank header(s) were given generated names")
    if duplicates:
        db.import_warnings.append(f"{label}: {duplicates} duplicate header(s) were renamed")
    return names


def add_table(db: Database, sandbox: Sandbox, table_name: str, columns: list[str], rows: list[list[Any]], used: set[str]) -> Table:
    types = [infer_type([row[i] for row in rows]) for i in range(len(columns))]
    name = unique_name(clean_identifier(table_name, "table"), used)
    table = Table(name=name, columns=[Column(name=c, data_type=t, ordinal=i + 1) for i, (c, t) in enumerate(zip(columns, types))],
                  row_count=len(rows))
    sandbox_name = sandbox.add_table(table)
    sandbox.insert(sandbox_name, columns, ([_convert(v, t) for v, t in zip(row, types)] for row in rows))
    db.tables.append(table)
    return table


def header_looks_real(first: Sequence[Any], rest: Sequence[Sequence[Any]]) -> bool:
    """A first row is a header unless it contains numbers or is blank where the data is not."""
    cells = [c for c in first if not is_null(c)]
    if not cells:
        return False
    for cell in cells:
        if not isinstance(cell, str):
            return False
        text = cell.strip()
        if _is_int(text) or _REAL_RE.match(text) or _is_date(text):
            return False
    return True
