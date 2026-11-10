"""Schema analyzer tests. Only this builder's catalog is loaded, because other catalogs may be changing."""
import sqlite3
from pathlib import Path

import pytest
import yaml

import dbintel.analyzers.schema  # noqa: F401
from dbintel.config import Profile
from dbintel.model import CheckConstraint, Column, Database, ForeignKey, Index, Table
from dbintel.rules.engine import CATALOG_DIR, RuleEngine, load_standards

CATALOG = yaml.safe_load(Path(CATALOG_DIR, "10_schema.yaml").read_text(encoding="utf-8"))


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


def pk(name="id", data_type="bigint"):
    return Column(name=name, data_type=data_type, nullable=False, is_identity=True)


def tbl(name, *columns, key=None, **kw):
    cols = list(columns)
    if key is None:
        key = [cols[0].name]
    return Table(name=name, columns=cols, primary_key=key, **kw)


def database(*tables, dialect="postgres", data=None):
    return Database(name="d", dialect=dialect, source="sql_dump", tables=list(tables), data=data)


def with_data(db, *statements):
    conn = sqlite3.connect(":memory:")
    for s in statements:
        conn.execute(s)
    db.data = SqliteData(conn)
    return db


def run(db, profile=None, catalog=CATALOG):
    findings, coverage = RuleEngine(profile or Profile(), catalog=catalog).run(db)
    assert not coverage.errors, coverage.errors
    return findings


def ids(findings):
    return {f.rule_id for f in findings}


def one(db, rule_id, profile=None):
    matched = [f for f in run(db, profile) if f.rule_id == rule_id]
    assert matched, f"{rule_id} did not fire"
    return matched[0]


def customers():
    return tbl("customers", pk("customer_id"), c("email_address", "varchar(255)"))


def orders(*extra, fks=None):
    return tbl("orders", pk("order_id"), *extra, foreign_keys=fks or [])


def clean_db():
    audit = [c("created_at", "timestamptz"), c("updated_at", "timestamptz"), c("created_by", "varchar(255)"),
             c("updated_by", "varchar(255)")]
    cust = tbl("customers", pk("customer_id"), c("full_name", "varchar(200)"), c("is_active", "boolean"),
               c("email_address", "varchar(255)"), *audit, primary_key_name="pk_customers",
               indexes=[Index("unique_customers_email_address", ["email_address"], unique=True)])
    order = tbl("orders", pk("order_id"), c("customer_id", "bigint"), c("net_amount", "decimal(19,4)"),
                c("currency_code", "char(3)"), c("order_date", "date"), c("order_status", "varchar(20)"), *audit,
                primary_key_name="pk_orders",
                foreign_keys=[ForeignKey("fk_orders_customer_id", ["customer_id"], "customers", ["customer_id"],
                                         on_delete="RESTRICT", on_update="NO ACTION")],
                indexes=[Index("index_orders_customer_id", ["customer_id"])],
                checks=[CheckConstraint("check_orders_status", "order_status IN ('open','paid')", ["order_status"])])
    return database(cust, order)


def test_catalog_valid_and_only_real_standards():
    standards = load_standards()
    RuleEngine(Profile(), catalog=CATALOG)
    for rule in CATALOG:
        for sid in rule["standards"]:
            assert standards[sid]["status"] != "superseded"
        if any(standards[s]["level"] == "MANDATORY" for s in rule["standards"]):
            assert rule["severity"] in ("high", "critical"), rule["id"]


def test_yaml_lists_are_strings():
    for rule in CATALOG:
        for key, value in (rule.get("params") or {}).items():
            if isinstance(value, list):
                assert all(isinstance(x, (str, int)) and x is not True and x is not False for x in value), (rule["id"], key)


def test_clean_fixture_has_no_findings():
    assert [(f.rule_id, f.evidence) for f in run(clean_db())] == []


def test_missing_primary_key():
    db = database(Table("logs", columns=[c("a")]))
    f = one(db, "SCH-001")
    assert f.severity.value == "critical"
    assert f.fix.op == "add_surrogate_primary_key"


def test_missing_pk_promotes_unique_key():
    t = Table("logs", columns=[c("a")], indexes=[Index("u", ["a"], unique=True)])
    assert one(database(t), "SCH-001").fix.params["columns"] == ["a"]


def test_missing_pk_is_oltp_only():
    db = database(Table("logs", columns=[c("a")]))
    assert "SCH-001" not in ids(run(db, Profile(workload="data_warehouse")))


def test_inferred_fk_name_only():
    f = one(database(customers(), orders(c("customer_id", "bigint"))), "SCH-002")
    assert f.kind.value == "context_dependent" and f.confidence == 0.55
    assert f.fix.op == "add_foreign_key" and f.fix.params["ref_table"] == "customers"
    assert f.fix.params["ref_columns"] == ["customer_id"]


def test_inferred_fk_verified_raises_confidence():
    db = with_data(database(customers(), orders(c("customer_id", "bigint"))),
                   "CREATE TABLE customers (customer_id INT)", "CREATE TABLE orders (customer_id INT)",
                   *[f"INSERT INTO customers VALUES ({i})" for i in range(30)],
                   *[f"INSERT INTO orders VALUES ({i})" for i in range(30)])
    assert one(db, "SCH-002").confidence == 0.85


def test_inferred_fk_suppressed_when_values_do_not_match():
    db = with_data(database(customers(), orders(c("customer_id", "bigint"))),
                   "CREATE TABLE customers (customer_id INT)", "CREATE TABLE orders (customer_id INT)",
                   *[f"INSERT INTO customers VALUES ({i})" for i in range(30)],
                   *[f"INSERT INTO orders VALUES ({i + 1000})" for i in range(30)])
    assert "SCH-002" not in ids(run(db))


def test_inferred_fk_excludes_external_and_incompatible():
    db = database(customers(), orders(c("stripe_id"), c("customer_id", "uuid"), c("old_customer_xid", "bigint")))
    assert "SCH-002" not in ids(run(db))


def test_fk_type_mismatch():
    fk = ForeignKey("fk_orders_customer_id", ["customer_id"], "customers", ["customer_id"], "RESTRICT", "RESTRICT")
    f = one(database(customers(), orders(c("customer_id", "int"), fks=[fk])), "SCH-003")
    assert f.fix.op == "alter_column_type" and f.fix.params["new_type"] == "bigint"


def test_fk_type_serial_is_int_equivalent():
    parent = tbl("customers", pk("customer_id", "serial"))
    fk = ForeignKey("fk", ["customer_id"], "customers", ["customer_id"], "RESTRICT", "RESTRICT")
    assert "SCH-003" not in ids(run(database(parent, orders(c("customer_id", "integer"), fks=[fk]))))


def test_fk_collation_mismatch():
    parent = tbl("customers", pk("customer_id"), c("code", "varchar(10)", charset="utf8mb4", collation="utf8mb4_bin"),
                 indexes=[Index("u", ["code"], unique=True)])
    fk = ForeignKey("fk", ["code"], "customers", ["code"], "RESTRICT", "RESTRICT")
    child = orders(c("code", "varchar(10)", charset="utf8mb4", collation="utf8mb4_general_ci"), fks=[fk])
    assert one(database(parent, child), "SCH-003").fix.op == "manual"


def test_nullable_primary_key():
    t = tbl("a", Column("x", "int", nullable=True))
    f = one(database(t), "SCH-004")
    assert f.fix.op == "set_not_null" and f.severity.value == "high"


def test_composite_fk_partially_nullable():
    fk = ForeignKey("fk", ["a", "b"], "p", ["a", "b"], "RESTRICT", "RESTRICT")
    t = tbl("orders", pk("order_id"), c("a"), c("b", nullable=True), foreign_keys=[fk])
    assert one(database(t), "SCH-005").fix.op == "set_not_null"


def test_nullable_fk_without_nulls_requires_data():
    fk = ForeignKey("fk", ["customer_id"], "customers", ["customer_id"], "RESTRICT", "RESTRICT")
    t = orders(c("customer_id", "bigint", nullable=True), fks=[fk])
    db = database(customers(), t)
    assert "SCH-006" not in ids(run(db))
    with_data(db, "CREATE TABLE orders (customer_id INT)", *[f"INSERT INTO orders VALUES ({i})" for i in range(120)])
    assert one(db, "SCH-006").fix.op == "set_not_null"


def test_nullable_fk_with_nulls_is_silent():
    fk = ForeignKey("fk", ["customer_id"], "customers", ["customer_id"], "RESTRICT", "RESTRICT")
    t = orders(c("customer_id", "bigint", nullable=True), fks=[fk])
    db = with_data(database(customers(), t), "CREATE TABLE orders (customer_id INT)",
                   *[f"INSERT INTO orders VALUES ({'NULL' if i % 2 else i})" for i in range(120)])
    assert "SCH-006" not in ids(run(db))


def test_fk_no_explicit_actions():
    fk = ForeignKey("fk_orders_customer_id", ["customer_id"], "customers", ["customer_id"])
    t = orders(c("customer_id", "bigint"), fks=[fk])
    assert one(database(customers(), t), "SCH-007").fix.op == "manual"


def test_repeating_columns():
    t = orders(c("phone1"), c("phone2"), c("phone3"))
    f = one(database(t), "SCH-010")
    assert f.severity.value == "high" and f.fix.op == "manual"


def test_repeating_columns_false_positive_guards():
    t = orders(c("address1"), c("address2"), c("address3"), c("sha256"), c("sha512"), c("q1"), c("q2"))
    assert "SCH-010" not in ids(run(database(t)))


def test_delimited_list_by_name_without_data():
    f = one(database(orders(c("role_ids", "text"))), "SCH-011")
    assert f.kind.value == "context_dependent" and f.confidence == 0.5


def test_delimited_list_verified_from_data():
    db = with_data(database(orders(c("alt_contacts", "varchar(200)"))),
                   "CREATE TABLE orders (alt_contacts TEXT)",
                   *["INSERT INTO orders VALUES ('a@x.io,b@x.io')" for _ in range(30)])
    f = one(db, "SCH-011")
    assert f.kind.value == "confirmed_defect" and f.confidence == 0.9


def test_delimited_list_ignores_free_text_and_numbers():
    db = with_data(database(orders(c("alt_contacts", "varchar(200)"), c("amount_text", "varchar(50)"))),
                   "CREATE TABLE orders (alt_contacts TEXT, amount_text TEXT)",
                   *["INSERT INTO orders VALUES ('12 Oak Street, Springfield', '1,234.50')" for _ in range(30)])
    assert "SCH-011" not in ids(run(db))


def test_redundant_attribute_without_data():
    parent = tbl("customers", pk("customer_id"), c("loyalty_tier"))
    fk = ForeignKey("fk", ["customer_id"], "customers", ["customer_id"], "RESTRICT", "RESTRICT")
    f = one(database(parent, orders(c("customer_id", "bigint"), c("loyalty_tier"), fks=[fk])), "SCH-012")
    assert f.confidence == 0.4 and f.kind.value == "context_dependent"


def _redundant_db(child_value):
    parent = tbl("customers", pk("customer_id"), c("loyalty_tier"))
    fk = ForeignKey("fk", ["customer_id"], "customers", ["customer_id"], "RESTRICT", "RESTRICT")
    return with_data(database(parent, orders(c("customer_id", "bigint"), c("loyalty_tier"), fks=[fk])),
                     "CREATE TABLE customers (customer_id INT, loyalty_tier TEXT)",
                     "CREATE TABLE orders (customer_id INT, loyalty_tier TEXT)",
                     *[f"INSERT INTO customers VALUES ({i}, 'gold')" for i in range(30)],
                     *[f"INSERT INTO orders VALUES ({i}, '{child_value}')" for i in range(30)])


def test_redundant_attribute_verified():
    assert one(_redundant_db("gold"), "SCH-012").confidence == 0.85


def test_redundant_attribute_snapshot_suppressed():
    assert "SCH-012" not in ids(run(_redundant_db("silver")))


def test_redundant_attribute_ignores_generic_and_money():
    parent = tbl("customers", pk("customer_id"), c("status"), c("unit_price", "decimal(10,2)"))
    fk = ForeignKey("fk", ["customer_id"], "customers", ["customer_id"], "RESTRICT", "RESTRICT")
    child = orders(c("customer_id", "bigint"), c("status"), c("unit_price", "decimal(10,2)"), fks=[fk])
    assert "SCH-012" not in ids(run(database(parent, child)))


def _fd_db(values):
    t = orders(c("customer_id", "bigint"), c("customer_name"))
    inserts = []
    for i in range(30):
        for j in range(3):
            inserts.append(f"INSERT INTO orders VALUES ({i}, '{values(i, j)}')")
    return with_data(database(t), "CREATE TABLE orders (customer_id INT, customer_name TEXT)", *inserts)


def test_functional_dependency_verified():
    f = one(_fd_db(lambda i, j: f"name{i}"), "SCH-013")
    assert f.confidence == 0.8 and f.fix.op == "manual"


def test_functional_dependency_counter_example():
    assert "SCH-013" not in ids(run(_fd_db(lambda i, j: f"name{i}{j}")))


def test_float_money():
    f = one(database(orders(c("net_amount", "double"))), "SCH-020")
    assert f.severity.value == "critical" and f.fix.params["new_type"] == "decimal(19,4)"


def test_float_money_name_guards():
    db = database(orders(c("tax_rate", "float"), c("total_rows", "float"), c("cost_center_ratio", "real")))
    assert "SCH-020" not in ids(run(db))


def test_proprietary_money():
    assert one(database(orders(c("net_amount", "money"))), "SCH-021").fix.params["new_type"] == "decimal(19,4)"


def test_low_scale_money():
    assert one(database(orders(c("net_amount", "decimal(10,0)"))), "SCH-022").fix.params["new_type"] == "decimal(12,2)"


def test_multi_currency_scale_and_exclusions():
    db = database(orders(c("net_amount", "decimal(19,2)"), c("unit_price", "decimal(19,2)"), c("currency_code", "char(3)")))
    findings = [f for f in run(db) if f.rule_id == "SCH-023"]
    assert [f.column for f in findings] == ["net_amount"]


def test_multi_currency_scale_silent_when_single_currency():
    assert "SCH-023" not in ids(run(database(orders(c("net_amount", "decimal(19,2)")))))


def test_amount_without_currency():
    db = database(orders(c("net_amount", "decimal(19,4)")), tbl("currencies", pk("currency_id"), c("iso", "char(3)")))
    f = one(db, "SCH-024")
    assert f.fix.op == "add_column" and f.fix.params["type"] == "char(3)" and f.fix.column == "currency_code"


def test_amount_currency_from_parent_is_silent():
    parent = orders(c("currency_code", "char(3)"))
    fk = ForeignKey("fk", ["order_id"], "orders", ["order_id"], "RESTRICT", "RESTRICT")
    lines = tbl("order_lines", pk("order_line_id"), c("order_id", "bigint"), c("line_amount", "decimal(19,4)"),
                foreign_keys=[fk])
    assert "SCH-024" not in ids(run(database(parent, lines)))


def test_timestamp_without_zone_postgres():
    f = one(database(orders(c("created_at", "timestamp"))), "SCH-030")
    assert f.fix.params["new_type"] == "timestamptz" and f.kind.value == "context_dependent"


def test_timestamp_mysql_timestamp_is_utc_normalizing():
    assert "SCH-030" not in ids(run(database(orders(c("created_at", "timestamp")), dialect="mysql")))


def test_timestamp_mysql_datetime_needs_decision():
    assert one(database(orders(c("created_at", "datetime")), dialect="mysql"), "SCH-030").fix.op == "manual"


def test_timestamp_utc_comment_is_silent():
    assert "SCH-030" not in ids(run(database(orders(c("created_at", "datetime", comment="Stored in UTC")))))


def test_date_as_text_name_only():
    f = one(database(orders(c("invoice_date"))), "SCH-031")
    assert f.kind.value == "context_dependent" and f.fix.params["new_type"] == "date"


def test_date_as_text_verified():
    db = with_data(database(orders(c("invoice_date"))), "CREATE TABLE orders (invoice_date TEXT)",
                   *["INSERT INTO orders VALUES ('2024-01-15')" for _ in range(30)])
    f = one(db, "SCH-031")
    assert f.kind.value == "confirmed_defect" and f.confidence == 0.9


def test_date_as_text_suppressed_by_data():
    db = with_data(database(orders(c("invoice_date"))), "CREATE TABLE orders (invoice_date TEXT)",
                   *["INSERT INTO orders VALUES ('not a date')" for _ in range(30)])
    assert "SCH-031" not in ids(run(db))


def test_number_as_text():
    db = with_data(database(orders(c("qty"))), "CREATE TABLE orders (qty TEXT)",
                   *[f"INSERT INTO orders VALUES ('{i + 1}')" for i in range(30)])
    assert one(db, "SCH-032").fix.params["new_type"] == "bigint"


def test_number_as_text_leading_zero_is_code():
    db = with_data(database(orders(c("qty"))), "CREATE TABLE orders (qty TEXT)",
                   *[f"INSERT INTO orders VALUES ('00{i}')" for i in range(30)])
    assert "SCH-032" not in ids(run(db))


def test_number_as_text_ignores_identifiers():
    db = with_data(database(orders(c("account_number"))), "CREATE TABLE orders (account_number TEXT)",
                   *[f"INSERT INTO orders VALUES ('{i + 1000}')" for i in range(30)])
    assert "SCH-032" not in ids(run(db))


def test_boolean_as_int():
    assert one(database(orders(c("is_active", "int"))), "SCH-033").fix.params["new_type"] == "boolean"


def test_boolean_char_needs_manual():
    assert one(database(orders(c("is_active", "char(1)"))), "SCH-033").fix.op == "manual"


def test_boolean_mysql_tinyint_accepted():
    assert "SCH-033" not in ids(run(database(orders(c("is_active", "tinyint")), dialect="mysql")))


def test_boolean_data_with_many_values_is_silent():
    db = with_data(database(orders(c("is_active", "int"))), "CREATE TABLE orders (is_active INT)",
                   *[f"INSERT INTO orders VALUES ({i})" for i in range(5)])
    assert "SCH-033" not in ids(run(db))


def test_enum_prefer_lookup():
    db = database(orders(c("stage", "enum('a','b','c','d','e')")))
    assert one(db, "SCH-034").fix.op == "manual"
    assert "SCH-034" not in ids(run(database(orders(c("stage", "enum('a','b')")))))


def test_json_in_text_explicit_name():
    f = one(database(orders(c("options_json", "text"))), "SCH-035")
    assert f.kind.value == "context_dependent" and f.fix.params["new_type"] == "jsonb"


def test_json_in_text_verified():
    db = with_data(database(orders(c("payload", "text"))), "CREATE TABLE orders (payload TEXT)",
                   *["INSERT INTO orders VALUES ('{\"a\": 1}')" for _ in range(15)])
    assert one(db, "SCH-035").kind.value == "confirmed_defect"


def test_json_likely_name_without_data_is_silent():
    assert "SCH-035" not in ids(run(database(orders(c("payload", "text")))))


def test_uuid_as_text():
    assert one(database(orders(c("customer_uuid", "char(36)"))), "SCH-036").fix.params["new_type"] == "uuid"


def test_uuid_as_text_verified_on_id_candidate():
    value = "550e8400-e29b-41d4-a716-446655440000"
    db = with_data(database(orders(c("external_ref_id", "char(36)"))), "CREATE TABLE orders (external_ref_id TEXT)",
                   *[f"INSERT INTO orders VALUES ('{value}')" for _ in range(30)])
    assert one(db, "SCH-036").kind.value == "confirmed_defect"


def test_uuid_mysql_is_manual():
    assert one(database(orders(c("row_uuid", "char(36)")), dialect="mysql"), "SCH-036").fix.op == "manual"


def test_key_32bit():
    t = tbl("orders", pk("order_id", "int"))
    assert one(database(t), "SCH-037").fix.params["new_type"] == "bigint"


def test_key_32bit_lookup_table_exempt():
    assert "SCH-037" not in ids(run(database(tbl("order_statuses", pk("id", "int")))))
    assert "SCH-037" not in ids(run(database(tbl("regions", pk("id", "int"), row_count=20))))


def test_key_natural_int_not_generated():
    t = Table("orders", columns=[Column("order_no", "int", nullable=False)], primary_key=["order_no"])
    assert "SCH-037" not in ids(run(database(t)))


def test_nullable_by_default():
    t = orders(*[c(f"a{i}", nullable=True) for i in range(6)])
    assert one(database(t), "SCH-038").fix.op == "manual"


def test_same_name_type_mismatch():
    t1 = tbl("a_things", pk("a_id"), c("region_id", "bigint"))
    t2 = tbl("b_things", pk("b_id"), c("region_id", "bigint"))
    t3 = tbl("c_things", pk("c_id"), c("region_id", "int"))
    f = one(database(t1, t2, t3), "SCH-039")
    assert f.table == "c_things" and f.fix.params["new_type"] == "bigint"


def test_same_name_type_tie_is_manual():
    t1 = tbl("a_things", pk("a_id"), c("region_id", "bigint"))
    t2 = tbl("b_things", pk("b_id"), c("region_id", "int"))
    assert one(database(t1, t2), "SCH-039").fix.op == "manual"


def test_same_name_length_differences_are_ignored():
    t1 = tbl("a_things", pk("a_id"), c("region_id", "varchar(10)"))
    t2 = tbl("b_things", pk("b_id"), c("region_id", "varchar(20)"))
    assert "SCH-039" not in ids(run(database(t1, t2)))


def test_polymorphic_pair():
    t = tbl("comments", pk("comment_id"), c("commentable_type"), c("commentable_id", "bigint"))
    assert one(database(t), "SCH-040").fix.op == "manual"


def test_polymorphic_guard_real_parent():
    t = tbl("attachments", pk("attachment_id"), c("document_type"), c("document_id", "bigint"))
    assert "SCH-040" not in ids(run(database(t, tbl("documents", pk("document_id")))))


def test_eav_shape():
    t = tbl("product_attributes", pk("id"), c("product_id", "bigint"), c("attribute_name"), c("attribute_value"))
    assert one(database(t), "SCH-041").fix.op == "manual"


def test_key_value_config_is_not_eav():
    assert "SCH-041" not in ids(run(database(tbl("settings", pk("id"), c("property"), c("value")))))


def test_god_table():
    t = orders(*[c(f"col_x{i}") for i in range(61)])
    assert one(database(t), "SCH-042").fix.op == "manual"


def test_charset_mixture():
    t1 = tbl("a_things", pk("a_id"), c("x", charset="utf8mb4", collation="utf8mb4_bin"))
    t2 = tbl("b_things", pk("b_id"), c("x", charset="utf8mb4", collation="utf8mb4_bin"))
    t3 = tbl("c_things", pk("c_id"), c("x", charset="latin1", collation="latin1_swedish_ci"))
    t4 = tbl("d_things", pk("d_id"), c("x", charset="utf8mb4", collation="utf8mb4_general_ci"))
    findings = [f for f in run(database(t1, t2, t3, t4)) if f.rule_id == "SCH-043"]
    assert {f.table for f in findings} == {"c_things", "d_things"}


def test_missing_audit_columns():
    f = one(database(orders()), "SCH-044")
    assert f.fix.op == "add_column" and f.fix.column == "created_at"
    assert f.fix.params["type"] == "timestamptz" and f.fix.params["nullable"] is True


def test_audit_exempt_and_association_tables():
    profile = Profile(audit_exempt_tables=["orders"])
    assert "SCH-044" not in ids(run(database(orders()), profile))
    fks = [ForeignKey("fa", ["a_id"], "a", ["id"], "RESTRICT", "RESTRICT"),
           ForeignKey("fb", ["b_id"], "b", ["id"], "RESTRICT", "RESTRICT")]
    link = Table("a_b", columns=[c("a_id", "bigint"), c("b_id", "bigint")], primary_key=["a_id", "b_id"], foreign_keys=fks)
    assert "SCH-044" not in ids(run(database(link)))


def test_table_no_relationships():
    db = database(tbl("alpha_things", pk("a")), tbl("betas", pk("b")))
    assert one(db, "SCH-045").severity.value == "informational"


def test_table_no_relationships_needs_two_tables():
    assert "SCH-045" not in ids(run(database(tbl("alphas", pk("a")))))


def test_status_without_check_data():
    db = with_data(database(orders(c("order_status"))), "CREATE TABLE orders (order_status TEXT)",
                   "INSERT INTO orders VALUES ('open')", "INSERT INTO orders VALUES ('paid')")
    f = one(db, "SCH-046")
    assert f.fix.op == "add_check" and "'open', 'paid'" in f.fix.params["expression"]


def test_status_without_check_many_values_silent():
    db = with_data(database(orders(c("order_status"))), "CREATE TABLE orders (order_status TEXT)",
                   *[f"INSERT INTO orders VALUES ('{i}')" for i in range(50)])
    assert "SCH-046" not in ids(run(db))


def test_status_without_data_is_manual():
    assert one(database(orders(c("order_status"))), "SCH-046").fix.op == "manual"


def test_unbounded_varchar_informational():
    f = one(database(orders(c("label_x", "varchar"))), "SCH-047")
    assert f.severity.value == "informational"
    assert "SCH-047" not in ids(run(database(orders(c("description", "varchar")))))


def test_reserved_word_column_and_table():
    f = one(database(orders(c("order"))), "SCH-050")
    assert f.severity.value == "high" and f.fix.op == "rename_column" and f.fix.params["new_name"] == "order_value"
    t = one(database(tbl("user", pk("user_id"))), "SCH-050")
    assert t.fix.op == "rename_table" and t.fix.params["new_name"] == "users"


def test_reserved_word_respects_engines():
    db = database(orders(c("user")), dialect="mysql")
    assert "SCH-050" not in ids(run(db, Profile(target_engines=["mysql"])))
    assert "SCH-050" in ids(run(db, Profile(target_engines=["postgres", "mysql"])))


def test_non_reserved_keywords_not_flagged():
    assert "SCH-050" not in ids(run(database(orders(c("name"), c("status"), c("value"), c("type")))))


def test_identifier_characters():
    f = one(database(orders(c("bad name"), c("1st"))), "SCH-051")
    assert f.severity.value == "high" and f.fix.op == "rename_column"


def test_identifier_case():
    f = one(database(orders(c("createdDate"))), "SCH-052")
    assert f.fix.params["new_name"] == "created_date"


def test_identifier_length():
    f = one(database(orders(c("x" * 70))), "SCH-053")
    assert f.severity.value == "high" and len(f.fix.params["new_name"]) == 63


def test_identifier_collision():
    assert one(database(orders(c("Total", "int"), c("total", "int"))), "SCH-054").fix.op == "manual"


def test_table_plural_each_when_mixed():
    db = database(*[tbl(n, pk("x")) for n in ("orders", "customers", "items", "product")])
    f = one(db, "SCH-055")
    assert f.table == "product" and f.fix.op == "rename_table" and f.fix.params["new_name"] == "products"


def test_table_plural_uniform_singular_reported_once():
    db = database(*[tbl(n, pk("x")) for n in ("order", "customer", "item", "product", "invoice")])
    findings = [f for f in run(db) if f.rule_id == "SCH-055"]
    assert len(findings) == 1 and findings[0].table is None and findings[0].fix.op == "manual"


def test_table_singular_convention():
    db = database(tbl("products", pk("x")))
    assert "SCH-055" in ids(run(db, Profile(table_plural=False)))
    assert "SCH-055" not in ids(run(database(tbl("product", pk("x"))), Profile(table_plural=False)))


def test_table_uncountable_not_flagged():
    assert "SCH-055" not in ids(run(database(tbl("audit_log", pk("x")), tbl("inventory", pk("y")))))


def test_type_prefix():
    db = database(tbl("tbl_customers", pk("customer_id")), orders(c("str_label")))
    assert {f.fix.params["new_name"] for f in run(db) if f.rule_id == "SCH-056"} == {"customers", "label"}


def test_pk_naming_single_table():
    db = database(tbl("customers", pk("id")), tbl("orders", pk("order_id")), tbl("items", pk("item_id")))
    f = one(db, "SCH-057")
    assert f.fix.params["new_name"] == "customer_id"


def test_pk_naming_uniform_bare_id_reported_once():
    db = database(tbl("customers", pk("id")), tbl("orders", pk("id")), tbl("items", pk("id")))
    findings = [f for f in run(db) if f.rule_id == "SCH-057"]
    assert len(findings) == 1 and findings[0].table is None


def test_fk_naming():
    fk = ForeignKey("fk", ["cust"], "customers", ["customer_id"], "RESTRICT", "RESTRICT")
    t = orders(c("cust", "bigint"), fks=[fk])
    assert one(database(customers(), t), "SCH-058").fix.params["new_name"] == "customer_id"


def test_fk_naming_role_and_self_reference_ok():
    fk1 = ForeignKey("fk1", ["billing_customer_id"], "customers", ["customer_id"], "RESTRICT", "RESTRICT")
    fk2 = ForeignKey("fk2", ["parent_order_id"], "orders", ["order_id"], "RESTRICT", "RESTRICT")
    t = orders(c("billing_customer_id", "bigint"), c("parent_order_id", "bigint"), fks=[fk1, fk2])
    assert "SCH-058" not in ids(run(database(customers(), t)))


def test_constraint_naming():
    fk = ForeignKey("orders_customer_id_fkey", ["customer_id"], "customers", ["customer_id"], "RESTRICT", "RESTRICT")
    t = orders(c("customer_id", "bigint"), fks=[fk])
    t.indexes = [Index("idx_x", ["customer_id"])]
    assert one(database(customers(), t), "SCH-059").fix.op == "manual"


def test_constraint_naming_mysql_primary_exempt():
    t = orders()
    t.primary_key_name = "PRIMARY"
    assert "SCH-059" not in ids(run(database(t), catalog=[r for r in CATALOG if r["id"] == "SCH-059"]))


def test_boolean_naming():
    assert one(database(orders(c("active", "boolean"))), "SCH-060").fix.params["new_name"] == "is_active"


def test_temporal_naming():
    f = one(database(orders(c("placed_on", "timestamptz"))), "SCH-061")
    assert f.fix.params["new_name"] == "placed_at"
    d = one(database(orders(c("ship_day_x", "date"))), "SCH-061")
    assert d.fix.params["new_name"] == "ship_day_x_date"


def test_profile_disable():
    db = database(Table("logs", columns=[c("a")]))
    profile = Profile(rules={"SCH-001": {"enabled": False}})
    findings, coverage = RuleEngine(profile, catalog=CATALOG).run(db)
    assert "SCH-001" not in ids(findings) and coverage.skipped["SCH-001"] == "disabled by configuration"


def test_profile_severity_override():
    db = database(Table("logs", columns=[c("a")]))
    assert one(db, "SCH-001", Profile(rules={"SCH-001": {"severity": "low"}})).severity.value == "low"


def test_profile_params_override():
    t = orders(*[c(f"col_x{i}") for i in range(10)])
    assert "SCH-042" not in ids(run(database(t)))
    assert "SCH-042" in ids(run(database(t), Profile(rules={"SCH-042": {"params": {"max_columns": 5}}})))


def test_sampled_values_do_not_appear_in_evidence():
    secret = "topsecret"
    db = with_data(database(orders(c("alt_contacts", "varchar(200)"))), "CREATE TABLE orders (alt_contacts TEXT)",
                   *[f"INSERT INTO orders VALUES ('{secret},b')" for _ in range(30)])
    assert all(secret not in f.evidence for f in run(db))


def test_unreadable_data_falls_back_to_metadata():
    class Broken:
        dialect = "sqlite"

        def query(self, sql, params=()):
            raise RuntimeError("no access")

        def quote(self, identifier):
            return identifier

    db = database(customers(), orders(c("customer_id", "bigint")), data=Broken())
    assert one(db, "SCH-002").confidence == 0.55
