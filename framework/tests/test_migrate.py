import ast
import json
import re
import sqlite3
from pathlib import Path

import pytest
import sqlglot

from dbintel.config import Profile
from dbintel.connectors import ReadOnlyViolation, assert_read_only, open_connector
from dbintel.findings import Finding, FindingKind, Fix, Severity
from dbintel.migrate import (ApprovalRequired, SandboxRefused, detect_destructive, generate_plan, is_destructive,
                             plan_hash, require_approval, write_migration_files)
from dbintel.migrate import test_plan_in_sandbox as run_sandbox
from dbintel.migrate._sql import IdentifierError, make_name, quote, type_change_kind
from dbintel.migrate.safety import backup_recommendation, is_financial_table
from dbintel.model import Column, Database, ForeignKey, Grant, Index, Routine, Table, View

ROOT = Path(__file__).resolve().parent.parent
DIALECTS = ("postgres", "mysql", "sqlite")


class Sqlite3Data:
    dialect = "sqlite"

    def __init__(self, conn):
        self.conn = conn
        self.queries = []

    def query(self, sql, params=()):
        self.queries.append(sql)
        return self.conn.execute(sql, params).fetchall()

    def quote(self, identifier):
        return '"' + identifier.replace('"', '""') + '"'


def finding(op, table=None, col=None, fid=None, **params):
    return Finding(id=fid or f"F-{op}-{table}-{col}-{sorted(params.items(), key=str)}", rule_id="R-1", title=op,
                   severity=Severity.HIGH, kind=FindingKind.CONFIRMED_DEFECT, category="schema_quality", database="shop",
                   table=table, column=col, evidence="e", root_cause="c", business_impact="b", technical_impact="t",
                   standards=[], standard_statements={}, recommended_solution="s", complexity="low", migration_requirements="m",
                   risks="r", validation_strategy="v", fix=Fix(op, table, col, params))


def model(dialect="postgres", row_count=10):
    customers = Table("customers", columns=[Column("id", "int", False), Column("email", "varchar(100)", True), Column("name", "varchar(50)", False),
                                            Column("legacy", "text", True), Column("code", "varchar(20)", True)],
                      primary_key=["id"], row_count=row_count,
                      indexes=[Index("ix_customers_name", ["name"]), Index("ix_customers_code", ["code"], unique=True)])
    orders = Table("orders", columns=[Column("id", "int", True), Column("customer_id", "int", True), Column("total", "decimal(10,2)", True),
                                      Column("status", "varchar(20)", True), Column("tenant_id", "int", True)], row_count=row_count)
    invoices = Table("invoices", columns=[Column("id", "int", False), Column("amount", "decimal(10,2)", True), Column("note", "varchar(50)", True)],
                     primary_key=["id"], row_count=row_count)
    return Database("shop", dialect, "live", tables=[customers, orders, invoices],
                    grants=[Grant("report_role", "SELECT", table="customers")])


ALL_OPS = [
    ("add_primary_key", "orders", None, {"columns": ["id"]}),
    ("add_surrogate_primary_key", "orders", None, {"column": "row_id"}),
    ("add_foreign_key", "orders", "customer_id", {"columns": ["customer_id"], "ref_table": "customers", "ref_columns": ["id"]}),
    ("add_index", "orders", None, {"columns": ["status"], "unique": False}),
    ("add_index", "orders", None, {"columns": ["status", "tenant_id"], "unique": True}),
    ("drop_index", "customers", None, {"name": "ix_customers_name"}),
    ("alter_column_type", "customers", "name", {"new_type": "varchar(200)"}),
    ("set_not_null", "customers", "email", {}),
    ("add_column", "orders", "created_at", {"type": "timestamp", "nullable": True, "default": None}),
    ("add_check", "orders", None, {"expression": "total >= 0", "name": "ck_total"}),
    ("rename_column", "customers", "legacy", {"new_name": "legacy_notes"}),
    ("rename_table", "orders", None, {"new_name": "orders_v2"}),
    ("enable_rls", "orders", None, {"tenant_column": "tenant_id"}),
    ("revoke_grant", "customers", None, {"grantee": "report_role", "privilege": "SELECT"}),
    ("manual", "customers", None, {"description": "Decide retention."}),
]
EXPECT_MANUAL = {("enable_rls", "mysql"), ("enable_rls", "sqlite"), ("revoke_grant", "sqlite"), ("manual", "postgres"), ("manual", "mysql"), ("manual", "sqlite")}


def expected_lints(op, dialect):
    return {
        ("add_index", "postgres"): "CONCURRENTLY", ("add_primary_key", "postgres"): "USING INDEX",
        ("add_foreign_key", "postgres"): "NOT VALID", ("add_check", "postgres"): "NOT VALID",
        ("set_not_null", "postgres"): "NOT VALID", ("add_index", "mysql"): "ALGORITHM=INPLACE",
        ("add_column", "mysql"): "ALGORITHM=INPLACE", ("add_foreign_key", "mysql"): "ALGORITHM=COPY",
    }.get((op, dialect))


@pytest.mark.parametrize("dialect", DIALECTS)
@pytest.mark.parametrize("op,table,column,params", ALL_OPS, ids=[f"{o[0]}-{i}" for i, o in enumerate(ALL_OPS)])
def test_every_op_in_every_dialect(op, table, column, params, dialect):
    plan = generate_plan(model(dialect), [finding(op, table, column, **params)], dialect)
    assert plan.steps, "the op produced no step"
    step = plan.steps[0]
    if (op, dialect) in EXPECT_MANUAL:
        assert step.manual and not step.up_sql and not step.down_sql
        assert step.manual_description
        assert plan.manual_steps == [step]
        return
    assert not step.manual, step.manual_description
    assert step.up_sql
    expected = expected_lints(op, dialect)
    if expected:
        assert expected in step.up_script
    assert step.postchecks
    if dialect in ("postgres", "mysql"):
        for statement in step.up_sql + step.down_sql:
            sqlglot.parse_one(statement, read=dialect)
    for check in step.prechecks + step.postchecks:
        assert re.match(r"\s*SELECT\b", check.sql, re.I)
        assert isinstance(check.expected, int)


@pytest.mark.parametrize("dialect", DIALECTS)
def test_identifiers_are_quoted_and_validated(dialect):
    db = Database("x", dialect, tables=[Table('we"ird`', columns=[Column("a b", "int", True)], row_count=0)])
    plan = generate_plan(db, [finding("set_not_null", 'we"ird`', "a b")], dialect)
    text = plan.steps[0].up_script
    if dialect == "mysql":
        assert "`we\"ird```" in text and "`a b`" in text
    else:
        assert '"we""ird`"' in text and '"a b"' in text


@pytest.mark.parametrize("bad", ["", "bad\x00name", "x" * 300])
def test_bad_identifier_rejected(bad):
    with pytest.raises(IdentifierError):
        quote(bad, "postgres")


@pytest.mark.parametrize("op,params", [("add_column", {"type": "int; DROP TABLE x", "nullable": True}),
                                       ("alter_column_type", {"new_type": "int); DROP TABLE x; --"}),
                                       ("add_check", {"expression": "1=1; DROP TABLE x", "name": "c"}),
                                       ("add_check", {"expression": "(SELECT 1) = 1", "name": "c"}),
                                       ("rename_column", {"new_name": "bad\x01"})])
def test_injection_like_inputs_become_manual(op, params):
    column = "name" if op != "add_column" else "newcol"
    plan = generate_plan(model(), [finding(op, "customers", column, **params)])
    assert plan.steps[0].manual and not plan.steps[0].up_sql


def test_long_names_truncated_within_limit():
    name = make_name("ix", "t" * 100, ["c" * 100], "postgres")
    assert len(name) <= 63


def test_missing_table_and_unknown_op_are_manual():
    plan = generate_plan(model(), [finding("add_index", "ghost", None, columns=["a"]), finding("frobnicate", "customers")])
    assert len(plan.steps) == 2 and all(s.manual for s in plan.steps)


def test_findings_without_fix_listed():
    f = finding("manual", "customers", description="x")
    f.fix = None
    plan = generate_plan(model(), [f])
    assert plan.unaddressed_findings == [f.id] and not plan.steps


def test_unknown_dialect_rejected():
    with pytest.raises(ValueError):
        generate_plan(model(), [], "oracle")


def test_generic_defaults_to_postgres():
    db = model("generic")
    assert generate_plan(db, [finding("add_index", "orders", None, columns=["status"])]).dialect == "postgres"


# --- safe forms and expand/contract ----------------------------------------

def test_postgres_concurrent_index_is_marked_non_transactional():
    step = generate_plan(model(), [finding("add_index", "orders", None, columns=["status"])]).steps[0]
    assert step.transactional is False and "CONCURRENTLY" in step.up_script and "CONCURRENTLY" in step.down_script
    assert step.up_sql[0].startswith("SET lock_timeout")


def test_mysql_sets_lock_wait_timeout():
    step = generate_plan(model("mysql"), [finding("add_index", "orders", None, columns=["status"])], "mysql").steps[0]
    assert "lock_wait_timeout" in step.up_sql[0]


def test_set_not_null_uses_check_on_populated_and_direct_on_empty():
    step = generate_plan(model(row_count=5), [finding("set_not_null", "customers", "email")]).steps[0]
    assert "VALIDATE CONSTRAINT" in step.up_script and "SET NOT NULL" in step.up_script
    empty = generate_plan(model(row_count=0), [finding("set_not_null", "customers", "email")]).steps[0]
    assert "VALIDATE" not in empty.up_script and "SET NOT NULL" in empty.up_script


def test_row_count_unknown_treated_as_populated():
    step = generate_plan(model(row_count=None), [finding("set_not_null", "customers", "email")]).steps[0]
    assert "NOT VALID" in step.up_script


def test_type_change_expand_contract_on_populated_table():
    plan = generate_plan(model(), [finding("alter_column_type", "orders", "id", new_type="bigint")])
    labels = [s.phase_label for s in plan.steps]
    assert labels == ["expand", "swap", "contract"]
    expand, swap, cleanup = plan.steps
    assert "ADD COLUMN" in expand.up_script and "UPDATE" in expand.up_script
    assert "RENAME COLUMN" in swap.up_script
    assert "DROP COLUMN" in cleanup.up_script
    assert cleanup.destructive and cleanup.requires_backup and not cleanup.reversible and not cleanup.down_sql
    assert swap.depends_on == [expand.id] and cleanup.depends_on == [swap.id]
    assert any("IS DISTINCT FROM" in c.sql for c in swap.prechecks)


def test_varchar_widening_is_direct_on_populated_postgres():
    plan = generate_plan(model(), [finding("alter_column_type", "customers", "name", new_type="varchar(200)")])
    assert len(plan.steps) == 1
    assert "ALTER COLUMN" in plan.steps[0].up_script and plan.steps[0].reversible


def test_type_change_on_empty_table_is_direct_with_rollback():
    plan = generate_plan(model(row_count=0), [finding("alter_column_type", "orders", "id", new_type="bigint")])
    assert len(plan.steps) == 1 and plan.steps[0].reversible and plan.steps[0].down_sql


def test_narrowing_has_no_fabricated_rollback():
    step = generate_plan(model(row_count=0), [finding("alter_column_type", "customers", "name", new_type="varchar(5)")]).steps[0]
    assert step.reversible is False and step.down_sql == [] and step.irreversible_reason
    assert step.data_loss_risk == "high" and step.destructive and step.requires_backup


def test_narrowing_precheck_detects_long_values():
    step = generate_plan(model(row_count=0), [finding("alter_column_type", "customers", "name", new_type="varchar(5)")]).steps[0]
    assert any("CHAR_LENGTH" in c.sql and c.kind == "data" for c in step.prechecks)


def test_mysql_varchar_boundary_uses_expand_contract():
    db = model("mysql")
    plan = generate_plan(db, [finding("alter_column_type", "customers", "name", new_type="varchar(300)")], "mysql")
    assert [s.phase_label for s in plan.steps] == ["expand", "swap", "contract"]


def test_mysql_varchar_same_boundary_is_online():
    db = model("mysql")
    db.table("customers").column("name").data_type = "varchar(100)"
    step = generate_plan(db, [finding("alter_column_type", "customers", "name", new_type="varchar(200)")], "mysql").steps[0]
    assert "ALGORITHM=INPLACE, LOCK=NONE" in step.up_script


def test_type_kinds():
    assert type_change_kind("int", "bigint", "postgres") == "widening"
    assert type_change_kind("varchar(10)", "text", "postgres") == "binary_compatible"
    assert type_change_kind("bigint", "int", "postgres") == "narrowing"
    assert type_change_kind("text", "int", "postgres") == "narrowing"


# --- merging, conflicts, ordering ------------------------------------------

def test_duplicate_findings_merge():
    a = finding("add_index", "orders", None, fid="A", columns=["status"])
    b = finding("add_index", "orders", None, fid="B", columns=["status"], unique=True)
    plan = generate_plan(model(), [a, b])
    assert len(plan.steps) == 1 and plan.steps[0].finding_ids == ["A", "B"]
    assert "UNIQUE" in plan.steps[0].up_script


def test_conflicting_types_produce_one_decision_step():
    a = finding("alter_column_type", "orders", "status", fid="A", new_type="varchar(5)")
    b = finding("alter_column_type", "orders", "status", fid="B", new_type="text")
    plan = generate_plan(model(), [a, b])
    assert len(plan.steps) == 1 and plan.steps[0].manual and set(plan.steps[0].finding_ids) == {"A", "B"}


def test_conflicting_renames_and_pk_proposals():
    plan = generate_plan(model(), [finding("rename_column", "customers", "legacy", fid="A", new_name="x"),
                                   finding("rename_column", "customers", "legacy", fid="B", new_name="y"),
                                   finding("add_primary_key", "orders", None, fid="C", columns=["id"]),
                                   finding("add_surrogate_primary_key", "orders", None, fid="D")])
    assert all(s.manual for s in plan.steps) and len(plan.steps) == 2


def test_add_pk_on_table_with_pk_is_manual():
    assert generate_plan(model(), [finding("add_primary_key", "customers", None, columns=["id"])]).steps[0].manual


def test_set_not_null_covered_by_primary_key():
    a = finding("add_primary_key", "orders", None, fid="A", columns=["id"])
    b = finding("set_not_null", "orders", "id", fid="B")
    plan = generate_plan(model(), [a, b])
    assert len(plan.steps) == 1 and set(plan.steps[0].finding_ids) == {"A", "B"}


def test_set_not_null_on_new_column_merges():
    a = finding("add_column", "orders", "c", fid="A", type="int", nullable=True, default=0)
    b = finding("set_not_null", "orders", "c", fid="B")
    plan = generate_plan(model(row_count=0), [a, b])
    assert len(plan.steps) == 1 and "NOT NULL" in plan.steps[0].up_script


def test_existing_index_is_satisfied_not_regenerated():
    plan = generate_plan(model(), [finding("add_index", "customers", None, fid="A", columns=["name"])])
    assert not plan.steps and plan.satisfied_findings == ["A"]


def test_already_not_null_is_satisfied():
    plan = generate_plan(model(), [finding("set_not_null", "customers", "name", fid="A")])
    assert not plan.steps and plan.satisfied_findings == ["A"]


def test_same_type_change_is_satisfied():
    plan = generate_plan(model(), [finding("alter_column_type", "customers", "name", fid="A", new_type="varchar(50)")])
    assert not plan.steps and plan.satisfied_findings == ["A"]


def test_dependency_order():
    findings = [finding("rename_table", "orders", None, new_name="o2"), finding("add_foreign_key", "orders", "customer_id", columns=["customer_id"], ref_table="customers", ref_columns=["id"]),
                finding("add_primary_key", "orders", None, columns=["id"]), finding("add_index", "orders", None, columns=["customer_id"]),
                finding("add_column", "orders", "x", type="int", nullable=True), finding("rename_column", "customers", "legacy", new_name="l2"),
                finding("set_not_null", "orders", "x"), finding("add_check", "orders", None, expression="total >= 0", name="ck")]
    plan = generate_plan(model(), findings)
    ops = [s.op for s in plan.steps]
    assert ops.index("add_column") < ops.index("add_primary_key") < ops.index("add_index") < ops.index("add_foreign_key") < ops.index("add_check")
    assert ops.index("rename_column") < ops.index("rename_table") and ops.index("add_foreign_key") < ops.index("rename_column")
    assert ops.index("add_column") < ops.index("set_not_null") if "set_not_null" in ops else True
    assert [s.order for s in plan.steps] == list(range(1, len(plan.steps) + 1))


def test_fk_depends_on_planned_parent_key():
    db = model()
    db.table("customers").primary_key = []
    db.table("customers").indexes = []
    plan = generate_plan(db, [finding("add_primary_key", "customers", None, columns=["id"]),
                              finding("add_foreign_key", "orders", "customer_id", columns=["customer_id"], ref_table="customers", ref_columns=["id"])])
    pk = next(s for s in plan.steps if s.op == "add_primary_key")
    fk = next(s for s in plan.steps if s.op == "add_foreign_key")
    assert pk.order < fk.order and pk.id in fk.depends_on


def test_fk_without_parent_key_is_manual():
    db = model()
    db.table("customers").primary_key = []
    db.table("customers").indexes = []
    plan = generate_plan(db, [finding("add_foreign_key", "orders", "customer_id", columns=["customer_id"], ref_table="customers", ref_columns=["id"])])
    assert plan.steps[0].manual


def test_step_depending_on_manual_is_blocked():
    db = model()
    db.table("customers").primary_key = []
    db.table("customers").indexes = []
    plan = generate_plan(db, [finding("add_foreign_key", "orders", "customer_id", columns=["customer_id"], ref_table="customers", ref_columns=["id"]),
                              finding("add_index", "orders", None, columns=["ghost"])])
    assert all(s.manual for s in plan.steps)


# --- prechecks -------------------------------------------------------------

def test_prechecks_detect_bad_data_kinds():
    plan = generate_plan(model(), [finding("set_not_null", "customers", "email"),
                                   finding("add_index", "orders", None, columns=["status"], unique=True),
                                   finding("add_foreign_key", "orders", "customer_id", columns=["customer_id"], ref_table="customers", ref_columns=["id"]),
                                   finding("add_check", "orders", None, expression="total >= 0", name="ck")])
    by_op = {s.op: s for s in plan.steps}
    assert any("IS NULL" in c.sql and c.kind == "data" for c in by_op["set_not_null"].prechecks)
    assert any("HAVING COUNT(*) > 1" in c.sql for c in by_op["add_index"].prechecks)
    assert any("LEFT JOIN" in c.sql for c in by_op["add_foreign_key"].prechecks)
    assert any("NOT (" in c.sql for c in by_op["add_check"].prechecks)
    assert all(s.requires_data_repair for s in by_op.values())


def sqlite_db(rows=None):
    conn = sqlite3.connect(":memory:")
    conn.execute('CREATE TABLE parent (id INTEGER PRIMARY KEY, code TEXT)')
    conn.execute('CREATE TABLE child (id INTEGER, parent_id INTEGER, label TEXT, qty INTEGER)')
    conn.executemany("INSERT INTO parent VALUES (?, ?)", [(1, "a"), (2, "b")])
    for row in rows if rows is not None else [(1, 1, "x", 1), (2, 2, "y", 2)]:
        conn.execute("INSERT INTO child VALUES (?, ?, ?, ?)", row)
    conn.commit()
    parent = Table("parent", columns=[Column("id", "INTEGER", False), Column("code", "TEXT", True)], primary_key=["id"], row_count=2)
    child = Table("child", columns=[Column("id", "INTEGER", True), Column("parent_id", "INTEGER", True), Column("label", "TEXT", True), Column("qty", "INTEGER", True)],
                  row_count=2)
    return Database("t", "sqlite", "live", tables=[parent, child], data=Sqlite3Data(conn))


def test_prechecks_evaluated_on_real_data_detect_nulls():
    db = sqlite_db([(1, 1, None, 1)])
    plan = generate_plan(db, [finding("set_not_null", "child", "label")], "sqlite")
    check = next(c for c in plan.steps[0].prechecks if c.kind == "data")
    assert check.status == "failed" and check.observed == 1
    assert plan.steps[0].requires_data_repair


def test_prechecks_clean_data_not_flagged_for_repair():
    plan = generate_plan(sqlite_db(), [finding("set_not_null", "child", "label")], "sqlite")
    assert not plan.steps[0].requires_data_repair
    assert all(c.status == "passed" for c in plan.steps[0].prechecks if c.kind == "data")


def test_prechecks_detect_duplicates_and_orphans():
    plan = generate_plan(sqlite_db([(1, 1, "x", 1), (1, 9, "y", 2)]), [finding("add_index", "child", None, columns=["id"], unique=True),
                                                                        finding("add_foreign_key", "child", "parent_id", columns=["parent_id"], ref_table="parent", ref_columns=["id"])], "sqlite")
    index_step = next(s for s in plan.steps if s.op == "add_index")
    rebuild = next(s for s in plan.steps if s.op == "rebuild")
    assert next(c for c in index_step.prechecks if c.kind == "data").observed == 1
    orphan = next(c for c in rebuild.prechecks if c.kind == "data")
    assert orphan.status == "failed" and orphan.observed == 1


def test_precheck_not_run_without_data_access_requires_repair():
    plan = generate_plan(model(), [finding("set_not_null", "customers", "email")])
    assert plan.steps[0].requires_data_repair
    assert all(c.status == "not_run" for c in plan.steps[0].prechecks)


# --- destructive detection -------------------------------------------------

@pytest.mark.parametrize("sql,kind", [
    ("DROP TABLE t", "drop_table"), ("drop table if exists t", "drop_table"), ("ALTER TABLE t DROP COLUMN c", "drop_column"),
    ("ALTER TABLE t DROP c", "drop_column"), ("TRUNCATE t", "truncate"), ("TRUNCATE TABLE t", "truncate"),
    ("DELETE FROM t WHERE id = 1", "delete"), ("UPDATE t SET a = 1", "update_without_where"), ("DROP DATABASE x", "drop_database"),
    ("DROP SCHEMA s CASCADE", "drop_database"), ("REPLACE INTO t VALUES (1)", "replace_into"),
    ("ALTER TABLE t DROP PARTITION p1", "drop_partition"),
])
def test_destructive_statements(sql, kind):
    assert kind in {h.kind for h in detect_destructive(sql)}


@pytest.mark.parametrize("sql,kind", [
    ("dRoP/**/tAbLe t", "drop_table"), ("DROP\n\t TABLE\n t", "drop_table"), ("SELECT 1; DROP TABLE x", "drop_table"),
    ("SELECT /* x */ 1 ; /* y */ TRUNCATE TABLE t", "truncate"), ("/*!50000 DROP TABLE t */", "drop_table"),
    ("/*M!100100 TRUNCATE t */", "truncate"), ("UPDATE t SET a = (SELECT b FROM u WHERE u.id = 1)", "update_without_where"),
    ("UPDATE t SET a = 1 WHERE 1=1", "update_always_true"), ("UPDATE t SET a = 1 WHERE TRUE", "update_always_true"),
    ("UPDATE t SET a = 1 WHERE id = 3 OR 1=1", "update_always_true"), ("DELETE FROM t WHERE 'a'='a'", "delete_always_true"),
    ("WITH d AS (DELETE FROM t RETURNING *) SELECT * FROM d", "delete"),
    ("DO $$ BEGIN DROP TABLE t; END $$", "dynamic_sql"), ("EXECUTE 'DROP TABLE t'", "dynamic_sql"),
    ("PREPARE s FROM 'TRUNCATE t'", "dynamic_sql"), ("SELECT 'a\\'; DROP TABLE x; --'", "drop_table"), ("this is not sql; DROP TABLE t", "drop_table"), ("DROP TABLE `odd name`", "drop_table"),
])
def test_bypass_like_text_is_detected(sql, kind):
    assert kind in {h.kind for h in detect_destructive(sql)}, detect_destructive(sql)


@pytest.mark.parametrize("sql", ["SELECT 'DROP TABLE x'", "SELECT 1 -- DROP TABLE x", "SELECT 1 /* DROP TABLE x */", "SELECT \"drop table\" FROM t",
                                 "CREATE INDEX i ON t (a)", "SELECT TRUNCATE(1.5, 1)", "ALTER TABLE t ADD COLUMN c int",
                                 "INSERT INTO t VALUES ('UPDATE t SET x = 1')", "UPDATE t SET a = 1 WHERE id = 2",
                                 "SELECT 'x' FROM t ON DELETE CASCADE"])
def test_non_destructive_text_not_flagged(sql):
    assert not is_destructive(sql), detect_destructive(sql)


def test_narrowing_detection_uses_known_types():
    assert is_destructive("ALTER TABLE t ALTER COLUMN c TYPE varchar(5)", known_types={"t.c": "varchar(50)"})
    assert not is_destructive("ALTER TABLE t ALTER COLUMN c TYPE varchar(100)", known_types={"t.c": "varchar(50)"})
    assert is_destructive("ALTER TABLE t MODIFY c decimal(5,2) NOT NULL", known_types={"t.c": "decimal(10,2)"})


def test_unknown_type_change_treated_as_possible_narrowing():
    hits = detect_destructive("ALTER TABLE t ALTER COLUMN c TYPE varchar(5)")
    assert any(h.kind == "type_narrowing" for h in hits)


def test_drop_index_is_risky_not_destructive():
    hits = detect_destructive("DROP INDEX i")
    assert hits and all(h.severity == "risky" for h in hits)


def test_rename_flagged_risky():
    assert any(h.kind == "rename" for h in detect_destructive("ALTER TABLE t RENAME COLUMN a TO b"))


# --- approval, hash, financial, backup ------------------------------------

def simple_plan():
    return generate_plan(model(), [finding("add_index", "orders", None, columns=["status"])])


def test_plan_hash_stable_and_sensitive():
    a, b = simple_plan(), simple_plan()
    assert plan_hash(a) == plan_hash(b)
    b.steps[0].up_sql.append("SELECT 1")
    assert plan_hash(a) != plan_hash(b)


def test_require_approval():
    plan = simple_plan()
    assert require_approval(plan, plan_hash(plan)) == plan_hash(plan)
    for token in (None, "", "wrong", plan_hash(plan) + "x"):
        with pytest.raises(ApprovalRequired):
            require_approval(plan, token)


def test_changed_plan_rejected_with_old_token():
    plan = simple_plan()
    token = plan_hash(plan)
    plan.steps[0].down_sql = ["DROP TABLE orders"]
    with pytest.raises(ApprovalRequired):
        require_approval(plan, token)


@pytest.mark.parametrize("dialect,tool", [("postgres", "pg_basebackup"), ("mysql", "XtraBackup"), ("sqlite", ".backup")])
def test_backup_text_per_dialect(dialect, tool):
    text = backup_recommendation(dialect)
    assert tool in text and "not a backup" in text


@pytest.mark.parametrize("name,expected", [("journal_entries", True), ("general_ledger", True), ("invoices", True), ("payments", True), ("customers", False), ("Invoice", True)])
def test_financial_table_detection(name, expected):
    assert is_financial_table(name) is expected


def fin_db():
    table = Table("invoices", columns=[Column("id", "int", False), Column("amount", "decimal(10,2)", True), Column("legacy", "text", True)], primary_key=["id"], row_count=5)
    return Database("x", "postgres", tables=[table])


def test_financial_destructive_step_refused():
    plan = generate_plan(fin_db(), [finding("alter_column_type", "invoices", "amount", new_type="decimal(5,1)")])
    expand, swap, cleanup = plan.steps
    assert cleanup.manual and cleanup.refused_reason and not cleanup.up_sql
    assert not expand.manual


def test_financial_narrowing_direct_refused():
    db = fin_db()
    db.table("invoices").row_count = 0
    plan = generate_plan(db, [finding("alter_column_type", "invoices", "amount", new_type="decimal(5,1)")])
    assert plan.steps[0].manual and not plan.steps[0].up_sql and "financial" in plan.steps[0].refused_reason


def test_financial_rename_refused():
    plan = generate_plan(fin_db(), [finding("rename_column", "invoices", "legacy", new_name="note")])
    assert plan.steps[0].manual


def test_financial_safe_step_generated():
    plan = generate_plan(fin_db(), [finding("add_index", "invoices", None, columns=["amount"])])
    assert not plan.steps[0].manual and plan.steps[0].up_sql


def test_financial_patterns_from_profile_and_kwarg():
    db = fin_db()
    db.table("invoices").name = "wallets"
    finding_obj = finding("rename_column", "wallets", "legacy", new_name="n")
    assert not generate_plan(db, [finding_obj]).steps[0].manual
    profile = Profile(rules={"migration.financial": {"patterns": ["wallet"]}})
    assert generate_plan(db, [finding_obj], profile=profile).steps[0].manual
    assert generate_plan(db, [finding_obj], financial_patterns=["wall"]).steps[0].manual


# --- rename dependency risk -------------------------------------------------

def test_rename_reports_dependency_risk():
    db = model()
    db.views.append(View("v_customers", "SELECT legacy FROM customers"))
    db.routines.append(Routine("p", definition="SELECT legacy FROM customers"))
    step = generate_plan(db, [finding("rename_column", "customers", "legacy", new_name="l2")]).steps[0]
    text = " ".join(step.dependency_risks)
    assert step.breaking and "v_customers" in text and "p" in text and "Application code" in text


# --- rollback is real -------------------------------------------------------

def test_add_column_down_sql_drops_it_and_warns():
    step = generate_plan(model(), [finding("add_column", "orders", "c", type="int", nullable=True)]).steps[0]
    assert "DROP COLUMN" in step.down_script and step.reversible
    assert any("discards" in n for n in step.online_notes)


def test_unknown_grant_has_no_fabricated_grant():
    step = generate_plan(model(), [finding("revoke_grant", "orders", None, grantee="ghost", privilege="SELECT")]).steps[0]
    assert not step.reversible and not step.down_sql and step.irreversible_reason


def test_known_grant_is_restored():
    step = generate_plan(model(), [finding("revoke_grant", "customers", None, grantee="report_role", privilege="SELECT")]).steps[0]
    assert step.reversible and step.down_sql[0].startswith("GRANT SELECT")


def test_add_column_not_null_on_populated_becomes_nullable_with_repair():
    step = generate_plan(model(), [finding("add_column", "orders", "c", type="int", nullable=False)]).steps[0]
    assert "NOT NULL" not in step.up_script and step.requires_data_repair and step.data_repair_notes


# --- sandbox ---------------------------------------------------------------

def rebuild_findings():
    return [finding("set_not_null", "child", "label"), finding("add_check", "child", None, expression="qty >= 0", name="ck_qty"),
            finding("add_primary_key", "child", None, columns=["id"]),
            finding("add_foreign_key", "child", "parent_id", columns=["parent_id"], ref_table="parent", ref_columns=["id"]),
            finding("add_column", "child", "extra", type="int", nullable=True), finding("add_index", "child", None, columns=["qty"]),
            finding("rename_column", "child", "label", new_name="label2"), finding("alter_column_type", "child", "qty", new_type="bigint")]


def test_sandbox_requires_approval():
    db = sqlite_db()
    plan = generate_plan(db, [finding("add_index", "child", None, columns=["qty"])], "sqlite")
    with pytest.raises(ApprovalRequired):
        run_sandbox(db, plan, "nope")


def test_sandbox_rollback_restores_schema_and_keeps_source_intact():
    db = sqlite_db()
    source_before = db.data.conn.execute("SELECT sql FROM sqlite_master ORDER BY name").fetchall()
    plan = generate_plan(db, rebuild_findings(), "sqlite")
    report = run_sandbox(db, plan, plan_hash(plan))
    statuses = {r.step_id: r for r in report.results}
    assert report.overall == "passed", [(r.title, r.status, r.reason) for r in report.results]
    assert report.schema_restored is True, report.schema_restored_reason
    for result in report.results:
        assert result.rollback == "passed" and result.schema_restored is True, result
    assert db.data.conn.execute("SELECT sql FROM sqlite_master ORDER BY name").fetchall() == source_before
    assert db.data.conn.execute("SELECT count(*) FROM child").fetchone()[0] == 2


@pytest.mark.parametrize("op,table,col,params", [
    ("add_column", "child", "extra", {"type": "int", "nullable": True}),
    ("add_index", "child", None, {"columns": ["label"]}),
    ("drop_index", "child", None, {"name": "ix_child_qty"}),
    ("rename_column", "child", "label", {"new_name": "label2"}),
    ("rename_table", "child", None, {"new_name": "child2"}),
    ("set_not_null", "child", "label", {}),
    ("add_primary_key", "child", None, {"columns": ["id"]}),
    ("add_surrogate_primary_key", "child", None, {"column": "row_id"}),
    ("add_foreign_key", "child", "parent_id", {"columns": ["parent_id"], "ref_table": "parent", "ref_columns": ["id"]}),
    ("add_check", "child", None, {"expression": "qty >= 0", "name": "ck_qty"}),
    ("alter_column_type", "child", "qty", {"new_type": "bigint"}),
])
def test_sandbox_rollback_returns_schema_to_original_for_each_sqlite_op(op, table, col, params):
    db = sqlite_db()
    db.table("child").indexes.append(Index("ix_child_qty", ["qty"]))
    plan = generate_plan(db, [finding(op, table, col, **params)], "sqlite")
    report = run_sandbox(db, plan, plan_hash(plan))
    assert report.results[0].status == "passed", report.results[0].reason
    assert report.results[0].rollback == "passed" and report.results[0].schema_restored is True
    assert report.schema_restored is True, report.schema_restored_reason


def test_sandbox_never_writes_through_db_data():
    db = sqlite_db()
    plan = generate_plan(db, [finding("add_index", "child", None, columns=["qty"])], "sqlite")
    db.data.queries.clear()
    run_sandbox(db, plan, plan_hash(plan))
    assert db.data.queries and all(re.match(r"\s*SELECT\b", q, re.I) for q in db.data.queries)


def test_sandbox_data_copy_contains_sample_rows_so_constraints_are_exercised():
    db = sqlite_db()
    plan = generate_plan(db, [finding("add_primary_key", "child", None, columns=["id"])], "sqlite")
    report = run_sandbox(db, plan, plan_hash(plan))
    assert report.results[0].status == "passed"


def test_sandbox_precheck_failure_reports_failed_with_repair():
    db = sqlite_db([(1, 1, None, 1)])
    plan = generate_plan(db, [finding("set_not_null", "child", "label")], "sqlite")
    report = run_sandbox(db, plan, plan_hash(plan))
    assert report.overall == "failed"
    assert report.results[0].status == "failed" and "data repair" in report.results[0].reason
    assert report.schema_restored is None


def test_sandbox_postgres_plan_is_not_testable_with_reason():
    db = model()
    plan = generate_plan(db, [finding("add_index", "orders", None, columns=["status"])], "postgres")
    report = run_sandbox(db, plan, plan_hash(plan))
    assert report.results[0].status == "not_testable"
    assert "SET" in report.results[0].reason or "CONCURRENTLY" in report.results[0].reason
    assert report.overall == "not_testable"


def test_sandbox_mysql_plan_not_testable():
    db = model("mysql")
    plan = generate_plan(db, [finding("add_column", "orders", "c", type="int", nullable=True)], "mysql")
    report = run_sandbox(db, plan, plan_hash(plan))
    assert report.results[0].status == "not_testable" and report.overall == "not_testable"


def test_sandbox_manual_step_not_testable():
    db = sqlite_db()
    plan = generate_plan(db, [finding("manual", "child", description="decide")], "sqlite")
    report = run_sandbox(db, plan, plan_hash(plan))
    assert report.results[0].status == "not_testable"


def test_sandbox_irreversible_step_has_no_claimed_rollback():
    db = sqlite_db()
    plan = generate_plan(db, [finding("alter_column_type", "child", "label", new_type="varchar(3)")], "sqlite")
    report = run_sandbox(db, plan, plan_hash(plan))
    result = report.results[0]
    assert result.status == "passed" and result.rollback == "not_available" and result.schema_restored is None
    assert report.schema_restored is None


def test_sandbox_detects_incomplete_rollback():
    db = sqlite_db()
    plan = generate_plan(db, [finding("add_index", "child", None, columns=["qty"])], "sqlite")
    plan.steps[0].down_sql = ["SELECT 1"]
    report = run_sandbox(db, plan, plan_hash(plan))
    assert report.results[0].status == "failed" and report.results[0].rollback == "failed"


def test_sandbox_from_sql_script():
    plan = generate_plan(Database("x", "sqlite", tables=[Table("a", columns=[Column("b", "int", True)], row_count=0)]),
                         [finding("add_index", "a", None, columns=["b"])], "sqlite")
    report = run_sandbox("CREATE TABLE a (b int);", plan, plan_hash(plan))
    assert report.overall == "passed"


def test_sandbox_blocks_attach():
    db = sqlite_db()
    plan = generate_plan(db, [finding("add_index", "child", None, columns=["qty"])], "sqlite")
    plan.steps[0].up_sql = ["ATTACH DATABASE 'x.db' AS other"] + plan.steps[0].up_sql
    report = run_sandbox(db, plan, plan_hash(plan))
    assert report.results[0].status == "failed"


def test_sandbox_rejects_bad_input_type():
    plan = generate_plan(sqlite_db(), [finding("add_index", "child", None, columns=["qty"])], "sqlite")
    with pytest.raises(TypeError):
        run_sandbox(123, plan, plan_hash(plan))


@pytest.mark.parametrize("url,hosts", [
    ("postgresql://u@scratch.local/dbintel_sandbox_x", []),
    ("postgresql://u@scratch.local/dbintel_sandbox_x", ["other.host"]),
    ("postgresql://u@prod.local/dbintel_sandbox_x", ["scratch.local"]),
    ("postgresql://u@scratch.local/production", ["scratch.local"]),
    ("postgresql://u@scratch.local/xdbintel_sandbox_x", ["scratch.local"]),
    ("postgresql://u:pw@scratch.local/dbintel_sandbox_x", ["scratch.local"]),
    ("postgresql://u@scratch.local/dbintel_sandbox_x/../prod", ["scratch.local"]),
])
def test_scratch_server_refused_unless_allow_listed(url, hosts):
    plan = simple_plan()
    with pytest.raises(SandboxRefused):
        run_sandbox(None, plan, plan_hash(plan), scratch_url=url, allow_hosts=hosts, connect=lambda u: pytest.fail("connected"))


def test_scratch_server_dialect_mismatch_refused():
    plan = simple_plan()
    with pytest.raises(SandboxRefused):
        run_sandbox(None, plan, plan_hash(plan), scratch_url="mysql://u@h/dbintel_sandbox_x", allow_hosts=["h"], connect=lambda u: pytest.fail("connected"))


def test_scratch_server_used_when_allowed():
    calls = []

    class Cur:
        def execute(self, sql):
            calls.append(sql)

        def fetchall(self):
            return [(1,)]

    class Conn:
        def cursor(self):
            return Cur()

        def close(self):
            pass

    plan = generate_plan(model(), [finding("add_index", "orders", None, columns=["status"])])
    report = run_sandbox(None, plan, plan_hash(plan), scratch_url="postgresql://u@scratch.local/dbintel_sandbox_x", allow_hosts=["scratch.local"], connect=lambda u: Conn())
    assert report.engine == "postgres-scratch" and report.isolated
    assert calls


# --- no apply path ----------------------------------------------------------

def _functions_in(paths):
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                yield path, node


def test_no_public_apply_function_exists():
    pattern = re.compile(r"(?i)\b(apply|execute|run|deploy|migrate)_?(plan|migration|step|sql)|apply_to|migrate_(source|database)")
    src = ROOT / "src" / "dbintel"
    offenders = [f"{p.relative_to(src)}:{fn.name}" for p, fn in _functions_in(src.rglob("*.py")) if pattern.search(fn.name) and not fn.name.startswith("_")]
    assert offenders == []


def test_up_sql_only_executed_inside_sandbox_module():
    src = ROOT / "src" / "dbintel"
    offenders = []
    for path in src.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "up_sql" in text and ("execute(" in text or "executescript(" in text):
            offenders.append(path.name)
    assert set(offenders) <= {"sandbox.py"}


def test_generate_plan_does_not_write_through_data():
    db = sqlite_db()
    db.data.queries.clear()
    generate_plan(db, [finding("set_not_null", "child", "label")], "sqlite")
    assert db.data.queries and all(re.match(r"\s*SELECT\b", q, re.I) for q in db.data.queries)


def all_plans():
    for dialect in DIALECTS:
        db = model(dialect)
        yield dialect, generate_plan(db, [finding(*op[:1], op[1], op[2], **op[3]) for op in ALL_OPS if op[0] != "manual"], dialect)


def test_prechecks_and_postchecks_pass_the_connector_guard():
    for dialect, plan in all_plans():
        for step in plan.executable_steps:
            for check in step.prechecks + step.postchecks:
                assert_read_only(check.sql, dialect)


def test_connector_guard_rejects_every_generated_up_and_down_statement():
    for dialect, plan in all_plans():
        for step in plan.executable_steps:
            for statement in step.up_sql + step.down_sql:
                with pytest.raises(ReadOnlyViolation):
                    assert_read_only(statement, dialect)


def test_sqlite_connector_rejects_plan_and_leaves_database_unchanged(tmp_path):
    path = tmp_path / "source.db"
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE t (a int)")
    conn.commit()
    conn.close()
    plan = generate_plan(Database("x", "sqlite", tables=[Table("t", columns=[Column("a", "int", True)], row_count=0)]),
                         [finding("add_index", "t", None, columns=["a"])], "sqlite")
    connector = open_connector(f"sqlite:///{path.as_posix()}")
    try:
        for statement in plan.steps[0].up_sql:
            with pytest.raises(Exception) as caught:
                connector.query(statement)
            assert isinstance(caught.value, ReadOnlyViolation) or "read" in str(caught.value).lower()
    finally:
        connector.close()
    check = sqlite3.connect(path)
    assert check.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index'").fetchone()[0] == 0
    check.close()


# --- writer -----------------------------------------------------------------

def test_writer_outputs_numbered_files_and_warning(tmp_path):
    plan = generate_plan(model(), [finding("alter_column_type", "orders", "status", new_type="varchar(5)", fid="A"),
                                   finding("manual", "customers", description="decide")])
    written = write_migration_files(plan, tmp_path)
    names = sorted(p.name for p in written)
    assert any(n.startswith("0001_") and n.endswith(".up.sql") for n in names)
    assert any(n.endswith(".manual.txt") for n in names)
    assert "plan.json" in names and "README.md" in names
    readme = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert "PROPOSALS" in readme and "pg_basebackup" in readme and plan_hash(plan) in readme
    assert json.loads((tmp_path / "plan.json").read_text(encoding="utf-8"))["plan_hash"] == plan_hash(plan)


def test_writer_irreversible_down_file_has_no_statements(tmp_path):
    db = model(row_count=0)
    plan = generate_plan(db, [finding("alter_column_type", "customers", "name", new_type="varchar(5)")])
    write_migration_files(plan, tmp_path)
    down = next(tmp_path.glob("*.down.sql")).read_text(encoding="utf-8")
    assert "NOT REVERSIBLE" in down
    assert not [line for line in down.splitlines() if line.strip() and not line.startswith("--")]
