"""Shared helpers: identifier quoting and validation, type classification, table rendering and virtual fix effects."""
from __future__ import annotations

import copy
import contextlib
import hashlib
import logging
import re
from typing import Any, Optional

import sqlglot
from sqlglot import exp

from ..model import CheckConstraint, Column, Database, ForeignKey, Index, Table, parse_type

DIALECTS = ("postgres", "mysql", "sqlite")
IDENT_LIMITS = {"postgres": 63, "mysql": 64, "sqlite": 128}
_DIALECT_ALIASES = {"postgresql": "postgres", "pg": "postgres", "postgres": "postgres", "mysql": "mysql",
                    "mariadb": "mysql", "sqlite": "sqlite", "sqlite3": "sqlite"}


@contextlib.contextmanager
def quiet_sqlglot():
    """Silence the 'falling back to Command' warning, which is expected for engine-specific DDL."""
    logger = logging.getLogger("sqlglot")
    previous = logger.level
    logger.setLevel(logging.ERROR)
    try:
        yield
    finally:
        logger.setLevel(previous)


class IdentifierError(ValueError):
    """An identifier, type or expression cannot be used safely in generated SQL."""


def normalize_dialect(dialect: Optional[str]) -> str:
    key = (dialect or "").strip().lower()
    if key in _DIALECT_ALIASES:
        return _DIALECT_ALIASES[key]
    raise ValueError(f"Unsupported migration dialect: {dialect!r}. Supported: {', '.join(DIALECTS)}")


def validate_identifier(name: Any, dialect: str) -> str:
    if not isinstance(name, str) or not name:
        raise IdentifierError(f"Identifier must be a non-empty string, got {name!r}")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in name):
        raise IdentifierError(f"Identifier contains a control character: {name!r}")
    limit = IDENT_LIMITS[dialect]
    if len(name.encode("utf-8")) > limit:
        raise IdentifierError(f"Identifier exceeds the {dialect} limit of {limit} bytes: {name!r}")
    if dialect == "mysql" and name.endswith(" "):
        raise IdentifierError(f"MySQL identifiers cannot end with a space: {name!r}")
    return name


def quote(name: str, dialect: str) -> str:
    validate_identifier(name, dialect)
    if dialect == "mysql":
        return "`" + name.replace("`", "``") + "`"
    return '"' + name.replace('"', '""') + '"'


def qualified(table: Table, dialect: str, name: Optional[str] = None) -> str:
    base = quote(name or table.name, dialect)
    if table.schema and not (dialect == "sqlite" and table.schema.lower() == "main"):
        if dialect == "sqlite":
            raise IdentifierError(f"SQLite target cannot address schema {table.schema!r}")
        return f"{quote(table.schema, dialect)}.{base}"
    return base


def literal(value: Any, dialect: str) -> str:
    text = str(value)
    if "\x00" in text:
        raise IdentifierError("String literal contains a NUL character")
    text = text.replace("'", "''")
    if dialect == "mysql":
        text = text.replace("\\", "\\\\")
    return f"'{text}'"


def columns_sql(columns: list[str], dialect: str) -> str:
    return ", ".join(quote(c, dialect) for c in columns)


def make_name(prefix: str, table: str, columns: list[str], dialect: str) -> str:
    raw = "_".join([prefix, table.split(".")[-1], *columns])
    raw = re.sub(r"[^0-9a-zA-Z_]+", "_", raw).strip("_").lower() or prefix
    limit = min(IDENT_LIMITS[dialect], 63)
    if len(raw) <= limit:
        return raw
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:8]
    return f"{raw[:limit - 9].rstrip('_')}_{digest}"


_TYPE_OK = re.compile(r"^[A-Za-z][A-Za-z0-9_ ]{0,60}"
                      r"(\(\s*(\d+(\s*,\s*\d+)?|'(?:[^'\\]|'')*'(\s*,\s*'(?:[^'\\]|'')*')*)\s*\))?"
                      r"( ?[A-Za-z ]{0,40})?(\[\])?$")


def validate_type(type_name: Any) -> str:
    if not isinstance(type_name, str) or not _TYPE_OK.match(type_name.strip()):
        raise IdentifierError(f"Unsafe or invalid SQL type: {type_name!r}")
    return type_name.strip()


_LITERAL_DEFAULT = re.compile(r"^(?:[+-]?\d+(?:\.\d+)?|'(?:[^']|'')*'|NULL|TRUE|FALSE)$", re.I)
_FUNC_DEFAULT = re.compile(r"^(?:CURRENT_TIMESTAMP|CURRENT_DATE|CURRENT_TIME|LOCALTIMESTAMP|NOW|GEN_RANDOM_UUID|UUID|"
                           r"UTC_TIMESTAMP)(?:\s*\(\s*\d*\s*\))?$", re.I)


def is_literal_default(value: str) -> bool:
    return bool(_LITERAL_DEFAULT.match(value.strip()))


def render_default(value: Any, dialect: str) -> str:
    """Render a default from a finding. Anything that is not a recognised literal or function becomes a string."""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return repr(value)
    text = str(value).strip()
    if _LITERAL_DEFAULT.match(text) or _FUNC_DEFAULT.match(text):
        return text
    return literal(text, dialect)


_SQLITE_NEUTRAL_DEFAULT = re.compile(r"^(?:CURRENT_TIMESTAMP|CURRENT_DATE|CURRENT_TIME)$", re.I)


def is_sqlite_constant_default(value: Optional[str]) -> bool:
    """SQLite ADD COLUMN accepts only constant defaults, so CURRENT_* and function calls need a rebuild."""
    return value is None or bool(_LITERAL_DEFAULT.match(str(value).strip()))


_SOURCE_READ = {"postgres": "postgres", "mysql": "mysql", "sqlite": "sqlite"}


def render_expression(expression: Any, dialect: str, read: Optional[str] = None) -> str:
    """Validate a CHECK or policy expression and re-render it. Multiple statements and subqueries are rejected."""
    text = str(expression or "").strip()
    if not text:
        raise IdentifierError("Empty expression")
    try:
        with quiet_sqlglot():
            parsed = sqlglot.parse(text, read=_SOURCE_READ.get(read or "", None))
    except Exception as exc:
        raise IdentifierError(f"Expression could not be parsed: {text!r}: {exc}") from exc
    if len(parsed) != 1 or parsed[0] is None:
        raise IdentifierError(f"Expression must be a single expression: {text!r}")
    node = parsed[0]
    if isinstance(node, (exp.DDL, exp.DML, exp.Drop, exp.Command, exp.Select, exp.Alter)):
        raise IdentifierError(f"Expression must not be a statement: {text!r}")
    if any(True for _ in node.find_all(exp.Subquery, exp.Select)):
        raise IdentifierError(f"Expression must not contain a subquery: {text!r}")
    return node.sql(dialect=_SOURCE_READ[dialect])


_NORMAL_RE = re.compile(r"\s+")


def _norm_type(raw: str) -> str:
    return _NORMAL_RE.sub(" ", (raw or "").strip().lower())


def type_change_kind(old: str, new: str, dialect: str) -> str:
    """Return same, binary_compatible, widening or narrowing. Anything not proven safe counts as narrowing."""
    if _norm_type(old) == _norm_type(new):
        return "same"
    a, b = parse_type(old), parse_type(new)
    if a == b and a.family != "other":
        return "same"
    if a.family == b.family:
        fam = a.family
        if fam == "int":
            if (b.bits or 0) > (a.bits or 0):
                return "widening"
            return "narrowing" if (b.bits or 0) < (a.bits or 0) else "same"
        if fam in ("text", "char"):
            if b.length is None and a.length is None:
                return "binary_compatible" if dialect == "postgres" else "widening"
            if b.length is None:
                if dialect == "postgres" and fam == "text":
                    return "binary_compatible"
                return "widening"
            if a.length is None:
                return "narrowing"
            if b.length < a.length:
                return "narrowing"
            if b.length == a.length:
                return "same"
            if fam == "text" and dialect == "mysql" and (a.length <= 63) != (b.length <= 63):
                return "widening"  # the InnoDB length prefix changes, so it cannot be done in place
            return "binary_compatible" if fam == "text" else "widening"
        if fam == "decimal":
            if a.precision is None:
                return "narrowing" if b.precision is not None else "same"
            if b.precision is None:
                return "widening"
            a_int, b_int = a.precision - (a.scale or 0), b.precision - (b.scale or 0)
            if b_int < a_int or (b.scale or 0) < (a.scale or 0):
                return "narrowing"
            if (b.scale or 0) == (a.scale or 0) and b.precision > a.precision:
                return "binary_compatible" if dialect == "postgres" else "widening"
            return "widening" if b.precision >= a.precision else "narrowing"
        if fam == "float":
            size = {"real": 4, "float4": 4, "float": 8, "double": 8, "double precision": 8, "float8": 8}
            sa, sb = size.get(_norm_type(old), 8), size.get(_norm_type(new), 8)
            return "widening" if sb > sa else ("same" if sa == sb else "narrowing")
        return "narrowing"
    safe = {("int", "decimal"), ("int", "float"), ("int", "text"), ("decimal", "text"), ("char", "text"),
            ("uuid", "text"), ("date", "datetime"), ("date", "timestamptz"), ("datetime", "timestamptz"),
            ("json", "text"), ("bool", "int"), ("date", "text"), ("datetime", "text"), ("enum", "text")}
    if (a.family, b.family) in safe:
        if b.family == "text" and b.length is not None:
            return "narrowing"
        if b.family == "decimal" and a.family == "int":
            digits = {8: 3, 16: 5, 24: 8, 32: 10, 64: 19}.get(a.bits or 32, 19)
            if b.precision is not None and b.precision - (b.scale or 0) < digits:
                return "narrowing"
        return "widening"
    return "narrowing"


def sqlite_type(raw: str) -> str:
    """Map a source type to a name SQLite accepts while keeping the original spelling where possible."""
    text = (raw or "").strip()
    if re.match(r"^[A-Za-z][A-Za-z0-9_ ]*(\s*\(\s*\d+(\s*,\s*\d+)?\s*\))?( [A-Za-z ]+)?$", text):
        return text
    fam = parse_type(text).family
    return {"int": "INTEGER", "decimal": "NUMERIC", "float": "REAL", "money": "NUMERIC", "binary": "BLOB",
            "bool": "INTEGER"}.get(fam, "TEXT")


def _sqlite_default(raw: str) -> str:
    text = raw.strip()
    if _LITERAL_DEFAULT.match(text) or _SQLITE_NEUTRAL_DEFAULT.match(text):
        return text
    return f"({text})"


def is_autoincrement_pk(table: Table, col: Column) -> bool:
    return (col.is_identity and table.primary_key == [col.name]
            and parse_type(col.data_type).family == "int")


def render_sqlite_create(table: Table, name: Optional[str] = None, keep_unsafe_defaults: bool = True) -> str:
    """CREATE TABLE text for SQLite. Column order and constraints follow the model."""
    lines: list[str] = []
    target = name or table.name
    for col in table.columns:
        if is_autoincrement_pk(table, col):
            lines.append(f"{quote(col.name, 'sqlite')} INTEGER PRIMARY KEY AUTOINCREMENT")
            continue
        part = f"{quote(col.name, 'sqlite')} {sqlite_type(col.data_type)}"
        if not col.nullable:
            part += " NOT NULL"
        if col.default is not None:
            default = col.default.strip()
            if is_literal_default(default) or _SQLITE_NEUTRAL_DEFAULT.match(default) or keep_unsafe_defaults:
                part += f" DEFAULT {_sqlite_default(default)}"
        lines.append(part)
    has_auto = any(is_autoincrement_pk(table, c) for c in table.columns)
    if table.primary_key and not has_auto:
        lines.append(f"PRIMARY KEY ({columns_sql(table.primary_key, 'sqlite')})")
    for idx in table.indexes:
        if idx.unique and not idx.primary and _is_inline_unique(idx):
            lines.append(f"UNIQUE ({columns_sql(idx.columns, 'sqlite')})")
    for fk in table.foreign_keys:
        clause = f"FOREIGN KEY ({columns_sql(fk.columns, 'sqlite')}) REFERENCES {quote(fk.ref_table, 'sqlite')} ({columns_sql(fk.ref_columns, 'sqlite')})"
        if fk.on_delete:
            clause += f" ON DELETE {fk.on_delete}"
        if fk.on_update:
            clause += f" ON UPDATE {fk.on_update}"
        if fk.name:
            clause = f"CONSTRAINT {quote(fk.name, 'sqlite')} {clause}"
        lines.append(clause)
    for chk in table.checks:
        clause = f"CHECK ({chk.expression})"
        if chk.name:
            clause = f"CONSTRAINT {quote(chk.name, 'sqlite')} {clause}"
        lines.append(clause)
    body = ",\n  ".join(lines)
    return f"CREATE TABLE {quote(target, 'sqlite')} (\n  {body}\n)"


def _is_inline_unique(idx: Index) -> bool:
    return idx.is_constraint or not idx.name or idx.name.startswith("sqlite_autoindex")


def render_sqlite_indexes(table: Table, name: Optional[str] = None) -> list[str]:
    out: list[str] = []
    target = name or table.name
    for idx in table.indexes:
        if idx.primary or (idx.unique and _is_inline_unique(idx)) or not idx.name:
            continue
        unique = "UNIQUE " if idx.unique else ""
        sql = f"CREATE {unique}INDEX {quote(idx.name, 'sqlite')} ON {quote(target, 'sqlite')} ({columns_sql(idx.columns, 'sqlite')})"
        if idx.where:
            sql += f" WHERE {idx.where}"
        out.append(sql)
    return out


def apply_fix_effect(table: Table, op: str, column: Optional[str], params: dict[str, Any]) -> None:
    """Change an in-memory table the way a fix would change the real one. Used for rebuilds and before/after text."""
    if op == "add_column":
        table.columns.append(Column(column or "", str(params.get("type", "text")), bool(params.get("nullable", True)),
                                    None if params.get("default") is None else str(params.get("default"))))
    elif op == "add_primary_key":
        cols = _names(params.get("columns")) or ([column] if column else [])
        table.primary_key = list(cols)
        for name in cols:
            found = table.column(name)
            if found:
                found.nullable = False
    elif op == "add_surrogate_primary_key":
        name = params.get("column") or column or "id"
        table.columns.insert(0, Column(name, str(params.get("type", "bigint")), False, is_identity=True))
        table.primary_key = [name]
    elif op == "add_foreign_key":
        table.foreign_keys.append(ForeignKey(params.get("name"), _names(params.get("columns")) or [column or ""],
                                             params.get("ref_table", ""), _names(params.get("ref_columns")),
                                             on_delete=params.get("on_delete"), on_update=params.get("on_update")))
    elif op == "add_index":
        table.indexes.append(Index(params.get("name"), _names(params.get("columns")) or [column or ""],
                                   bool(params.get("unique", False))))
    elif op == "drop_index":
        wanted = str(params.get("name", "")).lower()
        table.indexes = [i for i in table.indexes if (i.name or "").lower() != wanted]
    elif op == "alter_column_type":
        found = table.column(column or "")
        if found:
            found.data_type = str(params.get("new_type"))
    elif op == "set_not_null":
        found = table.column(column or "")
        if found:
            found.nullable = False
    elif op == "add_check":
        table.checks.append(CheckConstraint(params.get("name"), str(params.get("expression", ""))))
    elif op == "rename_column":
        _rename_col(table, column or "", str(params.get("new_name", "")))
    elif op == "rename_table":
        table.name = str(params.get("new_name", table.name))
    elif op == "enable_rls":
        table.rls_enabled = True


def _rename_col(table: Table, old: str, new: str) -> None:
    low = old.lower()
    swap = lambda names: [new if n.lower() == low else n for n in names]  # noqa: E731
    found = table.column(old)
    if found:
        found.name = new
    table.primary_key = swap(table.primary_key)
    for idx in table.indexes:
        idx.columns = swap(idx.columns)
    for fk in table.foreign_keys:
        fk.columns = swap(fk.columns)


def _names(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return [str(v) for v in value]


def names(value: Any) -> list[str]:
    return _names(value)


def clone_tables(db: Database) -> list[Table]:
    return copy.deepcopy(db.tables)


def _fmt_col(col: Column, table: Table) -> str:
    parts = [col.name, col.data_type]
    if not col.nullable:
        parts.append("NOT NULL")
    if col.is_identity:
        parts.append("IDENTITY")
    if col.default is not None:
        parts.append(f"DEFAULT {col.default}")
    return " ".join(parts)


def render_table_ddl(table: Table) -> str:
    """Readable, DDL-like text for a table. Used for before and after comparisons, not intended to be executed."""
    lines = [_fmt_col(c, table) for c in table.columns]
    if table.primary_key:
        lines.append(f"PRIMARY KEY ({', '.join(table.primary_key)})")
    for fk in table.foreign_keys:
        line = f"FOREIGN KEY ({', '.join(fk.columns)}) REFERENCES {fk.ref_table} ({', '.join(fk.ref_columns)})"
        if fk.on_delete:
            line += f" ON DELETE {fk.on_delete}"
        lines.append(line)
    for chk in table.checks:
        lines.append(f"CHECK ({chk.expression})" + (f" -- {chk.name}" if chk.name else ""))
    body = ",\n  ".join(lines)
    text = f"TABLE {table.fqname} (\n  {body}\n)"
    extra = []
    for idx in table.indexes:
        if idx.primary:
            continue
        unique = "UNIQUE " if idx.unique else ""
        extra.append(f"{unique}INDEX {idx.name or '(unnamed)'} ON {table.name} ({', '.join(idx.columns)})")
    if table.rls_enabled:
        extra.append(f"ROW LEVEL SECURITY ENABLED ON {table.name}")
    return "\n".join([text, *extra])
