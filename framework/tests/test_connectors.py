"""Read-only guard, URL handling and connectors.

PostgreSQL tests run against a real server that pgserver starts in a temp directory; they skip if pgserver is unavailable.
MySQL is tested against a fake driver module; a real server is used only when DBINTEL_MYSQL_URL is set.
"""
import os
import sqlite3
import sys
import types

import pytest

from dbintel.connectors import (ConnectorError, ReadOnlyViolation, assert_read_only, open_connector, redact_url,
                                register_connector)
from dbintel.connectors.base import Connector, parse_url
from dbintel.model import Database

ALLOWED = [
    "SELECT 1",
    "select * from t;",
    "  \n SELECT a FROM t -- trailing comment\n",
    "/* header */ SELECT 1",
    "SELECT REPLACE(name, 'a', 'b') FROM t",
    "SELECT 'DROP TABLE x; DELETE FROM y' AS note",
    'SELECT "update" FROM "delete"',
    "SELECT t.update FROM t",
    "WITH c AS (SELECT 1) SELECT * FROM c",
    "EXPLAIN SELECT 1",
    "EXPLAIN ANALYZE SELECT * FROM t",
    "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) SELECT * FROM t",
    "EXPLAIN FORMAT=JSON SELECT 1",
    "EXPLAIN QUERY PLAN SELECT 1",
    "EXPLAIN UPDATE t SET a = 1",
    "SHOW server_version",
    "SHOW TABLES",
    "DESCRIBE t",
    "DESC db.t",
    "PRAGMA table_info(t)",
    "PRAGMA main.table_xinfo('t')",
    "PRAGMA foreign_key_list(t)",
    "PRAGMA encoding",
]

BYPASSES = [
    "",
    "   ",
    "-- only a comment",
    "DELETE FROM t",
    "drop table t",
    "UPDATE t SET a=1",
    "INSERT INTO t VALUES (1)",
    "TRUNCATE t",
    "CREATE TABLE x (a int)",
    "GRANT ALL ON t TO u",
    "CALL p()",
    "SET x = 1",
    "COPY t TO '/tmp/x'",
    "VACUUM",
    "SELECT 1; DROP TABLE t",
    "SELECT 1;;DROP TABLE t",
    "SELECT 1; -- x\nDROP TABLE t",
    "SELECT 1 /* a */ ; /* b */ DELETE FROM t",
    "/* SELECT */ DROP TABLE t",
    "-- SELECT\nDROP TABLE t",
    "/*! DROP TABLE t */",
    "SELECT 1 /*!50000 ; DROP TABLE t */",
    "SELECT 1 /*M!100000 ; DROP TABLE t */",
    "/* /* nested */ DROP TABLE t -- */",
    "SELECT 1 /* unterminated",
    "SELECT 'unterminated",
    "WITH d AS (DELETE FROM t RETURNING *) SELECT * FROM d",
    "WITH i AS (INSERT INTO t VALUES (1) RETURNING id) SELECT * FROM i",
    "WITH u AS (UPDATE t SET a=1 RETURNING *) SELECT 1",
    "WITH RECURSIVE r AS (SELECT 1) INSERT INTO t SELECT * FROM r",
    "WITH m AS (SELECT 1) MERGE INTO t USING m ON true WHEN MATCHED THEN DELETE",
    "SELECT * INTO new_t FROM t",
    "SELECT * FROM t INTO OUTFILE '/tmp/x'",
    "SELECT * FROM t FOR UPDATE",
    "SELECT * FROM t FOR NO KEY UPDATE",
    "SELECT * FROM t FOR SHARE",
    "SELECT * FROM t LOCK IN SHARE MODE",
    "EXPLAIN ANALYZE DELETE FROM t",
    "EXPLAIN ANALYSE DELETE FROM t",
    "EXPLAIN (ANALYZE) UPDATE t SET a=1",
    "EXPLAIN (ANALYZE true, BUFFERS) INSERT INTO t VALUES (1)",
    "EXPLAIN ANALYZE VERBOSE MERGE INTO t USING s ON true WHEN MATCHED THEN DELETE",
    "EXPLAIN ANALYZE WITH d AS (DELETE FROM t RETURNING *) SELECT * FROM d",
    "EXPLAIN CREATE TABLE x AS SELECT 1",
    "DESCRIBE ANALYZE DELETE FROM t",
    "DESC DELETE FROM t",
    "PRAGMA writable_schema = ON",
    "PRAGMA journal_mode = WAL",
    "PRAGMA journal_mode(WAL)",
    "PRAGMA user_version(5)",
    "PRAGMA unknown_thing",
    "SELECT pg_read_file('/etc/passwd')",
    'SELECT "pg_read_file"(\'/etc/passwd\')',
    "SELECT pg_catalog.pg_terminate_backend(1)",
    "SELECT setval('s', 1)",
    "SELECT nextval('s')",
    "SELECT set_config('default_transaction_read_only', 'off', false)",
    "SELECT lo_export(1, '/tmp/x')",
    "SELECT dblink_exec('x', 'DROP TABLE t')",
    "SELECT SLEEP(100)",
    "SELECT load_extension('evil')",
    "SELECT LOAD_FILE('/etc/passwd')",
    "SELECT '\\'; DROP TABLE t; -- '",
    "SELECT E'\\''; DROP TABLE t; --",
    "SELECT $$x$$; DROP TABLE t",
    "SELECT 1 # '\n; DROP TABLE t; -- '",
    "SELECT 1--1 ; DROP TABLE t",
    "SELECT `; DROP TABLE t; `",
    "SELECT ['] ; DROP TABLE t; --'",
    "SELECT 1\x00; DROP TABLE t",
    "(SELECT 1); DROP TABLE t",
]


@pytest.mark.parametrize("sql", ALLOWED)
def test_guard_allows_reads(sql):
    assert_read_only(sql)


@pytest.mark.parametrize("sql", BYPASSES)
def test_guard_rejects_bypasses(sql):
    with pytest.raises(ReadOnlyViolation):
        assert_read_only(sql)


def test_guard_rejects_non_text():
    with pytest.raises(ReadOnlyViolation):
        assert_read_only(None)  # type: ignore[arg-type]


def test_guard_is_dialect_aware_for_dollar_quotes():
    assert_read_only("SELECT $$ DROP TABLE t; $$", dialect="postgres")
    with pytest.raises(ReadOnlyViolation):
        assert_read_only("SELECT $$; DROP TABLE t; $$", dialect="mysql")


def test_guard_mysql_hash_comment_cannot_hide_a_statement():
    assert_read_only("SELECT 1 # just a note", dialect="mysql")
    with pytest.raises(ReadOnlyViolation):
        assert_read_only("SELECT 1 # note\n; DROP TABLE t", dialect="mysql")


# --------------------------------------------------------------------------------------------------------------------
# URLs and redaction
# --------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("url,expected", [
    ("postgresql://u:hunter2@h:5432/d", "postgresql://u:***@h:5432/d"),
    ("mysql://u:p%40ss@h/d", "mysql://u:***@h/d"),
    ("postgresql://u:p@ss:w/rd@h/d", "postgresql://u:***@h/d"),
    ("postgresql://u@h/d", "postgresql://u@h/d"),
    ("postgresql://u:s3@h/d?password=abc&sslmode=require", "postgresql://u:***@h/d?password=***&sslmode=require"),
    ("sqlite:///C:/a/b.db", "sqlite:///C:/a/b.db"),
])
def test_redact_url(url, expected):
    assert redact_url(url) == expected


def test_parse_url_decodes_and_hides_password():
    info = parse_url("postgresql://me:p%40ss@db.example:5433/shop?sslmode=require")
    assert (info.user, info.password, info.host, info.port, info.database) == ("me", "p@ss", "db.example", 5433, "shop")
    assert info.options == {"sslmode": "require"}
    assert "p@ss" not in repr(info)


def test_parse_sqlite_urls():
    assert parse_url("sqlite:///C:/x/y.db").database == "C:/x/y.db"
    assert parse_url("sqlite:////abs/y.db").database == "/abs/y.db"


def test_missing_password_env_names_variable_only(monkeypatch):
    monkeypatch.delenv("DBINTEL_NOPE", raising=False)
    with pytest.raises(ConnectorError, match="DBINTEL_NOPE"):
        open_connector("postgresql://u:secretvalue@h/d", password_env="DBINTEL_NOPE")


def test_unknown_scheme_is_redacted():
    with pytest.raises(ConnectorError) as err:
        open_connector("oracle://u:secretvalue@h/d")
    assert "secretvalue" not in str(err.value)


def _fake_module(monkeypatch, name, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    monkeypatch.setitem(sys.modules, name, module)
    return module


def test_postgres_connect_error_is_redacted(monkeypatch):
    def connect(**kwargs):
        raise RuntimeError(f"failed with password={kwargs['password']} on postgresql://u:{kwargs['password']}@h/d")
    _fake_module(monkeypatch, "psycopg", connect=connect)
    with pytest.raises(ConnectorError) as err:
        open_connector("postgresql://u:sup3rsecret@h/d")
    assert "sup3rsecret" not in str(err.value)
    assert err.value.__cause__ is None and err.value.__suppress_context__


def test_password_from_env_takes_precedence(monkeypatch):
    seen = {}

    class Stop(Exception):
        pass

    def connect(**kwargs):
        seen.update(kwargs)
        raise Stop(kwargs["password"])
    _fake_module(monkeypatch, "psycopg", connect=connect)
    monkeypatch.setenv("DBINTEL_TEST_PW", "fromenvironment")
    with pytest.raises(ConnectorError) as err:
        open_connector("postgresql://u:inurl@h/d", password_env="DBINTEL_TEST_PW")
    assert seen["password"] == "fromenvironment"
    assert "fromenvironment" not in str(err.value)


def test_query_errors_are_scrubbed():
    class Leaky(Connector):
        dialect = "sqlite"

        def _execute(self, sql, params):
            raise RuntimeError("boom pw=topsecret url mysql://a:topsecret@h/d")

        def extract(self):
            return Database(name="x")

        def close(self):
            pass

    leaky = Leaky(parse_url("mysql://a:topsecret@h/d"))
    with pytest.raises(ConnectorError) as err:
        leaky.query("SELECT 1")
    assert "topsecret" not in str(err.value)


def test_missing_driver_is_explained(monkeypatch):
    monkeypatch.setitem(sys.modules, "pymysql", None)
    with pytest.raises(ConnectorError, match=r"dbintel\[mysql\]"):
        open_connector("mysql://u@h/d")


def test_register_custom_connector():
    class Custom(Connector):
        dialect = "generic"

        def __init__(self, info):
            super().__init__(info)

        def _execute(self, sql, params):
            return [(sql,)]

        def extract(self):
            return Database(name="custom", data=self)

        def close(self):
            self.closed = True

    register_connector("customdb", Custom)
    with open_connector("customdb://u:pw@h/d") as conn:
        assert isinstance(conn, Custom)
        assert conn.query("SELECT 1") == [("SELECT 1",)]
        with pytest.raises(ReadOnlyViolation):
            conn.query("DROP TABLE t")
    assert conn.closed


# --------------------------------------------------------------------------------------------------------------------
# SQLite
# --------------------------------------------------------------------------------------------------------------------

SQLITE_SCHEMA = """
CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
    age INTEGER CHECK (age >= 0),
    note TEXT DEFAULT 'none',
    full_name TEXT GENERATED ALWAYS AS (email || '!') VIRTUAL
);
CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE ON UPDATE RESTRICT,
    amount REAL,
    CHECK (amount > 0)
);
CREATE TABLE tags (a TEXT, b TEXT, PRIMARY KEY (a, b)) WITHOUT ROWID;
CREATE INDEX ix_orders_customer ON orders (customer_id);
CREATE UNIQUE INDEX ux_partial ON orders (amount) WHERE amount > 100;
CREATE VIEW big_orders AS SELECT o.id, c.email FROM orders o JOIN customers c ON c.id = o.customer_id;
CREATE TRIGGER tr_note AFTER INSERT ON orders BEGIN UPDATE customers SET note = 'x' WHERE id = NEW.customer_id; END;
INSERT INTO customers (email, age) VALUES ('a@x.io', 30), ('b@x.io', 40);
INSERT INTO orders (customer_id, amount) VALUES (1, 10.5);
"""


@pytest.fixture
def sqlite_file(tmp_path):
    path = tmp_path / "shop.db"
    conn = sqlite3.connect(path)
    conn.executescript(SQLITE_SCHEMA)
    conn.close()
    return path


def _url(path):
    return f"sqlite:///{path.as_posix()}"


def test_sqlite_extract(sqlite_file):
    with open_connector(_url(sqlite_file)) as conn:
        db = conn.extract()
        assert db.dialect == "sqlite" and db.source == "live" and db.data is conn and db.name == "shop"
        assert conn.dialect == "sqlite" and callable(conn.query) and callable(conn.quote), "satisfies model.DataAccess"
        customers, orders = db.table("customers"), db.table("orders")
        assert customers.primary_key == ["id"]
        assert customers.column("id").is_identity and not customers.column("id").nullable
        assert not customers.column("email").nullable
        assert customers.column("email").collation.upper() == "NOCASE"
        assert customers.column("note").default == "'none'"
        assert customers.column("full_name").is_generated
        assert customers.row_count == 2
        assert [c.columns for c in customers.checks] == [["age"]]
        assert any(i.unique and i.is_constraint and i.columns == ["email"] for i in customers.indexes)
        fk = orders.foreign_keys[0]
        assert (fk.columns, fk.ref_table, fk.ref_columns, fk.on_delete, fk.on_update) == (["customer_id"], "customers", ["id"], "CASCADE", "RESTRICT")
        assert orders.index_leading(["customer_id"])
        partial = next(i for i in orders.indexes if i.name == "ux_partial")
        assert partial.unique and partial.where == "amount > 100"
        assert [c.expression for c in orders.checks] == ["amount > 0"]
        assert db.table("tags").primary_key == ["a", "b"]
        view = db.views[0]
        assert view.name == "big_orders" and sorted(view.references) == ["customers", "orders"]
        trigger = db.routines[0]
        assert trigger.kind == "trigger" and trigger.table == "orders"
        assert db.settings["encoding"] == "UTF-8" and db.settings["server_version"]
        assert not db.security_metadata
        assert not db.import_warnings
        assert conn.query("SELECT email FROM customers WHERE id = ?", (2,)) == [("b@x.io",)]
        assert conn.query("SELECT email FROM customers WHERE id = %s", (2,)) == [("b@x.io",)]


def test_sqlite_refuses_writes_even_past_the_guard(sqlite_file):
    with open_connector(_url(sqlite_file)) as conn:
        with pytest.raises(ReadOnlyViolation):
            conn.query("DELETE FROM customers")
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            conn._execute("DELETE FROM customers", ())
        with pytest.raises(ConnectorError):
            conn.query("SELECT * FROM no_such_table")
        assert conn.query("SELECT COUNT(*) FROM customers") == [(2,)]


def test_sqlite_missing_file(tmp_path):
    with pytest.raises(ConnectorError, match="not found"):
        open_connector(_url(tmp_path / "missing.db"))


def test_sqlite_does_not_create_files(tmp_path):
    target = tmp_path / "new.db"
    with pytest.raises(ConnectorError):
        open_connector(_url(target))
    assert not target.exists()


# --------------------------------------------------------------------------------------------------------------------
# MySQL, faked driver
# --------------------------------------------------------------------------------------------------------------------


class FakeMySQLCursor:
    def __init__(self, conn):
        self.conn = conn
        self.description = None
        self._rows = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        pass

    def execute(self, sql, args=None):
        self.conn.executed.append(sql)
        result = self.conn.route(sql, args)
        if isinstance(result, Exception):
            raise result
        self._rows = result or []
        self.description = [("x",)] if result is not None else None

    def fetchall(self):
        return tuple(self._rows)


class FakeMySQLConn:
    def __init__(self, deny=()):
        self.executed = []
        self.deny = deny
        self.closed = False

    def cursor(self):
        return FakeMySQLCursor(self)

    def close(self):
        self.closed = True

    def route(self, sql, args):
        low = " ".join(sql.split()).lower()
        for fragment in self.deny:
            if fragment in low:
                return RuntimeError("(1142, 'SELECT command denied to user')")
        if low.startswith("set session transaction read only"):
            return None
        if "@@session.transaction_read_only" in low:
            return [(1,)]
        if "from information_schema.tables" in low:
            return [("shop", "orders", "InnoDB", "utf8mb4_0900_ai_ci", 1234, "order table", 1235),
                    ("shop", "customers", "InnoDB", "utf8mb4_0900_ai_ci", 10, "", None)]
        if "from information_schema.columns" in low:
            return [
                ("shop", "orders", "id", b"int unsigned", "NO", None, "auto_increment", "", None, None, 1),
                ("shop", "orders", "customer_id", "int", "NO", None, "", "", None, None, 2),
                ("shop", "orders", "status", "varchar(20)", "YES", "new", "", "the status", "utf8mb4", "utf8mb4_0900_ai_ci", 3),
                ("shop", "orders", "total", "decimal(10,2)", "YES", None, "STORED GENERATED", "", None, None, 4),
                ("shop", "orders", "created", "timestamp", "YES", "CURRENT_TIMESTAMP", "DEFAULT_GENERATED", "", None, None, 5),
                ("shop", "customers", "id", "int", "NO", None, "", "", None, None, 1),
            ]
        if "from information_schema.statistics" in low:
            return [("shop", "orders", "PRIMARY", 0, 1, "id", "BTREE"),
                    ("shop", "orders", "ix_cust", 1, 1, "customer_id", "BTREE"),
                    ("shop", "orders", "ix_cust", 1, 2, "status", "BTREE"),
                    ("shop", "customers", "PRIMARY", 0, 1, "id", "BTREE")]
        if "key_column_usage" in low:
            return [("shop", "orders", "fk_c", "customer_id", "shop", "customers", "id", "CASCADE", "RESTRICT")]
        if "check_constraints" in low:
            return [("shop", "orders", "ck_s", "(`status` <> _utf8mb4'x')")]
        if "information_schema.partitions" in low:
            return [("shop", "orders", "`created`")]
        if "information_schema.views" in low:
            return [("shop", "v_orders", "select `shop`.`orders`.`id` AS `id` from `shop`.`orders`")]
        if "information_schema.routines" in low:
            return [("shop", "p1", "PROCEDURE", "BEGIN SELECT 1; END")]
        if "information_schema.triggers" in low:
            return [("shop", "t1", "orders", "BEFORE", "INSERT", "SET NEW.status = 'x'")]
        if "from mysql.user" in low:
            return [("app", "%", "N", "N", 1), ("root", "localhost", "Y", "N", 1), ("mysql.sys", "localhost", "N", "Y", 0)]
        if "user_privileges" in low:
            return [("'root'@'localhost'", "SUPER", "YES"), ("'app'@'%'", "USAGE", "NO")]
        if "schema_privileges" in low:
            return [("'app'@'%'", "SELECT", "NO", "shop"), ("'app'@'%'", "SELECT", "NO", "mysql")]
        if "table_privileges" in low:
            return [("'app'@'%'", "INSERT", "NO", "shop", "orders")]
        if "column_privileges" in low:
            return [("'app'@'%'", "UPDATE", "NO", "shop", "orders", "status")]
        if low.startswith("show variables"):
            return [("version", "8.0.35"), ("character_set_server", "utf8mb4"), ("sql_mode", "STRICT_ALL_TABLES"), ("log_bin", "ON")]
        if "performance_schema" in low:
            return [("SELECT * FROM orders", 10, 50.0, 5.0, 100)]
        return []


@pytest.fixture
def fake_mysql(monkeypatch):
    state = {}

    def connect(**kwargs):
        state["kwargs"] = kwargs
        state["conn"] = FakeMySQLConn(state.get("deny", ()))
        return state["conn"]
    _fake_module(monkeypatch, "pymysql", connect=connect)
    return state


def test_mysql_session_is_read_only_before_anything_else(fake_mysql):
    with open_connector("mysql://u:pw@h:3307/shop") as conn:
        assert fake_mysql["conn"].executed[0] == "SET SESSION TRANSACTION READ ONLY"
        assert fake_mysql["kwargs"]["port"] == 3307 and fake_mysql["kwargs"]["password"] == "pw"
    assert fake_mysql["conn"].closed


def test_mysql_refuses_when_server_does_not_confirm(monkeypatch):
    class NotReadOnly(FakeMySQLConn):
        def route(self, sql, args):
            return [(0,)] if "@@session.transaction_read_only" in sql.lower() else super().route(sql, args)
    conn = NotReadOnly()
    _fake_module(monkeypatch, "pymysql", connect=lambda **k: conn)
    with pytest.raises(ConnectorError, match="read-only"):
        open_connector("mysql://u@h/shop")
    assert conn.closed


def test_mysql_guard_applies_and_uses_backticks(fake_mysql):
    with open_connector("mysql://u@h/shop") as conn:
        assert conn.quote("a`b") == "`a``b`"
        with pytest.raises(ReadOnlyViolation):
            conn.query("UPDATE orders SET status = 'x'")
        assert not any("UPDATE orders" in sql for sql in fake_mysql["conn"].executed)


def test_mysql_extract(fake_mysql):
    with open_connector("mysql://u@h/shop") as conn:
        db = conn.extract()
    assert db.dialect == "mysql" and db.source == "live" and db.data is conn
    orders = db.table("orders")
    assert orders.engine == "InnoDB" and orders.charset == "utf8mb4" and orders.row_count == 1234 and orders.comment == "order table"
    assert orders.column("id").data_type == "int unsigned" and orders.column("id").is_identity
    assert orders.column("status").default == "new" and orders.column("status").collation == "utf8mb4_0900_ai_ci"
    assert orders.column("total").is_generated
    assert not orders.column("created").is_generated, "DEFAULT_GENERATED is not a generated column"
    assert orders.primary_key == ["id"]
    assert orders.indexes[0].columns == ["customer_id", "status"]
    fk = orders.foreign_keys[0]
    assert (fk.ref_table, fk.on_delete, fk.on_update) == ("customers", "CASCADE", "RESTRICT")
    assert orders.checks[0].name == "ck_s"
    assert orders.partition_columns == ["created"]
    assert db.views[0].references == ["orders"]
    assert {(r.kind, r.name) for r in db.routines} == {("procedure", "p1"), ("trigger", "t1")}
    assert {r.name for r in db.roles} == {"app", "root"}
    assert next(r for r in db.roles if r.name == "root").superuser
    assert db.security_metadata
    assert any(g.grantee == "root" and g.privilege == "SUPER" and g.table is None and g.grantable for g in db.grants)
    assert any(g.grantee == "app" and g.schema == "shop" and g.table == "*" for g in db.grants)
    assert any(g.grantee == "app" and g.column == "status" for g in db.grants)
    assert not any(g.schema == "mysql" or g.privilege == "USAGE" for g in db.grants), "system schemas and USAGE are excluded"
    assert db.settings["server_version"] == "8.0.35" and db.settings["log_bin"] == "ON" and db.settings["sql_mode"]
    assert db.query_stats[0].calls == 10 and db.query_stats[0].mean_ms == 5.0
    assert db.settings["auto_increment"] == {"orders": 1235}, "tables without a counter are omitted"
    assert not db.import_warnings


def test_mysql_missing_privileges_become_warnings(fake_mysql):
    fake_mysql["deny"] = ("from mysql.user", "performance_schema")
    with open_connector("mysql://u@h/shop") as conn:
        db = conn.extract()
    assert not db.security_metadata
    assert db.tables and db.query_stats == []
    assert any("accounts" in w for w in db.import_warnings)
    assert any("performance_schema" in w for w in db.import_warnings)
    assert db.settings["query_stats_available"] is False


@pytest.mark.live
@pytest.mark.skipif(not os.environ.get("DBINTEL_MYSQL_URL"), reason="DBINTEL_MYSQL_URL is not set")
def test_mysql_live():
    with open_connector(os.environ["DBINTEL_MYSQL_URL"]) as conn:
        db = conn.extract()
        assert db.dialect == "mysql"
        with pytest.raises(ConnectorError):
            conn._execute("CREATE TABLE dbintel_write_probe (a int)", ())


# --------------------------------------------------------------------------------------------------------------------
# PostgreSQL, real server in a temp directory
# --------------------------------------------------------------------------------------------------------------------

PG_SCHEMA = """
CREATE TYPE mood AS ENUM ('ok', 'bad');
CREATE TABLE customers (
    id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    email character varying(200) NOT NULL UNIQUE,
    mood mood DEFAULT 'ok',
    tenant integer NOT NULL
);
COMMENT ON TABLE customers IS 'people';
COMMENT ON COLUMN customers.email IS 'login';
CREATE TABLE orders (
    id serial PRIMARY KEY,
    customer_id bigint NOT NULL REFERENCES customers (id) ON DELETE SET NULL ON UPDATE CASCADE,
    amount numeric(12,2) CHECK (amount >= 0),
    double_amount numeric GENERATED ALWAYS AS (amount * 2) STORED,
    created timestamptz DEFAULT now()
);
CREATE INDEX ix_orders_customer ON orders (customer_id) INCLUDE (amount);
CREATE INDEX ix_orders_partial ON orders (created) WHERE amount > 10;
CREATE TABLE events (id int, at date, primary key (id, at)) PARTITION BY RANGE (at);
CREATE TABLE events_2024 PARTITION OF events FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
CREATE VIEW v_orders AS SELECT o.id, c.email FROM orders o JOIN customers c ON c.id = o.customer_id;
CREATE MATERIALIZED VIEW mv_totals AS SELECT customer_id, sum(amount) AS total FROM orders GROUP BY customer_id;
CREATE FUNCTION touch() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN NEW.created := now(); RETURN NEW; END $$;
CREATE TRIGGER tr_touch BEFORE UPDATE ON orders FOR EACH ROW EXECUTE FUNCTION touch();
CREATE ROLE app_reader LOGIN NOSUPERUSER;
GRANT SELECT ON customers TO app_reader;
GRANT SELECT (amount) ON orders TO PUBLIC;
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
CREATE POLICY p_tenant ON customers FOR SELECT TO app_reader USING (tenant = 1);
INSERT INTO customers (email, tenant) VALUES ('a@x.io', 1), ('b@x.io', 2);
INSERT INTO orders (customer_id, amount) VALUES (1, 5.5);
"""


@pytest.fixture(scope="module")
def pg_url(tmp_path_factory):
    pgserver = pytest.importorskip("pgserver")
    psycopg = pytest.importorskip("psycopg")
    pgdata = tmp_path_factory.mktemp("pgdata")
    server = pgserver.get_server(pgdata, cleanup_mode="stop")
    admin_uri = server.get_uri()
    with psycopg.connect(admin_uri, autocommit=True) as admin:
        admin.execute("CREATE DATABASE shop")
    base = admin_uri.replace("postgres:@", "postgres@").rsplit("/", 1)[0]
    url = f"{base}/shop"
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute(PG_SCHEMA)
        conn.execute("ANALYZE")
    yield url
    server.cleanup()


def test_pg_live_extract(pg_url):
    with open_connector(pg_url) as conn:
        db = conn.extract()
    assert db.dialect == "postgres" and db.source == "live" and db.name == "shop"
    assert not db.import_warnings
    assert {t.name for t in db.tables} == {"customers", "orders", "events"}, "partitions are represented by their parent"
    customers, orders, events = db.table("customers"), db.table("orders"), db.table("events")
    assert customers.schema == "public" and customers.comment == "people"
    assert customers.column("id").is_identity and customers.column("id").data_type == "bigint"
    assert customers.column("email").data_type == "character varying(200)" and customers.column("email").comment == "login"
    assert not customers.column("email").nullable
    assert customers.column("mood").default.startswith("'ok'")
    assert customers.primary_key == ["id"]
    assert customers.rls_enabled is True and orders.rls_enabled is False
    assert any(i.unique and i.is_constraint and i.columns == ["email"] for i in customers.indexes)
    assert not any(i.columns == ["id"] for i in customers.indexes), "the primary key index is not repeated"
    assert customers.row_count == 2

    assert orders.column("id").is_identity, "serial is an identity"
    assert orders.column("double_amount").is_generated
    assert orders.column("amount").data_type == "numeric(12,2)"
    assert orders.primary_key_name == "orders_pkey"
    fk = orders.foreign_keys[0]
    assert (fk.columns, fk.ref_table, fk.ref_schema, fk.ref_columns, fk.on_delete, fk.on_update) == (
        ["customer_id"], "customers", "public", ["id"], "SET NULL", "CASCADE")
    assert orders.checks[0].columns == ["amount"] and "amount" in orders.checks[0].expression
    include = next(i for i in orders.indexes if i.name == "ix_orders_customer")
    assert include.columns == ["customer_id"] and include.include == ["amount"]
    assert next(i for i in orders.indexes if i.name == "ix_orders_partial").where
    assert events.partition_columns == ["at"]

    views = {v.name: v for v in db.views}
    assert sorted(views["v_orders"].references) == ["customers", "orders"]
    assert views["mv_totals"].materialized
    kinds = {(r.kind, r.name) for r in db.routines}
    assert ("function", "touch") in kinds and ("trigger", "tr_touch") in kinds
    assert next(r for r in db.routines if r.name == "tr_touch").table == "orders"

    roles = {r.name: r for r in db.roles}
    assert "app_reader" in roles and roles["app_reader"].can_login and not roles["app_reader"].superuser
    assert not any(n.startswith("pg_") for n in roles)
    assert roles["postgres"].superuser
    assert any(g.grantee == "app_reader" and g.privilege == "SELECT" and g.table == "customers" for g in db.grants)
    assert any(g.grantee == "PUBLIC" and g.column == "amount" and g.table == "orders" for g in db.grants)
    assert db.security_metadata

    policy = db.policies[0]
    assert (policy.name, policy.table, policy.command, policy.roles) == ("p_tenant", "customers", "SELECT", ["app_reader"])
    assert "tenant" in policy.expression

    for key in ("server_version", "encoding", "wal_level", "archive_mode", "ssl"):
        assert key in db.settings
    assert db.settings["query_stats_available"] is False, "pg_stat_statements is not installed here and that is not an error"
    assert db.settings["auto_increment"] == {"customers": 2, "orders": 1}, "from sequence last_value"


def test_pg_live_query_and_placeholders(pg_url):
    with open_connector(pg_url) as conn:
        assert conn.query("SELECT email FROM customers WHERE id = %s", (1,)) == [("a@x.io",)]
        assert conn.query("SELECT email FROM customers WHERE id = ?", (2,)) == [("b@x.io",)]
        assert conn.query("SELECT email FROM customers WHERE email LIKE '%@x.io' AND id = ?", (1,)) == [("a@x.io",)]
        assert conn.query('SELECT count(*) FROM orders') == [(1,)]
        assert conn.quote('a"b') == '"a""b"'


def test_pg_live_writes_fail_with_and_without_the_guard(pg_url):
    import psycopg
    with open_connector(pg_url) as conn:
        for sql in ("DELETE FROM customers", "SELECT 1; DROP TABLE orders",
                    "WITH d AS (DELETE FROM customers RETURNING *) SELECT * FROM d"):
            with pytest.raises(ReadOnlyViolation):
                conn.query(sql)
        for sql in ("DELETE FROM customers", "DROP TABLE orders", "CREATE TABLE probe (a int)",
                    "UPDATE customers SET tenant = 9", "WITH d AS (DELETE FROM customers RETURNING *) SELECT * FROM d"):
            with pytest.raises(Exception) as err:
                conn._execute(sql, ())
            assert "read-only" in str(err.value), f"server should refuse {sql}: {err.value}"
        with pytest.raises(ConnectorError):
            conn.query("SELECT * FROM no_such_table")
        assert conn.query("SELECT 1") == [(1,)], "the session survives failed statements"
    with psycopg.connect(pg_url, autocommit=True) as writer:
        assert writer.execute("SELECT count(*) FROM customers").fetchone() == (2,)
        assert writer.execute("SELECT count(*) FROM orders").fetchone() == (1,)


def test_pg_live_low_privilege_user_warns_without_failing(pg_url):
    import psycopg
    with psycopg.connect(pg_url, autocommit=True) as admin:
        admin.execute("DROP ROLE IF EXISTS limited")
        admin.execute("CREATE ROLE limited LOGIN")
    limited = pg_url.replace("postgres@", "limited@")
    with open_connector(limited) as conn:
        db = conn.extract()
    assert db.table("customers") is not None
    assert all(r.password_set is None for r in db.roles), "pg_authid is unreadable, so password state stays unknown"
    assert isinstance(db.import_warnings, list)
    assert "auto_increment" not in db.settings, "sequence positions are hidden from this role, so the key is omitted"
