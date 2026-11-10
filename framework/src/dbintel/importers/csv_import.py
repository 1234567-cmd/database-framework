"""CSV and other delimited text into a Database, with rows in the read-only sandbox."""
from __future__ import annotations

import csv
import io
import os
from pathlib import Path
from typing import Optional, Union

from ..model import Database
from ._common import Sandbox, read_text
from .tabular import add_table, header_looks_real, normalize_headers

_EXTENSIONS = {".csv", ".tsv", ".txt", ".gz"}
_DELIMITERS = [",", ";", "\t", "|"]


def sniff_delimiter(sample: str) -> str:
    """Prefer the delimiter that splits lines into the most consistent, largest number of fields."""
    lines = [line for line in sample.splitlines() if line.strip()][:50]
    if not lines:
        return ","
    best, best_score = ",", (-1.0, 0)
    for delimiter in _DELIMITERS:
        counts = [len(next(csv.reader([line], delimiter=delimiter))) if line else 0 for line in lines]
        common = max(set(counts), key=counts.count)
        if common < 2:
            continue
        score = (counts.count(common) / len(counts), common)
        if score > best_score:
            best, best_score = delimiter, score
    return best


def _load_file(db: Database, sandbox: Sandbox, path: Path, used: set[str]) -> None:
    label = path.name
    text = read_text(path).replace("\x00", "")
    if not text.strip():
        db.import_warnings.append(f"{label}: file is empty; no table created")
        return
    delimiter = sniff_delimiter(text[:65536])
    csv.field_size_limit(2 ** 31 - 1)
    records = [row for row in csv.reader(io.StringIO(text, newline=""), delimiter=delimiter) if any(cell.strip() for cell in row)]
    if not records:
        db.import_warnings.append(f"{label}: no rows found; no table created")
        return
    has_header = header_looks_real(records[0], records[1:])
    header = records[0] if has_header else []
    body = records[1:] if has_header else records
    if not has_header:
        db.import_warnings.append(f"{label}: no header row detected; columns were given generated names")
    width = max(len(header), max((len(r) for r in body), default=0))
    columns = normalize_headers(header, width, label, db)
    short = sum(1 for r in body if len(r) < width)
    long_rows = sum(1 for r in body if len(r) > len(header)) if header else 0
    if short:
        db.import_warnings.append(f"{label}: {short} short row(s) padded with NULL")
    if long_rows:
        db.import_warnings.append(f"{label}: {long_rows} row(s) had more fields than the header")
    rows = [list(r) + [None] * (width - len(r)) for r in body]
    add_table(db, sandbox, path.name.split(".")[0], columns, rows, used)


def import_csv(path_or_dir: Union[str, "os.PathLike[str]"], name: Optional[str] = None) -> Database:
    """Load one delimited file, or every delimited file directly inside a directory, one table per file."""
    target = Path(path_or_dir)
    if not target.exists():
        raise FileNotFoundError(f"no such file or directory: {target}")
    files = sorted(p for p in target.iterdir() if p.is_file() and p.suffix.lower() in _EXTENSIONS) if target.is_dir() else [target]
    db = Database(name=name or target.stem, dialect="generic", source="csv")
    sandbox = Sandbox(db.name)
    used: set[str] = set()
    for path in files:
        try:
            _load_file(db, sandbox, path, used)
        except (OSError, csv.Error, ValueError) as exc:
            db.import_warnings.append(f"{path.name}: could not be read: {exc}")
    if not files:
        db.import_warnings.append(f"{target}: no delimited files found")
    sandbox.freeze()
    db.data = sandbox
    return db
