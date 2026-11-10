"""Importers: turn dumps, files and URLs into a Database."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Union

from ..connectors import open_connector, redact_url
from ..model import Database
from .csv_import import import_csv
from .excel_import import import_excel
from .metadata import export_metadata, import_metadata, load_pipelines, load_query_log
from .sql_dump import detect_dialect, import_sql

_SQLITE_MAGIC = b"SQLite format 3\x00"
_SQL_EXT = {".sql", ".dump", ".ddl"}
_CSV_EXT = {".csv", ".tsv"}
_EXCEL_EXT = {".xlsx", ".xlsm"}
_SQLITE_EXT = {".db", ".sqlite", ".sqlite3", ".db3"}


def _is_sqlite_file(path: Path) -> bool:
    try:
        with open(path, "rb") as handle:
            return handle.read(16) == _SQLITE_MAGIC
    except OSError:
        return False


def load_source(path_or_url: Union[str, "os.PathLike[str]"], dialect: Optional[str] = None, name: Optional[str] = None,
                password_env: Optional[str] = None) -> Database:
    """Open a connection URL, or import a file or directory chosen by its extension or content."""
    text = os.fspath(path_or_url)
    if "://" in text:
        return _extract(text, password_env, name)
    path = Path(text)
    if not path.exists():
        raise FileNotFoundError(f"no such file or directory: {redact_url(text)}")
    if path.is_dir():
        return import_csv(path, name)
    suffix = path.suffix.lower()
    if suffix == ".gz":
        inner = Path(path.stem).suffix.lower()
        if inner in _SQL_EXT:
            return import_sql(path, dialect, name)
        if inner in _CSV_EXT:
            return import_csv(path, name)
    if suffix in _SQLITE_EXT or _is_sqlite_file(path):
        return _extract(f"sqlite:///{path.resolve().as_posix()}", None, name)
    if suffix in _SQL_EXT:
        return import_sql(path, dialect, name)
    if suffix in _CSV_EXT:
        return import_csv(path, name)
    if suffix in _EXCEL_EXT:
        return import_excel(path, name)
    if suffix == ".json":
        return _named(import_metadata(path), name)
    raise ValueError(f"cannot tell how to import {path.name}; expected a URL or a "
                     ".sql, .csv, .tsv, .xlsx, .json or SQLite file")


def _extract(url: str, password_env: Optional[str], name: Optional[str]) -> Database:
    """Open and read a live source. The connector stays open as ``db.data``; if extraction fails it is closed here."""
    connector = open_connector(url, password_env)
    try:
        return _named(connector.extract(), name)
    except BaseException:
        connector.close()
        raise


def _named(db: Database, name: Optional[str]) -> Database:
    if name:
        db.name = name
    return db


__all__ = ["detect_dialect", "export_metadata", "import_csv", "import_excel", "import_metadata", "import_sql", "load_pipelines",
           "load_query_log", "load_source"]
