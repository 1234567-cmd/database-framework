"""PostgreSQL connector (psycopg). Sessions are read-only at the server as well as through the guard."""
from __future__ import annotations

import re
from typing import Any, Optional, Sequence

from ..model import (CheckConstraint, Column, Database, ForeignKey, Grant, Index, RlsPolicy, Role, Routine, QueryStat,
                     Table, View)
from .base import ConnectionInfo, Connector, ConnectorError, import_driver, sql_references

_USER_NS = "n.nspname NOT IN ('pg_catalog', 'information_schema') AND n.nspname !~ '^pg_'"
_FK_ACTIONS = {"a": "NO ACTION", "r": "RESTRICT", "c": "CASCADE", "n": "SET NULL", "d": "SET DEFAULT"}
_POLICY_CMD = {"*": "ALL", "r": "SELECT", "a": "INSERT", "w": "UPDATE", "d": "DELETE"}
_SETTINGS = ("server_version", "server_encoding", "wal_level", "archive_mode", "archive_command", "ssl",
             "log_statement", "log_min_duration_statement", "max_connections", "shared_buffers", "work_mem",
             "password_encryption", "shared_preload_libraries", "track_counts", "autovacuum", "statement_timeout")
_CHECK_RE = re.compile(r"^CHECK\s*\((.*)\)(?:\s+NOT\s+VALID)?\s*$", re.S | re.I)
_NAMES_RE = re.compile(r'"((?:[^"]|"")+)"|\b([A-Za-z_][A-Za-z_0-9$]*)\b')


def _unquote_ident(text: str) -> str:
    text = text.strip()
    return text[1:-1].replace('""', '"') if len(text) >= 2 and text[0] == text[-1] == '"' else text


class PostgresConnector(Connector):
    dialect = "postgres"
    paramstyle = "format"

    def __init__(self, info: ConnectionInfo):
        super().__init__(info)
        psycopg = import_driver("psycopg", "postgres")
        kwargs: dict[str, Any] = {k: v for k, v in info.options.items()}
        for key, value in (("host", info.host), ("port", info.port), ("user", info.user),
                           ("password", info.password), ("dbname", info.database or None)):
            if value is not None:
                kwargs[key] = value
        extra = kwargs.pop("options", "")
        kwargs["options"] = f"-c default_transaction_read_only=on {extra}".strip()
        kwargs.setdefault("connect_timeout", 15)
        try:
            self._conn = psycopg.connect(**kwargs)
            self._conn.read_only = True
        except Exception as exc:
            raise ConnectorError(f"could not connect to PostgreSQL: {self._clean(exc)}") from None
        self._require_read_only()

    def _require_read_only(self) -> None:
        """Verify, on the server, that writes are refused before anything else may run."""
        try:
            with self._conn.cursor() as cur:
                cur.execute("SET default_transaction_read_only = on")
                cur.execute("SHOW transaction_read_only")
                row = cur.fetchone()
            self._conn.rollback()
        except Exception as exc:
            self.close()
            raise ConnectorError(f"could not enforce a read-only session: {self._clean(exc)}") from None
        if not row or row[0] != "on":
            self.close()
            raise ConnectorError("the server did not accept a read-only session; refusing to continue")

    def _execute(self, sql: str, params: Sequence[Any]) -> list[tuple]:
        try:
            with self._conn.cursor() as cur:
                cur.execute(sql, params or None)
                rows = cur.fetchall() if cur.description else []
            return [tuple(r) for r in rows]
        finally:
            self._conn.rollback()  # never stay idle in a transaction, and clear aborted ones

    def close(self) -> None:
        conn, self._conn = getattr(self, "_conn", None), None
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass

    # ----------------------------------------------------------------------------------------------------------------

    def extract(self) -> Database:
        db = Database(name=self.info.database if self.info and self.info.database else "postgres", dialect="postgres",
                      source="live", data=self)
        version = self._server_version(db)
        tables = self._tables(db)
        db.tables = list(tables.values())
        attrs = self._columns(db, tables, version)
        self._constraints(db, tables, attrs)
        self._indexes(db, tables, version)
        self._partitions(db, tables, version)
        self._views(db)
        self._routines(db, version)
        self._triggers(db)
        self._security(db)
        self._policies(db)
        self._settings(db)
        self._query_stats(db, version)
        self._sequences(db, version)
        return db

    def _server_version(self, db: Database) -> int:
        rows = self._section(db, "server version", "SHOW server_version_num")
        try:
            return int(rows[0][0]) if rows else 0
        except (TypeError, ValueError):
            return 0

    def _tables(self, db: Database) -> dict[int, Table]:
        rows = self._section(db, "tables", f"""
            SELECT c.oid, n.nspname, c.relname, c.reltuples, c.relrowsecurity, obj_description(c.oid, 'pg_class'),
                   CASE WHEN c.relkind = 'p' THEN (SELECT sum(GREATEST(k.reltuples, 0)) FROM pg_inherits i
                        JOIN pg_class k ON k.oid = i.inhrelid WHERE i.inhparent = c.oid) END
            FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relkind IN ('r', 'p') AND NOT c.relispartition AND {_USER_NS}
            ORDER BY n.nspname, c.relname""")
        tables: dict[int, Table] = {}
        for oid, schema, name, tuples, rls, comment, partition_rows in rows or []:
            estimate = partition_rows if partition_rows is not None else tuples
            row_count = int(estimate) if estimate is not None and estimate >= 0 else None
            tables[oid] = Table(name=name, schema=schema, comment=comment, row_count=row_count, rls_enabled=bool(rls))
        return tables

    def _columns(self, db: Database, tables: dict[int, Table], version: int) -> dict[int, dict[int, str]]:
        identity = "a.attidentity" if version >= 100000 else "''"
        generated = "a.attgenerated" if version >= 120000 else "''"
        rows = self._section(db, "columns", f"""
            SELECT a.attrelid, a.attnum, a.attname, format_type(a.atttypid, a.atttypmod), a.attnotnull,
                   pg_get_expr(d.adbin, d.adrelid), {identity}, {generated}, col_description(a.attrelid, a.attnum),
                   CASE WHEN a.attcollation <> t.typcollation THEN co.collname END
            FROM pg_attribute a
            JOIN pg_class c ON c.oid = a.attrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            JOIN pg_type t ON t.oid = a.atttypid
            LEFT JOIN pg_attrdef d ON d.adrelid = a.attrelid AND d.adnum = a.attnum
            LEFT JOIN pg_collation co ON co.oid = a.attcollation
            WHERE a.attnum > 0 AND NOT a.attisdropped AND c.relkind IN ('r', 'p') AND {_USER_NS}
            ORDER BY a.attrelid, a.attnum""")
        attrs: dict[int, dict[int, str]] = {}
        for oid, num, name, dtype, notnull, default, ident, gen, comment, collation in rows or []:
            attrs.setdefault(oid, {})[num] = name
            table = tables.get(oid)
            if table is None:
                continue
            is_generated = bool(gen)
            is_serial = bool(default) and str(default).lower().startswith("nextval(")
            table.columns.append(Column(
                name=name, data_type=dtype, nullable=not notnull, default=None if is_generated else default,
                is_identity=bool(ident) or is_serial, is_generated=is_generated, comment=comment,
                collation=collation, ordinal=num))
        return attrs

    def _constraints(self, db: Database, tables: dict[int, Table], attrs: dict[int, dict[int, str]]) -> None:
        rows = self._section(db, "constraints", f"""
            SELECT c.conrelid, c.conname, c.contype, c.conkey, c.confrelid, c.confkey, c.confdeltype, c.confupdtype,
                   pg_get_constraintdef(c.oid), fn.nspname, fc.relname
            FROM pg_constraint c
            JOIN pg_class r ON r.oid = c.conrelid
            JOIN pg_namespace n ON n.oid = r.relnamespace
            LEFT JOIN pg_class fc ON fc.oid = c.confrelid
            LEFT JOIN pg_namespace fn ON fn.oid = fc.relnamespace
            WHERE c.contype IN ('p', 'f', 'c') AND {_USER_NS}
            ORDER BY c.conrelid, c.conname""")
        for oid, name, kind, key, ref_oid, ref_key, on_delete, on_update, definition, ref_schema, ref_table in rows or []:
            table = tables.get(oid)
            if table is None:
                continue
            names = [attrs.get(oid, {}).get(n, str(n)) for n in (key or [])]
            if kind == "p":
                table.primary_key, table.primary_key_name = names, name
            elif kind == "f":
                table.foreign_keys.append(ForeignKey(
                    name=name, columns=names, ref_table=ref_table, ref_schema=ref_schema,
                    ref_columns=[attrs.get(ref_oid, {}).get(n, str(n)) for n in (ref_key or [])],
                    on_delete=_FK_ACTIONS.get(on_delete), on_update=_FK_ACTIONS.get(on_update)))
            else:
                match = _CHECK_RE.match(definition or "")
                table.checks.append(CheckConstraint(name=name, expression=match.group(1) if match else (definition or ""),
                                                    columns=names))

    def _indexes(self, db: Database, tables: dict[int, Table], version: int) -> None:
        key_count = "i.indnkeyatts" if version >= 110000 else "i.indnatts"
        rows = self._section(db, "indexes", f"""
            SELECT i.indrelid, x.relname, i.indisunique, i.indisprimary, am.amname, pg_get_expr(i.indpred, i.indrelid),
                   {key_count}, ARRAY(SELECT pg_get_indexdef(i.indexrelid, k, true)
                                      FROM generate_series(1, i.indnatts) k ORDER BY k),
                   EXISTS (SELECT 1 FROM pg_constraint con WHERE con.conindid = i.indexrelid AND con.contype IN ('u', 'x'))
            FROM pg_index i
            JOIN pg_class x ON x.oid = i.indexrelid
            JOIN pg_class t ON t.oid = i.indrelid
            JOIN pg_namespace n ON n.oid = t.relnamespace
            JOIN pg_am am ON am.oid = x.relam
            WHERE i.indisvalid AND {_USER_NS}
            ORDER BY i.indrelid, x.relname""")
        for oid, name, unique, primary, method, where, keys, columns, is_constraint in rows or []:
            table = tables.get(oid)
            if table is None or primary:  # the primary key is held in Table.primary_key
                continue
            all_columns = [_unquote_ident(c) for c in columns or []]
            table.indexes.append(Index(name=name, columns=all_columns[:keys], unique=bool(unique), method=method,
                                       where=where, include=all_columns[keys:], is_constraint=bool(is_constraint)))

    def _partitions(self, db: Database, tables: dict[int, Table], version: int) -> None:
        if version and version < 100000:
            return
        rows = self._section(db, "partition keys", f"""
            SELECT c.oid, pg_get_partkeydef(c.oid) FROM pg_partitioned_table p
            JOIN pg_class c ON c.oid = p.partrelid JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE {_USER_NS}""")
        for oid, definition in rows or []:
            table = tables.get(oid)
            match = re.search(r"\((.*)\)", definition or "", re.S)
            if table is not None and match:
                table.partition_columns = [_unquote_ident(p) for p in match.group(1).split(",")]

    def _views(self, db: Database) -> None:
        rows = self._section(db, "views", f"""
            SELECT n.nspname, c.relname, c.relkind, pg_get_viewdef(c.oid, true)
            FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relkind IN ('v', 'm') AND {_USER_NS} ORDER BY n.nspname, c.relname""")
        for schema, name, kind, definition in rows or []:
            text = (definition or "").strip().rstrip(";")
            db.views.append(View(name=name, schema=schema, definition=text, materialized=kind == "m",
                                 references=sql_references(text, "postgres")))

    def _routines(self, db: Database, version: int) -> None:
        kind = "p.prokind" if version >= 110000 else "CASE WHEN p.proisagg THEN 'a' WHEN p.proiswindow THEN 'w' ELSE 'f' END"
        rows = self._section(db, "routines", f"""
            SELECT n.nspname, p.proname, {kind}, pg_get_functiondef(p.oid)
            FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
            WHERE {kind} IN ('f', 'p') AND {_USER_NS}
              AND NOT EXISTS (SELECT 1 FROM pg_depend d WHERE d.objid = p.oid AND d.deptype = 'e')
            ORDER BY n.nspname, p.proname""")
        for schema, name, routine_kind, definition in rows or []:
            db.routines.append(Routine(name=name, schema=schema, definition=definition or "",
                                       kind="procedure" if routine_kind == "p" else "function"))

    def _triggers(self, db: Database) -> None:
        rows = self._section(db, "triggers", f"""
            SELECT n.nspname, c.relname, t.tgname, pg_get_triggerdef(t.oid, true)
            FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE NOT t.tgisinternal AND {_USER_NS} ORDER BY n.nspname, c.relname, t.tgname""")
        for schema, table, name, definition in rows or []:
            db.routines.append(Routine(name=name, kind="trigger", table=table, schema=schema, definition=definition or ""))

    def _security(self, db: Database) -> None:
        roles = self._section(db, "roles", """
            SELECT rolname, rolsuper, rolcanlogin, rolbypassrls FROM pg_roles WHERE rolname !~ '^pg_' ORDER BY rolname""")
        for name, superuser, login, bypass in roles or []:
            db.roles.append(Role(name=name, superuser=bool(superuser), can_login=bool(login), bypass_rls=bool(bypass)))
        try:  # pg_authid needs superuser; password_set simply stays unknown otherwise
            passwords = dict(self.query("SELECT rolname, rolpassword IS NOT NULL FROM pg_authid"))
            for role in db.roles:
                role.password_set = bool(passwords.get(role.name))
        except ConnectorError:
            pass
        grantee = "CASE WHEN acl.grantee = 0 THEN 'PUBLIC' ELSE pg_get_userbyid(acl.grantee) END"
        table_grants = self._section(db, "table grants", f"""
            SELECT {grantee}, acl.privilege_type, n.nspname, c.relname, acl.is_grantable
            FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
            CROSS JOIN LATERAL aclexplode(COALESCE(c.relacl, acldefault('r', c.relowner))) acl
            WHERE c.relkind IN ('r', 'p', 'v', 'm') AND acl.grantee <> c.relowner AND {_USER_NS}""")
        column_grants = self._section(db, "column grants", f"""
            SELECT {grantee}, acl.privilege_type, n.nspname, c.relname, a.attname, acl.is_grantable
            FROM pg_attribute a JOIN pg_class c ON c.oid = a.attrelid JOIN pg_namespace n ON n.oid = c.relnamespace
            CROSS JOIN LATERAL aclexplode(a.attacl) acl
            WHERE a.attacl IS NOT NULL AND a.attnum > 0 AND NOT a.attisdropped AND {_USER_NS}""")
        schema_grants = self._section(db, "schema grants", f"""
            SELECT {grantee}, acl.privilege_type, n.nspname, acl.is_grantable
            FROM pg_namespace n CROSS JOIN LATERAL aclexplode(COALESCE(n.nspacl, acldefault('n', n.nspowner))) acl
            WHERE acl.grantee <> n.nspowner AND {_USER_NS}""")
        for g, privilege, schema, table, grantable in table_grants or []:
            db.grants.append(Grant(grantee=g, privilege=privilege, schema=schema, table=table, grantable=bool(grantable)))
        for g, privilege, schema, table, column, grantable in column_grants or []:
            db.grants.append(Grant(grantee=g, privilege=privilege, schema=schema, table=table, column=column,
                                   grantable=bool(grantable)))
        for g, privilege, schema, grantable in schema_grants or []:
            db.grants.append(Grant(grantee=g, privilege=privilege, schema=schema, grantable=bool(grantable)))
        db.security_metadata = roles is not None and table_grants is not None

    def _policies(self, db: Database) -> None:
        rows = self._section(db, "row level security policies", """
            SELECT schemaname, tablename, policyname, cmd, roles, qual, with_check FROM pg_policies
            ORDER BY schemaname, tablename, policyname""")
        for schema, table, name, command, roles, qual, with_check in rows or []:
            db.policies.append(RlsPolicy(table=table, name=name, schema=schema, command=(command or "ALL").upper(),
                                         expression=qual or with_check or "", roles=list(roles or [])))

    def _settings(self, db: Database) -> None:
        rows = self._section(db, "settings", "SELECT name, setting FROM pg_settings WHERE name = ANY(%s)", (list(_SETTINGS),))
        db.settings.update(dict(rows or []))
        if "server_encoding" in db.settings:
            db.settings["encoding"] = db.settings["server_encoding"]
        version_rows = self._section(db, "database encoding", "SELECT current_database(), pg_encoding_to_char(encoding), datcollate "
                                                              "FROM pg_database WHERE datname = current_database()")
        if version_rows:
            db.name, db.settings["encoding"], db.settings["collation"] = version_rows[0]

    def _sequences(self, db: Database, version: int) -> None:
        """Last value of each table's owned sequence. pg_sequences hides it (NULL) from roles that may not read it."""
        if version and version < 100000:
            return
        rows = self._section(db, "sequence positions", f"""
            SELECT c.relname, s.last_value
            FROM pg_depend d
            JOIN pg_class q ON q.oid = d.objid AND q.relkind = 'S'
            JOIN pg_namespace sn ON sn.oid = q.relnamespace
            JOIN pg_sequences s ON s.schemaname = sn.nspname AND s.sequencename = q.relname
            JOIN pg_class c ON c.oid = d.refobjid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE d.classid = 'pg_class'::regclass AND d.refclassid = 'pg_class'::regclass AND d.deptype IN ('a', 'i')
              AND s.last_value IS NOT NULL AND {_USER_NS}""")
        counters: dict[str, int] = {}
        for table, last_value in rows or []:
            counters[table] = max(int(last_value), counters.get(table, 0))
        if counters:
            db.settings["auto_increment"] = counters

    def _query_stats(self, db: Database, version: int) -> None:
        rows = self._section(db, "pg_stat_statements lookup", """
            SELECT n.nspname FROM pg_extension e JOIN pg_namespace n ON n.oid = e.extnamespace
            WHERE e.extname = 'pg_stat_statements'""")
        db.settings["query_stats_available"] = False
        if not rows:
            return
        schema = self.quote(rows[0][0])
        total, mean = ("total_exec_time", "mean_exec_time") if version >= 130000 else ("total_time", "mean_time")
        stats = self._section(db, "pg_stat_statements", f"""
            SELECT query, calls, {total}, {mean}, rows FROM {schema}.pg_stat_statements
            WHERE query IS NOT NULL ORDER BY {total} DESC LIMIT 500""")
        if stats is None:
            return
        db.settings["query_stats_available"] = True
        for sql, calls, total_ms, mean_ms, returned in stats:
            db.query_stats.append(QueryStat(sql=sql, calls=int(calls or 0), total_ms=float(total_ms or 0),
                                            mean_ms=float(mean_ms or 0), rows=None if returned is None else int(returned)))
