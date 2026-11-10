import json
import sqlite3

import pytest
import yaml

from dbintel.config import Profile
from dbintel.model import Column, Database, ForeignKey, Index, Table
from dbintel.rules.engine import CATALOG_DIR, RuleEngine


def catalog():
    return yaml.safe_load((CATALOG_DIR / "40_data_quality.yaml").read_text(encoding="utf-8"))


class SqliteData:
    dialect = "sqlite"

    def __init__(self, conn):
        self.conn = conn

    def query(self, sql, params=()):
        return self.conn.execute(sql, params).fetchall()

    def quote(self, identifier):
        return '"' + identifier.replace('"', '""') + '"'


def from_sqlite(script, **kw):
    conn = sqlite3.connect(":memory:")
    conn.executescript(script)
    tables = []
    for (name,) in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"):
        info = conn.execute(f'PRAGMA table_info("{name}")').fetchall()
        pk = [r[1] for r in sorted((x for x in info if x[5]), key=lambda x: x[5])]
        fks = {}
        for row in conn.execute(f'PRAGMA foreign_key_list("{name}")'):
            fk = fks.setdefault(row[0], ForeignKey(f"fk_{row[0]}", [], row[2], []))
            fk.columns.append(row[3])
            fk.ref_columns.append(row[4])
        indexes = []
        for row in conn.execute(f'PRAGMA index_list("{name}")'):
            if row[3] == "pk":
                continue
            cols = [r[2] for r in conn.execute(f'PRAGMA index_info("{row[1]}")')]
            indexes.append(Index(row[1], cols, unique=bool(row[2])))
        tables.append(Table(name, columns=[Column(r[1], r[2] or "text", not r[3]) for r in info], primary_key=pk,
                            foreign_keys=list(fks.values()), indexes=indexes))
    return Database("t", dialect="sqlite", tables=tables, data=SqliteData(conn), **kw)


def run(db, profile=None):
    findings, coverage = RuleEngine(profile or Profile(), catalog=catalog()).run(db)
    assert not coverage.errors, coverage.errors
    return findings


def by_rule(findings, rule):
    return [f for f in findings if f.rule_id == rule]


def lower(rule, **params):
    return Profile(rules={rule: {"params": params}})


def inserts(table, rows):
    return "".join(f"INSERT INTO {table} VALUES ({', '.join(repr(v) if v is not None else 'NULL' for v in row)});" for row in rows)


def test_catalog_valid():
    RuleEngine(Profile(), catalog=catalog())


def test_rules_are_skipped_without_data():
    db = Database("t", tables=[Table("a", columns=[Column("id", "int")], primary_key=["id"])])
    findings, coverage = RuleEngine(Profile(), catalog=catalog()).run(db)
    assert findings == [] and "DQ-001" in coverage.skipped and "input not available" in coverage.skipped["DQ-001"]


CLEAN = """
CREATE TABLE customers (id INTEGER PRIMARY KEY, code TEXT UNIQUE, name TEXT NOT NULL, email TEXT, currency TEXT);
CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL REFERENCES customers(id), total DECIMAL(12,2),
  status TEXT, start_date DATE, end_date DATE, created_at DATETIME);
CREATE TABLE journal_lines (id INTEGER PRIMARY KEY, journal_id INTEGER, debit DECIMAL(12,2), credit DECIMAL(12,2), status TEXT);
""" + inserts("customers", [(i, f"C{i}", f"Name{i}", f"u{i}@example.com", "USD") for i in range(1, 6)]) + inserts(
    "orders", [(i, i, 10.5, "open", "2024-01-01", "2024-02-01", "2024-01-01 00:00:00") for i in range(1, 6)]) + inserts(
    "journal_lines", [(1, 1, 100, 0, "posted"), (2, 1, 0, 100, "posted"), (3, 2, 50, 0, "posted"), (4, 2, 0, 50, "posted")])


def test_clean_database_has_no_findings():
    assert run(from_sqlite(CLEAN)) == []


def test_empty_table():
    hit = by_rule(run(from_sqlite("CREATE TABLE a (id INTEGER PRIMARY KEY);")), "DQ-001")
    assert hit[0].severity.value == "informational"


def test_exact_duplicates_without_key_is_confirmed():
    db = from_sqlite("CREATE TABLE ev (a TEXT, b TEXT);" + inserts("ev", [("x", "y"), ("x", "y"), ("p", "q")]))
    hit = by_rule(run(db), "DQ-002")[0]
    assert hit.kind.value == "confirmed_defect" and hit.fix.op == "manual" and hit.data["rows"] == 2


def test_exact_duplicates_excluding_key_is_context_dependent():
    db = from_sqlite("CREATE TABLE ev (id INTEGER PRIMARY KEY, a TEXT, b TEXT);" + inserts("ev", [(1, "x", "y"), (2, "x", "y")]))
    assert by_rule(run(db), "DQ-002")[0].kind.value == "context_dependent"


def test_natural_key_duplicates():
    db = from_sqlite("CREATE TABLE p (id INTEGER PRIMARY KEY, sku TEXT, currency_code TEXT);"
                     + inserts("p", [(1, "A", "USD"), (2, "A", "USD"), (3, "B", "USD"), (4, "C", "USD"), (5, "D", "USD")]))
    hits = by_rule(run(db), "DQ-003")
    assert [h.column for h in hits] == ["sku"] and hits[0].kind.value == "context_dependent" and hits[0].fix.op == "manual"


def test_natural_key_scoped_to_tenant_is_clean():
    db = from_sqlite("CREATE TABLE p (id INTEGER PRIMARY KEY, tenant_id INTEGER, sku TEXT);"
                     + inserts("p", [(1, 1, "A"), (2, 2, "A"), (3, 1, "B")]))
    assert not by_rule(run(db, Profile(tenancy="pool")), "DQ-003")


def test_unique_column_not_reported_as_natural_duplicate():
    db = from_sqlite("CREATE TABLE p (id INTEGER PRIMARY KEY, sku TEXT UNIQUE);" + inserts("p", [(1, "A"), (2, "B")]))
    assert not by_rule(run(db), "DQ-003")


def test_low_cardinality_code_is_not_natural_key():
    db = from_sqlite("CREATE TABLE p (id INTEGER PRIMARY KEY, code TEXT);" + inserts("p", [(i, "A") for i in range(1, 8)]))
    assert not by_rule(run(db), "DQ-003")


def test_unenforced_key_in_warehouse():
    db = from_sqlite("CREATE TABLE d (a INTEGER, b TEXT);" + inserts("d", [(1, "x"), (1, "y")]))
    db.tables[0].primary_key = ["a"]
    hit = by_rule(run(db, Profile(workload="data_warehouse")), "DQ-004")[0]
    assert hit.kind.value == "confirmed_defect" and hit.fix.op == "manual"
    assert not by_rule(run(db), "DQ-004")


def test_null_rates_respect_param():
    db = from_sqlite("CREATE TABLE n (id INTEGER PRIMARY KEY, val TEXT);" + inserts("n", [(i, None if i < 8 else "x") for i in range(1, 11)]))
    assert not by_rule(run(db), "DQ-005")
    hit = by_rule(run(db, lower("DQ-005", min_rows=5)), "DQ-005")[0]
    assert hit.column == "val" and "70%" in hit.evidence
    assert not by_rule(run(db, lower("DQ-005", min_rows=5, max_null_ratio=0.9)), "DQ-005")


def test_mandatory_looking_nulls():
    db = from_sqlite("CREATE TABLE c (id INTEGER PRIMARY KEY, name TEXT);" + inserts("c", [(1, "a"), (2, "b"), (3, "c"), (4, "d"), (5, None), (6, "e")]))
    hit = by_rule(run(db), "DQ-006")[0]
    assert hit.kind.value == "context_dependent" and hit.fix.op == "manual"


def test_mostly_null_name_is_not_mandatory_looking():
    db = from_sqlite("CREATE TABLE c (id INTEGER PRIMARY KEY, name TEXT);" + inserts("c", [(1, "a"), (2, None), (3, None)]))
    assert not by_rule(run(db), "DQ-006")


ORPHANS = """
CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER REFERENCES customers(id));
CREATE TABLE notes (id INTEGER PRIMARY KEY, customer_id INTEGER);
""" + inserts("customers", [(i, f"n{i}") for i in range(1, 21)]) + inserts(
    "orders", [(1, 1), (2, 2), (3, 999)]) + inserts("notes", [(i, i) for i in range(1, 20)] + [(50, 777)])


def test_orphans_declared_fk_confirmed_and_uses_manual_repair():
    hit = by_rule(run(from_sqlite(ORPHANS)), "DQ-007")[0]
    assert hit.kind.value == "confirmed_defect" and hit.fix.op == "manual"
    assert "automatically" in hit.fix.params["description"]


def test_strong_inferred_reference_is_confirmed():
    hit = by_rule(run(from_sqlite(ORPHANS)), "DQ-009")[0]
    assert hit.table == "notes" and hit.kind.value == "confirmed_defect" and hit.confidence == 0.85


def test_weak_inferred_reference_is_context_dependent():
    db = from_sqlite("CREATE TABLE customers (id INTEGER PRIMARY KEY); CREATE TABLE notes (id INTEGER PRIMARY KEY, customer_id INTEGER);"
                     + inserts("customers", [(1,), (2,), (3,)]) + inserts("notes", [(1, 1), (2, 2), (3, 3), (4, 900)]))
    hit = by_rule(run(db), "DQ-009")[0]
    assert hit.kind.value == "context_dependent" and hit.confidence == 0.5


def test_unrelated_id_column_is_not_inferred():
    db = from_sqlite("CREATE TABLE customers (id INTEGER PRIMARY KEY); CREATE TABLE notes (id INTEGER PRIMARY KEY, customer_id INTEGER);"
                     + inserts("customers", [(1,)]) + inserts("notes", [(1, 500), (2, 501), (3, 502)]))
    assert not by_rule(run(db), "DQ-009")


def test_orphans_in_warehouse_use_analytical_rule():
    f = run(from_sqlite(ORPHANS), Profile(workload="data_warehouse"))
    assert by_rule(f, "DQ-008") and not by_rule(f, "DQ-007")


def test_invalid_formats_masked_except_code_lists():
    db = from_sqlite("CREATE TABLE c (id INTEGER PRIMARY KEY, email TEXT, currency TEXT, birth_date TEXT);"
                     + inserts("c", [(1, "good@example.com", "USD", "2020-02-30"), (2, "not-an-email", "EURO", "2020-02-02"),
                                     (3, "a@b.co", "GBP", "2020-01-01")]))
    f = by_rule(run(db), "DQ-011")
    formats = {h.column: h for h in f}
    assert "not-an-email" not in formats["email"].evidence and "***" in formats["email"].evidence
    assert "EURO" in formats["currency"].evidence
    assert "2020-02-30" not in formats["birth_date"].evidence
    assert "good@example.com" not in json.dumps([x.to_dict() for x in f], default=str)


def test_valid_formats_clean():
    db = from_sqlite("CREATE TABLE c (id INTEGER PRIMARY KEY, email TEXT, currency TEXT, country_code TEXT, order_date TEXT, amount TEXT);"
                     + inserts("c", [(1, "a@b.co", "USD", "PK", "2024-01-01", "12.50"), (2, "b@c.io", "AED", "GB", "2024-02-29 10:00:00", "-3")]))
    assert not by_rule(run(db), "DQ-011")


def test_mostly_invalid_column_is_not_assumed_to_be_that_format():
    db = from_sqlite("CREATE TABLE c (id INTEGER PRIMARY KEY, email TEXT);" + inserts("c", [(1, "x"), (2, "y"), (3, "z"), (4, "a@b.co")]))
    assert not by_rule(run(db), "DQ-011")


def test_negative_only_for_configured_columns():
    db = from_sqlite("CREATE TABLE l (id INTEGER PRIMARY KEY, unit_price DECIMAL(10,2), balance DECIMAL(10,2));"
                     + inserts("l", [(1, -5, -100), (2, 3, 1)]))
    hits = by_rule(run(db), "DQ-012")
    assert [h.column for h in hits] == ["unit_price"] and hits[0].fix.op == "manual"


def test_future_dates_and_tolerance():
    db = from_sqlite("CREATE TABLE f (id INTEGER PRIMARY KEY, created_at DATETIME, due_at DATETIME);"
                     + inserts("f", [(1, "2999-01-01 00:00:00", "2999-01-01 00:00:00"), (2, "2020-01-01 00:00:00", "2020-01-01 00:00:00")]))
    hits = by_rule(run(db), "DQ-013")
    assert [h.column for h in hits] == ["created_at"]


def test_end_before_start():
    db = from_sqlite("CREATE TABLE r (id INTEGER PRIMARY KEY, valid_from DATE, valid_to DATE);"
                     + inserts("r", [(1, "2024-02-01", "2024-01-01"), (2, "2024-01-01", "2024-03-01")]))
    hit = by_rule(run(db), "DQ-014")[0]
    assert hit.column == "valid_to" and hit.kind.value == "confirmed_defect"


def test_casing_and_whitespace_variants_are_masked():
    db = from_sqlite("CREATE TABLE s (id INTEGER PRIMARY KEY, city TEXT);" + inserts("s", [(1, "Karachi"), (2, "karachi"), (3, " Lahore"), (4, "Lahore")]))
    hit = by_rule(run(db), "DQ-015")[0]
    assert hit.data["variant_groups"] == 2 and "Karachi" not in hit.evidence and "***" in hit.evidence


def test_constant_columns():
    db = from_sqlite("CREATE TABLE k (id INTEGER PRIMARY KEY, kind TEXT, tenant_id INTEGER);" + inserts("k", [(i, "same", 1) for i in range(1, 6)]))
    assert not by_rule(run(db), "DQ-016")
    hits = by_rule(run(db, lower("DQ-016", min_rows=3)), "DQ-016")
    assert [h.column for h in hits] == ["kind"]


JOURNAL = """
CREATE TABLE journal_lines (id INTEGER PRIMARY KEY, journal_id INTEGER, debit DECIMAL(12,2), credit DECIMAL(12,2), status TEXT);
""" + inserts("journal_lines", [(1, 1, 100, 0, "posted"), (2, 1, 0, 90, "posted"), (3, 2, 10, 0, "draft"), (4, 3, 5, 0, "posted"), (5, 3, 0, 5, "posted")])


def test_ledger_imbalance_cites_fin_025_and_ignores_drafts():
    hit = by_rule(run(from_sqlite(JOURNAL)), "FINA-001")[0]
    assert hit.standards == ["FIN-025"] and hit.kind.value == "confirmed_defect" and hit.severity.value == "critical"
    assert hit.data == {"unbalanced": 1, "checked": 2} and hit.fix.op == "manual"
    assert "Do not edit or delete" in hit.fix.params["description"]


def test_ledger_checks_posted_status_on_the_journal_header():
    db = from_sqlite("""
    CREATE TABLE journals (id INTEGER PRIMARY KEY, status TEXT);
    CREATE TABLE journal_lines (id INTEGER PRIMARY KEY, journal_id INTEGER REFERENCES journals(id), debit DECIMAL(12,2), credit DECIMAL(12,2));
    """ + inserts("journals", [(1, "posted"), (2, "draft")]) + inserts("journal_lines", [(1, 1, 10, 0), (2, 2, 7, 0)]))
    hit = by_rule(run(db), "FINA-001")[0]
    assert hit.data == {"unbalanced": 1, "checked": 1} and hit.confidence == 0.95


def test_ledger_without_status_has_lower_confidence():
    db = from_sqlite("CREATE TABLE gl_entries (id INTEGER PRIMARY KEY, journal_id INTEGER, debit DECIMAL(10,2), credit DECIMAL(10,2));"
                     + inserts("gl_entries", [(1, 1, 10, 0)]))
    hit = by_rule(run(db), "FINA-001")[0]
    assert hit.confidence == 0.7 and "drafts" in hit.evidence


def test_sample_never_splits_a_journal():
    rows = [(i, j, 10 if i % 2 else 0, 0 if i % 2 else 10, "posted") for j in range(1, 6) for i in [j * 10, j * 10 + 1]]
    db = from_sqlite("CREATE TABLE journal_lines (id INTEGER PRIMARY KEY, journal_id INTEGER, debit DECIMAL(12,2), credit DECIMAL(12,2), status TEXT);" + inserts("journal_lines", rows))
    assert not by_rule(run(db, Profile(data_sample_limit=3)), "FINA-001")


def test_document_totals():
    db = from_sqlite("""
    CREATE TABLE invoices (id INTEGER PRIMARY KEY, status TEXT, total DECIMAL(12,2));
    CREATE TABLE invoice_lines (id INTEGER PRIMARY KEY, invoice_id INTEGER REFERENCES invoices(id), amount DECIMAL(12,2));
    """ + inserts("invoices", [(1, "posted", 100), (2, "posted", 50), (3, "draft", 999)])
      + inserts("invoice_lines", [(1, 1, 60), (2, 1, 40), (3, 2, 10), (4, 3, 1)]))
    hit = by_rule(run(db), "FINA-002")[0]
    assert hit.data == {"mismatched": 1, "checked": 2} and hit.kind.value == "context_dependent" and hit.fix.op == "manual"


def test_document_totals_skipped_with_tax_column_and_no_net_total():
    db = from_sqlite("""
    CREATE TABLE invoices (id INTEGER PRIMARY KEY, status TEXT, total DECIMAL(12,2), tax_amount DECIMAL(12,2));
    CREATE TABLE invoice_lines (id INTEGER PRIMARY KEY, invoice_id INTEGER REFERENCES invoices(id), amount DECIMAL(12,2));
    """ + inserts("invoices", [(1, "posted", 118, 18)]) + inserts("invoice_lines", [(1, 1, 100)]))
    assert not by_rule(run(db), "FINA-002")


def test_number_gaps_are_context_dependent_and_require_legal_review():
    db = from_sqlite("CREATE TABLE invoices (id INTEGER PRIMARY KEY, invoice_number TEXT);"
                     + inserts("invoices", [(1, "INV-1"), (2, "INV-2"), (3, "INV-5"), (4, "CN-1"), (5, "CN-2")]))
    hit = by_rule(run(db), "FINA-003")[0]
    assert hit.kind.value == "context_dependent" and hit.data == {"gaps": 2, "series": 1}
    assert "requires legal review" in hit.recommended_solution.lower() and hit.provisional_standard


def test_no_gaps_clean_and_oversized_series_warns_instead_of_false_gaps():
    rows = [(i, f"INV-{i}") for i in range(1, 6)]
    db = from_sqlite("CREATE TABLE invoices (id INTEGER PRIMARY KEY, invoice_number TEXT);" + inserts("invoices", rows))
    assert not by_rule(run(db), "FINA-003")
    run(db, Profile(data_sample_limit=2))
    assert any("Document number gap check skipped" in w for w in db.import_warnings)


def test_sample_limit_bounds_table_scans():
    seen = []
    db = from_sqlite("CREATE TABLE ev (a TEXT, b TEXT);" + inserts("ev", [("x", "y")] * 20))
    inner = db.data.query
    db.data.query = lambda sql, params=(): seen.append(sql) or inner(sql, params)
    run(db, Profile(data_sample_limit=5))
    assert all("LIMIT" in s for s in seen)
    assert any("LIMIT 5" in s for s in seen)


def test_duplicates_never_suggest_deletion():
    db = from_sqlite("CREATE TABLE ev (a TEXT, b TEXT);" + inserts("ev", [("x", "y"), ("x", "y")]))
    hit = by_rule(run(db), "DQ-002")[0]
    text = (hit.fix.params["description"] + hit.recommended_solution + hit.migration_requirements).lower()
    assert "not delete" in text or "not deleted" in text
