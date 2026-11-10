"""Test a proposed plan in isolation. The only write target is a temporary SQLite file created here, or a scratch
server the caller has explicitly allow-listed. The source database and its connector are only ever read."""
from __future__ import annotations

import os
import re
import shutil
import sqlite3
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional, Sequence
from urllib.parse import unquote, urlsplit

from ..model import Database
from ._sql import normalize_dialect, render_sqlite_create, render_sqlite_indexes
from .generator import Check, MigrationPlan, MigrationStep
from .safety import require_approval

SANDBOX_DB_PREFIX = "dbintel_sandbox_"
SQLITE_DENY = 1
SQLITE_OK = 0
SQLITE_ATTACH = 24
SQLITE_DETACH = 25

# Text that cannot run on SQLite; the tested SQL must be what would actually run, so such a step is not translated.
_NOT_SQLITE = [(re.compile(p, re.I), why) for p, why in [
    (r"\bCONCURRENTLY\b", "CREATE/DROP INDEX CONCURRENTLY is PostgreSQL-only"),
    (r"\bNOT\s+VALID\b", "NOT VALID constraints are PostgreSQL-only"),
    (r"\bVALIDATE\s+CONSTRAINT\b", "VALIDATE CONSTRAINT is PostgreSQL-only"),
    (r"\bUSING\s+INDEX\b", "ADD CONSTRAINT USING INDEX is PostgreSQL-only"),
    (r"\bALTER\s+COLUMN\b", "ALTER COLUMN is not supported by SQLite"),
    (r"\bROW\s+LEVEL\s+SECURITY\b|\bCREATE\s+POLICY\b", "row level security is PostgreSQL-only"),
    (r"\bALGORITHM\s*=|\bLOCK\s*=", "ALGORITHM and LOCK clauses are MySQL-only"),
    (r"\bMODIFY\s+COLUMN\b", "MODIFY COLUMN is MySQL-only"),
    (r"\bADD\s+CONSTRAINT\b|\bDROP\s+CONSTRAINT\b|\bDROP\s+PRIMARY\s+KEY\b", "constraint changes need a table rebuild on SQLite"),
    (r"\b(?:REVOKE|GRANT)\b", "SQLite has no grants"),
    (r"^\s*SET\b", "session SET statements are not valid on SQLite"),
    (r"\binformation_schema\b|\bpg_(?:indexes|class|policies|namespace)\b", "catalog queries use another engine"),
    (r"\bRENAME\s+TABLE\b", "RENAME TABLE is MySQL-only"),
]]


class SandboxRefused(PermissionError):
    """The requested target is not an allowed sandbox."""


@dataclass
class StepResult:
    step_id: str
    title: str
    status: str  # passed | failed | not_testable
    reason: str = ""
    engine: str = ""
    up_applied: bool = False
    postchecks: str = "not_run"  # passed | failed | not_run
    rollback: str = "not_tested"  # passed | failed | not_tested | not_available
    schema_restored: Optional[bool] = None
    rows_preserved: Optional[bool] = None


@dataclass
class SandboxReport:
    plan_hash: str
    engine: str
    isolated: bool
    results: list[StepResult] = field(default_factory=list)
    schema_restored: Optional[bool] = None
    schema_restored_reason: str = ""
    warnings: list[str] = field(default_factory=list)

    @property
    def overall(self) -> str:
        statuses = {r.status for r in self.results}
        if "failed" in statuses:
            return "failed"
        if not statuses or statuses == {"not_testable"}:
            return "not_testable"
        return "partial" if "not_testable" in statuses else "passed"

    def by_step(self, step_id: str) -> StepResult:
        return next(r for r in self.results if r.step_id == step_id)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["overall"] = self.overall
        return data


def _normal(text: Optional[str]) -> str:
    return re.sub(r"\s+", "", (text or "").lower())


def _sqlite_checks(sql: Optional[str]) -> list[str]:
    """Extract CHECK clause bodies from CREATE TABLE text, comparing them regardless of formatting."""
    text = sql or ""
    out: list[str] = []
    for m in re.finditer(r"\bCHECK\s*\(", text, re.I):
        depth, i, quote_char = 1, m.end(), ""
        while i < len(text) and depth:
            ch = text[i]
            if quote_char:
                if ch == quote_char:
                    quote_char = ""
            elif ch in "'\"":
                quote_char = ch
            elif ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            i += 1
        out.append(_normal(text[m.end():i - 1]))
    return sorted(out)


class _Engine:
    name = ""

    def execute(self, sql: str) -> None:
        raise NotImplementedError

    def scalar(self, sql: str) -> Any:
        raise NotImplementedError

    def snapshot(self) -> dict:
        raise NotImplementedError

    def counts(self) -> dict:
        raise NotImplementedError

    def close(self) -> None:
        pass


class _SqliteEngine(_Engine):
    name = "sqlite-temp-copy"

    def __init__(self) -> None:
        self.dir = tempfile.mkdtemp(prefix="dbintel_sandbox_")
        self.conn = sqlite3.connect(str(Path(self.dir) / "sandbox.db"), isolation_level=None)
        self.conn.set_authorizer(self._authorize)

    @staticmethod
    def _authorize(action, arg1, arg2, dbname, source):
        return SQLITE_DENY if action in (SQLITE_ATTACH, SQLITE_DETACH) else SQLITE_OK

    def execute(self, sql: str) -> None:
        self.conn.execute(sql)

    def rollback_if_needed(self) -> None:
        if self.conn.in_transaction:
            self.conn.execute("ROLLBACK")

    def scalar(self, sql: str) -> Any:
        row = self.conn.execute(sql).fetchone()
        return row[0] if row else None

    def snapshot(self) -> dict:
        snap: dict[str, Any] = {}
        rows = self.conn.execute("SELECT type, name, tbl_name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name").fetchall()
        for kind, name, _, sql in rows:
            if kind == "table":
                columns = [tuple(r[1:]) for r in self.conn.execute(f'PRAGMA table_info("{name}")').fetchall()]
                columns = [(c[0], (c[1] or "").lower(), c[2], _normal(c[3]), c[4]) for c in columns]
                indexes = []
                for idx in self.conn.execute(f'PRAGMA index_list("{name}")').fetchall():
                    cols = tuple(r[2] for r in self.conn.execute(f'PRAGMA index_info("{idx[1]}")').fetchall())
                    label = "" if str(idx[1]).startswith("sqlite_autoindex") else idx[1]
                    indexes.append((label, idx[2], idx[3], cols))
                fks = sorted((r[2], r[3], r[4], r[5], r[6]) for r in self.conn.execute(f'PRAGMA foreign_key_list("{name}")').fetchall())
                snap[f"table:{name}"] = {"columns": columns, "indexes": sorted(indexes, key=str), "fks": fks, "checks": _sqlite_checks(sql)}
            elif kind in ("view", "trigger"):
                snap[f"{kind}:{name}"] = _normal(sql)
        return snap

    def counts(self) -> dict:
        names = [r[0] for r in self.conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()]
        return {n: self.conn.execute(f'SELECT COUNT(*) FROM "{n}"').fetchone()[0] for n in names}

    def close(self) -> None:
        self.conn.close()
        shutil.rmtree(self.dir, ignore_errors=True)


class _ScratchEngine(_Engine):
    """A user-owned scratch server. Only reachable through the allow-list checks in ``test_plan_in_sandbox``."""

    def __init__(self, conn: Any, dialect: str) -> None:
        self.conn = conn
        self.dialect = dialect
        self.name = f"{dialect}-scratch"

    def _rows(self, sql: str) -> list[tuple]:
        cur = self.conn.cursor()
        cur.execute(sql)
        try:
            return [tuple(r) for r in cur.fetchall()]
        except Exception:
            return []

    def execute(self, sql: str) -> None:
        self.conn.cursor().execute(sql)

    def rollback_if_needed(self) -> None:
        pass

    def scalar(self, sql: str) -> Any:
        rows = self._rows(sql)
        return rows[0][0] if rows else None

    def _schema_clause(self, column: str) -> str:
        return f"{column} = current_schema()" if self.dialect == "postgres" else f"{column} = DATABASE()"

    def snapshot(self) -> dict:
        snap: dict[str, Any] = {}
        where = self._schema_clause("table_schema")
        for row in self._rows(f"SELECT table_name, column_name, data_type, is_nullable, column_default FROM information_schema.columns WHERE {where} ORDER BY 1, 2"):
            snap.setdefault(f"table:{row[0]}", {"columns": [], "constraints": [], "indexes": []})["columns"].append(tuple(row[1:]))
        for row in self._rows(f"SELECT table_name, constraint_name, constraint_type FROM information_schema.table_constraints WHERE {where} ORDER BY 1, 2"):
            snap.setdefault(f"table:{row[0]}", {"columns": [], "constraints": [], "indexes": []})["constraints"].append(tuple(row[1:]))
        if self.dialect == "postgres":
            sql = f"SELECT tablename, indexname, indexdef FROM pg_indexes WHERE {self._schema_clause('schemaname')} ORDER BY 1, 2"
        else:
            sql = f"SELECT table_name, index_name, GROUP_CONCAT(column_name ORDER BY seq_in_index) FROM information_schema.statistics WHERE {where} GROUP BY 1, 2 ORDER BY 1, 2"
        for row in self._rows(sql):
            snap.setdefault(f"table:{row[0]}", {"columns": [], "constraints": [], "indexes": []})["indexes"].append(tuple(row[1:]))
        return snap

    def counts(self) -> dict:
        return {}

    def close(self) -> None:
        self.conn.close()


def _portability_problem(step: MigrationStep, engine: _SqliteEngine) -> Optional[str]:
    for statement in step.up_sql + step.down_sql + [c.sql for c in step.prechecks + step.postchecks]:
        for pattern, why in _NOT_SQLITE:
            if pattern.search(statement):
                return f"{why}; not executed on SQLite: {statement[:100]}"
    return None


def _build_from_model(engine: _SqliteEngine, db: Database, sample_limit: int, warnings: list[str]) -> None:
    engine.execute("PRAGMA foreign_keys=OFF")
    keep_unsafe = db.dialect == "sqlite"
    for table in db.tables:
        engine.execute(render_sqlite_create(table, keep_unsafe_defaults=keep_unsafe))
        for sql in render_sqlite_indexes(table):
            try:
                engine.execute(sql)
            except sqlite3.Error as exc:
                warnings.append(f"Index on {table.name} was not built: {exc}")
        if not keep_unsafe and any(c.default and not re.match(r"^(?:[-\d.]+|'.*'|NULL|TRUE|FALSE)$", c.default.strip(), re.I) for c in table.columns):
            warnings.append(f"Non-portable default values on {table.name} were omitted from the SQLite copy.")
    if db.dialect == "sqlite":
        for view in db.views:
            if view.definition and re.match(r"\s*CREATE\b", view.definition, re.I):
                _try(engine, view.definition, f"View {view.name}", warnings)
        for routine in db.routines:
            if routine.kind == "trigger" and routine.definition:
                _try(engine, routine.definition, f"Trigger {routine.name}", warnings)
    elif db.views or db.routines:
        warnings.append("Views and routines from a non-SQLite source are not recreated in the SQLite copy.")
    if db.data is None:
        warnings.append("No data access was available; the copy has no sample rows, so data-dependent paths are untested.")
        return
    for table in db.tables:
        _copy_rows(engine, db, table, sample_limit, warnings)


def _try(engine: _SqliteEngine, sql: str, label: str, warnings: list[str]) -> None:
    try:
        engine.execute(sql)
    except sqlite3.Error as exc:
        warnings.append(f"{label} was not recreated: {exc}")


def _copy_rows(engine: _SqliteEngine, db: Database, table, sample_limit: int, warnings: list[str]) -> None:
    columns = [c.name for c in table.columns if not c.is_generated]
    if not columns:
        return
    q = db.data.quote
    source = f"{q(table.schema)}.{q(table.name)}" if table.schema else q(table.name)
    try:
        rows = db.data.query(f"SELECT {', '.join(q(c) for c in columns)} FROM {source} LIMIT {int(sample_limit)}")
    except Exception as exc:
        warnings.append(f"Sample rows from {table.name} could not be read: {type(exc).__name__}")
        return
    target = ", ".join('"' + c.replace('"', '""') + '"' for c in columns)
    marks = ", ".join("?" for _ in columns)
    sql = f'INSERT INTO "{table.name.replace(chr(34), chr(34) * 2)}" ({target}) VALUES ({marks})'
    failed = 0
    for row in rows:
        try:
            engine.conn.execute(sql, tuple(_adapt(v) for v in row))
        except sqlite3.Error:
            failed += 1
    if failed:
        warnings.append(f"{failed} sample rows of {table.name} did not fit the SQLite copy and were skipped.")


def _adapt(value: Any) -> Any:
    if value is None or isinstance(value, (int, float, str, bytes)):
        return value
    if isinstance(value, (memoryview, bytearray)):
        return bytes(value)
    return str(value)


def _validate_scratch_url(url: str, allow_hosts: Optional[Sequence[str]]) -> tuple[str, str, Any]:
    parts = urlsplit(url)
    scheme = parts.scheme.split("+")[0].lower()
    if scheme not in ("postgres", "postgresql", "mysql"):
        raise SandboxRefused(f"Unsupported scratch server scheme: {parts.scheme!r}")
    host = (parts.hostname or "").lower()
    allowed = {str(h).strip().lower() for h in (allow_hosts or []) if str(h).strip()}
    if not host or host not in allowed:
        raise SandboxRefused(f"Scratch host {parts.hostname!r} is not in allow_hosts; the caller must list it explicitly.")
    database = unquote(parts.path.lstrip("/"))
    if "/" in database or not database.startswith(SANDBOX_DB_PREFIX):
        raise SandboxRefused(f"Scratch database name must begin with {SANDBOX_DB_PREFIX!r}; got {database!r}.")
    if parts.password:
        raise SandboxRefused("Scratch URLs must not embed a password; pass password_env with an environment variable name.")
    return normalize_dialect(scheme), database, parts


def _driver_connect(url_parts: Any, dialect: str, database: str, password_env: Optional[str]) -> Any:
    password = os.environ.get(password_env) if password_env else None
    if dialect == "postgres":
        import psycopg  # optional extra

        return psycopg.connect(host=url_parts.hostname, port=url_parts.port or 5432, user=url_parts.username, password=password, dbname=database, autocommit=True)
    import pymysql  # optional extra

    return pymysql.connect(host=url_parts.hostname, port=url_parts.port or 3306, user=url_parts.username, password=password or "", database=database, autocommit=True)


def _run_checks(engine: _Engine, checks: list[Check]) -> Optional[str]:
    for check in checks:
        try:
            value = engine.scalar(check.sql)
        except Exception as exc:
            return f"Check could not run ({check.description}): {exc}"
        if value != check.expected:
            return f"{check.description}: returned {value}, expected {check.expected}"
    return None


def _exec_all(engine: _Engine, statements: list[str]) -> Optional[str]:
    for sql in statements:
        try:
            engine.execute(sql)
        except Exception as exc:
            if hasattr(engine, "rollback_if_needed"):
                try:
                    engine.rollback_if_needed()
                except Exception:
                    pass
            return f"{type(exc).__name__}: {exc} in statement: {sql[:120]}"
    return None


def _test_step(step: MigrationStep, engine: _Engine, result: StepResult) -> None:
    problem = _run_checks(engine, step.prechecks)
    if problem:
        result.status = "failed"
        result.reason = f"Precheck failed, data repair needed before this step: {problem}"
        return
    before = engine.snapshot()
    count_before = engine.counts()
    error = _exec_all(engine, step.up_sql)
    if error:
        result.status = "failed"
        result.reason = f"Up SQL failed: {error}"
        return
    result.up_applied = True
    problem = _run_checks(engine, step.postchecks)
    if problem:
        result.postchecks = "failed"
        result.status = "failed"
        result.reason = f"Postcheck failed: {problem}"
        return
    result.postchecks = "passed"
    if not step.postchecks:
        result.status = "not_testable"
        result.reason = "The step defines no postchecks, so the outcome cannot be verified."
        return
    if not step.reversible or not step.down_sql:
        result.status = "passed"
        result.rollback = "not_available"
        result.reason = step.irreversible_reason or "No rollback is defined for this step."
        return
    error = _exec_all(engine, step.down_sql)
    if error:
        result.status = "failed"
        result.rollback = "failed"
        result.reason = f"Down SQL failed: {error}"
        result.schema_restored = False
        return
    after_down = engine.snapshot()
    result.schema_restored = after_down == before
    result.rows_preserved = engine.counts() == count_before
    if not result.schema_restored:
        result.status = "failed"
        result.rollback = "failed"
        result.reason = f"Rollback did not restore the schema: {_diff(before, after_down)}"
        return
    if result.rows_preserved is False:
        result.status = "failed"
        result.rollback = "failed"
        result.reason = "Rollback changed row counts."
        return
    error = _exec_all(engine, step.up_sql)
    if error:
        result.status = "failed"
        result.rollback = "passed"
        result.reason = f"Redeploy after rollback failed: {error}"
        return
    result.rollback = "passed"
    result.status = "passed"


def _diff(a: dict, b: dict) -> str:
    keys = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
    return ", ".join(keys[:5]) or "(no difference found)"


def test_plan_in_sandbox(db_or_sql: Any, plan: MigrationPlan, approval_token: str, *, scratch_url: Optional[str] = None,
                         allow_hosts: Optional[Sequence[str]] = None, password_env: Optional[str] = None,
                         connect: Optional[Callable[[str], Any]] = None, sample_limit: int = 1000) -> SandboxReport:
    """Apply, verify and roll back each step in isolation.

    Default target: a temporary SQLite file built from ``db_or_sql`` (a ``Database``, whose rows are copied by SELECT
    through ``db.data``, or a SQL script string). ``scratch_url`` selects a user-supplied server instead; its host must
    be listed in ``allow_hosts`` and its database name must begin with ``dbintel_sandbox_``.
    """
    token = require_approval(plan, approval_token)
    warnings: list[str] = []
    if scratch_url is not None:
        dialect, database, parts = _validate_scratch_url(scratch_url, allow_hosts)
        if dialect != plan.dialect:
            raise SandboxRefused(f"Plan is for {plan.dialect} but the scratch server is {dialect}.")
        conn = connect(scratch_url) if connect else _driver_connect(parts, dialect, database, password_env)
        engine: _Engine = _ScratchEngine(conn, dialect)
    else:
        engine = _SqliteEngine()
        if isinstance(db_or_sql, Database):
            _build_from_model(engine, db_or_sql, sample_limit, warnings)
        elif isinstance(db_or_sql, str):
            engine.conn.executescript(db_or_sql)
        else:
            engine.close()
            raise TypeError("db_or_sql must be a Database or a SQL script string")
        engine.execute("PRAGMA foreign_keys=ON")
    report = SandboxReport(plan_hash=token, engine=engine.name, isolated=True, warnings=warnings)
    try:
        original = engine.snapshot()
        untested: set[str] = set()
        applied: list[MigrationStep] = []
        for step in sorted(plan.steps, key=lambda s: s.order):
            result = StepResult(step_id=step.id, title=step.title, status="not_testable", engine=engine.name)
            report.results.append(result)
            if step.manual:
                result.reason = "Manual step: it has no SQL to run."
                untested.add(step.id)
                continue
            blocked = next((d for d in step.depends_on if d in untested), None)
            if blocked:
                result.reason = f"It depends on step {blocked}, which was not applied in this sandbox."
                untested.add(step.id)
                continue
            if isinstance(engine, _SqliteEngine) and plan.dialect != "sqlite":
                problem = _portability_problem(step, engine)
                if problem:
                    result.reason = f"{problem} The plan targets {plan.dialect}; test it on a scratch server of that engine (TST-004)."
                    untested.add(step.id)
                    continue
            _test_step(step, engine, result)
            if result.status != "passed":
                untested.add(step.id)
                if result.up_applied:
                    if step.down_sql:
                        _exec_all(engine, step.down_sql)
                    else:
                        result.reason += " The step remains applied in the sandbox because it has no rollback."
            else:
                applied.append(step)
        report.schema_restored, report.schema_restored_reason = _restore_plan(engine, applied, original)
    finally:
        engine.close()
    return report


test_plan_in_sandbox.__test__ = False  # keep pytest from collecting this API function


def _restore_plan(engine: _Engine, applied: list[MigrationStep], original: dict) -> tuple[Optional[bool], str]:
    if not applied:
        return None, "No step was applied, so there is nothing to compare."
    missing = [s.id for s in applied if not s.reversible or not s.down_sql]
    if missing:
        return None, f"Steps {', '.join(missing)} have no rollback, so the full plan could not be reversed."
    for step in reversed(applied):
        error = _exec_all(engine, step.down_sql)
        if error:
            return False, f"Rolling back step {step.id} failed: {error}"
    current = engine.snapshot()
    if current == original:
        return True, "The schema snapshot after the full rollback equals the original."
    return False, f"Schema differs after rollback: {_diff(original, current)}"
