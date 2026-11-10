"""SQLite connector (standard library). Files are opened with a mode=ro URI."""
from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path
from typing import Any, Optional, Sequence

from ..model import Column, Database, ForeignKey, Index, Routine, Table, View
from .base import ConnectionInfo, Connector, ConnectorError, sql_references

_IS_AUTOINCREMENT = re.compile(r"\bAUTOINCREMENT\b", re.I)
_WHERE = re.compile(r"\bWHERE\b(.*)$", re.I | re.S)


class SQLiteConnector(Connector):
    dialect = "sqlite"
    paramstyle = "qmark"

    def __init__(self, info: ConnectionInfo):
        super().__init__(info)
        path = info.database
        if not path or not os.path.isfile(path):
            raise ConnectorError(f"SQLite file not found: {path}")
        uri = Path(path).resolve().as_uri() + "?mode=ro"
        try:
            self._conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
            self._conn.execute("PRAGMA query_only = ON")
        except sqlite3.Error as exc:
            raise ConnectorError(f"could not open SQLite file: {self._clean(exc)}") from None
        self._name = Path(path).stem

    def _execute(self, sql: str, params: Sequence[Any]) -> list[tuple]:
        return [tuple(r) for r in self._conn.execute(sql, tuple(params)).fetchall()]

    def close(self) -> None:
        conn, self._conn = getattr(self, "_conn", None), None
        if conn is not None:
            conn.close()

    def extract(self) -> Database:
        db = Database(name=self._name, dialect="sqlite", source="live", data=self)
        objects = self._section(db, "schema", "SELECT type, name, tbl_name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' "
                                              "ORDER BY type, name") or []
        for kind, name, _table, sql in objects:
            if kind == "table":
                db.tables.append(self._table(db, name, sql or ""))
            elif kind == "view":
                definition = re.sub(r"(?is)^.*?\bAS\b\s*", "", sql or "", count=1).strip().rstrip(";")
                db.views.append(View(name=name, definition=definition, references=sql_references(definition, "sqlite")))
            elif kind == "trigger":
                db.routines.append(Routine(name=name, kind="trigger", table=_table, definition=sql or "",
                                           references=sql_references(sql or "", "sqlite")))
        by_name = {t.name: t for t in db.tables}
        for kind, name, table_name, sql in objects:
            if kind == "index" and table_name in by_name:
                by_name[table_name].indexes.extend(self._named_index(db, name, sql or ""))
        version = self._section(db, "version", "SELECT sqlite_version()")
        encoding = self._section(db, "encoding", "PRAGMA encoding")
        foreign_keys = self._section(db, "foreign key mode", "PRAGMA foreign_keys")
        if version:
            db.settings["server_version"] = version[0][0]
        if encoding:
            db.settings["encoding"] = encoding[0][0]
        if foreign_keys:
            db.settings["foreign_keys"] = bool(foreign_keys[0][0])
        return db

    def _table(self, db: Database, name: str, create_sql: str) -> Table:
        table = Table(name=name)
        info = self._section(db, f"columns of {name}", f"PRAGMA table_xinfo({self.quote(name)})") or []
        pk_columns: list[tuple[int, str]] = []
        for cid, column, dtype, notnull, default, pk, hidden in info:
            if hidden == 1:
                continue  # hidden column of a virtual table
            if pk:
                pk_columns.append((pk, column))
            table.columns.append(Column(name=column, data_type=dtype or "", nullable=not notnull and not pk,
                                        default=default, is_generated=hidden in (2, 3), ordinal=cid + 1))
        table.primary_key = [c for _, c in sorted(pk_columns)]
        if len(table.primary_key) == 1:
            column = table.column(table.primary_key[0])
            if column is not None and (column.data_type.upper() == "INTEGER" or _IS_AUTOINCREMENT.search(create_sql)):
                column.is_identity = True
        self._apply_definition(db, table, create_sql)
        self._automatic_indexes(db, table)
        self._foreign_keys(db, table)
        rows = self._section(db, f"row count of {name}", f"SELECT COUNT(*) FROM {self.quote(name)}")
        table.row_count = rows[0][0] if rows else None
        return table

    def _apply_definition(self, db: Database, table: Table, create_sql: str) -> None:
        """Checks and collations are visible only in the CREATE TABLE text."""
        if not create_sql:
            return
        from ..importers.sql_dump import parse_create_table  # local: importers depend on this package
        try:
            parsed = parse_create_table(create_sql, "sqlite")
        except Exception as exc:
            db.import_warnings.append(f"definition of {table.name} not parsed; check constraints may be missing: {exc}")
            return
        table.checks = parsed.checks
        for column in table.columns:
            source = parsed.column(column.name)
            if source is not None:
                column.collation = source.collation
                column.comment = source.comment

    def _automatic_indexes(self, db: Database, table: Table) -> None:
        rows = self._section(db, f"indexes of {table.name}", f"PRAGMA index_list({self.quote(table.name)})") or []
        for _seq, name, unique, origin, _partial in rows:
            if origin == "u":  # created implicitly by a UNIQUE constraint
                table.indexes.append(Index(name=name, columns=self._index_columns(db, name), unique=bool(unique), is_constraint=True))

    def _named_index(self, db: Database, name: str, create_sql: str) -> list[Index]:
        unique = bool(re.match(r"(?is)\s*CREATE\s+UNIQUE\b", create_sql))
        tail = create_sql[create_sql.rfind(")") + 1:]
        match = _WHERE.search(tail) or _WHERE.search(create_sql)
        return [Index(name=name, columns=self._index_columns(db, name), unique=unique,
                      where=match.group(1).strip() if match else None)]

    def _index_columns(self, db: Database, name: str) -> list[str]:
        rows = self._section(db, f"columns of index {name}", f"PRAGMA index_info({self.quote(name)})") or []
        return [column if column is not None else "<expression>" for _seq, _cid, column in rows]

    def _foreign_keys(self, db: Database, table: Table) -> None:
        rows = self._section(db, f"foreign keys of {table.name}", f"PRAGMA foreign_key_list({self.quote(table.name)})") or []
        grouped: dict[int, ForeignKey] = {}
        for fk_id, _seq, ref_table, column, ref_column, on_update, on_delete, _match in rows:
            fk = grouped.get(fk_id)
            if fk is None:
                fk = grouped[fk_id] = ForeignKey(name=None, columns=[], ref_table=ref_table, ref_columns=[],
                                                 on_delete=on_delete, on_update=on_update)
                table.foreign_keys.append(fk)
            fk.columns.append(column)
            if ref_column is not None:
                fk.ref_columns.append(ref_column)
