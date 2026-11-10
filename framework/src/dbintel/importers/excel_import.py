"""Excel workbooks into a Database: one table per worksheet, with rows in the read-only sandbox."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional, Union

from ..model import Database
from ._common import Sandbox
from .tabular import add_table, header_looks_real, is_null, normalize_headers


def import_excel(path: Union[str, "os.PathLike[str]"], name: Optional[str] = None) -> Database:
    """Read an .xlsx workbook. Formulas are read as their last calculated values."""
    target = Path(path)
    if not target.exists():
        raise FileNotFoundError(f"no such file: {target}")
    try:
        import openpyxl
    except ImportError:
        raise ImportError("openpyxl is not installed; run: pip install dbintel[excel]") from None
    db = Database(name=name or target.stem, dialect="generic", source="excel")
    sandbox = Sandbox(db.name)
    used: set[str] = set()
    workbook = openpyxl.load_workbook(target, read_only=True, data_only=True)
    try:
        for sheet in workbook.worksheets:
            _load_sheet(db, sandbox, sheet, used)
    finally:
        workbook.close()
    if not db.tables:
        db.import_warnings.append(f"{target.name}: no worksheet contained data")
    sandbox.freeze()
    db.data = sandbox
    return db


def _load_sheet(db: Database, sandbox: Sandbox, sheet: Any, used: set[str]) -> None:
    label = f"sheet {sheet.title}"
    records = [list(row) for row in sheet.iter_rows(values_only=True) if not all(is_null(c) for c in row)]
    if not records:
        db.import_warnings.append(f"{label}: empty; no table created")
        return
    width = max(max((i + 1 for i, c in enumerate(row) if not is_null(c)), default=0) for row in records)
    records = [row[:width] + [None] * (width - len(row)) for row in records]
    has_header = header_looks_real(records[0], records[1:])
    header = records[0] if has_header else []
    body = records[1:] if has_header else records
    if not has_header:
        db.import_warnings.append(f"{label}: no header row detected; columns were given generated names")
    columns = normalize_headers(header, width, label, db)
    add_table(db, sandbox, sheet.title, columns, body, used)
