"""Turn finding fixes into a reviewed, ordered migration proposal. Nothing here touches a database except read-only
precheck queries through ``db.data``."""
from __future__ import annotations

import copy
import hashlib
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Optional, Sequence

from ..findings import Finding
from ..model import Database, Index, Table, parse_type
from ._sql import (IdentifierError, apply_fix_effect, columns_sql, is_sqlite_constant_default, literal, make_name,
                   names, normalize_dialect, qualified, quote, render_default, render_expression,
                   render_sqlite_create, render_sqlite_indexes, type_change_kind, validate_identifier, validate_type)
from .safety import DESTRUCTIVE, backup_recommendation, detect_destructive, financial_patterns_from, is_financial_table

LOCK_TIMEOUT = "5s"  # MIG-008 sets no framework-wide value; this is a starting point to tune from rehearsal.
LOCK_WAIT_SECONDS = 5
PHASE = {"add_column": 10, "alter_column_type": 15, "set_not_null": 20, "add_primary_key": 25,
         "add_surrogate_primary_key": 25, "add_index_unique": 30, "add_index": 35, "rebuild": 38, "add_foreign_key": 40,
         "add_check": 45, "drop_index": 50, "enable_rls": 55, "revoke_grant": 60, "rename_column": 70, "rename_table": 80,
         "manual": 90}
_SQLITE_REBUILD = {"set_not_null", "add_primary_key", "add_surrogate_primary_key", "add_foreign_key", "add_check",
                   "alter_column_type"}
_PRIVILEGES = {"SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER", "ALL", "ALL PRIVILEGES",
               "USAGE", "CREATE", "DROP", "ALTER", "INDEX", "EXECUTE"}
_ACTIONS = {"CASCADE", "RESTRICT", "NO ACTION", "SET NULL", "SET DEFAULT"}


@dataclass
class Check:
    """A read-only query returning one scalar, with the expected value."""
    description: str
    sql: str
    expected: int = 0
    kind: str = "schema"  # schema | data; a data check can fail on existing rows
    status: str = "not_run"  # not_run | passed | failed | error
    observed: Optional[int] = None

    @property
    def can_fail(self) -> bool:
        return self.kind == "data"


@dataclass
class MigrationStep:
    id: str
    finding_ids: list[str]
    title: str
    up_sql: list[str] = field(default_factory=list)
    down_sql: list[str] = field(default_factory=list)
    destructive: bool = False
    reversible: bool = True
    data_loss_risk: str = "none"
    lock_risk: str = "low"
    prechecks: list[Check] = field(default_factory=list)
    postchecks: list[Check] = field(default_factory=list)
    requires_backup: bool = False
    online_notes: list[str] = field(default_factory=list)
    order: int = 0
    op: str = ""
    table: Optional[str] = None
    column: Optional[str] = None
    manual: bool = False
    manual_description: str = ""
    refused_reason: str = ""
    requires_data_repair: bool = False
    data_repair_notes: list[str] = field(default_factory=list)
    irreversible_reason: str = ""
    breaking: bool = False
    dependency_risks: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    transactional: bool = True
    phase_label: str = ""
    destructive_hits: list[dict] = field(default_factory=list)

    @property
    def up_script(self) -> str:
        return ";\n".join(self.up_sql) + (";" if self.up_sql else "")

    @property
    def down_script(self) -> str:
        return ";\n".join(self.down_sql) + (";" if self.down_sql else "")


@dataclass
class MigrationPlan:
    database: str
    source_dialect: str
    dialect: str
    steps: list[MigrationStep] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    unaddressed_findings: list[str] = field(default_factory=list)
    satisfied_findings: list[str] = field(default_factory=list)
    backup_recommendation: str = ""

    @property
    def manual_steps(self) -> list[MigrationStep]:
        return [s for s in self.steps if s.manual]

    @property
    def executable_steps(self) -> list[MigrationStep]:
        return [s for s in self.steps if not s.manual]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class _Op:
    kind: str
    table: Optional[Table]
    table_ref: Optional[str]
    column: Optional[str]
    params: dict[str, Any]
    finding_ids: list[str]
    subops: list["_Op"] = field(default_factory=list)

    @property
    def phase_key(self) -> str:
        return "add_index_unique" if self.kind == "add_index" and self.params.get("unique") else self.kind


@dataclass
class _Draft:
    op: str
    title: str
    table: Optional[Table]
    column: Optional[str]
    finding_ids: list[str]
    up: list[str] = field(default_factory=list)
    down: list[str] = field(default_factory=list)
    reversible: bool = True
    irreversible_reason: str = ""
    data_loss_risk: str = "none"
    lock_risk: str = "low"
    pre: list[Check] = field(default_factory=list)
    post: list[Check] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    transactional: bool = True
    breaking: bool = False
    dependency_risks: list[str] = field(default_factory=list)
    manual: bool = False
    manual_description: str = ""
    refused_reason: str = ""
    repair_notes: list[str] = field(default_factory=list)
    effects: list[tuple] = field(default_factory=list)
    creates: set = field(default_factory=set)
    needs: set = field(default_factory=set)
    needs_any: list[set] = field(default_factory=list)
    phase_label: str = ""
    destructive: bool = False
    hits: list[dict] = field(default_factory=list)


class _Manual(Exception):
    """Raised while drafting an operation that cannot be generated safely."""


def _tok(prefix: str, table: Table, *rest: str) -> str:
    return (prefix + ":" + table.fqname + ":" + ":".join(rest)).lower()


class _Planner:
    def __init__(self, db: Database, dialect: str, patterns: Sequence[str], profile: Any, evaluate: bool):
        self.db = db
        self.dialect = dialect
        self.patterns = patterns
        self.profile = profile
        self.evaluate = evaluate
        self.state: dict[str, Table] = {t.fqname.lower(): copy.deepcopy(t) for t in db.tables}
        self.notes: list[str] = []
        self.unaddressed: list[str] = []
        self.satisfied: list[str] = []
        self.drafts: list[_Draft] = []
        self.creators: dict[str, _Draft] = {}
        self.planned: set[str] = set()

    # --- resolving -----------------------------------------------------------

    def _find(self, ref: Optional[str]) -> Optional[Table]:
        if not ref:
            return None
        low = ref.lower()
        for t in self.db.tables:
            if t.fqname.lower() == low:
                return self.state[t.fqname.lower()]
        schema, _, name = ref.rpartition(".")
        found = self.db.table(name, schema or None)
        return self.state.get(found.fqname.lower()) if found else None

    def _collect(self, findings: Sequence[Finding]) -> list[_Op]:
        ops: list[_Op] = []
        for f in findings:
            if f.fix is None:
                self.unaddressed.append(f.id)
                continue
            params = dict(f.fix.params or {})
            table_ref = f.fix.table or f.table
            column = f.fix.column or f.column
            if f.fix.op == "manual":
                ops.append(_Op("manual", self._find(table_ref), table_ref, column, params, [f.id]))
                continue
            table = self._find(table_ref)
            if f.fix.op not in PHASE and f.fix.op != "add_index":
                self._manual_early(f.fix.op, table, table_ref, column, [f.id], f"Fix operation {f.fix.op!r} is not supported by the generator.")
                continue
            if table is None and f.fix.op != "revoke_grant":
                self._manual_early(f.fix.op, None, table_ref, column, [f.id], f"Table {table_ref!r} was not found in the assessed model.")
                continue
            ops.append(_Op(f.fix.op, table, table_ref, column, params, [f.id]))
        return ops

    def _manual_early(self, op: str, table: Optional[Table], table_ref: Optional[str], column: Optional[str], ids: list[str],
                      reason: str, title: str = "") -> None:
        d = _Draft(op=op, title=title or f"Manual review: {op} on {table_ref or 'database'}", table=table, column=column,
                   finding_ids=list(ids), manual=True, manual_description=reason)
        self._finish_manual(d)

    def _finish_manual(self, d: _Draft) -> None:
        d.reversible = False
        d.irreversible_reason = d.irreversible_reason or "Manual step: no SQL is generated, so no rollback exists."
        d.up, d.down = [], []
        self.drafts.append(d)

    def _columns(self, op: _Op) -> list[str]:
        return names(op.params.get("columns")) or ([op.column] if op.column else [])

    def _key(self, op: _Op) -> tuple:
        t = op.table_ref or ""
        low = lambda items: tuple(i.lower() for i in items)  # noqa: E731
        if op.kind in ("add_index", "add_primary_key", "add_foreign_key"):
            extra = (str(op.params.get("ref_table", "")).lower(), low(names(op.params.get("ref_columns")))) if op.kind == "add_foreign_key" else ()
            return (op.kind, t.lower(), low(self._columns(op))) + extra
        if op.kind == "drop_index":
            return (op.kind, t.lower(), str(op.params.get("name", "")).lower())
        if op.kind == "add_check":
            return (op.kind, t.lower(), re.sub(r"\s+", "", str(op.params.get("expression", ""))).lower())
        if op.kind == "revoke_grant":
            return (op.kind, t.lower(), str(op.params.get("grantee")).lower(), str(op.params.get("privilege")).upper())
        if op.kind == "enable_rls":
            return (op.kind, t.lower())
        if op.kind == "manual":
            return (op.kind, op.finding_ids[0])
        distinguishing = re.sub(r"\s+", " ", str(op.params.get("new_type") or op.params.get("new_name") or op.params.get("type") or "")).strip().lower()
        return (op.kind, t.lower(), (op.column or "").lower(), distinguishing)

    def _merge(self, ops: list[_Op]) -> list[_Op]:
        merged: dict[tuple, _Op] = {}
        for op in ops:
            key = self._key(op)
            if key in merged:
                base = merged[key]
                base.finding_ids.extend(x for x in op.finding_ids if x not in base.finding_ids)
                if op.params.get("unique"):
                    base.params["unique"] = True
            else:
                merged[key] = op
        return list(merged.values())

    def _resolve(self, ops: list[_Op]) -> list[_Op]:
        ops = self._merge(ops)
        by_table: dict[str, list[_Op]] = {}
        for op in ops:
            by_table.setdefault((op.table_ref or "").lower(), []).append(op)
        result: list[_Op] = []
        for group in by_table.values():
            result.extend(self._resolve_table(group))
        return result

    def _to_conflict(self, ops: list[_Op], reason: str) -> None:
        first = ops[0]
        ids = [i for op in ops for i in op.finding_ids]
        self._manual_early(first.kind, first.table, first.table_ref, first.column, ids, reason,
                           f"Decision needed: conflicting proposals for {first.table_ref}{'.' + first.column if first.column else ''}")

    def _resolve_table(self, group: list[_Op]) -> list[_Op]:
        drop: set[int] = set()
        by = lambda kind: [o for o in group if o.kind == kind and id(o) not in drop]  # noqa: E731

        def conflict(items: list[_Op], reason: str) -> None:
            self._to_conflict(items, reason)
            drop.update(id(o) for o in items)

        def noop(op: _Op, note: str) -> None:
            self.satisfied.extend(op.finding_ids)
            self.notes.append(note)
            drop.add(id(op))

        # add_column
        seen_cols: dict[str, _Op] = {}
        for op in by("add_column"):
            name = (op.column or "").lower()
            if op.table is not None and op.table.has_column(name):
                conflict([op], f"Column {op.table_ref}.{op.column} already exists; adding it would fail.")
            elif name in seen_cols:
                other = seen_cols[name]
                if str(other.params.get("type")).lower() != str(op.params.get("type")).lower():
                    conflict([other, op], f"Two proposals add {op.table_ref}.{op.column} with different types.")
                    del seen_cols[name]
            else:
                seen_cols[name] = op
        # primary keys
        keys = by("add_primary_key") + by("add_surrogate_primary_key")
        table = group[0].table
        if keys and table is not None and table.primary_key:
            conflict(keys, f"Table {table.fqname} already has a primary key; replacing one needs a separate review.")
        elif len(keys) > 1:
            conflict(keys, f"Several incompatible primary key proposals exist for {group[0].table_ref}.")
        keys = by("add_primary_key") + by("add_surrogate_primary_key")
        # set_not_null
        for op in by("set_not_null"):
            col = (op.column or "").lower()
            handled = False
            for key in keys:
                if key.kind == "add_primary_key" and col in {c.lower() for c in self._columns(key)}:
                    key.finding_ids.extend(op.finding_ids)
                    drop.add(id(op))
                    self.notes.append(f"NOT NULL on {op.table_ref}.{op.column} is covered by the primary key step.")
                    handled = True
            if not handled and col in seen_cols:
                seen_cols[col].params["nullable"] = False
                seen_cols[col].finding_ids.extend(op.finding_ids)
                drop.add(id(op))
                handled = True
            if not handled and op.table is not None:
                current = op.table.column(op.column or "")
                if current is not None and not current.nullable:
                    noop(op, f"{op.table_ref}.{op.column} is already NOT NULL.")
        # type changes
        types: dict[str, list[_Op]] = {}
        for op in by("alter_column_type"):
            types.setdefault((op.column or "").lower(), []).append(op)
        for col, items in types.items():
            distinct = {re.sub(r"\s+", " ", str(o.params.get("new_type", "")).strip().lower()) for o in items}
            if len(distinct) > 1:
                conflict(items, f"Conflicting target types for {items[0].table_ref}.{items[0].column}: {sorted(distinct)}.")
            elif len(items) > 1:
                items[0].finding_ids.extend(i for o in items[1:] for i in o.finding_ids)
                drop.update(id(o) for o in items[1:])
        # renames
        renames: dict[str, list[_Op]] = {}
        for op in by("rename_column"):
            renames.setdefault((op.column or "").lower(), []).append(op)
        for items in renames.values():
            targets = {str(o.params.get("new_name")).lower() for o in items}
            if len(targets) > 1:
                conflict(items, f"Conflicting new names for {items[0].table_ref}.{items[0].column}: {sorted(targets)}.")
            elif len(items) > 1:
                items[0].finding_ids.extend(i for o in items[1:] for i in o.finding_ids)
                drop.update(id(o) for o in items[1:])
        for op in by("rename_column"):
            new = str(op.params.get("new_name", "")).lower()
            if (op.table is not None and op.table.has_column(new)) or new in seen_cols:
                conflict([op], f"Cannot rename {op.table_ref}.{op.column} to an existing column {new!r}.")
        table_renames = by("rename_table")
        if len({str(o.params.get("new_name")).lower() for o in table_renames}) > 1:
            conflict(table_renames, f"Conflicting new names for table {table_renames[0].table_ref}.")
        # indexes
        drops = {str(o.params.get("name", "")).lower() for o in by("drop_index")}
        for op in by("add_index"):
            name = str(op.params.get("name", "")).lower()
            if name and name in drops:
                conflict([o for o in group if o.kind in ("add_index", "drop_index") and str(o.params.get("name", "")).lower() == name],
                         f"Both creating and dropping index {name} is contradictory.")
                continue
            cols = [c.lower() for c in self._columns(op)]
            if op.table is not None:
                pk = [c.lower() for c in op.table.primary_key]
                existing = [[c.lower() for c in i.columns] for i in op.table.indexes if i.unique >= bool(op.params.get("unique"))]
                if pk == cols or cols in existing:
                    noop(op, f"An equivalent index already exists on {op.table_ref} ({', '.join(cols)}).")
        return [o for o in group if id(o) not in drop]

    # --- ordering ------------------------------------------------------------

    def _with_rebuilds(self, ops: list[_Op]) -> list[_Op]:
        if self.dialect != "sqlite":
            return ops
        out: list[_Op] = []
        groups: dict[str, _Op] = {}
        for op in ops:
            default_needs = op.kind == "add_column" and not is_sqlite_constant_default(op.params.get("default"))
            if op.kind in _SQLITE_REBUILD or default_needs:
                key = (op.table_ref or "").lower()
                if key not in groups:
                    groups[key] = _Op("rebuild", op.table, op.table_ref, None, {}, [], subops=[])
                    out.append(groups[key])
                groups[key].subops.append(op)
                groups[key].finding_ids.extend(op.finding_ids)
            else:
                out.append(op)
        return out

    def _plan_tokens(self, ops: list[_Op]) -> None:
        for op in ops:
            for sub in (op.subops or [op]):
                table = sub.table
                if table is None:
                    continue
                cols = [c.lower() for c in self._columns(sub)]
                if sub.kind == "add_column":
                    self.planned.add(_tok("col", table, (sub.column or "").lower()))
                elif sub.kind in ("add_primary_key", "add_surrogate_primary_key"):
                    self.planned.add(_tok("pk", table))
                    self.planned.add(_tok("uq", table, *cols))
                elif sub.kind == "add_index" and sub.params.get("unique"):
                    self.planned.add(_tok("uq", table, *cols))

    # --- check builders ------------------------------------------------------

    @property
    def d(self) -> str:
        return self.dialect

    def _t(self, table: Table) -> str:
        return qualified(table, self.d)

    def _q(self, name: str) -> str:
        return quote(name, self.d)

    def _lit(self, value: str) -> str:
        return literal(value, self.d)

    def _schema_filter(self, table: Table, column: str = "table_schema") -> str:
        if table.schema:
            return f" AND {column} = {self._lit(table.schema)}"
        return f" AND {column} = current_schema()" if self.d == "postgres" else f" AND {column} = DATABASE()"

    def _lock(self) -> list[str]:
        if self.d == "postgres":
            return [f"SET lock_timeout = '{LOCK_TIMEOUT}'"]
        if self.d == "mysql":
            return [f"SET SESSION lock_wait_timeout = {LOCK_WAIT_SECONDS}"]
        return []

    def _table_exists(self, table: Table) -> Check:
        if self.d == "sqlite":
            sql = f"SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name = {self._lit(table.name)}"
        else:
            sql = f"SELECT COUNT(*) FROM information_schema.tables WHERE table_name = {self._lit(table.name)}{self._schema_filter(table)}"
        return Check(f"Table {table.fqname} exists", sql, 1)

    def _col_exists(self, table: Table, col: str, expected: int = 1, name: Optional[str] = None) -> Check:
        if self.d == "sqlite":
            sql = f"SELECT COUNT(*) FROM pragma_table_info({self._lit(name or table.name)}) WHERE name = {self._lit(col)}"
        else:
            sql = (f"SELECT COUNT(*) FROM information_schema.columns WHERE table_name = {self._lit(name or table.name)}"
                   f"{self._schema_filter(table)} AND column_name = {self._lit(col)}")
        return Check(f"Column {table.name}.{col} {'exists' if expected else 'does not exist'}", sql, expected)

    def _col_not_null(self, table: Table, col: str) -> Check:
        if self.d == "sqlite":
            sql = f'SELECT COUNT(*) FROM pragma_table_info({self._lit(table.name)}) WHERE name = {self._lit(col)} AND "notnull" = 1'
        else:
            sql = (f"SELECT COUNT(*) FROM information_schema.columns WHERE table_name = {self._lit(table.name)}"
                   f"{self._schema_filter(table)} AND column_name = {self._lit(col)} AND is_nullable = 'NO'")
        return Check(f"{table.name}.{col} is NOT NULL", sql, 1)

    def _col_type(self, table: Table, col: str, new_type: str) -> Check:
        family = re.match(r"[A-Za-z_ ]+", new_type).group(0).strip().lower()
        if self.d == "sqlite":
            sql = f"SELECT COUNT(*) FROM pragma_table_info({self._lit(table.name)}) WHERE name = {self._lit(col)} AND LOWER(type) LIKE {self._lit(family + '%')}"
        else:
            base = family.replace("character varying", "varchar") if self.d == "mysql" else family
            field_name = "column_type" if self.d == "mysql" else "udt_name"
            alias = {"bigint": "int8", "integer": "int4", "int": "int4", "smallint": "int2", "numeric": "numeric",
                     "decimal": "numeric", "varchar": "varchar", "character varying": "varchar", "text": "text",
                     "boolean": "bool", "timestamp with time zone": "timestamptz", "timestamptz": "timestamptz",
                     "double precision": "float8", "real": "float4", "timestamp without time zone": "timestamp"}.get(base, base) if self.d == "postgres" else base
            sql = (f"SELECT COUNT(*) FROM information_schema.columns WHERE table_name = {self._lit(table.name)}"
                   f"{self._schema_filter(table)} AND column_name = {self._lit(col)} AND LOWER({field_name}) LIKE {self._lit(alias + '%')}")
        return Check(f"{table.name}.{col} has type {new_type}", sql, 1)

    def _index_exists(self, table: Table, name: str, expected: int = 1) -> Check:
        if self.d == "sqlite":
            sql = f"SELECT COUNT(*) FROM sqlite_master WHERE type = 'index' AND name = {self._lit(name)}"
        elif self.d == "postgres":
            sql = (f"SELECT COUNT(*) FROM pg_indexes WHERE tablename = {self._lit(table.name)}"
                   f"{self._schema_filter(table, 'schemaname')} AND indexname = {self._lit(name)}")
        else:
            sql = (f"SELECT COUNT(DISTINCT index_name) FROM information_schema.statistics WHERE table_name = {self._lit(table.name)}"
                   f"{self._schema_filter(table)} AND index_name = {self._lit(name)}")
        return Check(f"Index {name} {'exists' if expected else 'is absent'}", sql, expected)

    def _constraint_exists(self, table: Table, name: str, ctype: str, expected: int = 1) -> Check:
        sql = (f"SELECT COUNT(*) FROM information_schema.table_constraints WHERE table_name = {self._lit(table.name)}"
               f"{self._schema_filter(table)} AND constraint_name = {self._lit(name)} AND constraint_type = {self._lit(ctype)}")
        return Check(f"Constraint {name} exists", sql, expected)

    def _pk_check(self, table: Table, cols: list[str]) -> Check:
        if self.d == "sqlite":
            items = ", ".join(self._lit(c) for c in cols)
            sql = f"SELECT COUNT(*) FROM pragma_table_info({self._lit(table.name)}) WHERE pk > 0 AND name IN ({items})"
            return Check(f"{table.name} primary key covers {', '.join(cols)}", sql, len(cols))
        name = "PRIMARY" if self.d == "mysql" else make_name("pk", table.name, [], self.d)
        return self._constraint_exists(table, name, "PRIMARY KEY")

    def _null_check(self, table: Table, col: str, what: str = "NOT NULL") -> Check:
        return Check(f"No NULLs in {table.name}.{col} ({what} would fail)",
                     f"SELECT COUNT(*) FROM {self._t(table)} WHERE {self._q(col)} IS NULL", 0, "data")

    def _dup_check(self, table: Table, cols: list[str]) -> Check:
        qcols = columns_sql(cols, self.d)
        filt = " AND ".join(f"{self._q(c)} IS NOT NULL" for c in cols)
        sql = (f"SELECT COUNT(*) FROM (SELECT {qcols} FROM {self._t(table)} WHERE {filt} GROUP BY {qcols} HAVING COUNT(*) > 1) d")
        return Check(f"No duplicate values in {table.name} ({', '.join(cols)}) (UNIQUE would fail)", sql, 0, "data")

    def _orphan_check(self, table: Table, cols: list[str], ref: Table, ref_cols: list[str]) -> Check:
        on = " AND ".join(f"c.{self._q(a)} = p.{self._q(b)}" for a, b in zip(cols, ref_cols))
        notnull = " AND ".join(f"c.{self._q(c)} IS NOT NULL" for c in cols)
        sql = (f"SELECT COUNT(*) FROM {self._t(table)} c LEFT JOIN {self._t(ref)} p ON {on} "
               f"WHERE {notnull} AND p.{self._q(ref_cols[0])} IS NULL")
        return Check(f"No orphan rows in {table.name} ({', '.join(cols)}) referencing {ref.name} (FK would fail)", sql, 0, "data")

    def _cast_checks(self, table: Table, col: str, old: str, new: str, kind: str) -> tuple[list[Check], list[str]]:
        q = self._q(col)
        t = self._t(table)
        a, b = parse_type(old), parse_type(new)
        checks: list[Check] = []
        notes: list[str] = []
        length = "LENGTH" if self.d == "sqlite" else "CHAR_LENGTH"

        def add(desc: str, where: str) -> None:
            checks.append(Check(desc, f"SELECT COUNT(*) FROM {t} WHERE {q} IS NOT NULL AND ({where})", 0, "data"))

        if b.family in ("text", "char") and b.length is not None:
            add(f"Values in {table.name}.{col} fit length {b.length}", f"{length}({q}) > {b.length}")
        if a.family in ("text", "char") and b.family == "int":
            add(f"{table.name}.{col} holds only integers", self._regex_not(q, "^[+-]?[0-9]+$"))
        elif a.family in ("text", "char") and b.family == "decimal":
            add(f"{table.name}.{col} holds only numbers", self._regex_not(q, "^[+-]?[0-9]+([.][0-9]+)?$"))
        elif a.family in ("text", "char") and b.family in ("date", "datetime", "timestamptz"):
            add(f"{table.name}.{col} holds ISO dates", self._regex_not(q, "^[0-9]{4}-[0-9]{2}-[0-9]{2}"))
        elif a.family == "int" and b.family == "int" and kind == "narrowing":
            limit = 2 ** ((b.bits or 32) - 1)
            add(f"Values in {table.name}.{col} fit the new integer range", f"{q} < -{limit} OR {q} > {limit - 1}")
        elif a.family in ("decimal", "float") and b.family == "int":
            add(f"{table.name}.{col} has no fractional values", f"{q} <> FLOOR({q})")
        elif a.family == "decimal" and b.family == "decimal" and kind == "narrowing":
            digits = (b.precision or 38) - (b.scale or 0)
            add(f"Values in {table.name}.{col} fit decimal({b.precision},{b.scale})",
                f"ABS({q}) >= POWER(10, {digits}) OR {q} <> ROUND({q}, {b.scale or 0})")
        elif kind == "narrowing":
            notes.append(f"Could not write a generic check that {table.name}.{col} converts from {old} to {new}. Verify conversion by hand before running.")
        return checks, notes

    def _regex_not(self, q: str, pattern: str) -> str:
        if self.d == "postgres":
            return f"{q} !~ {self._lit(pattern)}"
        if self.d == "mysql":
            return f"{q} NOT REGEXP {self._lit(pattern)}"
        return f"NOT ({q} GLOB {self._lit(pattern)})"

    # --- shared SQL ----------------------------------------------------------

    def _mysql_coldef(self, col, type_name: Optional[str] = None, nullable: Optional[bool] = None) -> str:
        if col.is_generated:
            raise _Manual(f"Generated column {col.name} cannot be restated safely.")
        spec = type_name or col.data_type
        validate_type(spec)
        parts = [self._q(col.name), spec]
        if col.charset:
            parts.append(f"CHARACTER SET {col.charset}")
        if col.collation:
            parts.append(f"COLLATE {col.collation}")
        allow_null = col.nullable if nullable is None else nullable
        parts.append("NULL" if allow_null else "NOT NULL")
        if col.default is not None:
            if ";" in col.default:
                raise _Manual(f"Default of {col.name} is not safe to restate.")
            parts.append(f"DEFAULT {col.default}")
        if col.is_identity:
            parts.append("AUTO_INCREMENT")
        if col.comment:
            parts.append(f"COMMENT {self._lit(col.comment)}")
        return " ".join(parts)

    _IN_PLACE = ", ALGORITHM=INPLACE, LOCK=NONE"
    _COPY = ", ALGORITHM=COPY, LOCK=SHARED"
    _REBUILD_NOTE = "SQLite cannot alter this in place, so the table is rebuilt: copy to a new table, drop the old one and rename."

    def _dependency_risks(self, table: Table, column: Optional[str] = None) -> list[str]:
        risks: list[str] = []
        target = column or table.name
        pattern = re.compile(rf"\b{re.escape(target)}\b", re.I)
        for view in self.db.views:
            if pattern.search(view.definition or "") or any(r.lower() == table.name.lower() for r in view.references):
                if column is None or pattern.search(view.definition or ""):
                    risks.append(f"View {view.fqname} references {table.name}{'.' + column if column else ''}; check its definition.")
        for routine in self.db.routines:
            if pattern.search(routine.definition or ""):
                risks.append(f"{routine.kind} {routine.name} references {target}; engines do not always update routine bodies.")
        for job in self.db.pipelines:
            for step in job.steps:
                if pattern.search(step.sql or "") or target.lower() in {s.lower() for s in step.sources + step.targets}:
                    risks.append(f"Pipeline {job.name} step {step.name} references {target}.")
        for owner, fk in self.db.referencing(table):
            if column is None or column.lower() in {c.lower() for c in fk.ref_columns}:
                risks.append(f"Foreign key from {owner.fqname} references {table.name}{'.' + column if column else ''}.")
        risks.append("Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the "
                     "migration generator and may use this name.")
        return risks

    # --- operations ----------------------------------------------------------

    def _draft(self, op: _Op, title: str, **kw: Any) -> _Draft:
        d = _Draft(op=op.kind, title=title, table=op.table, column=op.column, finding_ids=list(op.finding_ids), **kw)
        return d

    def _require_column(self, table: Table, column: Optional[str]):
        if not column:
            raise _Manual(f"No column was given for a change on {table.fqname}.")
        col = table.column(column)
        if col is None:
            raise _Manual(f"Column {table.fqname}.{column} was not found in the assessed model.")
        return col

    def _build(self, op: _Op) -> list[_Draft]:
        return getattr(self, f"_op_{op.kind}")(op)

    def _op_manual(self, op: _Op) -> list[_Draft]:
        description = str(op.params.get("description") or "Manual change required; see the finding.")
        d = self._draft(op, f"Manual: {description[:80]}", manual=True, manual_description=description)
        return [d]

    def _op_add_column(self, op: _Op) -> list[_Draft]:
        table, name = op.table, op.column
        if not name:
            raise _Manual("add_column requires a column name.")
        type_name = validate_type(op.params.get("type"))
        nullable = bool(op.params.get("nullable", True))
        has_default = op.params.get("default") is not None
        default = render_default(op.params.get("default"), self.d) if has_default else None
        d = self._draft(op, f"Add column {table.name}.{name} {type_name}")
        need_backfill = not nullable and not has_default
        apply_nullable = nullable or (need_backfill and (table.row_count != 0 or self.d == "sqlite"))
        clause = f"{self._q(name)} {type_name}"
        if default is not None:
            clause += f" DEFAULT {default}"
        if not apply_nullable:
            clause += " NOT NULL"
        alter = f"ALTER TABLE {self._t(table)} ADD COLUMN {clause}"
        if self.d == "mysql":
            alter += self._IN_PLACE
        d.up = self._lock() + [alter]
        drop = f"ALTER TABLE {self._t(table)} DROP COLUMN {self._q(name)}"
        d.down = self._lock() + [drop + (self._IN_PLACE if self.d == "mysql" else "")]
        d.notes.append("Rollback drops the column and discards any values written to it after the change.")
        d.pre = [self._table_exists(table), self._col_exists(table, name, 0)]
        d.post = [self._col_exists(table, name)]
        if self.d == "postgres":
            d.notes.append("On PostgreSQL 11 and later a constant default does not rewrite the table; the brief ACCESS EXCLUSIVE lock is bounded by lock_timeout.")
        elif self.d == "mysql":
            d.notes.append("MySQL 8.0 allows ADD COLUMN with INPLACE and LOCK=NONE; INSTANT may also be available from 8.0.12 and later.")
        if need_backfill and apply_nullable:
            d.repair_notes.append(f"The table may hold rows, so {name} is added as nullable. Backfill it, then apply NOT NULL in a later migration.")
        effect_params = {**op.params, "nullable": apply_nullable, "type": type_name}
        if has_default:
            effect_params["default"] = default
        d.effects.append(("add_column", name, effect_params))
        d.creates.add(_tok("col", table, name.lower()))
        return [d]

    def _op_alter_column_type(self, op: _Op) -> list[_Draft]:
        table, name = op.table, op.column
        col = self._require_column(table, name)
        new_type = validate_type(op.params.get("new_type"))
        kind = type_change_kind(col.data_type, new_type, self.d)
        if kind == "same":
            self.satisfied.extend(op.finding_ids)
            self.notes.append(f"{table.name}.{name} already has type {new_type}.")
            return []
        populated = table.row_count != 0
        direct = kind == "binary_compatible" or not populated
        checks, repair = self._cast_checks(table, name, col.data_type, new_type, kind)
        if direct:
            return [self._type_direct(op, col, new_type, kind, checks, repair)]
        return self._type_expand_contract(op, col, new_type, kind, checks, repair)

    def _type_direct(self, op: _Op, col, new_type: str, kind: str, checks: list[Check], repair: list[str]) -> _Draft:
        table, name = op.table, op.column
        d = self._draft(op, f"Change type of {table.name}.{name} to {new_type} ({kind.replace('_', ' ')})")
        tq = self._t(table)
        q = self._q(name)
        if self.d == "postgres":
            up = f"ALTER TABLE {tq} ALTER COLUMN {q} TYPE {new_type} USING CAST({q} AS {new_type})"
            down = f"ALTER TABLE {tq} ALTER COLUMN {q} TYPE {col.data_type} USING CAST({q} AS {col.data_type})"
        else:
            clause = self._IN_PLACE if kind == "binary_compatible" else self._COPY
            up = f"ALTER TABLE {tq} MODIFY COLUMN {self._mysql_coldef(col, new_type)}{clause}"
            down = f"ALTER TABLE {tq} MODIFY COLUMN {self._mysql_coldef(col)}{clause}"
        d.up = self._lock() + [up]
        d.pre = [self._table_exists(table), self._col_exists(table, name)] + checks
        d.post = [self._col_type(table, name, new_type)]
        d.repair_notes.extend(repair)
        d.lock_risk = "low" if kind == "binary_compatible" else "medium"
        if kind == "narrowing":
            d.reversible = False
            d.irreversible_reason = f"Narrowing from {col.data_type} to {new_type} cannot be undone without loss; values changed by it cannot be recovered from the column."
            d.data_loss_risk = "high"
        else:
            d.down = self._lock() + [down]
            d.notes.append("Rollback converts back to the original type and fails if newer values no longer fit it.")
            d.data_loss_risk = "low"
        d.effects.append(("alter_column_type", name, {"new_type": new_type}))
        return d

    def _type_expand_contract(self, op: _Op, col, new_type: str, kind: str, checks: list[Check], repair: list[str]) -> list[_Draft]:
        table, name = op.table, op.column
        tq = self._t(table)
        old, new, old_copy = self._q(name), self._q(f"{name}__dbintel_new"), self._q(f"{name}__dbintel_old")
        ids = list(op.finding_ids)
        col_tok = _tok("col", table, f"{name}__dbintel_new")
        # expand
        expand = self._draft(op, f"Expand: add {name}__dbintel_new {new_type} on {table.name} and backfill", phase_label="expand")
        add = f"ALTER TABLE {tq} ADD COLUMN {new} {new_type}"
        if self.d == "mysql":
            add += self._IN_PLACE
        cast = f"CAST({old} AS {new_type})" if self.d == "postgres" else old
        where = f"{new} IS NULL AND {old} IS NOT NULL"
        if self.d == "mysql":
            backfill = f"UPDATE {tq} SET {new} = {cast} WHERE {where} LIMIT 1000"
        elif table.primary_key:
            pk = columns_sql(table.primary_key, self.d)
            backfill = f"UPDATE {tq} SET {new} = {cast} WHERE ({pk}) IN (SELECT {pk} FROM {tq} WHERE {where} LIMIT 1000)"
        else:
            backfill = f"UPDATE {tq} SET {new} = {cast} WHERE {where}"
        expand.up = self._lock() + [add, backfill]
        expand.down = self._lock() + [f"ALTER TABLE {tq} DROP COLUMN {new}" + (self._IN_PLACE if self.d == "mysql" else "")]
        expand.pre = [self._table_exists(table), self._col_exists(table, name)] + checks
        expand.post = [self._col_exists(table, f"{name}__dbintel_new")]
        expand.repair_notes.extend(repair)
        expand.notes += ["The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).",
                         "The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016)."]
        expand.lock_risk = "medium"
        expand.creates.add(col_tok)
        # swap
        swap = self._draft(op, f"Swap: make {name}__dbintel_new the live {table.name}.{name}", phase_label="swap")
        same = f"CAST({old} AS {new_type}) IS DISTINCT FROM {new}" if self.d == "postgres" else f"NOT ({old} <=> {new})"
        swap.pre = [Check(f"Backfill of {name}__dbintel_new is complete", f"SELECT COUNT(*) FROM {tq} WHERE {where}", 0, "data"),
                    Check(f"{name}__dbintel_new matches {name}", f"SELECT COUNT(*) FROM {tq} WHERE {same}", 0, "data")]
        rename = lambda a, b: f"ALTER TABLE {tq} RENAME COLUMN {a} TO {b}"  # noqa: E731
        swap.up = self._lock() + [rename(old, old_copy), rename(new, old)]
        swap.down = self._lock() + [rename(old, new), rename(old_copy, old)]
        swap.post = [self._col_exists(table, name), self._col_exists(table, f"{name}__dbintel_old"), self._col_exists(table, f"{name}__dbintel_new", 0)]
        swap.notes.append("The application should tolerate both types before this step and deploy between expand and swap (MIG-004).")
        swap.effects.append(("alter_column_type", name, {"new_type": new_type}))
        swap.lock_risk = "medium"
        swap.needs.add(col_tok)
        swap.creates.add(_tok("swap", table, name.lower()))
        # cleanup
        cleanup = self._draft(op, f"Contract: drop the old {table.name}.{name}__dbintel_old", phase_label="contract")
        cleanup.up = self._lock() + [f"ALTER TABLE {tq} DROP COLUMN {old_copy}" + (self._IN_PLACE if self.d == "mysql" else "")]
        cleanup.reversible = False
        cleanup.irreversible_reason = "Dropping the old column removes its data. Restoring it requires a backup."
        cleanup.data_loss_risk = "high"
        cleanup.lock_risk = "medium"
        cleanup.pre = [self._col_exists(table, f"{name}__dbintel_old")]
        cleanup.post = [self._col_exists(table, f"{name}__dbintel_old", 0)]
        cleanup.notes.append("Run only after the new column has been verified in production through at least one release (MIG-004).")
        cleanup.needs.add(_tok("swap", table, name.lower()))
        return [expand, swap, cleanup]

    def _op_set_not_null(self, op: _Op) -> list[_Draft]:
        table, name = op.table, op.column
        col = self._require_column(table, name)
        d = self._draft(op, f"Set {table.name}.{name} NOT NULL")
        tq, q = self._t(table), self._q(name)
        d.pre = [self._table_exists(table), self._col_exists(table, name), self._null_check(table, name)]
        d.post = [self._col_not_null(table, name)]
        d.needs.add(_tok("col", table, name.lower()))
        if self.d == "postgres":
            if table.row_count == 0:
                d.up = self._lock() + [f"ALTER TABLE {tq} ALTER COLUMN {q} SET NOT NULL"]
            else:
                ck = self._q(make_name("nn", table.name, [name], self.d))
                d.up = self._lock() + [f"ALTER TABLE {tq} ADD CONSTRAINT {ck} CHECK ({q} IS NOT NULL) NOT VALID",
                                       f"ALTER TABLE {tq} VALIDATE CONSTRAINT {ck}",
                                       f"ALTER TABLE {tq} ALTER COLUMN {q} SET NOT NULL",
                                       f"ALTER TABLE {tq} DROP CONSTRAINT {ck}"]
                d.notes.append("PostgreSQL 12 and later use the validated CHECK to skip the full scan under ACCESS EXCLUSIVE.")
            d.down = self._lock() + [f"ALTER TABLE {tq} ALTER COLUMN {q} DROP NOT NULL"]
        else:  # mysql
            d.up = self._lock() + [f"ALTER TABLE {tq} MODIFY COLUMN {self._mysql_coldef(col, nullable=False)}{self._IN_PLACE}"]
            d.down = self._lock() + [f"ALTER TABLE {tq} MODIFY COLUMN {self._mysql_coldef(col, nullable=True)}{self._IN_PLACE}"]
            d.notes.append("MySQL needs STRICT_ALL_TABLES or STRICT_TRANS_TABLES for INPLACE and rejects NULLs instead of converting them.")
        d.lock_risk = "low" if table.row_count == 0 else "medium"
        d.effects.append(("set_not_null", name, {}))
        return [d]

    def _op_add_primary_key(self, op: _Op) -> list[_Draft]:
        table = op.table
        cols = self._columns(op)
        if not cols:
            raise _Manual("add_primary_key requires columns.")
        for name in cols:
            self._require_column(table, name)
        d = self._draft(op, f"Add primary key ({', '.join(cols)}) to {table.name}")
        tq = self._t(table)
        nullable = [c for c in cols if table.column(c).nullable]
        d.pre = [self._table_exists(table)] + [self._col_exists(table, c) for c in cols]
        d.pre += [self._null_check(table, c, "PRIMARY KEY") for c in cols] + [self._dup_check(table, cols)]
        d.post = [self._pk_check(table, cols)]
        if self.d == "postgres":
            pk = make_name("pk", table.name, [], self.d)
            idx = self._q(pk)
            d.transactional = False
            d.up = self._lock()
            for c in nullable:
                ck = self._q(make_name("nn", table.name, [c], self.d))
                d.up += [f"ALTER TABLE {tq} ADD CONSTRAINT {ck} CHECK ({self._q(c)} IS NOT NULL) NOT VALID",
                         f"ALTER TABLE {tq} VALIDATE CONSTRAINT {ck}",
                         f"ALTER TABLE {tq} ALTER COLUMN {self._q(c)} SET NOT NULL",
                         f"ALTER TABLE {tq} DROP CONSTRAINT {ck}"]
            d.up += [f"CREATE UNIQUE INDEX CONCURRENTLY {idx} ON {tq} ({columns_sql(cols, self.d)})",
                     f"ALTER TABLE {tq} ADD CONSTRAINT {idx} PRIMARY KEY USING INDEX {idx}"]
            d.down = self._lock() + [f"ALTER TABLE {tq} DROP CONSTRAINT {idx}"]
            d.down += [f"ALTER TABLE {tq} ALTER COLUMN {self._q(c)} DROP NOT NULL" for c in nullable]
            d.notes.append("CREATE INDEX CONCURRENTLY must run outside a transaction. If it fails it leaves an INVALID index to drop.")
            d.lock_risk = "medium"
        else:
            up = [f"ALTER TABLE {tq} MODIFY COLUMN {self._mysql_coldef(table.column(c), nullable=False)}{self._IN_PLACE}" for c in nullable]
            down_mod = [f"ALTER TABLE {tq} MODIFY COLUMN {self._mysql_coldef(table.column(c), nullable=True)}{self._IN_PLACE}" for c in nullable]
            d.up = self._lock() + up + [f"ALTER TABLE {tq} ADD PRIMARY KEY ({columns_sql(cols, self.d)}){self._IN_PLACE}"]
            d.down = self._lock() + [f"ALTER TABLE {tq} DROP PRIMARY KEY, ALGORITHM=COPY, LOCK=SHARED"] + down_mod
            d.notes.append("MySQL rebuilds the table for ADD PRIMARY KEY; INPLACE with LOCK=NONE is allowed when the columns are already NOT NULL.")
            d.lock_risk = "high" if table.row_count != 0 else "low"
        d.effects.append(("add_primary_key", None, {"columns": cols}))
        d.creates |= {_tok("pk", table), _tok("uq", table, *[c.lower() for c in cols])}
        d.needs |= {_tok("col", table, c.lower()) for c in cols}
        return [d]

    def _op_add_surrogate_primary_key(self, op: _Op) -> list[_Draft]:
        table = op.table
        name = op.params.get("column") or op.column or "id"
        validate_identifier(name, self.d)
        if table.has_column(name):
            raise _Manual(f"Column {table.fqname}.{name} already exists; choose another name for the surrogate key.")
        d = self._draft(op, f"Add surrogate primary key {name} to {table.name}")
        tq, q = self._t(table), self._q(name)
        d.pre = [self._table_exists(table), self._col_exists(table, name, 0)]
        d.post = [self._col_exists(table, name), self._pk_check(table, [name])]
        d.lock_risk = "high" if table.row_count != 0 else "low"
        if self.d == "postgres":
            pk = self._q(make_name("pk", table.name, [], self.d))
            d.transactional = False
            d.up = self._lock() + [f"ALTER TABLE {tq} ADD COLUMN {q} bigint GENERATED BY DEFAULT AS IDENTITY",
                                   f"CREATE UNIQUE INDEX CONCURRENTLY {pk} ON {tq} ({q})",
                                   f"ALTER TABLE {tq} ADD CONSTRAINT {pk} PRIMARY KEY USING INDEX {pk}"]
            d.down = self._lock() + [f"ALTER TABLE {tq} DROP CONSTRAINT {pk}", f"ALTER TABLE {tq} DROP COLUMN {q}"]
            d.notes.append("Adding an identity column rewrites the table under ACCESS EXCLUSIVE. On large tables stage it: add a nullable column, attach a sequence, backfill in batches.")
        else:
            d.up = self._lock() + [f"ALTER TABLE {tq} ADD COLUMN {q} BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY FIRST, ALGORITHM=INPLACE, LOCK=SHARED"]
            d.down = self._lock() + [f"ALTER TABLE {tq} DROP PRIMARY KEY, DROP COLUMN {q}, ALGORITHM=COPY, LOCK=SHARED"]
            d.notes.append("Adding an AUTO_INCREMENT column rebuilds the table and blocks concurrent DML in MySQL; use an online schema change tool on large tables.")
        d.effects.append(("add_surrogate_primary_key", None, {"column": name}))
        d.creates |= {_tok("pk", table), _tok("col", table, name.lower())}
        return [d]

    def _op_add_foreign_key(self, op: _Op) -> list[_Draft]:
        table = op.table
        cols = self._columns(op)
        ref_cols = names(op.params.get("ref_columns"))
        ref = self._find(op.params.get("ref_table"))
        if not cols or not ref_cols or len(cols) != len(ref_cols):
            raise _Manual("add_foreign_key needs matching column lists.")
        if ref is None:
            raise _Manual(f"Referenced table {op.params.get('ref_table')!r} was not found in the assessed model.")
        for c in cols:
            self._require_column(table, c)
        for c in ref_cols:
            self._require_column(ref, c)
        self._require_unique(ref, ref_cols)
        fk_name = op.params.get("name") or make_name("fk", table.name, cols, self.d)
        op.params["name"] = validate_identifier(fk_name, self.d)
        fk = self._q(fk_name)
        rc = f"REFERENCES {self._t(ref)} ({columns_sql(ref_cols, self.d)})"
        rc += self._fk_actions(op.params)
        d = self._draft(op, f"Add foreign key {table.name} ({', '.join(cols)}) -> {ref.name}")
        tq = self._t(table)
        d.pre = [self._table_exists(table), self._table_exists(ref), self._orphan_check(table, cols, ref, ref_cols)]
        d.post = [self._constraint_exists(table, fk_name, "FOREIGN KEY")]
        add = f"ALTER TABLE {tq} ADD CONSTRAINT {fk} FOREIGN KEY ({columns_sql(cols, self.d)}) {rc}"
        if self.d == "postgres":
            d.up = self._lock() + [f"{add} NOT VALID", f"ALTER TABLE {tq} VALIDATE CONSTRAINT {fk}"]
            d.down = self._lock() + [f"ALTER TABLE {tq} DROP CONSTRAINT {fk}"]
            d.notes.append("NOT VALID takes a brief lock; VALIDATE scans existing rows under a weaker lock that does not block writes.")
            d.lock_risk = "medium"
        else:
            d.up = self._lock() + [add + self._COPY]
            d.down = self._lock() + [f"ALTER TABLE {tq} DROP FOREIGN KEY {fk}", ]
            d.notes.append("MySQL only allows INPLACE when foreign_key_checks is off, which would skip validation, so COPY with LOCK=SHARED is used. It blocks writes while running; schedule accordingly.")
            d.lock_risk = "high" if table.row_count != 0 else "low"
        d.effects.append(("add_foreign_key", None, {**op.params, "columns": cols, "ref_table": ref.name, "ref_columns": ref_cols}))
        d.needs |= {_tok("col", table, c.lower()) for c in cols}
        d.needs_any.append({_tok("pk", ref), _tok("uq", ref, *[c.lower() for c in ref_cols])})
        return [d]

    def _require_unique(self, ref: Table, ref_cols: list[str]) -> None:
        wanted = [c.lower() for c in ref_cols]
        keys = [[c.lower() for c in k] for k in ref.unique_keys()]
        if not any(sorted(k) == sorted(wanted) for k in keys) and _tok("uq", ref, *wanted) not in self.planned:
            raise _Manual(f"{ref.fqname} ({', '.join(ref_cols)}) has no primary key or unique constraint, so a foreign key cannot reference it. Add one first.")

    def _fk_actions(self, params: dict[str, Any]) -> str:
        text = ""
        for key, keyword in (("on_delete", "ON DELETE"), ("on_update", "ON UPDATE")):
            value = params.get(key)
            if value:
                upper = str(value).upper().strip()
                if upper not in _ACTIONS:
                    raise _Manual(f"Unsupported referential action {value!r}.")
                text += f" {keyword} {upper}"
        return text

    def _op_add_index(self, op: _Op) -> list[_Draft]:
        table = op.table
        cols = self._columns(op)
        if not cols:
            raise _Manual("add_index requires columns.")
        for c in cols:
            col = self._require_column(table, c)
            if self.d == "mysql" and col.type.family in ("text", "binary") and col.type.length is None:
                raise _Manual(f"MySQL needs a prefix length for {table.name}.{c} ({col.data_type}); choose one and create the index by hand.")
        unique = bool(op.params.get("unique"))
        name = op.params.get("name") or make_name("uq" if unique else "ix", table.name, cols, self.d)
        validate_identifier(name, self.d)
        d = self._draft(op, f"Add {'unique ' if unique else ''}index on {table.name} ({', '.join(cols)})")
        tq, q, keyword = self._t(table), self._q(name), "UNIQUE " if unique else ""
        d.pre = [self._table_exists(table)] + [self._col_exists(table, c) for c in cols]
        if unique:
            d.pre.append(self._dup_check(table, cols))
        d.post = [self._index_exists(table, name)]
        qcols = columns_sql(cols, self.d)
        if self.d == "postgres":
            d.transactional = False
            d.up = self._lock() + [f"CREATE {keyword}INDEX CONCURRENTLY {q} ON {tq} ({qcols})"]
            d.down = self._lock() + [f"DROP INDEX CONCURRENTLY {self._index_qualified(table, name)}"]
            d.notes.append("CREATE INDEX CONCURRENTLY must run outside a transaction. If it fails it leaves an INVALID index to drop before retrying.")
        elif self.d == "mysql":
            d.up = self._lock() + [f"ALTER TABLE {tq} ADD {keyword}INDEX {q} ({qcols}){self._IN_PLACE}"]
            d.down = self._lock() + [f"ALTER TABLE {tq} DROP INDEX {q}{self._IN_PLACE}"]
            d.notes.append("MySQL builds secondary indexes in place and permits concurrent DML with LOCK=NONE.")
        else:
            d.up = [f"CREATE {keyword}INDEX {q} ON {tq} ({qcols})"]
            d.down = [f"DROP INDEX {q}"]
        d.lock_risk = "low" if self.d != "sqlite" else "medium"
        d.effects.append(("add_index", None, {"columns": cols, "unique": unique, "name": name}))
        if unique:
            d.creates.add(_tok("uq", table, *[c.lower() for c in cols]))
        d.needs |= {_tok("col", table, c.lower()) for c in cols}
        return [d]

    def _index_qualified(self, table: Table, name: str) -> str:
        if table.schema and self.d == "postgres":
            return f"{self._q(table.schema)}.{self._q(name)}"
        return self._q(name)

    def _op_drop_index(self, op: _Op) -> list[_Draft]:
        table = op.table
        name = op.params.get("name")
        validate_identifier(name, self.d)
        index: Optional[Index] = next((i for i in table.indexes if (i.name or "").lower() == str(name).lower()), None)
        if index is None:
            raise _Manual(f"Index {name!r} was not found on {table.fqname}.")
        if index.primary or index.is_constraint:
            raise _Manual(f"Index {name!r} backs a constraint on {table.fqname}; removing it means removing the constraint and needs review.")
        d = self._draft(op, f"Drop index {name} on {table.name}")
        recreated = ", ".join(self._q(c) for c in index.columns)
        keyword = "UNIQUE " if index.unique else ""
        tq, q = self._t(table), self._q(index.name or str(name))
        if self.d == "postgres":
            d.transactional = False
            up = f"DROP INDEX CONCURRENTLY {self._index_qualified(table, index.name)}"
            down = f"CREATE {keyword}INDEX CONCURRENTLY {q} ON {tq}"
        elif self.d == "mysql":
            up = f"ALTER TABLE {tq} DROP INDEX {q}{self._IN_PLACE}"
            down = f"ALTER TABLE {tq} ADD {keyword}INDEX {q}"
        else:
            up = f"DROP INDEX {q}"
            down = f"CREATE {keyword}INDEX {q} ON {tq}"
        down += f" ({recreated})"
        if self.d == "mysql":
            down += self._IN_PLACE
        if index.where:
            if self.d == "mysql":
                raise _Manual(f"Partial index {name} cannot be recreated on MySQL.")
            render_expression(index.where, self.d, self.db.dialect)
            down += f" WHERE {index.where}"
        if index.include or (index.method and index.method.lower() not in ("btree", "")):
            d.reversible = False
            d.irreversible_reason = f"Index {name} uses features the generated rollback does not reproduce (method or INCLUDE columns)."
        else:
            d.down = self._lock() + [down]
        d.up = self._lock() + [up]
        d.pre = [self._table_exists(table), self._index_exists(table, index.name or str(name))]
        d.post = [self._index_exists(table, index.name or str(name), 0)]
        d.notes.append("Queries that use this index will degrade after it is dropped. Confirm with usage statistics first.")
        d.effects.append(("drop_index", None, {"name": str(name)}))
        return [d]

    def _op_add_check(self, op: _Op) -> list[_Draft]:
        table = op.table
        expr = render_expression(op.params.get("expression"), self.d, self.db.dialect)
        digest = hashlib.sha256(expr.encode("utf-8")).hexdigest()[:8]
        name = op.params.get("name") or make_name("ck", table.name, [digest], self.d)
        validate_identifier(name, self.d)
        op.params["name"] = name
        d = self._draft(op, f"Add check constraint {name} on {table.name}")
        tq, q = self._t(table), self._q(name)
        d.pre = [self._table_exists(table),
                 Check(f"No rows violate {expr}", f"SELECT COUNT(*) FROM {tq} WHERE NOT ({expr})", 0, "data")]
        d.post = [self._constraint_exists(table, name, "CHECK")]
        add = f"ALTER TABLE {tq} ADD CONSTRAINT {q} CHECK ({expr})"
        if self.d == "postgres":
            d.up = self._lock() + [f"{add} NOT VALID", f"ALTER TABLE {tq} VALIDATE CONSTRAINT {q}"]
            d.down = self._lock() + [f"ALTER TABLE {tq} DROP CONSTRAINT {q}"]
            d.notes.append("NOT VALID then VALIDATE avoids scanning under a write-blocking lock.")
        else:
            d.up = self._lock() + [add]
            d.down = self._lock() + [f"ALTER TABLE {tq} DROP CHECK {q}"]
            d.notes.append("MySQL enforces CHECK from 8.0.16; earlier versions parse and ignore it.")
            d.lock_risk = "medium"
        d.effects.append(("add_check", None, {"expression": expr, "name": name}))
        return [d]

    def _op_enable_rls(self, op: _Op) -> list[_Draft]:
        table = op.table
        tenant = op.params.get("tenant_column") or op.column
        if self.d != "postgres":
            raise _Manual(f"{self.d} has no row level security; enforce tenant isolation in the application or through views.")
        col = self._require_column(table, tenant)
        policy = validate_identifier(op.params.get("policy_name") or make_name("rls", table.name, [tenant], self.d), self.d)
        d = self._draft(op, f"Enable row level security on {table.name} by {tenant}")
        tq, p = self._t(table), self._q(policy)
        expr = f"{self._q(tenant)} = CAST(current_setting('app.tenant_id') AS {validate_type(col.data_type)})"
        d.pre = [self._table_exists(table), self._col_exists(table, tenant), self._null_check(table, tenant, "tenant isolation")]
        d.up = self._lock() + [f"CREATE POLICY {p} ON {tq} USING ({expr}) WITH CHECK ({expr})",
                               f"ALTER TABLE {tq} ENABLE ROW LEVEL SECURITY"]
        d.down = self._lock() + [f"ALTER TABLE {tq} DISABLE ROW LEVEL SECURITY", f"DROP POLICY {p} ON {tq}"]
        schema = self._lit(table.schema) if table.schema else "current_schema()"
        d.post = [Check(f"RLS is enabled on {table.name}", f"SELECT COUNT(*) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE c.relname = {self._lit(table.name)} AND n.nspname = {schema} AND c.relrowsecurity", 1),
                  Check(f"Policy {policy} exists", f"SELECT COUNT(*) FROM pg_policies WHERE tablename = {self._lit(table.name)} AND policyname = {self._lit(policy)}", 1)]
        d.notes += ["The session setting app.tenant_id is a placeholder convention; confirm how the application sets tenant context before use.",
                    "Table owners and BYPASSRLS roles are exempt unless FORCE ROW LEVEL SECURITY is added; confirm application roles."]
        d.lock_risk = "medium"
        d.breaking = True
        d.dependency_risks = self._dependency_risks(table)
        d.effects.append(("enable_rls", None, {}))
        d.needs.add(_tok("col", table, tenant.lower()))
        return [d]

    def _op_revoke_grant(self, op: _Op) -> list[_Draft]:
        if self.d == "sqlite":
            raise _Manual("SQLite has no grant system; restrict access at the file level.")
        privilege = str(op.params.get("privilege", "")).upper().strip()
        grantee = op.params.get("grantee")
        if privilege not in _PRIVILEGES:
            raise _Manual(f"Privilege {op.params.get('privilege')!r} is not recognised.")
        if not grantee or op.table is None:
            raise _Manual("revoke_grant needs a grantee and a table scope.")
        table = op.table
        target = self._t(table)
        account = self._grantee(str(grantee))
        on = f"ON TABLE {target}" if self.d == "postgres" else f"ON {target}"
        d = self._draft(op, f"Revoke {privilege} on {table.name} from {grantee}")
        d.up = [f"REVOKE {privilege} {on} FROM {account}"]
        match = next((g for g in self.db.grants if g.grantee.lower() == str(grantee).split("@")[0].lower()
                      and g.privilege.upper() == privilege and (g.table or "").lower() == table.name.lower()), None)
        if match is None:
            d.reversible = False
            d.irreversible_reason = "The grant was not found in collected metadata, so a matching GRANT cannot be written with confidence."
        else:
            d.down = [f"GRANT {privilege} {on} TO {account}" + (" WITH GRANT OPTION" if match.grantable else "")]
        d.pre = [self._table_exists(table)]
        if self.d == "postgres":
            d.post = [Check("Grant is removed", f"SELECT COUNT(*) FROM information_schema.role_table_grants WHERE table_name = {self._lit(table.name)} AND grantee = {self._lit(str(grantee))} AND privilege_type = {self._lit(privilege)}", 0)]
        else:
            d.post = [Check("Grant is removed", f"SELECT COUNT(*) FROM information_schema.table_privileges WHERE table_name = {self._lit(table.name)} AND grantee LIKE {self._lit('%' + str(grantee).split('@')[0] + '%')} AND privilege_type = {self._lit(privilege)}", 0)]
        d.notes.append("Revocation can break applications that depend on this privilege; confirm the role is unused for it.")
        d.breaking = True
        d.lock_risk = "none"
        return [d]

    def _grantee(self, grantee: str) -> str:
        if self.d == "postgres":
            return "PUBLIC" if grantee.upper() == "PUBLIC" else quote(grantee, self.d)
        user, _, host = grantee.partition("@")
        user = user.strip("'`\"")
        host = host.strip("'`\"") or next((r.host for r in self.db.roles if r.name.lower() == user.lower() and r.host), "%")
        return f"{self._lit(user)}@{self._lit(host)}"

    def _rename_column_up(self, table: Table, old: str, new: str) -> str:
        sql = f"ALTER TABLE {self._t(table)} RENAME COLUMN {self._q(old)} TO {self._q(new)}"
        return sql + (self._IN_PLACE if self.d == "mysql" else "")

    def _op_rename_column(self, op: _Op) -> list[_Draft]:
        table, old = op.table, op.column
        self._require_column(table, old)
        new = validate_identifier(op.params.get("new_name"), self.d)
        d = self._draft(op, f"Rename column {table.name}.{old} to {new}")
        d.up = self._lock() + [self._rename_column_up(table, old, new)]
        d.down = self._lock() + [self._rename_column_up(table, new, old)]
        d.pre = [self._col_exists(table, old), self._col_exists(table, new, 0)]
        d.post = [self._col_exists(table, new), self._col_exists(table, old, 0)]
        d.breaking = True
        d.dependency_risks = self._dependency_risks(table, old)
        d.notes.append("Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).")
        if self.d == "mysql":
            d.notes.append("RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.")
        d.effects.append(("rename_column", old, {"new_name": new}))
        d.needs.add(_tok("col", table, old.lower()))
        return [d]

    def _op_rename_table(self, op: _Op) -> list[_Draft]:
        table = op.table
        new = validate_identifier(op.params.get("new_name"), self.d)
        if self._find(new) is not None:
            raise _Manual(f"A table named {new!r} already exists.")
        d = self._draft(op, f"Rename table {table.name} to {new}")
        tq, newq = self._t(table), self._q(new)
        if self.d == "mysql":
            schema = f"{self._q(table.schema)}." if table.schema else ""
            d.up = self._lock() + [f"RENAME TABLE {tq} TO {schema}{newq}"]
            d.down = self._lock() + [f"RENAME TABLE {schema}{newq} TO {tq}"]
        else:
            renamed = f"{self._q(table.schema)}.{newq}" if table.schema and self.d == "postgres" else newq
            d.up = self._lock() + [f"ALTER TABLE {tq} RENAME TO {newq}"]
            d.down = self._lock() + [f"ALTER TABLE {renamed} RENAME TO {self._q(table.name)}"]
        d.pre = [self._table_exists(table)]
        d.post = [self._table_exists(Table(name=new, schema=table.schema))]
        d.breaking = True
        d.dependency_risks = self._dependency_risks(table)
        d.notes.append("Renaming a table breaks every reader that uses the old name. Consider a compatibility view for one release.")
        d.effects.append(("rename_table", None, {"new_name": new}))
        return [d]

    def _op_rebuild(self, op: _Op) -> list[_Draft]:
        table = op.table
        kept: list[_Op] = []
        drafts: list[_Draft] = []
        for sub in op.subops:
            blocked = self._blocked(sub)
            if blocked:
                drafts.append(self._blocked_draft(sub, blocked))
            else:
                kept.append(sub)
        if not kept:
            return drafts
        after = copy.deepcopy(table)
        reversible = True
        reason = ""
        pre: list[Check] = [self._table_exists(table)]
        post: list[Check] = [self._table_exists(table)]
        labels: list[str] = []
        repair: list[str] = []
        creates: set = set()
        for sub in kept:
            cols = self._columns(sub)
            if sub.kind == "set_not_null":
                self._require_column(after, sub.column)
                pre.append(self._null_check(table, sub.column))
                post.append(self._col_not_null(table, sub.column))
                apply_fix_effect(after, "set_not_null", sub.column, {})
                labels.append(f"NOT NULL {sub.column}")
            elif sub.kind == "add_primary_key":
                for c in cols:
                    self._require_column(after, c)
                pre += [self._null_check(table, c, "PRIMARY KEY") for c in cols] + [self._dup_check(table, cols)]
                post.append(self._pk_check(table, cols))
                apply_fix_effect(after, "add_primary_key", None, {"columns": cols})
                labels.append(f"primary key ({', '.join(cols)})")
                creates |= {_tok("pk", table), _tok("uq", table, *[c.lower() for c in cols])}
            elif sub.kind == "add_surrogate_primary_key":
                name = sub.params.get("column") or sub.column or "id"
                validate_identifier(name, self.d)
                if after.has_column(name):
                    raise _Manual(f"Column {table.fqname}.{name} already exists.")
                apply_fix_effect(after, "add_surrogate_primary_key", None, {"column": name})
                post.append(self._col_exists(table, name))
                post.append(self._pk_check(table, [name]))
                labels.append(f"surrogate key {name}")
                creates |= {_tok("pk", table), _tok("col", table, name.lower())}
            elif sub.kind == "add_foreign_key":
                ref_cols = names(sub.params.get("ref_columns"))
                ref = self._find(sub.params.get("ref_table"))
                if ref is None or not cols or len(cols) != len(ref_cols):
                    raise _Manual(f"Foreign key on {table.fqname} has an unknown target or mismatched columns.")
                self._require_unique(ref, ref_cols)
                self._fk_actions(sub.params)
                fk_name = validate_identifier(sub.params.get("name") or make_name("fk", table.name, cols, self.d), self.d)
                sub.params["name"] = fk_name
                pre.append(self._orphan_check(table, cols, ref, ref_cols))
                apply_fix_effect(after, "add_foreign_key", None, {**sub.params, "columns": cols, "ref_table": ref.name, "ref_columns": ref_cols})
                post.append(Check(f"Foreign key on {table.name} ({', '.join(cols)}) exists",
                                  f"SELECT COUNT(*) FROM pragma_foreign_key_list({self._lit(table.name)}) WHERE \"table\" = {self._lit(ref.name)} AND \"from\" = {self._lit(cols[0])}", 1))
                labels.append(f"foreign key ({', '.join(cols)})")
            elif sub.kind == "add_check":
                expr = render_expression(sub.params.get("expression"), self.d, self.db.dialect)
                digest = hashlib.sha256(expr.encode("utf-8")).hexdigest()[:8]
                name = validate_identifier(sub.params.get("name") or make_name("ck", table.name, [digest], self.d), self.d)
                pre.append(Check(f"No rows violate {expr}", f"SELECT COUNT(*) FROM {self._t(table)} WHERE NOT ({expr})", 0, "data"))
                apply_fix_effect(after, "add_check", None, {"expression": expr, "name": name})
                post.append(Check(f"Check {name} exists", f"SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name = {self._lit(table.name)} AND sql LIKE {self._lit('%' + name + '%')}", 1))
                labels.append(f"check {name}")
            elif sub.kind == "alter_column_type":
                col = self._require_column(after, sub.column)
                new_type = validate_type(sub.params.get("new_type"))
                kind = type_change_kind(col.data_type, new_type, self.d)
                if kind == "same":
                    self.satisfied.extend(sub.finding_ids)
                    self.notes.append(f"{table.name}.{sub.column} already has type {new_type}.")
                    continue
                checks, notes = self._cast_checks(table, sub.column, col.data_type, new_type, kind)
                pre += checks
                repair += notes
                if kind == "narrowing":
                    reversible = False
                    reason = f"Narrowing {sub.column} to {new_type} cannot be undone without loss."
                apply_fix_effect(after, "alter_column_type", sub.column, {"new_type": new_type})
                post.append(self._col_type(table, sub.column, new_type))
                labels.append(f"type of {sub.column}")
            elif sub.kind == "add_column":
                type_name = validate_type(sub.params.get("type"))
                effect = {**sub.params, "type": type_name, "default": render_default(sub.params.get("default"), self.d)}
                apply_fix_effect(after, "add_column", sub.column, effect)
                post.append(self._col_exists(table, sub.column))
                labels.append(f"add column {sub.column}")
                creates.add(_tok("col", table, (sub.column or "").lower()))
        if not labels:
            return drafts
        d = _Draft(op="rebuild", title=f"Rebuild {table.name}: {'; '.join(labels)}", table=table, column=None,
                   finding_ids=[i for s in kept for i in s.finding_ids])
        d.up = self._rebuild_sql(table, after)
        if reversible:
            d.down = self._rebuild_sql(after, table)
            d.notes.append("Rollback rebuilds the table to its previous definition; columns added by this step and their values are lost.")
        else:
            d.reversible = False
            d.irreversible_reason = reason
        d.data_loss_risk = "high" if not reversible else "low"
        d.lock_risk = "high" if table.row_count != 0 else "low"
        d.pre, d.post = pre, post
        d.post.append(Check("No foreign key violations", f"SELECT COUNT(*) FROM pragma_foreign_key_check({self._lit(table.name)})", 0))
        d.notes.insert(0, self._REBUILD_NOTE)
        d.repair_notes = repair
        d.creates = creates
        d.effects.extend((s.kind, s.column, {**s.params, "columns": self._columns(s)}) for s in kept)
        return drafts + [d]

    def _rebuild_sql(self, source: Table, target: Table) -> list[str]:
        temp = f"{target.name}__dbintel_rebuild"
        tq = quote(temp, "sqlite")
        common: list[str] = []
        for col in target.columns:
            src = source.column(col.name)
            if src is None:
                continue
            if col.is_generated:
                raise _Manual(f"Generated column {target.name}.{col.name} cannot be copied in a rebuild.")
            if src.data_type.lower() != col.data_type.lower():
                common.append(f"CAST({quote(col.name, 'sqlite')} AS {col.data_type})")
            else:
                common.append(quote(col.name, "sqlite"))
        dest_cols = ", ".join(quote(c.name, "sqlite") for c in target.columns if source.column(c.name) is not None)
        triggers = []
        for routine in self.db.routines:
            if routine.kind == "trigger" and (routine.table or "").lower() == target.name.lower():
                if not re.match(r"\s*CREATE\s+(TEMP\s+|TEMPORARY\s+)?TRIGGER", routine.definition or "", re.I):
                    raise _Manual(f"Trigger {routine.name} has no usable definition; a rebuild would lose it.")
                triggers.append(routine.definition.strip().rstrip(";"))
        for chk in target.checks:
            if chk.expression and not chk.name:
                raise _Manual(f"An unnamed CHECK on {target.name} must be preserved by hand during a rebuild.")
        keep_unsafe = self.db.dialect == "sqlite"
        return (["PRAGMA foreign_keys=OFF", "PRAGMA legacy_alter_table=ON", "BEGIN",
                 render_sqlite_create(target, temp, keep_unsafe_defaults=keep_unsafe),
                 f"INSERT INTO {tq} ({dest_cols}) SELECT {', '.join(common)} FROM {quote(source.name, 'sqlite')}",
                 f"DROP TABLE {quote(source.name, 'sqlite')}",
                 f"ALTER TABLE {tq} RENAME TO {quote(target.name, 'sqlite')}"]
                + render_sqlite_indexes(target) + triggers
                + ["COMMIT", "PRAGMA legacy_alter_table=OFF", "PRAGMA foreign_keys=ON"])

    # --- finalisation --------------------------------------------------------

    def _blocked(self, op: _Op) -> Optional[str]:
        table = op.table
        if table is None:
            return None
        needed: set[str] = set()
        if op.kind in ("set_not_null", "alter_column_type", "rename_column"):
            needed.add(_tok("col", table, (op.column or "").lower()))
        for c in self._columns(op):
            needed.add(_tok("col", table, c.lower()))
        if op.kind == "add_foreign_key":
            ref = self._find(op.params.get("ref_table"))
            if ref is not None:
                cols = [c.lower() for c in names(op.params.get("ref_columns"))]
                options = {_tok("pk", ref), _tok("uq", ref, *cols)}
                if not any(self._token_live(t) for t in options) and options & self.planned:
                    return f"its referenced key on {ref.name} was deferred to a manual step"
                needed |= {_tok("col", ref, c) for c in cols}
        for token in needed:
            creator = self.creators.get(token)
            if creator is not None and creator.manual:
                return f"it depends on {creator.title!r}, which is a manual step"
        return None

    def _token_live(self, token: str) -> bool:
        creator = self.creators.get(token)
        return creator is not None and not creator.manual

    def _blocked_draft(self, op: _Op, reason: str) -> _Draft:
        return _Draft(op=op.kind, title=f"Manual: {op.kind} on {op.table_ref}", table=op.table, column=op.column,
                      finding_ids=list(op.finding_ids), manual=True, manual_description=f"Deferred because {reason}.",
                      creates=self._creates_of(op))

    def _creates_of(self, op: _Op) -> set:
        table = op.table
        out: set = set()
        if table is None:
            return out
        for sub in op.subops:
            out |= self._creates_of(sub)
        cols = [c.lower() for c in self._columns(op)]
        if op.kind == "add_column":
            out.add(_tok("col", table, (op.column or "").lower()))
        elif op.kind in ("add_primary_key", "add_surrogate_primary_key"):
            out.add(_tok("pk", table))
            out.add(_tok("uq", table, *cols))
        elif op.kind == "add_index" and op.params.get("unique"):
            out.add(_tok("uq", table, *cols))
        return out

    def _known_types(self) -> dict[str, str]:
        return {f"{t.name}.{c.name}".lower(): c.data_type for t in self.state.values() for c in t.columns}

    def _finalize(self, draft: _Draft) -> None:
        table_name = draft.table.name if draft.table is not None else None
        hits = detect_destructive("; ".join(draft.up), self.dialect, self._known_types()) if draft.up else []
        destructive = any(h.severity == DESTRUCTIVE for h in hits)
        financial = is_financial_table(table_name, self.patterns)
        if not draft.manual and financial and (destructive or draft.breaking or not draft.reversible):
            kinds = sorted({h.kind for h in hits if h.severity == DESTRUCTIVE}) or (["breaking rename or access change"] if draft.breaking else ["irreversible change"])
            draft.refused_reason = (f"Table {table_name} matches the financial table protection; {', '.join(kinds)} is not "
                                    "generated automatically and needs a separately reviewed change.")
            draft.manual_description = draft.refused_reason + f" Intended change: {draft.title}."
            draft.manual = True
        if draft.manual:
            self._finish_manual(draft)
            for token in draft.creates:
                self.creators[token] = draft
            return
        draft.hits = [h.to_dict() for h in hits]
        draft.destructive = destructive
        if destructive:
            if draft.data_loss_risk == "none":
                draft.data_loss_risk = "medium"
        for op, column, params in draft.effects:
            if draft.table is not None:
                apply_fix_effect(draft.table, op, column, params)
        self.drafts.append(draft)
        for token in draft.creates:
            self.creators[token] = draft

    def _check_status(self, check: Check, table: Optional[Table]) -> None:
        data = self.db.data
        if not self.evaluate or data is None or check.kind != "data":
            return
        if getattr(data, "dialect", self.dialect) != self.dialect:
            return
        limit = getattr(self.profile, "data_sample_limit", 100000) if self.profile is not None else 100000
        if table is not None and table.row_count is not None and table.row_count > limit:
            return
        if not re.match(r"\s*SELECT\b", check.sql, re.I):
            return
        try:
            rows = data.query(check.sql)
        except Exception:
            check.status = "error"
            return
        try:
            check.observed = int(rows[0][0])
            check.status = "passed" if check.observed == check.expected else "failed"
        except (IndexError, TypeError, ValueError):
            check.status = "error"

    def run(self, findings: Sequence[Finding]) -> MigrationPlan:
        ops = self._collect(findings)
        ops = self._resolve(ops)
        ops = self._with_rebuilds(ops)
        ops.sort(key=lambda o: (PHASE.get(o.phase_key, 99), (o.table_ref or "").lower(), (o.column or "").lower(), o.finding_ids[0] if o.finding_ids else ""))
        self._plan_tokens(ops)
        for op in ops:
            self._draft_op(op)
        return self._assemble()

    def _draft_op(self, op: _Op) -> None:
        if op.kind != "rebuild":
            reason = self._blocked(op)
            if reason:
                self._finalize(self._blocked_draft(op, reason))
                return
        try:
            for draft in self._build(op):
                self._finalize(draft)
        except (_Manual, IdentifierError) as exc:
            draft = _Draft(op=op.kind, title=f"Manual: {op.kind} on {op.table_ref or 'database'}", table=op.table, column=op.column,
                           finding_ids=list(op.finding_ids), manual=True, manual_description=str(exc), creates=self._creates_of(op))
            self._finish_manual(draft)
            for token in draft.creates:
                self.creators[token] = draft

    def _assemble(self) -> MigrationPlan:
        ordered = [d for d in self.drafts if not d.manual] + [d for d in self.drafts if d.manual]
        steps: list[MigrationStep] = []
        ids: dict[int, str] = {}
        for pos, draft in enumerate(ordered, start=1):
            ids[id(draft)] = f"M{pos:03d}"
        for pos, draft in enumerate(ordered, start=1):
            depends: list[str] = []
            for token in draft.needs | {t for group in draft.needs_any for t in group}:
                creator = self.creators.get(token)
                if creator is not None and creator is not draft and id(creator) in ids:
                    depends.append(ids[id(creator)])
            for check in draft.pre:
                self._check_status(check, draft.table)
            repair = [c.description for c in draft.pre if c.can_fail and c.status != "passed"]
            destructive = draft.destructive
            backup = destructive or not draft.reversible or draft.data_loss_risk in ("medium", "high")
            if draft.manual:
                backup = False
                destructive = False
            steps.append(MigrationStep(
                id=ids[id(draft)], finding_ids=sorted(set(draft.finding_ids)), title=draft.title, up_sql=draft.up, down_sql=draft.down,
                destructive=destructive, reversible=draft.reversible and not draft.manual, data_loss_risk=draft.data_loss_risk,
                lock_risk=draft.lock_risk, prechecks=draft.pre, postchecks=draft.post, requires_backup=backup,
                online_notes=draft.notes, order=pos, op=draft.op, table=draft.table.fqname if draft.table is not None else None,
                column=draft.column, manual=draft.manual, manual_description=draft.manual_description,
                refused_reason=draft.refused_reason, requires_data_repair=(bool(repair) or bool(draft.repair_notes)) and not draft.manual,
                data_repair_notes=[*draft.repair_notes, *repair] if not draft.manual else [],
                irreversible_reason=draft.irreversible_reason, breaking=draft.breaking, dependency_risks=draft.dependency_risks,
                depends_on=sorted(set(depends)), transactional=draft.transactional, phase_label=draft.phase_label,
                destructive_hits=draft.hits))
        return MigrationPlan(database=self.db.name, source_dialect=self.db.dialect, dialect=self.dialect, steps=steps,
                             notes=self.notes, unaddressed_findings=sorted(self.unaddressed),
                             satisfied_findings=sorted(set(self.satisfied)), backup_recommendation=backup_recommendation(self.dialect))


def generate_plan(db: Database, findings: Sequence[Finding], target_dialect: Optional[str] = None, *, profile: Any = None,
                  financial_patterns: Optional[Sequence[str]] = None, evaluate_prechecks: bool = True) -> MigrationPlan:
    """Build a proposed plan for the findings that carry a fix. Prechecks are read-only and only run through ``db.data``."""
    chosen = target_dialect or db.dialect
    if chosen in (None, "", "generic"):
        chosen = "postgres"
    dialect = normalize_dialect(chosen)
    patterns = financial_patterns_from(profile, financial_patterns)
    return _Planner(db, dialect, patterns, profile, evaluate_prechecks).run(findings)
