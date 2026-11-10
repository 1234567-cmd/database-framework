"""Helpers shared by the importers: reading text with unknown encodings and the in-memory SQLite sandbox."""
from __future__ import annotations

import datetime as _dt
import decimal
import gzip
import os
import re
import sqlite3
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence

from ..connectors.base import Connector
from ..connectors.sqlite import SQLiteConnector
from ..model import Table

_MAX_INT = 2 ** 63 - 1


def decode_bytes(raw: bytes) -> str:
    """Decode by byte-order mark, then UTF-8, then Latin-1, which accepts anything."""
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw[3:].decode("utf-8", "replace")
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):  # e.g. PowerShell redirection of mysqldump output
        return raw.decode("utf-16", "replace")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


def read_text(path: "str | os.PathLike[str]") -> str:
    p = Path(path)
    raw = gzip.decompress(p.read_bytes()) if p.suffix.lower() == ".gz" else p.read_bytes()
    return decode_bytes(raw)


def sqlite_type(table_column: Any) -> str:
    family = table_column.type.family
    if family in {"int", "bool"}:
        return "INTEGER"
    if family in {"decimal", "float", "money"}:
        return "NUMERIC"
    return "BLOB" if family == "binary" else "TEXT"


def _bindable(value: Any) -> Any:
    if value is None or isinstance(value, (str, float, bytes)):
        return value
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value if -_MAX_INT - 1 <= value <= _MAX_INT else str(value)
    if isinstance(value, (_dt.datetime, _dt.date, _dt.time)):
        return value.isoformat()
    if isinstance(value, decimal.Decimal):
        return str(value)
    return str(value)


def _qualified_pattern(schema: str, table: str) -> re.Pattern:
    part = lambda name: "[\"`]?" + re.escape(name) + "[\"`]?"  # noqa: E731
    return re.compile(rf"(?<![\w.]){part(schema)}\.{part(table)}(?![\w])", re.I)


class Sandbox(SQLiteConnector):
    """A private in-memory SQLite database holding imported rows. It is read-only once ``freeze`` has been called.

    Tables are created from model objects and rows are inserted with bound parameters; dump SQL is never executed.
    """

    def __init__(self, name: str = "sandbox"):
        Connector.__init__(self, None)
        self._conn = sqlite3.connect(":memory:", check_same_thread=False)
        self._name = name
        self._used: set[str] = set()
        self._aliases: list[tuple[re.Pattern, str]] = []

    def add_table(self, table: Table) -> str:
        """Create a constraint-free table with the model's columns, so dirty data still loads. Returns its name."""
        name = table.name
        if name.lower() in self._used:  # same table name in two schemas
            name = f"{table.schema}.{table.name}"
        self._used.add(name.lower())
        if table.schema:
            self._aliases.append((_qualified_pattern(table.schema, table.name), self.quote(name)))
        cols = ", ".join(f"{self.quote(c.name)} {sqlite_type(c)}" for c in table.columns)
        self._conn.execute(f"CREATE TABLE {self.quote(name)} ({cols})")
        return name

    def _execute(self, sql: str, params: Sequence[Any]) -> list[tuple]:
        """Rows live in one flat SQLite namespace, so a schema-qualified name from an analyzer is rewritten to its table."""
        for pattern, name in self._aliases:
            sql = pattern.sub(name, sql)
        return super()._execute(sql, params)

    def insert(self, table: str, columns: Sequence[str], rows: Iterable[Sequence[Any]]) -> int:
        col_list = ", ".join(self.quote(c) for c in columns)
        marks = ", ".join("?" * len(columns))
        sql = f"INSERT INTO {self.quote(table)} ({col_list}) VALUES ({marks})"
        count = 0

        def bound():
            nonlocal count
            for row in rows:
                count += 1
                yield [_bindable(v) for v in row]

        self._conn.executemany(sql, bound())
        return count

    def freeze(self) -> None:
        self._conn.commit()
        self._conn.execute("PRAGMA query_only = ON")

    def column_count(self, table: str) -> int:
        return len(self._conn.execute(f"PRAGMA table_info({self.quote(table)})").fetchall())


def unique_name(name: str, used: set[str]) -> str:
    base = name
    n = 2
    while name.lower() in used:
        name = f"{base}_{n}"
        n += 1
    used.add(name.lower())
    return name


def clean_identifier(text: Optional[str], fallback: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in (text or "").strip())
    cleaned = cleaned.strip("_")
    return cleaned or fallback
