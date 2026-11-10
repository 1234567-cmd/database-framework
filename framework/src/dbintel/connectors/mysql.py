"""MySQL and MariaDB connector (PyMySQL). Sessions are read-only at the server as well as through the guard."""
from __future__ import annotations

import re
from typing import Any, Optional, Sequence

from ..model import (CheckConstraint, Column, Database, ForeignKey, Grant, Index, QueryStat, Role, Routine, Table, View)
from .base import ConnectionInfo, Connector, ConnectorError, import_driver, sql_references

_SYSTEM = ("mysql", "information_schema", "performance_schema", "sys")
_SYSTEM_ACCOUNTS = ("mysql.sys", "mysql.session", "mysql.infoschema", "mariadb.sys")
_SETTINGS = ("version", "version_comment", "character_set_server", "collation_server", "sql_mode", "log_bin", "binlog_format",
             "binlog_row_image", "innodb_flush_log_at_trx_commit", "require_secure_transport", "have_ssl", "max_connections",
             "general_log", "slow_query_log", "default_storage_engine", "local_infile", "secure_file_priv", "lower_case_table_names")


def _text(value: Any) -> Any:
    """information_schema often returns text as bytes, depending on server version and column collation."""
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).decode("utf-8", "replace")
    return value


def _flag(value: Any) -> bool:
    value = _text(value)
    return str(value).strip().upper() in {"1", "Y", "YES", "ON", "TRUE"}


def _split_grantee(grantee: str) -> str:
    """information_schema writes grantees as ``'user'@'host'``; Grant.grantee holds the user, matching Role.name."""
    match = re.match(r"^'((?:[^']|'')*)'(?:@'(.*)')?$", grantee or "")
    return match.group(1).replace("''", "'") if match else (grantee or "")


class MySQLConnector(Connector):
    dialect = "mysql"
    paramstyle = "format"

    def __init__(self, info: ConnectionInfo):
        super().__init__(info)
        pymysql = import_driver("pymysql", "mysql")
        options = dict(info.options)
        kwargs: dict[str, Any] = {"host": info.host or "localhost", "port": info.port or 3306, "user": info.user,
                                  "password": info.password or "", "database": info.database or None,
                                  "charset": options.get("charset", "utf8mb4"), "autocommit": True,
                                  "connect_timeout": int(options.get("connect_timeout", 15))}
        try:
            self._conn = pymysql.connect(**kwargs)
        except Exception as exc:
            raise ConnectorError(f"could not connect to MySQL: {self._clean(exc)}") from None
        self._require_read_only()

    def _raw(self, sql: str) -> list[tuple]:
        with self._conn.cursor() as cur:
            cur.execute(sql)
            return list(cur.fetchall()) if cur.description else []

    def _require_read_only(self) -> None:
        """Set the session read-only and confirm the server agrees before anything else may run."""
        try:
            self._raw("SET SESSION TRANSACTION READ ONLY")
            try:
                row = self._raw("SELECT @@SESSION.transaction_read_only")
            except Exception:  # MySQL before 5.7.20 and MariaDB use the older name
                row = self._raw("SELECT @@SESSION.tx_read_only")
        except Exception as exc:
            self.close()
            raise ConnectorError(f"could not enforce a read-only session: {self._clean(exc)}") from None
        if not row or not _flag(row[0][0]):
            self.close()
            raise ConnectorError("the server did not accept a read-only session; refusing to continue")

    def _execute(self, sql: str, params: Sequence[Any]) -> list[tuple]:
        with self._conn.cursor() as cur:
            cur.execute(sql, tuple(params) if params else None)
            rows = cur.fetchall() if cur.description else []
        return [tuple(r) for r in rows]

    def quote(self, identifier: str) -> str:
        return "`" + identifier.replace("`", "``") + "`"

    def close(self) -> None:
        conn, self._conn = getattr(self, "_conn", None), None
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass

    # ----------------------------------------------------------------------------------------------------------------

    def _rows(self, db: Database, label: str, sql: str, params: Sequence[Any] = ()) -> Optional[list[tuple]]:
        rows = self._section(db, label, sql, params)
        return None if rows is None else [tuple(_text(v) for v in r) for r in rows]

    def _schema_filter(self, column: str) -> tuple[str, list[str]]:
        if self.info and self.info.database:
            return f"{column} = %s", [self.info.database]
        return f"{column} NOT IN ({', '.join(['%s'] * len(_SYSTEM))})", list(_SYSTEM)

    def extract(self) -> Database:
        db = Database(name=self.info.database if self.info and self.info.database else "mysql", dialect="mysql",
                      source="live", data=self)
        tables = self._tables(db)
        db.tables = list(tables.values())
        self._columns(db, tables)
        self._indexes(db, tables)
        self._foreign_keys(db, tables)
        self._checks(db, tables)
        self._partitions(db, tables)
        self._views(db)
        self._routines(db)
        self._security(db)
        self._settings(db)
        self._query_stats(db)
        return db

    def _tables(self, db: Database) -> dict[tuple[str, str], Table]:
        where, params = self._schema_filter("TABLE_SCHEMA")
        rows = self._rows(db, "tables", f"""
            SELECT TABLE_SCHEMA, TABLE_NAME, ENGINE, TABLE_COLLATION, TABLE_ROWS, TABLE_COMMENT, AUTO_INCREMENT
            FROM information_schema.TABLES WHERE TABLE_TYPE = 'BASE TABLE' AND {where}
            ORDER BY TABLE_SCHEMA, TABLE_NAME""", params)
        tables: dict[tuple[str, str], Table] = {}
        counters: dict[str, int] = {}
        for schema, name, engine, collation, row_count, comment, auto_increment in rows or []:
            if auto_increment is not None:
                counters[name] = int(auto_increment)
            tables[(schema, name)] = Table(
                name=name, schema=schema, engine=engine, collation=collation,
                charset=collation.split("_")[0] if collation else None,
                row_count=None if row_count is None else int(row_count), comment=comment or None)
        if counters:
            db.settings["auto_increment"] = counters
        return tables

    def _columns(self, db: Database, tables: dict[tuple[str, str], Table]) -> None:
        where, params = self._schema_filter("TABLE_SCHEMA")
        rows = self._rows(db, "columns", f"""
            SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT, EXTRA, COLUMN_COMMENT,
                   CHARACTER_SET_NAME, COLLATION_NAME, ORDINAL_POSITION
            FROM information_schema.COLUMNS WHERE {where} ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION""", params)
        for schema, name, column, ctype, nullable, default, extra, comment, charset, collation, ordinal in rows or []:
            table = tables.get((schema, name))
            if table is None:
                continue
            extra_text = (extra or "").upper()
            table.columns.append(Column(
                name=column, data_type=ctype, nullable=_flag(nullable), default=default,
                is_identity="AUTO_INCREMENT" in extra_text,
                is_generated="VIRTUAL GENERATED" in extra_text or "STORED GENERATED" in extra_text,
                comment=comment or None, charset=charset, collation=collation, ordinal=int(ordinal or 0)))

    def _indexes(self, db: Database, tables: dict[tuple[str, str], Table]) -> None:
        where, params = self._schema_filter("TABLE_SCHEMA")
        rows = self._rows(db, "indexes", f"""
            SELECT TABLE_SCHEMA, TABLE_NAME, INDEX_NAME, NON_UNIQUE, SEQ_IN_INDEX, COLUMN_NAME, INDEX_TYPE
            FROM information_schema.STATISTICS WHERE {where}
            ORDER BY TABLE_SCHEMA, TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX""", params)
        grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
        for schema, name, index, non_unique, _seq, column, method in rows or []:
            entry = grouped.setdefault((schema, name, index), {"unique": not int(non_unique), "columns": [], "method": method})
            entry["columns"].append(column if column is not None else "<expression>")
        for (schema, name, index), entry in grouped.items():
            table = tables.get((schema, name))
            if table is None:
                continue
            if index == "PRIMARY":
                table.primary_key, table.primary_key_name = entry["columns"], "PRIMARY"
                for column in table.columns:
                    if column.name in entry["columns"]:
                        column.nullable = False
            else:
                table.indexes.append(Index(name=index, columns=entry["columns"], unique=entry["unique"],
                                           method=entry["method"], is_constraint=entry["unique"]))

    def _foreign_keys(self, db: Database, tables: dict[tuple[str, str], Table]) -> None:
        where, params = self._schema_filter("k.CONSTRAINT_SCHEMA")
        rows = self._rows(db, "foreign keys", f"""
            SELECT k.CONSTRAINT_SCHEMA, k.TABLE_NAME, k.CONSTRAINT_NAME, k.COLUMN_NAME, k.REFERENCED_TABLE_SCHEMA,
                   k.REFERENCED_TABLE_NAME, k.REFERENCED_COLUMN_NAME, r.DELETE_RULE, r.UPDATE_RULE
            FROM information_schema.KEY_COLUMN_USAGE k
            JOIN information_schema.REFERENTIAL_CONSTRAINTS r
              ON r.CONSTRAINT_SCHEMA = k.CONSTRAINT_SCHEMA AND r.CONSTRAINT_NAME = k.CONSTRAINT_NAME
             AND r.TABLE_NAME = k.TABLE_NAME
            WHERE k.REFERENCED_TABLE_NAME IS NOT NULL AND {where}
            ORDER BY k.CONSTRAINT_SCHEMA, k.TABLE_NAME, k.CONSTRAINT_NAME, k.ORDINAL_POSITION""", params)
        grouped: dict[tuple[str, str, str], ForeignKey] = {}
        for schema, table, name, column, ref_schema, ref_table, ref_column, on_delete, on_update in rows or []:
            fk = grouped.get((schema, table, name))
            if fk is None:
                fk = ForeignKey(name=name, columns=[], ref_table=ref_table, ref_columns=[], ref_schema=ref_schema,
                                on_delete=on_delete, on_update=on_update)
                grouped[(schema, table, name)] = fk
                if (schema, table) in tables:
                    tables[(schema, table)].foreign_keys.append(fk)
            fk.columns.append(column)
            fk.ref_columns.append(ref_column)

    def _checks(self, db: Database, tables: dict[tuple[str, str], Table]) -> None:
        where, params = self._schema_filter("c.CONSTRAINT_SCHEMA")
        try:  # check constraints exist from MySQL 8.0.16 and MariaDB 10.2; absence is not a problem to report
            rows = self.query(f"""
                SELECT c.CONSTRAINT_SCHEMA, t.TABLE_NAME, c.CONSTRAINT_NAME, c.CHECK_CLAUSE
                FROM information_schema.CHECK_CONSTRAINTS c
                JOIN information_schema.TABLE_CONSTRAINTS t
                  ON t.CONSTRAINT_SCHEMA = c.CONSTRAINT_SCHEMA AND t.CONSTRAINT_NAME = c.CONSTRAINT_NAME
                WHERE t.CONSTRAINT_TYPE = 'CHECK' AND {where}""", params)
        except ConnectorError:
            return
        for schema, table, name, clause in ([tuple(_text(v) for v in r) for r in rows]):
            if (schema, table) in tables:
                tables[(schema, table)].checks.append(CheckConstraint(name=name, expression=clause or ""))

    def _partitions(self, db: Database, tables: dict[tuple[str, str], Table]) -> None:
        where, params = self._schema_filter("TABLE_SCHEMA")
        rows = self._rows(db, "partitions", f"""
            SELECT DISTINCT TABLE_SCHEMA, TABLE_NAME, PARTITION_EXPRESSION FROM information_schema.PARTITIONS
            WHERE PARTITION_NAME IS NOT NULL AND PARTITION_EXPRESSION IS NOT NULL AND {where}""", params)
        for schema, name, expression in rows or []:
            table = tables.get((schema, name))
            if table is not None:
                columns = re.findall(r"`([^`]+)`", expression or "") or re.findall(r"[A-Za-z_]\w*", expression or "")
                table.partition_columns = list(dict.fromkeys(columns))

    def _views(self, db: Database) -> None:
        where, params = self._schema_filter("TABLE_SCHEMA")
        rows = self._rows(db, "views", f"""
            SELECT TABLE_SCHEMA, TABLE_NAME, VIEW_DEFINITION FROM information_schema.VIEWS WHERE {where}
            ORDER BY TABLE_SCHEMA, TABLE_NAME""", params)
        for schema, name, definition in rows or []:
            if not definition:
                db.import_warnings.append(f"view {schema}.{name}: definition not readable (SHOW VIEW privilege missing)")
            db.views.append(View(name=name, schema=schema, definition=definition or "",
                                 references=sql_references(definition or "", "mysql")))

    def _routines(self, db: Database) -> None:
        where, params = self._schema_filter("ROUTINE_SCHEMA")
        rows = self._rows(db, "routines", f"""
            SELECT ROUTINE_SCHEMA, ROUTINE_NAME, ROUTINE_TYPE, ROUTINE_DEFINITION FROM information_schema.ROUTINES
            WHERE {where} ORDER BY ROUTINE_SCHEMA, ROUTINE_NAME""", params)
        for schema, name, kind, definition in rows or []:
            db.routines.append(Routine(name=name, schema=schema, kind=(kind or "procedure").lower(), definition=definition or ""))
        where, params = self._schema_filter("TRIGGER_SCHEMA")
        rows = self._rows(db, "triggers", f"""
            SELECT TRIGGER_SCHEMA, TRIGGER_NAME, EVENT_OBJECT_TABLE, ACTION_TIMING, EVENT_MANIPULATION, ACTION_STATEMENT
            FROM information_schema.TRIGGERS WHERE {where} ORDER BY TRIGGER_SCHEMA, TRIGGER_NAME""", params)
        for schema, name, table, timing, event, statement in rows or []:
            db.routines.append(Routine(name=name, schema=schema, kind="trigger", table=table,
                                       definition=f"{timing} {event} ON {table} {statement or ''}".strip()))

    def _security(self, db: Database) -> None:
        roles = self._rows(db, "accounts", "SELECT User, Host, Super_priv, account_locked, authentication_string <> '' FROM mysql.user")
        for user, host, superuser, locked, has_password in roles or []:
            if user in _SYSTEM_ACCOUNTS:
                continue
            db.roles.append(Role(name=user, host=host, superuser=_flag(superuser), can_login=not _flag(locked),
                                 password_set=bool(int(has_password)) if has_password is not None else None))
        sections = [
            ("global grants", "SELECT GRANTEE, PRIVILEGE_TYPE, IS_GRANTABLE FROM information_schema.USER_PRIVILEGES", ()),
            ("schema grants", "SELECT GRANTEE, PRIVILEGE_TYPE, IS_GRANTABLE, TABLE_SCHEMA FROM information_schema.SCHEMA_PRIVILEGES", ()),
            ("table grants", "SELECT GRANTEE, PRIVILEGE_TYPE, IS_GRANTABLE, TABLE_SCHEMA, TABLE_NAME FROM information_schema.TABLE_PRIVILEGES", ()),
            ("column grants", "SELECT GRANTEE, PRIVILEGE_TYPE, IS_GRANTABLE, TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME FROM information_schema.COLUMN_PRIVILEGES", ()),
        ]
        grants_ok = roles is not None
        for label, sql, params in sections:
            rows = self._rows(db, label, sql, params)
            if rows is None:
                grants_ok = False
                continue
            for row in rows:
                grantee, privilege, grantable = row[0], row[1], _flag(row[2])
                schema = row[3] if len(row) > 3 else None
                if privilege == "USAGE" or (schema and schema.lower() in _SYSTEM):
                    continue
                table: Optional[str] = row[4] if len(row) > 4 else ("*" if schema else None)
                db.grants.append(Grant(grantee=_split_grantee(grantee), privilege=privilege, schema=schema, table=table,
                                       column=row[5] if len(row) > 5 else None, grantable=grantable))
        db.security_metadata = grants_ok

    def _settings(self, db: Database) -> None:
        names = ", ".join(f"'{n}'" for n in _SETTINGS)
        rows = self._rows(db, "settings", f"SHOW VARIABLES WHERE Variable_name IN ({names})")
        db.settings.update({str(k): v for k, v in rows or []})
        if "version" in db.settings:
            db.settings["server_version"] = db.settings["version"]
        if "character_set_server" in db.settings:
            db.settings["encoding"] = db.settings["character_set_server"]

    def _query_stats(self, db: Database) -> None:
        where, params = self._schema_filter("SCHEMA_NAME")
        rows = self._rows(db, "performance_schema statement statistics", f"""
            SELECT DIGEST_TEXT, COUNT_STAR, SUM_TIMER_WAIT / 1000000000, AVG_TIMER_WAIT / 1000000000, SUM_ROWS_SENT
            FROM performance_schema.events_statements_summary_by_digest
            WHERE DIGEST_TEXT IS NOT NULL AND {where} ORDER BY SUM_TIMER_WAIT DESC LIMIT 500""", params)
        db.settings["query_stats_available"] = rows is not None
        for sql, calls, total_ms, mean_ms, returned in rows or []:
            db.query_stats.append(QueryStat(sql=sql, calls=int(calls or 0), total_ms=float(total_ms or 0),
                                            mean_ms=float(mean_ms or 0), rows=None if returned is None else int(returned)))
