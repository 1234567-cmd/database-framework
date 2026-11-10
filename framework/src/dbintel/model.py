"""Engine-independent description of a database. Connectors and importers produce it; analyzers read it."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional, Protocol, Sequence

FAMILIES = {"int", "decimal", "float", "money", "text", "char", "bool", "date", "datetime", "timestamptz",
            "time", "json", "uuid", "binary", "enum", "other"}

_INT_BITS = {"tinyint": 8, "int1": 8, "smallint": 16, "int2": 16, "smallserial": 16, "mediumint": 24, "int": 32,
             "integer": 32, "int4": 32, "serial": 32, "bigint": 64, "int8": 64, "bigserial": 64}
_FAMILY = {
    "decimal": "decimal", "numeric": "decimal", "dec": "decimal", "number": "decimal", "fixed": "decimal",
    "float": "float", "real": "float", "double": "float", "double precision": "float", "float4": "float",
    "float8": "float", "money": "money", "smallmoney": "money",
    "varchar": "text", "character varying": "text", "nvarchar": "text", "text": "text", "tinytext": "text",
    "mediumtext": "text", "longtext": "text", "clob": "text", "varchar2": "text", "nvarchar2": "text", "citext": "text",
    "char": "char", "character": "char", "bpchar": "char", "nchar": "char",
    "bool": "bool", "boolean": "bool", "bit": "bool",
    "date": "date", "datetime": "datetime", "datetime2": "datetime", "timestamp": "datetime",
    "timestamp without time zone": "datetime", "timestamptz": "timestamptz", "timestamp with time zone": "timestamptz",
    "datetimeoffset": "timestamptz", "time": "time", "time without time zone": "time", "time with time zone": "time",
    "json": "json", "jsonb": "json", "uuid": "uuid", "uniqueidentifier": "uuid",
    "blob": "binary", "tinyblob": "binary", "mediumblob": "binary", "longblob": "binary", "bytea": "binary",
    "binary": "binary", "varbinary": "binary", "enum": "enum", "set": "enum",
}


@dataclass(frozen=True)
class TypeInfo:
    family: str
    bits: Optional[int] = None
    length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None
    values: tuple = ()


def parse_type(raw: str) -> TypeInfo:
    """Classify a raw SQL type string, for example ``decimal(12,2)`` or ``int unsigned``."""
    text = (raw or "").strip().lower()
    if not text:
        return TypeInfo("other")
    open_paren, close_paren = text.find("("), text.rfind(")")
    if open_paren >= 0 and close_paren > open_paren:
        base, args, suffix = text[:open_paren].strip(), text[open_paren + 1:close_paren], text[close_paren + 1:].strip()
    else:
        base, args, suffix = text, None, ""
    base = " ".join(base.split())
    suffix = " ".join(suffix.split())
    base = re.sub(r"(\s+(unsigned|signed|zerofill))+$", "", base).strip()
    if base in ("timestamp", "time") and suffix.startswith("with"):  # timestamp(3) with time zone
        base = f"{base} {suffix}"
    if base in _INT_BITS:
        if base == "tinyint" and (args or "").strip() == "1":
            return TypeInfo("bool", bits=8)
        return TypeInfo("int", bits=_INT_BITS[base])
    family = _FAMILY.get(base, "other")
    if family == "enum":
        return TypeInfo("enum", values=tuple(re.findall(r"'([^']*)'", args or "")))
    if base == "bit" and args and args.strip() != "1":
        family = "binary"
    nums = [int(a) for a in re.findall(r"\d+", args or "")]
    if family == "decimal":
        return TypeInfo("decimal", precision=nums[0] if nums else None,
                        scale=nums[1] if len(nums) > 1 else (0 if nums else None))
    return TypeInfo(family, length=nums[0] if nums else None)


@dataclass
class Column:
    name: str
    data_type: str
    nullable: bool = True
    default: Optional[str] = None
    is_identity: bool = False
    is_generated: bool = False
    comment: Optional[str] = None
    charset: Optional[str] = None
    collation: Optional[str] = None
    ordinal: int = 0

    @property
    def type(self) -> TypeInfo:
        return parse_type(self.data_type)


@dataclass
class Index:
    name: Optional[str]
    columns: list[str]
    unique: bool = False
    primary: bool = False
    method: Optional[str] = None
    where: Optional[str] = None
    include: list[str] = field(default_factory=list)
    is_constraint: bool = False


@dataclass
class ForeignKey:
    name: Optional[str]
    columns: list[str]
    ref_table: str
    ref_columns: list[str]
    ref_schema: Optional[str] = None
    on_delete: Optional[str] = None
    on_update: Optional[str] = None


@dataclass
class CheckConstraint:
    name: Optional[str]
    expression: str
    columns: list[str] = field(default_factory=list)


@dataclass
class Table:
    name: str
    schema: Optional[str] = None
    columns: list[Column] = field(default_factory=list)
    primary_key: list[str] = field(default_factory=list)
    primary_key_name: Optional[str] = None
    indexes: list[Index] = field(default_factory=list)
    foreign_keys: list[ForeignKey] = field(default_factory=list)
    checks: list[CheckConstraint] = field(default_factory=list)
    comment: Optional[str] = None
    engine: Optional[str] = None
    charset: Optional[str] = None
    collation: Optional[str] = None
    row_count: Optional[int] = None
    partition_columns: list[str] = field(default_factory=list)
    rls_enabled: Optional[bool] = None

    @property
    def fqname(self) -> str:
        return f"{self.schema}.{self.name}" if self.schema else self.name

    def column(self, name: str) -> Optional[Column]:
        low = name.lower()
        return next((c for c in self.columns if c.name.lower() == low), None)

    def has_column(self, name: str) -> bool:
        return self.column(name) is not None

    def unique_keys(self) -> list[list[str]]:
        keys = [self.primary_key] if self.primary_key else []
        keys += [i.columns for i in self.indexes if i.unique and not i.where]
        return keys

    def index_leading(self, columns: Sequence[str]) -> bool:
        """True if the primary key or some index starts with exactly these columns, in any order."""
        want = {c.lower() for c in columns}
        keys = [self.primary_key] + [i.columns for i in self.indexes]
        return any(len(k) >= len(want) and {c.lower() for c in k[: len(want)]} == want for k in keys if k)


@dataclass
class View:
    name: str
    definition: str = ""
    schema: Optional[str] = None
    references: list[str] = field(default_factory=list)
    materialized: bool = False

    @property
    def fqname(self) -> str:
        return f"{self.schema}.{self.name}" if self.schema else self.name


@dataclass
class Routine:
    name: str
    kind: str = "procedure"  # procedure | function | trigger
    definition: str = ""
    table: Optional[str] = None
    schema: Optional[str] = None
    references: list[str] = field(default_factory=list)


@dataclass
class Role:
    name: str
    superuser: bool = False
    can_login: bool = True
    bypass_rls: bool = False
    host: Optional[str] = None
    password_set: Optional[bool] = None


@dataclass
class Grant:
    grantee: str
    privilege: str
    table: Optional[str] = None  # None is database or global scope; "*" is all tables
    schema: Optional[str] = None
    column: Optional[str] = None
    grantable: bool = False


@dataclass
class RlsPolicy:
    table: str
    name: str
    expression: str = ""
    command: str = "ALL"
    roles: list[str] = field(default_factory=list)
    schema: Optional[str] = None


@dataclass
class QueryStat:
    sql: str
    calls: int = 1
    total_ms: float = 0.0
    mean_ms: float = 0.0
    rows: Optional[int] = None
    plan: Optional[str] = None  # engine EXPLAIN text or JSON, when available


@dataclass
class PipelineStep:
    name: str
    kind: str = "sql"  # sql | extract | load | transform
    sql: str = ""
    sources: list[str] = field(default_factory=list)
    targets: list[str] = field(default_factory=list)
    write_mode: str = ""  # append | overwrite | merge | ""
    merge_keys: list[str] = field(default_factory=list)
    incremental_column: Optional[str] = None


@dataclass
class PipelineJob:
    name: str
    steps: list[PipelineStep] = field(default_factory=list)
    schedule: Optional[str] = None
    owner: Optional[str] = None
    retries: Optional[int] = None
    idempotent: Optional[bool] = None
    records_run_metadata: Optional[bool] = None
    emits_lineage: Optional[bool] = None
    quality_checks: list[str] = field(default_factory=list)
    source_file: Optional[str] = None


class DataAccess(Protocol):
    """Read-only access to row data. Analyzers must use only this to reach data."""
    dialect: str

    def query(self, sql: str, params: Sequence[Any] = ()) -> list[tuple]: ...

    def quote(self, identifier: str) -> str: ...


@dataclass
class Database:
    name: str
    dialect: str = "generic"  # postgres | mysql | sqlite | generic
    source: str = ""  # live | sql_dump | csv | excel | metadata
    tables: list[Table] = field(default_factory=list)
    views: list[View] = field(default_factory=list)
    routines: list[Routine] = field(default_factory=list)
    roles: list[Role] = field(default_factory=list)
    grants: list[Grant] = field(default_factory=list)
    policies: list[RlsPolicy] = field(default_factory=list)
    query_stats: list[QueryStat] = field(default_factory=list)
    pipelines: list[PipelineJob] = field(default_factory=list)
    settings: dict[str, Any] = field(default_factory=dict)
    data: Optional[DataAccess] = None
    security_metadata: bool = False  # True when roles and grants were actually collected
    import_warnings: list[str] = field(default_factory=list)

    def table(self, name: str, schema: Optional[str] = None) -> Optional[Table]:
        low = name.lower()
        for t in self.tables:
            if t.name.lower() == low and (schema is None or (t.schema or "").lower() == schema.lower()):
                return t
        return None

    def referencing(self, table: Table) -> list[tuple[Table, ForeignKey]]:
        low = table.name.lower()
        return [(t, fk) for t in self.tables for fk in t.foreign_keys if fk.ref_table.lower() == low]
