"""Performance analyzer tests. Only this builder's catalog is loaded, because other catalogs may be changing."""
import json
import sqlite3
from pathlib import Path

import yaml

import dbintel.analyzers.performance as perf
from dbintel.config import Profile
from dbintel.model import Column, Database, ForeignKey, Index, QueryStat, Table
from dbintel.rules.engine import CATALOG_DIR, RuleEngine

CATALOG = yaml.safe_load(Path(CATALOG_DIR, "20_performance.yaml").read_text(encoding="utf-8"))


class SqliteData:
    dialect = "sqlite"

    def __init__(self, conn):
        self.conn = conn

    def query(self, sql, params=()):
        return self.conn.execute(sql, params).fetchall()

    def quote(self, identifier):
        return '"' + identifier.replace('"', '""') + '"'


def c(name, data_type="varchar(50)", nullable=False, **kw):
    return Column(name=name, data_type=data_type, nullable=nullable, **kw)


def pk(name="order_id", data_type="bigint"):
    return Column(name=name, data_type=data_type, nullable=False, is_identity=True)


def orders(*extra, **kw):
    return Table("orders", columns=[pk(), *extra], primary_key=["order_id"], **kw)


def database(*tables, dialect="postgres", stats=(), data=None):
    return Database(name="d", dialect=dialect, source="sql_dump", tables=list(tables), query_stats=list(stats), data=data)


def stat(sql, calls=100, total_ms=500.0, mean_ms=50.0, **kw):
    return QueryStat(sql=sql, calls=calls, total_ms=total_ms, mean_ms=mean_ms, **kw)


def run(db, profile=None):
    findings, coverage = RuleEngine(profile or Profile(), catalog=CATALOG).run(db)
    assert not coverage.errors, coverage.errors
    return findings


def ids(findings):
    return {f.rule_id for f in findings}


def one(db, rule_id, profile=None):
    matched = [f for f in run(db, profile) if f.rule_id == rule_id]
    assert matched, f"{rule_id} did not fire"
    return matched[0]


def query_table(rows=500000, *extra):
    return orders(c("customer_id", "bigint"), c("status"), c("email"), c("created_at", "timestamptz"), *extra, row_count=rows)


def test_clean_fixture_has_no_findings():
    fk = ForeignKey("fk", ["customer_id"], "customers", ["customer_id"], "RESTRICT", "RESTRICT")
    t = orders(c("customer_id", "bigint"), c("status"), row_count=5000, foreign_keys=[fk],
               indexes=[Index("index_orders_customer_id", ["customer_id"]), Index("index_orders_status", ["status"])])
    parent = Table("customers", columns=[pk("customer_id")], primary_key=["customer_id"], row_count=1000)
    s = stat("SELECT order_id, status FROM orders WHERE customer_id = $1 ORDER BY order_id LIMIT 20", calls=50, total_ms=100, mean_ms=2)
    assert [(f.rule_id, f.evidence) for f in run(database(t, parent, stats=[s]))] == []


def test_fk_without_index():
    fk = ForeignKey("fk", ["customer_id"], "customers", ["customer_id"])
    f = one(database(orders(c("customer_id", "bigint"), foreign_keys=[fk])), "PERF-001")
    assert f.fix.op == "add_index" and f.fix.params == {"columns": ["customer_id"], "unique": False}


def test_fk_with_index_silent():
    fk = ForeignKey("fk", ["customer_id"], "customers", ["customer_id"])
    t = orders(c("customer_id", "bigint"), foreign_keys=[fk], indexes=[Index("i", ["customer_id", "order_id"])])
    assert "PERF-001" not in ids(run(database(t)))


def test_fk_index_mysql_and_small_table_silent():
    fk = ForeignKey("fk", ["customer_id"], "customers", ["customer_id"])
    assert "PERF-001" not in ids(run(database(orders(c("customer_id", "bigint"), foreign_keys=[fk]), dialect="mysql")))
    t = orders(c("customer_id", "bigint"), foreign_keys=[fk], row_count=10)
    assert "PERF-001" not in ids(run(database(t)))


def test_fk_index_oltp_only():
    fk = ForeignKey("fk", ["customer_id"], "customers", ["customer_id"])
    db = database(orders(c("customer_id", "bigint"), foreign_keys=[fk]))
    assert "PERF-001" not in ids(run(db, Profile(workload="data_warehouse")))


def test_redundant_left_prefix():
    t = orders(c("a"), c("b"), indexes=[Index("short", ["a"]), Index("long", ["a", "b"])])
    f = one(database(t), "PERF-002")
    assert f.fix.op == "drop_index" and f.fix.params == {"name": "short"} and f.table == "orders"


def test_duplicate_index_keeps_one():
    t = orders(c("a"), indexes=[Index("idx_b", ["a"]), Index("idx_a", ["a"])])
    assert [f.fix.params["name"] for f in run(database(t)) if f.rule_id == "PERF-002"] == ["idx_b"]


def test_redundant_prefix_of_primary_key():
    t = Table("a_b", columns=[c("a_id", "bigint"), c("b_id", "bigint")], primary_key=["a_id", "b_id"],
              indexes=[Index("first_col", ["a_id"])])
    assert one(database(t), "PERF-002").fix.params == {"name": "first_col"}


def test_redundant_guards():
    t = orders(c("a"), c("b"), indexes=[Index("uniq", ["a"], unique=True), Index("long", ["a", "b"]),
                                        Index("partial", ["b"], where="a = 1"), Index("other", ["b", "a"]),
                                        Index("gin_a", ["a"], method="gin")])
    assert "PERF-002" not in ids(run(database(t)))


def test_too_many_indexes():
    t = orders(*[c(f"a{i}") for i in range(10)], indexes=[Index(f"i{i}", [f"a{i}"]) for i in range(9)])
    assert one(database(t), "PERF-003").fix.op == "manual"


def test_too_many_indexes_counts_only_secondary():
    t = orders(*[c(f"a{i}") for i in range(10)], indexes=[Index(f"i{i}", [f"a{i}"]) for i in range(8)])
    assert "PERF-003" not in ids(run(database(t)))


def test_missing_index_for_query():
    s = stat("SELECT order_id FROM orders WHERE customer_id = 5 AND created_at > '2024-01-01'")
    f = one(database(query_table(), stats=[s]), "PERF-004")
    assert f.fix.op == "add_index" and f.fix.params["columns"] == ["customer_id", "created_at"]


def test_missing_index_join_column():
    parent = Table("customers", columns=[pk("customer_id")], primary_key=["customer_id"], row_count=500000)
    s = stat("SELECT o.order_id FROM customers c JOIN orders o ON o.customer_id = c.customer_id")
    f = one(database(query_table(), parent, stats=[s]), "PERF-004")
    assert f.table == "orders" and f.fix.params["columns"] == ["customer_id"]


def test_missing_index_guards():
    assert "PERF-004" not in ids(run(database(
        orders(c("customer_id", "bigint"), indexes=[Index("i", ["customer_id"])], row_count=500000),
        stats=[stat("SELECT 1 FROM orders WHERE customer_id = 5")])))
    assert "PERF-004" not in ids(run(database(query_table(50), stats=[stat("SELECT 1 FROM orders WHERE customer_id = 5")])))
    assert "PERF-004" not in ids(run(database(query_table(), stats=[stat("SELECT 1 FROM orders WHERE customer_id = 5", calls=1)])))
    assert "PERF-004" not in ids(run(database(query_table(500000, c("is_paid", "boolean")),
                                              stats=[stat("SELECT 1 FROM orders WHERE is_paid = true")])))


def test_missing_index_unknown_size_lower_confidence():
    t = query_table(None)
    f = one(database(t, stats=[stat("SELECT 1 FROM orders WHERE customer_id = 5")]), "PERF-004")
    assert f.confidence == 0.5


def test_wide_index():
    t = orders(*[c(f"a{i}", "int") for i in range(6)], indexes=[Index("wide", [f"a{i}" for i in range(6)])])
    assert one(database(t), "PERF-005").fix.op == "manual"
    t2 = orders(c("x", "varchar(1000)"), indexes=[Index("wide2", ["x"])])
    assert "PERF-005" in ids(run(database(t2)))


def test_wide_index_guard():
    assert "PERF-005" not in ids(run(database(orders(c("x", "int"), indexes=[Index("i", ["x"])]))))


def _selectivity_db(values):
    t = orders(c("kind"), indexes=[Index("idx_kind", ["kind"])])
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE orders (kind TEXT)")
    conn.executemany("INSERT INTO orders VALUES (?)", [(v,) for v in values])
    return database(t, data=SqliteData(conn))


def test_low_selectivity():
    f = one(_selectivity_db(["a", "b"] * 6000), "PERF-006")
    assert f.fix.params == {"name": "idx_kind"} and f.kind.value == "context_dependent"


def test_low_selectivity_skewed_keeps_index():
    assert "PERF-006" not in ids(run(_selectivity_db(["a"] * 11900 + ["b"] * 100)))


def test_low_selectivity_needs_data():
    assert "PERF-006" not in ids(run(database(orders(c("kind"), indexes=[Index("i", ["kind"])]))))


def test_non_sargable_function():
    s = stat("SELECT order_id FROM orders WHERE LOWER(email) = 'a@b.c'")
    f = one(database(query_table(), stats=[s]), "PERF-010")
    assert f.column == "email" and f.fix.op == "manual" and "a@b.c" not in f.evidence


def test_non_sargable_wildcard_and_arithmetic():
    db = database(query_table(), stats=[stat("SELECT 1 FROM orders WHERE email LIKE '%x'"),
                                        stat("SELECT 1 FROM orders WHERE customer_id + 1 = 5")])
    assert sum(1 for f in run(db) if f.rule_id == "PERF-010") == 2


def test_non_sargable_guards():
    t = query_table()
    db = database(t, stats=[stat("SELECT 1 FROM orders WHERE email LIKE 'x%'"),
                            stat("SELECT 1 FROM orders WHERE customer_id = ABS(5)"),
                            stat("SELECT COUNT(*) FROM orders WHERE status = 'a'")])
    assert "PERF-010" not in ids(run(db))
    t2 = query_table(500000)
    t2.indexes = [Index("expr", ["lower(email)"])]
    assert "PERF-010" not in ids(run(database(t2, stats=[stat("SELECT 1 FROM orders WHERE LOWER(email) = 'a'")])))


def test_select_star():
    assert one(database(query_table(), stats=[stat("SELECT * FROM orders WHERE status = 'a' LIMIT 1")]), "PERF-011").fix.op == "manual"


def test_select_star_guards():
    db = database(query_table(), stats=[stat("SELECT COUNT(*) FROM orders"),
                                        stat("WITH x AS (SELECT status FROM orders) SELECT * FROM x"),
                                        stat("SELECT status FROM orders WHERE EXISTS (SELECT * FROM orders)")])
    assert "PERF-011" not in ids(run(db))


def test_offset_pagination():
    f = one(database(query_table(), stats=[stat("SELECT order_id FROM orders ORDER BY order_id LIMIT 20 OFFSET 5000")]), "PERF-012")
    assert f.severity.value == "medium" and f.confidence == 0.85


def test_offset_parameterized_is_lower():
    f = one(database(query_table(), stats=[stat("SELECT order_id FROM orders LIMIT 20 OFFSET $1")]), "PERF-012")
    assert f.severity.value == "low" and f.confidence == 0.5


def test_offset_shallow_silent():
    assert "PERF-012" not in ids(run(database(query_table(), stats=[stat("SELECT 1 FROM orders LIMIT 20 OFFSET 40")])))


def test_implicit_conversion():
    s = stat("SELECT 1 FROM orders WHERE status = 5")
    f = one(database(query_table(), stats=[s]), "PERF-013")
    assert f.table == "orders" and f.column == "status"
    s2 = stat("SELECT 1 FROM orders WHERE customer_id = 'abc'")
    assert "PERF-013" in ids(run(database(query_table(), stats=[s2])))


def test_implicit_conversion_guards():
    db = database(query_table(), stats=[stat("SELECT 1 FROM orders WHERE customer_id = '5'"),
                                        stat("SELECT 1 FROM orders WHERE status = 'open'"),
                                        stat("SELECT 1 FROM orders WHERE customer_id = $1")])
    assert "PERF-013" not in ids(run(db))


def test_unbounded_result():
    assert one(database(query_table(), stats=[stat("SELECT order_id FROM orders")]), "PERF-014").fix.op == "manual"


def test_unbounded_guards():
    db = database(query_table(), stats=[stat("SELECT COUNT(*) FROM orders"), stat("SELECT status FROM orders GROUP BY status"),
                                        stat("SELECT order_id FROM orders LIMIT 10")])
    assert "PERF-014" not in ids(run(db))
    assert "PERF-014" not in ids(run(database(query_table(100), stats=[stat("SELECT order_id FROM orders")])))


def test_n_plus_one():
    s = stat("SELECT email FROM orders WHERE order_id = 1", calls=5000, total_ms=1000, mean_ms=0.2)
    assert one(database(query_table(), stats=[s]), "PERF-015").kind.value == "context_dependent"


def test_n_plus_one_aggregates_logged_repeats():
    stats = [stat(f"SELECT email FROM orders WHERE order_id = {i}", calls=300, total_ms=10, mean_ms=0.1) for i in range(5)]
    assert one(database(query_table(), stats=stats), "PERF-015")


def test_n_plus_one_guards():
    s = stat("SELECT email FROM orders WHERE customer_id = 5", calls=5000, rows=50000)
    assert "PERF-015" not in ids(run(database(query_table(), stats=[s])))
    s2 = stat("SELECT email FROM orders WHERE order_id = 5", calls=10)
    assert "PERF-015" not in ids(run(database(query_table(), stats=[s2])))


def test_expensive_query():
    stats = [stat("SELECT 1 FROM orders WHERE status = 'a'", calls=10, total_ms=120000, mean_ms=12000),
             stat("SELECT 2 FROM orders WHERE status = 'b'", calls=10, total_ms=10, mean_ms=1)]
    findings = [f for f in run(database(query_table(), stats=stats)) if f.rule_id == "PERF-016"]
    assert len(findings) == 1


def test_expensive_query_below_threshold():
    assert "PERF-016" not in ids(run(database(query_table(), stats=[stat("SELECT 1 FROM orders", total_ms=500)])))


PG_TEXT = """Sort  (cost=1.00..2.00 rows=200000 width=8)
  Sort Key: created_at
  Sort Method: external merge  Disk: 1024kB
  ->  Seq Scan on orders  (cost=0.00..1.00 rows=200000 width=8)
"""

PG_JSON = json.dumps([{"Plan": {"Node Type": "Sort", "Plan Rows": 300000, "Plans": [
    {"Node Type": "Seq Scan", "Relation Name": "orders", "Plan Rows": 300000}]}}])

MYSQL_JSON = json.dumps({"query_block": {"ordering_operation": {"using_filesort": True, "table": {
    "table_name": "orders", "access_type": "ALL", "rows_examined_per_scan": 400000}}}})

MYSQL_TABLE = """+----+-------------+--------+------+---------------+------+---------+------+--------+----------------+
| id | select_type | table  | type | possible_keys | key  | key_len | ref  | rows   | Extra          |
+----+-------------+--------+------+---------------+------+---------+------+--------+----------------+
|  1 | SIMPLE      | orders | ALL  | NULL          | NULL | NULL    | NULL | 900000 | Using filesort |
+----+-------------+--------+------+---------------+------+---------+------+--------+----------------+"""

MYSQL_VERTICAL = """*************************** 1. row ***************************
           id: 1
        table: orders
         type: ALL
         rows: 900000
        Extra: Using filesort
"""

MYSQL_TREE = "-> Table scan on orders  (cost=100 rows=900000)"


def test_parse_plans():
    for plan in (PG_TEXT, PG_JSON, MYSQL_JSON, MYSQL_TABLE, MYSQL_VERTICAL):
        nodes = perf.parse_plan(plan)
        assert {"seq", "sort"} <= {n.kind for n in nodes}, plan
        assert all(n.rows and n.rows >= 200000 or n.kind == "sort" for n in nodes)
    assert perf.parse_plan(MYSQL_TREE)[0].relation == "orders"
    assert perf.parse_plan("not a plan") == []
    assert perf.parse_plan(None) == []


def test_plan_seq_scan_and_filesort():
    db = database(query_table(), stats=[stat("SELECT 1 FROM orders ORDER BY created_at", plan=PG_TEXT)])
    found = ids(run(db))
    assert {"PERF-020", "PERF-021"} <= found


def test_plan_small_table_silent():
    small = "Seq Scan on orders  (cost=0.00..1.00 rows=20 width=8)"
    assert "PERF-020" not in ids(run(database(query_table(20), stats=[stat("SELECT 1 FROM orders", plan=small)])))


def test_plan_filesort_external_small_row_count():
    plan = "Sort  (cost=1..2 rows=10 width=8)\n  Sort Method: external merge  Disk: 100kB"
    assert "PERF-021" in ids(run(database(query_table(20), stats=[stat("SELECT 1 FROM orders", plan=plan)])))


def test_key_exhaustion_from_counter():
    t = Table("orders", columns=[c("order_id", "int", is_identity=True)], primary_key=["order_id"])
    db = database(t)
    db.settings["auto_increment"] = {"orders": 2000000000}
    f = one(db, "PERF-030")
    assert f.severity.value == "critical" and f.fix.params["new_type"] == "bigint"


def test_key_exhaustion_from_data():
    t = Table("orders", columns=[Column("order_id", "int", nullable=False, is_identity=True)], primary_key=["order_id"])
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE orders (order_id INT)")
    conn.execute("INSERT INTO orders VALUES (1500000000)")
    db = database(t, data=SqliteData(conn))
    f = one(db, "PERF-030")
    assert f.severity.value == "high"


def test_key_exhaustion_from_row_count_lower_bound():
    t = Table("orders", columns=[Column("order_id", "int unsigned", nullable=False, is_identity=True)],
              primary_key=["order_id"], row_count=3000000000)
    f = one(database(t), "PERF-030")
    assert f.fix.params["new_type"] == "bigint unsigned"


def test_key_exhaustion_guards():
    t = Table("orders", columns=[Column("order_id", "int", nullable=False, is_identity=True)], primary_key=["order_id"], row_count=1000)
    assert "PERF-030" not in ids(run(database(t)))
    t2 = Table("orders", columns=[Column("order_id", "bigint", nullable=False, is_identity=True)], primary_key=["order_id"], row_count=2 ** 40)
    assert "PERF-030" not in ids(run(database(t2)))


def test_partition_key_missing():
    t = orders(c("created_at", "timestamptz"), partition_columns=["YEAR(created_at)"])
    f = one(database(t), "PERF-031")
    assert f.severity.value == "high" and f.column == "created_at" and f.kind.value == "confirmed_defect"


def test_partition_key_present_silent():
    t = Table("orders", columns=[pk(), c("created_at", "timestamptz")], primary_key=["order_id", "created_at"],
              partition_columns=["created_at"])
    assert "PERF-031" not in ids(run(database(t)))


def test_partition_non_enforcing_dialect_context():
    t = orders(c("created_at", "timestamptz"), partition_columns=["created_at"])
    assert one(database(t, dialect="generic"), "PERF-031").kind.value == "context_dependent"


def test_large_table_unpartitioned():
    t = orders(c("created_at", "timestamptz"), row_count=200000000)
    assert one(database(t), "PERF-032").kind.value == "context_dependent"


def test_large_table_guards():
    assert "PERF-032" not in ids(run(database(orders(row_count=200000000))))
    t = orders(c("created_at", "timestamptz"), row_count=200000000, partition_columns=["created_at"])
    assert "PERF-032" not in ids(run(database(t)))


def test_uuid_clustered_innodb():
    t = Table("orders", columns=[Column("order_id", "char(36)", nullable=False)], primary_key=["order_id"])
    assert one(database(t, dialect="mysql"), "PERF-033").kind.value == "context_dependent"


def test_uuid_clustered_guards():
    t = Table("orders", columns=[Column("order_id", "char(36)", nullable=False)], primary_key=["order_id"])
    assert "PERF-033" not in ids(run(database(t, dialect="postgres")))
    t2 = Table("orders", columns=[Column("order_id", "char(36)", nullable=False)], primary_key=["order_id"], engine="MyISAM")
    assert "PERF-033" not in ids(run(database(t2, dialect="mysql")))


def test_unparseable_sql_is_skipped():
    db = database(query_table(), stats=[stat("THIS IS NOT SQL (((")])
    assert ids(run(db)) <= {"PERF-016"}


def test_profile_disable():
    t = orders(c("a"), indexes=[Index("short", ["a"]), Index("long", ["a", "c1"])])
    profile = Profile(rules={"PERF-002": {"enabled": False}})
    assert "PERF-002" not in ids(run(database(t), profile))


def test_profile_severity():
    t = orders(c("a"), indexes=[Index("short", ["a"]), Index("long", ["a", "c1"])])
    assert one(database(t), "PERF-002", Profile(rules={"PERF-002": {"severity": "high"}})).severity.value == "high"


def test_profile_params():
    t = orders(*[c(f"a{i}") for i in range(4)], indexes=[Index(f"i{i}", [f"a{i}"]) for i in range(4)])
    assert "PERF-003" not in ids(run(database(t)))
    assert "PERF-003" in ids(run(database(t), Profile(rules={"PERF-003": {"params": {"max_indexes": 3}}})))


def test_query_rules_skip_without_stats():
    findings, coverage = RuleEngine(Profile(), catalog=CATALOG).run(database(query_table()))
    assert "input not available" in coverage.skipped["PERF-010"]
