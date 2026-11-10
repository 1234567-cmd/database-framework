import json
import sqlite3
from pathlib import Path

import pytest
import yaml

from dbintel.analyzers.security import is_luhn_valid, looks_like_pan, mask_value
from dbintel.config import Profile
from dbintel.model import Column, Database, ForeignKey, Grant, Index, RlsPolicy, Role, Table
from dbintel.rules.engine import CATALOG_DIR, RuleEngine, load_standards

CARD = "4111111111111111"
SSN = "123-45-6789"
EMAIL = "jane.doe@example.com"
PLAIN = "hunter2secret"
BCRYPT = "$2b$12$" + "a" * 53


def catalog():
    return yaml.safe_load((CATALOG_DIR / "30_security.yaml").read_text(encoding="utf-8"))


class SqliteData:
    dialect = "sqlite"

    def __init__(self, conn):
        self.conn = conn

    def query(self, sql, params=()):
        return self.conn.execute(sql, params).fetchall()

    def quote(self, identifier):
        return '"' + identifier.replace('"', '""') + '"'


def from_sqlite(ddl, **kw):
    conn = sqlite3.connect(":memory:")
    conn.executescript(ddl)
    tables = []
    for (name,) in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"):
        info = conn.execute(f'PRAGMA table_info("{name}")').fetchall()
        tables.append(Table(name, columns=[Column(r[1], r[2], not r[3]) for r in info],
                            primary_key=[r[1] for r in sorted((x for x in info if x[5]), key=lambda x: x[5])]))
    return Database("t", dialect=kw.pop("dialect", "sqlite"), tables=tables, data=SqliteData(conn), **kw)


def run(db, profile=None):
    findings, coverage = RuleEngine(profile or Profile(), catalog=catalog()).run(db)
    assert not coverage.errors, coverage.errors
    return findings


def ids(findings):
    return {f.rule_id for f in findings}


def by_rule(findings, rule):
    return [f for f in findings if f.rule_id == rule]


POOL = Profile(tenancy="pool", system_of_record=True, tenant_exempt_tables=["tenants", "countries"])


def tcol(nullable=False):
    return Column("tenant_id", "bigint", nullable)


def clean_tenant_db():
    orders = Table("orders", columns=[tcol(), Column("id", "bigint", False)], primary_key=["tenant_id", "id"], rls_enabled=True)
    lines = Table("order_lines", columns=[tcol(), Column("id", "bigint", False), Column("order_id", "bigint", False)],
                  primary_key=["tenant_id", "id"], rls_enabled=True,
                  foreign_keys=[ForeignKey("fk", ["tenant_id", "order_id"], "orders", ["tenant_id", "id"])],
                  indexes=[Index("uq", ["tenant_id", "order_id"], unique=True)])
    return Database("clean", dialect="postgres", tables=[orders, lines], security_metadata=True,
                    roles=[Role("app_user", password_set=True, host="10.0.0.1")],
                    grants=[Grant("app_user", "SELECT", "orders"), Grant("app_user", "INSERT", "order_lines")],
                    policies=[RlsPolicy("orders", "p", "tenant_id = current_tenant()"),
                              RlsPolicy("order_lines", "p", "tenant_id = current_tenant()")],
                    settings={"ssl": "on"})


# ---- catalog ----

def test_catalog_valid_and_prefixes_distinct():
    RuleEngine(Profile(), catalog=catalog())
    standards = load_standards()
    for rule in catalog():
        assert rule["id"] not in standards
        assert rule["id"].split("-")[0] in {"SECA", "TENA"}


def test_legal_standards_are_context_dependent_and_say_requires_legal_review():
    standards = load_standards()
    for path in ("30_security.yaml", "40_data_quality.yaml", "50_data_engineering.yaml", "60_governance.yaml"):
        for rule in yaml.safe_load((CATALOG_DIR / path).read_text(encoding="utf-8")):
            legal = [s for s in rule["standards"] if standards[s]["status"] == "provisional"
                     and "legal review" in standards[s]["rationale"].lower()]
            if legal:
                assert rule["kind"] == "context_dependent", rule["id"]
                text = " ".join(str(rule[k]) for k in ("root_cause", "business_impact", "solution", "technical_impact"))
                assert "requires legal review" in text.lower(), rule["id"]


# ---- clean fixture ----

def test_clean_tenant_database_has_no_findings():
    assert run(clean_tenant_db(), POOL) == []


def test_exempt_tables_are_not_tenant_scoped():
    db = clean_tenant_db()
    db.tables.append(Table("countries", columns=[Column("id", "bigint", False)], primary_key=["id"]))
    assert run(db, POOL) == []


def test_tenant_rules_do_not_run_outside_tenant_profile():
    db = Database("x", dialect="postgres", tables=[Table("orders", columns=[Column("id", "bigint", False)], primary_key=["id"])])
    assert not {i for i in ids(run(db, Profile(tenancy="none"))) if i.startswith("TENA")}


# ---- roles and grants ----

def role_db(roles=(), grants=()):
    return Database("r", tables=[Table("orders", columns=[Column("id", "bigint", False)], primary_key=["id"])],
                    roles=list(roles), grants=list(grants), security_metadata=True)


def test_runtime_superuser_is_critical_and_revoke_ddl():
    db = role_db([Role("app_user", superuser=True)], [Grant("app_user", "DROP", "orders")])
    hits = by_rule(run(db), "SECA-001")
    assert len(hits) == 2
    assert next(h for h in hits if h.fix.op == "manual").severity.value == "critical"
    revoke = next(h for h in hits if h.fix.op == "revoke_grant")
    assert revoke.fix.params == {"grantee": "app_user", "privilege": "DROP"}


def test_admin_role_is_not_a_runtime_role():
    db = role_db([Role("db_admin", superuser=True)], [Grant("db_admin", "DROP", "orders")])
    assert not by_rule(run(db), "SECA-001")


@pytest.mark.parametrize("grant,expected_kind", [
    (Grant("PUBLIC", "SELECT", "orders"), "confirmed_defect"),
    (Grant("reporter", "ALL PRIVILEGES", "orders"), "confirmed_defect"),
    (Grant("reporter", "SELECT", "*"), "context_dependent"),
    (Grant("reporter", "SELECT", "orders", grantable=True), "context_dependent"),
])
def test_broad_grants(grant, expected_kind):
    hits = by_rule(run(role_db(grants=[grant])), "SECA-002")
    assert len(hits) == 1 and hits[0].kind.value == expected_kind


def test_narrow_grant_is_not_broad_and_public_usage_ignored():
    grants = [Grant("reporter", "SELECT", "orders"), Grant("PUBLIC", "USAGE", None)]
    assert not by_rule(run(role_db(grants=grants)), "SECA-002")


def test_weak_logins():
    db = role_db([Role("a", password_set=False), Role("b", password_set=True, host="%"), Role("c", can_login=False, password_set=False)])
    assert sorted(f.kind.value for f in by_rule(run(db), "SECA-003")) == ["confirmed_defect", "context_dependent"]


def test_audit_table_writable_by_runtime():
    db = role_db(grants=[Grant("app_user", "UPDATE", "audit_log"), Grant("app_user", "INSERT", "audit_log")])
    db.tables.append(Table("audit_log", columns=[Column("id", "bigint", False)], primary_key=["id"]))
    hits = by_rule(run(db), "SECA-010")
    assert len(hits) == 1 and hits[0].fix.op == "revoke_grant" and hits[0].fix.params["privilege"] == "UPDATE"


# ---- tenant isolation ----

def test_tenant_column_missing_and_nullable():
    db = Database("t", dialect="postgres", tables=[
        Table("orders", columns=[Column("id", "bigint", False)], primary_key=["id"], rls_enabled=False),
        Table("invoices", columns=[tcol(True), Column("id", "bigint", False)], primary_key=["id"], rls_enabled=False)])
    f = run(db, POOL)
    missing = by_rule(f, "TENA-001")
    assert len(missing) == 1 and missing[0].table == "orders" and missing[0].fix.op == "add_column"
    assert missing[0].severity.value == "critical"
    assert missing[0].fix.params["nullable"] is True
    nullable = by_rule(f, "TENA-003")
    assert len(nullable) == 1 and nullable[0].fix.op == "set_not_null"
    assert by_rule(f, "TENA-004")[0].fix.op == "manual"


def test_bridge_uses_recommended_rule():
    db = Database("t", tables=[Table("orders", columns=[Column("id", "bigint", False)], primary_key=["id"])])
    f = run(db, Profile(tenancy="bridge"))
    assert not by_rule(f, "TENA-001")
    assert by_rule(f, "TENA-002")[0].kind.value == "optional_improvement"


def test_unique_key_without_tenant_uses_composite_index_fix():
    t = Table("customers", columns=[tcol(), Column("id", "bigint", False), Column("code", "text", False)],
              primary_key=["tenant_id", "id"], indexes=[Index("uq", ["code"], unique=True)])
    hit = by_rule(run(Database("t", tables=[t]), POOL), "TENA-005")[0]
    assert hit.fix.op == "add_index" and hit.fix.params == {"columns": ["tenant_id", "code"], "unique": True}


def test_fk_cross_tenant_detected_and_fix_depends_on_parent_key():
    child = Table("order_lines", columns=[tcol(), Column("id", "bigint", False), Column("order_id", "bigint", False)],
                  primary_key=["tenant_id", "id"], foreign_keys=[ForeignKey("fk", ["order_id"], "orders", ["id"])])
    parent = Table("orders", columns=[tcol(), Column("id", "bigint", False)], primary_key=["id"])
    hit = by_rule(run(Database("t", tables=[child, parent]), POOL), "TENA-006")[0]
    assert hit.fix.op == "manual" and hit.kind.value == "context_dependent"
    parent.indexes.append(Index("uq", ["tenant_id", "id"], unique=True))
    hit = by_rule(run(Database("t", tables=[child, parent]), POOL), "TENA-006")[0]
    assert hit.fix.op == "add_foreign_key"
    assert hit.fix.params["columns"] == ["tenant_id", "order_id"]
    assert hit.fix.params["ref_columns"] == ["tenant_id", "id"]


def test_rls_only_on_postgres_and_fix():
    t = Table("orders", columns=[tcol(), Column("id", "bigint", False)], primary_key=["tenant_id", "id"], rls_enabled=False)
    assert by_rule(run(Database("t", dialect="postgres", tables=[t]), POOL), "TENA-007")[0].fix.params == {"tenant_column": "tenant_id"}
    assert not by_rule(run(Database("t", dialect="mysql", tables=[t]), POOL), "TENA-007")


def test_rls_unknown_is_not_reported():
    t = Table("orders", columns=[tcol(), Column("id", "bigint", False)], primary_key=["tenant_id", "id"])
    assert not by_rule(run(Database("t", dialect="postgres", tables=[t]), POOL), "TENA-007")


def test_rls_enabled_without_policy():
    t = Table("orders", columns=[tcol(), Column("id", "bigint", False)], primary_key=["tenant_id", "id"], rls_enabled=True)
    hit = by_rule(run(Database("t", dialect="postgres", tables=[t], security_metadata=True), POOL), "TENA-007")[0]
    assert hit.fix.op == "manual"


def test_rls_bypass_runtime_is_a_defect_others_informational():
    t = Table("orders", columns=[tcol(), Column("id", "bigint", False)], primary_key=["tenant_id", "id"], rls_enabled=True)
    db = Database("t", dialect="postgres", tables=[t], security_metadata=True,
                  roles=[Role("app_user", bypass_rls=True), Role("db_admin", superuser=True)],
                  policies=[RlsPolicy("orders", "p")])
    hits = {h.data.get("x") or h.title: h for h in by_rule(run(db, POOL), "TENA-008")}
    kinds = sorted(h.kind.value for h in hits.values())
    assert kinds == ["confirmed_defect", "context_dependent"]
    assert any(h.severity.value == "critical" for h in hits.values())
    assert any(h.severity.value == "informational" for h in hits.values())


def test_per_tenant_objects():
    db = Database("t", tables=[Table("tenant_42_orders", columns=[tcol(), Column("id", "bigint", False)], primary_key=["tenant_id", "id"])])
    assert by_rule(run(db, POOL), "TENA-009")


def test_company_column_only_in_multi_company_profile():
    t = Table("journal_entries", columns=[tcol(), Column("id", "bigint", False)], primary_key=["tenant_id", "id"])
    assert not by_rule(run(Database("t", tables=[t]), POOL), "TENA-010")
    profile = Profile(tenancy="pool", multi_company=True)
    hit = by_rule(run(Database("t", tables=[t]), profile), "TENA-010")[0]
    assert hit.column == "company_id" and hit.fix.op == "add_column"
    shared = Table("customers", columns=[tcol(), Column("id", "bigint", False)], primary_key=["tenant_id", "id"])
    assert not by_rule(run(Database("t", tables=[shared]), profile), "TENA-010")


def test_tenant_isolation_rules_cite_only_tenant_standards_in_scope():
    rules = {r["id"]: r for r in catalog() if r["id"].startswith("TENA")}
    assert all(r["workloads"] == ["OLTP"] for r in rules.values())


# ---- masking and sensitive data ----

BROKEN_SENSITIVE = f"""
CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT, password TEXT, ssn TEXT, card_number TEXT, note TEXT);
INSERT INTO users VALUES (1, '{EMAIL}', '{PLAIN}', '{SSN}', '{CARD}', 'hi');
INSERT INTO users VALUES (2, 'x@example.org', '{PLAIN}x', '987-65-4321', '5500005555555559', 'ok');
CREATE TABLE payments (id INTEGER PRIMARY KEY, cvv TEXT, track2 TEXT, card_pin TEXT, pin TEXT);
CREATE TABLE pins (id INTEGER PRIMARY KEY, pin TEXT, pin_code TEXT);
"""


def test_mask_value_never_returns_the_value():
    for v in (EMAIL, CARD, SSN, "short", "abc1234567"):
        masked = mask_value(v)
        assert v not in masked and "***" in masked


def test_mask_keeps_at_most_last_two_characters():
    assert mask_value(CARD).endswith("11") and len(mask_value(CARD)) == 5


def test_luhn():
    assert is_luhn_valid(CARD) and not is_luhn_valid("4111111111111112")
    assert looks_like_pan("4111 1111 1111 1111") and not looks_like_pan("1111111111111111") and not looks_like_pan("12345")


def test_raw_sensitive_values_do_not_appear_anywhere():
    findings = run(from_sqlite(BROKEN_SENSITIVE))
    blob = json.dumps([f.to_dict() for f in findings], default=str)
    for raw in (EMAIL, CARD, SSN, PLAIN, "5500005555555559", "x@example.org", "987-65-4321"):
        assert raw not in blob, raw
    assert ids(findings) >= {"SECA-004", "SECA-005", "SECA-006", "SECA-007", "SECA-008"}


def test_sampling_categories():
    hits = {f.column: f for f in by_rule(run(from_sqlite(BROKEN_SENSITIVE)), "SECA-005") if f.data}
    assert hits["email"].data["matched"] == 2 and "j***@***.com" in hits["email"].evidence
    assert hits["ssn"].data["matched"] == 2


def test_card_rule_is_context_dependent_and_mentions_legal_review():
    hit = next(f for f in by_rule(run(from_sqlite(BROKEN_SENSITIVE)), "SECA-007") if f.column == "card_number")
    assert hit.kind.value == "context_dependent" and "requires legal review" in hit.recommended_solution.lower()
    assert hit.provisional_standard and hit.confidence == 0.9


def test_name_match_without_data_gives_low_confidence_card_finding():
    db = Database("t", tables=[Table("cards", columns=[Column("card_number", "text"), Column("id", "bigint", False)], primary_key=["id"])])
    hit = by_rule(run(db), "SECA-007")[0]
    assert hit.confidence == 0.5


def test_tokenized_card_column_is_not_reported():
    db = from_sqlite("CREATE TABLE c (id INTEGER PRIMARY KEY, card_number TEXT); INSERT INTO c VALUES (1,'tok_abcdefghijklmnop');")
    assert not by_rule(run(db), "SECA-007")


def test_forbidden_columns():
    columns = {f.column for f in by_rule(run(from_sqlite(BROKEN_SENSITIVE)), "SECA-006")}
    assert columns == {"cvv", "track2", "card_pin", "pin"}


def test_plain_pin_outside_payment_table_not_flagged():
    db = from_sqlite("CREATE TABLE locations (id INTEGER PRIMARY KEY, pin TEXT, pin_code TEXT);")
    assert not by_rule(run(db), "SECA-006")


def test_plaintext_password_is_confirmed_and_hashed_is_clean():
    hit = by_rule(run(from_sqlite(BROKEN_SENSITIVE)), "SECA-008")[0]
    assert hit.kind.value == "confirmed_defect" and hit.severity.value == "critical" and hit.data == {}
    db = from_sqlite(f"CREATE TABLE u (id INTEGER PRIMARY KEY, password TEXT); INSERT INTO u VALUES (1, '{BCRYPT}');")
    assert not by_rule(run(db), "SECA-008")


def test_fast_digest_password_is_context_dependent():
    db = from_sqlite("CREATE TABLE u (id INTEGER PRIMARY KEY, password_hash TEXT); "
                     "INSERT INTO u VALUES (1, '5f4dcc3b5aa765d61d8327deb882cf99');")
    hit = by_rule(run(db), "SECA-008")[0]
    assert hit.kind.value == "context_dependent"


def test_sensitive_unencrypted_skips_ciphertext():
    db = from_sqlite("CREATE TABLE e (id INTEGER PRIMARY KEY, ssn TEXT); "
                     "INSERT INTO e VALUES (1, 'AAECAwQFBgcICQoLDA0ODxAREhMUFRYX');")
    assert not by_rule(run(db), "SECA-009")
    db = from_sqlite(f"CREATE TABLE e (id INTEGER PRIMARY KEY, ssn TEXT); INSERT INTO e VALUES (1, '{SSN}');")
    assert by_rule(run(db), "SECA-009")


def test_sample_limit_is_respected():
    db = from_sqlite("CREATE TABLE u (id INTEGER PRIMARY KEY, email TEXT);"
                     + "".join(f"INSERT INTO u (email) VALUES ('u{i}@example.com');" for i in range(50)))
    profile = Profile(data_sample_limit=10)
    hit = next(f for f in by_rule(run(db, profile), "SECA-005") if f.column == "email")
    assert hit.data["sampled"] == 10


def test_unreadable_column_is_warned_without_values():
    db = from_sqlite("CREATE TABLE u (id INTEGER PRIMARY KEY, email TEXT); INSERT INTO u VALUES (1,'a@b.co');")
    inner = db.data.query
    db.data.query = lambda sql, params=(): (_ for _ in ()).throw(RuntimeError("secret a@b.co")) if '"email"' in sql else inner(sql, params)
    run(db)
    assert any("RuntimeError" in w and "a@b.co" not in w for w in db.import_warnings)


# ---- settings ----

def test_settings_ssl_and_local_infile():
    db = Database("t", dialect="postgres", settings={"SSL": "off", "password_encryption": "md5"})
    f = run(db)
    assert by_rule(f, "SECA-011")[0].evidence == "Setting ssl is off."
    assert "password_encryption" in by_rule(f, "SECA-012")[0].evidence
    mysql = Database("t", dialect="mysql", settings={"local_infile": "ON", "ssl": "off"})
    f = run(mysql)
    assert not by_rule(f, "SECA-011") and by_rule(f, "SECA-012")


def test_profile_can_override_a_runtime_role():
    profile = Profile(rules={"SECA-001": {"params": {"runtime_roles": ["custom_login"]}}})
    db = role_db([Role("custom_login", superuser=True), Role("app_user", superuser=True)])
    hits = by_rule(run(db, profile), "SECA-001")
    assert len(hits) == 1 and "custom_login" in hits[0].evidence
