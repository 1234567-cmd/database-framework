"""SQL dump, CSV, Excel, metadata, query log and pipeline importers."""
import gzip
import json
import textwrap

import pytest

from dbintel.connectors import ReadOnlyViolation
from dbintel.importers import (detect_dialect, export_metadata, import_csv, import_excel, import_metadata, import_sql,
                               load_pipelines, load_query_log, load_source)
from dbintel.importers.sql_dump import split_statements
import sqlite3

from dbintel.model import Database

MYSQLDUMP = r"""-- MySQL dump 10.13  Distrib 8.0.35, for Linux (x86_64)
--
-- Host: localhost    Database: shop
-- ------------------------------------------------------
-- Server version	8.0.35

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;

--
-- Table structure for table `customers`
--

DROP TABLE IF EXISTS `customers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `customers` (
  `id` int unsigned NOT NULL AUTO_INCREMENT COMMENT 'surrogate, it''s the key',
  `email` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `status` enum('active','closed') NOT NULL DEFAULT 'active',
  `balance` decimal(12,2) DEFAULT '0.00',
  `is_vip` tinyint(1) NOT NULL DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `full` varchar(300) GENERATED ALWAYS AS (concat(`email`,'!')) VIRTUAL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_email` (`email`),
  KEY `ix_status` (`status`,`created_at`) USING BTREE,
  FULLTEXT KEY `ft_email` (`email`),
  CONSTRAINT `ck_balance` CHECK ((`balance` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=42 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='people';
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `customers` WRITE;
/*!40000 ALTER TABLE `customers` DISABLE KEYS */;
INSERT INTO `customers` VALUES (1,'o\'neil@x.io','active','10.50',1,'2024-01-01 10:00:00','x'),(2,'semi;colon@x.io','closed',NULL,0,NULL,NULL);
/*!40000 ALTER TABLE `customers` ENABLE KEYS */;
UNLOCK TABLES;

DROP TABLE IF EXISTS `orders`;
CREATE TABLE `orders` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `customer_id` int unsigned DEFAULT NULL,
  `payload` blob,
  PRIMARY KEY (`id`),
  KEY `fk_cust` (`customer_id`),
  CONSTRAINT `fk_cust` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1
/*!50100 PARTITION BY HASH (`id`)
PARTITIONS 4 */;

LOCK TABLES `orders` WRITE;
INSERT INTO `orders` (`id`,`customer_id`,`payload`) VALUES (1,1,_binary 'abc'),(2,1,0xCAFE);
UNLOCK TABLES;

--
-- Temporary view structure for view `v_vip`
--
/*!50001 DROP VIEW IF EXISTS `v_vip`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_vip` AS SELECT
 1 AS `id`*/;
SET character_set_client = @saved_cs_client;

/*!50003 SET @saved_cs_client = @@character_set_client */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `tr_bi` BEFORE INSERT ON `orders` FOR EACH ROW BEGIN
  IF NEW.customer_id IS NULL THEN SET NEW.customer_id = 1; END IF;
END */;;
DELIMITER ;

DELIMITER ;;
CREATE DEFINER=`root`@`%` PROCEDURE `p_cleanup`(IN days INT)
BEGIN
  DELETE FROM orders WHERE id < days;
  SELECT COUNT(*) FROM customers;
END ;;
DELIMITER ;

/*!50001 DROP VIEW IF EXISTS `v_vip`*/;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_vip` AS select `customers`.`id` AS `id` from `customers` where (`customers`.`is_vip` = 1) */;

CREATE USER 'app'@'%' IDENTIFIED BY 'hush_secret_1';
GRANT SELECT, INSERT ON `shop`.* TO 'app'@'%';
GRANT SELECT (`email`) ON `shop`.`customers` TO 'app'@'%';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'localhost' WITH GRANT OPTION;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;
-- Dump completed on 2024-02-02 12:00:00
"""

PG_DUMP = r"""--
-- PostgreSQL database dump
--

-- Dumped from database version 15.4
-- Dumped by pg_dump version 15.4

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET default_tablespace = '';

\connect shopdb
\restrict abc123

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;
CREATE TYPE public.mood AS ENUM (
    'ok',
    'bad'
);

--
-- Name: touch(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.touch() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  NEW.updated := now(); -- a semicolon; in a body
  INSERT INTO public.audit_log (note) VALUES ('x;y');
  RETURN NEW;
END;
$$;

CREATE TABLE public.customers (
    id integer NOT NULL,
    email character varying(200) NOT NULL,
    mood public.mood DEFAULT 'ok'::public.mood,
    attrs jsonb DEFAULT '{}'::jsonb,
    created timestamp(3) with time zone DEFAULT now() NOT NULL,
    tags text[],
    active boolean DEFAULT true
);

ALTER TABLE public.customers OWNER TO postgres;

COMMENT ON TABLE public.customers IS 'people; and more';
COMMENT ON COLUMN public.customers.email IS 'login address';

CREATE SEQUENCE public.customers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.customers_id_seq OWNED BY public.customers.id;
ALTER TABLE ONLY public.customers ALTER COLUMN id SET DEFAULT nextval('public.customers_id_seq'::regclass);

CREATE TABLE public.orders (
    id bigint GENERATED BY DEFAULT AS IDENTITY,
    customer_id integer,
    amount numeric(12,2),
    tot numeric GENERATED ALWAYS AS (amount * 2) STORED,
    tenant integer,
    CONSTRAINT ck_amount CHECK ((amount >= (0)::numeric))
);

CREATE TABLE public.audit_log (
    id bigserial PRIMARY KEY,
    note text
);

COPY public.customers (id, email, mood, attrs, created, tags, active) FROM stdin;
1	o'neil@x.io	ok	{"a": 1}	2024-01-01 10:00:00+00	{a,b}	t
2	tab\there@x.io	\N	\N	2024-01-02 10:00:00+00	\N	f
\.


COPY public.orders (id, customer_id, amount, tenant) FROM stdin;
\.


ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_customer_fk FOREIGN KEY (customer_id) REFERENCES public.customers(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_email_key UNIQUE (email);

CREATE INDEX ix_orders_customer ON public.orders USING btree (customer_id) INCLUDE (amount);
CREATE UNIQUE INDEX ux_lower ON public.customers USING btree (lower((email)::text)) WHERE (active = true);

CREATE VIEW public.v_orders AS
 SELECT o.id,
    c.email
   FROM (public.orders o
     JOIN public.customers c ON ((c.id = o.customer_id)));

CREATE TRIGGER tr_touch BEFORE UPDATE ON public.customers FOR EACH ROW EXECUTE FUNCTION public.touch();

ALTER TABLE public.orders ENABLE ROW LEVEL SECURITY;

CREATE POLICY p_tenant ON public.orders FOR SELECT TO app_reader, admin USING ((tenant = 1));
CREATE POLICY p_write ON public.orders FOR INSERT WITH CHECK ((tenant = 2));

CREATE ROLE app_reader NOSUPERUSER LOGIN PASSWORD 'hush_secret_2';
CREATE ROLE admin SUPERUSER BYPASSRLS;

REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT SELECT ON TABLE public.customers TO app_reader;
GRANT SELECT(email), UPDATE(email) ON TABLE public.orders TO app_reader WITH GRANT OPTION;
GRANT USAGE ON SCHEMA public TO app_reader;
GRANT ALL ON ALL TABLES IN SCHEMA public TO admin;
GRANT admin TO app_reader;
GRANT USAGE ON SEQUENCE public.customers_id_seq TO app_reader;

--
-- PostgreSQL database dump complete
--
"""

SQLITE_DUMP = """PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE t1 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, other);
INSERT INTO t1 VALUES(1,'a;b',NULL);
INSERT INTO "t1" VALUES(2,'c''d',3.5);
DELETE FROM sqlite_sequence;
INSERT INTO sqlite_sequence VALUES('t1',2);
CREATE TABLE sqlite_stat1(tbl,idx,stat);
CREATE TRIGGER tr AFTER INSERT ON t1 BEGIN
  UPDATE t1 SET name = CASE WHEN id > 0 THEN 'x' ELSE 'y' END WHERE id = NEW.id;
  DELETE FROM t1 WHERE id < 0;
END;
COMMIT;
"""


@pytest.fixture
def mysql_db():
    return import_sql(MYSQLDUMP)


@pytest.fixture
def pg_db():
    return import_sql(PG_DUMP)


def test_detect_dialect():
    assert detect_dialect(MYSQLDUMP) == "mysql"
    assert detect_dialect(PG_DUMP) == "postgres"
    assert detect_dialect(SQLITE_DUMP) == "sqlite"
    assert detect_dialect("CREATE TABLE a (b int);") == "generic"


def test_mysqldump_structure(mysql_db):
    db = mysql_db
    assert db.dialect == "mysql" and db.source == "sql_dump"
    assert {t.name for t in db.tables} == {"customers", "orders"}
    c = db.table("customers")
    assert c.engine == "InnoDB" and c.charset == "utf8mb4" and c.collation == "utf8mb4_0900_ai_ci" and c.comment == "people"
    assert c.primary_key == ["id"]
    identity = c.column("id")
    assert identity.data_type == "int unsigned" and identity.is_identity and not identity.nullable
    assert identity.comment == "surrogate, it's the key"
    email = c.column("email")
    assert email.data_type == "varchar(255)" and email.charset == "utf8mb4" and email.collation == "utf8mb4_bin" and not email.nullable
    status = c.column("status")
    assert status.data_type == "enum('active','closed')" and status.type.values == ("active", "closed")
    assert status.default == "'active'"
    assert c.column("balance").default == "'0.00'" and c.column("balance").nullable
    assert c.column("created_at").data_type == "timestamp" and c.column("created_at").default == "CURRENT_TIMESTAMP"
    assert c.column("full").is_generated
    assert c.column("is_vip").type.family == "bool"
    assert [(i.name, i.columns, i.unique) for i in c.indexes[:2]] == [("uq_email", ["email"], True), ("ix_status", ["status", "created_at"], False)]
    assert next(i for i in c.indexes if i.name == "ix_status").method == "BTREE"
    assert next(i for i in c.indexes if i.name == "ft_email").method == "FULLTEXT"
    assert c.checks[0].name == "ck_balance" and c.checks[0].columns == ["balance"]
    o = db.table("orders")
    assert o.charset == "latin1" and o.partition_columns == ["id"]
    fk = o.foreign_keys[0]
    assert (fk.name, fk.columns, fk.ref_table, fk.ref_columns, fk.on_delete, fk.on_update) == (
        "fk_cust", ["customer_id"], "customers", ["id"], "SET NULL", "CASCADE")


def test_mysqldump_objects_and_security(mysql_db):
    db = mysql_db
    assert not db.import_warnings, db.import_warnings
    view = db.views[0]
    assert view.name == "v_vip" and "is_vip" in view.definition and view.references == ["customers"]
    assert db.table("v_vip") is None
    trigger = next(r for r in db.routines if r.kind == "trigger")
    assert trigger.name == "tr_bi" and trigger.table == "orders" and "NEW.customer_id" in trigger.definition
    procedure = next(r for r in db.routines if r.kind == "procedure")
    assert procedure.name == "p_cleanup" and set(procedure.references) >= {"orders", "customers"}
    assert db.security_metadata
    app = next(r for r in db.roles if r.name == "app")
    assert app.host == "%" and app.password_set is True and app.can_login
    assert any(g.grantee == "app" and g.privilege == "SELECT" and g.schema == "shop" and g.table == "*" for g in db.grants)
    assert any(g.grantee == "app" and g.column == "email" and g.table == "customers" for g in db.grants)
    assert any(g.grantee == "root" and g.privilege == "ALL" and g.table is None and g.schema is None and g.grantable for g in db.grants)
    assert db.settings["server_version"] == "8.0.35" and db.settings["encoding"] == "utf8mb4"
    assert "hush_secret_1" not in repr(db)


def test_auto_increment_captured_from_dumps(mysql_db, pg_db):
    assert mysql_db.settings["auto_increment"] == {"customers": 42}, "orders states no counter"
    assert "auto_increment" not in pg_db.settings
    db = import_sql("""CREATE TABLE `t` (`id` int NOT NULL) ENGINE=InnoDB;
        ALTER TABLE `t` MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;""", dialect="mysql")
    assert db.settings["auto_increment"] == {"t": 7} and not db.import_warnings, db.import_warnings
    assert db.table("t").column("id").is_identity


def test_foreign_key_actions_only_when_stated():
    db = import_sql("""CREATE TABLE p (id int PRIMARY KEY);
        CREATE TABLE a (x int REFERENCES p (id), y int REFERENCES p (id) ON DELETE CASCADE);
        CREATE TABLE b (x int, CONSTRAINT f FOREIGN KEY (x) REFERENCES p (id) ON UPDATE RESTRICT);
        CREATE TABLE c (x int);
        ALTER TABLE c ADD CONSTRAINT g FOREIGN KEY (x) REFERENCES p (id);""")
    assert [(f.on_delete, f.on_update) for f in db.table("a").foreign_keys] == [(None, None), ("CASCADE", None)]
    assert (db.table("b").foreign_keys[0].on_delete, db.table("b").foreign_keys[0].on_update) == (None, "RESTRICT")
    assert (db.table("c").foreign_keys[0].on_delete, db.table("c").foreign_keys[0].on_update) == (None, None)


def test_mysqldump_data(mysql_db):
    data = mysql_db.data
    assert data.dialect == "sqlite" and callable(data.query) and callable(data.quote)
    rows = data.query('SELECT id, email, balance, is_vip FROM customers ORDER BY id')
    assert rows == [(1, "o'neil@x.io", 10.5, 1), (2, "semi;colon@x.io", None, 0)]
    assert mysql_db.table("customers").row_count == 2
    assert data.query("SELECT payload FROM orders ORDER BY id") == [("abc",), (bytes.fromhex("CAFE"),)]


def test_pg_dump_structure(pg_db):
    db = pg_db
    assert not db.import_warnings, db.import_warnings
    assert db.dialect == "postgres" and db.name == "shopdb"
    assert db.settings["server_version"] == "15.4" and db.settings["encoding"] == "UTF8"
    c = db.table("customers", "public")
    assert c.schema == "public" and c.comment == "people; and more"
    assert c.primary_key == ["id"] and c.primary_key_name == "customers_pkey"
    assert not c.column("id").nullable and c.column("id").is_identity, "pg_dump serial style"
    assert c.column("id").default == "nextval('public.customers_id_seq'::regclass)"
    assert c.column("email").data_type == "character varying(200)" and c.column("email").comment == "login address"
    assert c.column("mood").default == "'ok'::public.mood"
    assert c.column("created").data_type == "timestamp(3) with time zone" and c.column("created").type.family == "timestamptz"
    assert c.column("tags").data_type == "text[]"
    assert c.rls_enabled is False
    assert any(i.name == "customers_email_key" and i.unique and i.is_constraint for i in c.indexes)
    ux = next(i for i in c.indexes if i.name == "ux_lower")
    assert ux.unique and ux.where == "(active = true)" and "lower" in ux.columns[0]
    o = db.table("orders", "public")
    assert o.column("id").is_identity and not o.column("id").nullable
    assert o.column("tot").is_generated
    assert o.checks[0].name == "ck_amount"
    assert o.rls_enabled is True
    fk = o.foreign_keys[0]
    assert (fk.ref_schema, fk.ref_table, fk.ref_columns, fk.on_delete) == ("public", "customers", ["id"], "CASCADE")
    ix = next(i for i in o.indexes if i.name == "ix_orders_customer")
    assert ix.method == "btree" and ix.include == ["amount"]
    assert db.table("audit_log").column("id").data_type == "bigserial" and db.table("audit_log").column("id").is_identity


def test_pg_dump_objects_and_security(pg_db):
    db = pg_db
    v = db.views[0]
    assert v.name == "v_orders" and sorted(v.references) == ["customers", "orders"]
    fn = next(r for r in db.routines if r.kind == "function")
    assert fn.name == "touch" and "audit_log" in fn.references and "a semicolon; in a body" in fn.definition
    assert next(r for r in db.routines if r.kind == "trigger").table == "customers"
    assert db.security_metadata
    policies = {p.name: p for p in db.policies}
    assert policies["p_tenant"].command == "SELECT" and policies["p_tenant"].roles == ["app_reader", "admin"]
    assert policies["p_tenant"].expression == "(tenant = 1)"
    assert policies["p_write"].expression == "(tenant = 2)"
    roles = {r.name: r for r in db.roles}
    assert roles["app_reader"].can_login and roles["app_reader"].password_set is True
    assert roles["admin"].superuser and roles["admin"].bypass_rls and not roles["admin"].can_login
    assert any(g.grantee == "app_reader" and g.table == "customers" and g.schema == "public" for g in db.grants)
    columns = [g for g in db.grants if g.column == "email"]
    assert {g.privilege for g in columns} == {"SELECT", "UPDATE"} and all(g.grantable for g in columns)
    assert any(g.grantee == "admin" and g.table == "*" and g.schema == "public" for g in db.grants)
    assert any(g.privilege == "USAGE" and g.table is None and g.schema == "public" for g in db.grants)
    assert "hush_secret_2" not in repr(db)


def test_pg_dump_copy_data(pg_db):
    rows = pg_db.data.query("SELECT id, email, mood, active FROM customers ORDER BY id")
    assert rows == [(1, "o'neil@x.io", "ok", 1), (2, "tab\there@x.io", None, 0)]
    assert pg_db.table("customers").row_count == 2 and pg_db.table("orders").row_count == 0


def test_sandbox_is_read_only_and_dump_sql_is_not_executed():
    db = import_sql("""CREATE TABLE a (b text);
        INSERT INTO a VALUES ('x''); DROP TABLE a; --');
        DROP TABLE a;""")
    assert db.data.query("SELECT b FROM a") == [("x'); DROP TABLE a; --",)]
    with pytest.raises(ReadOnlyViolation):
        db.data.query("DELETE FROM a")
    with pytest.raises(sqlite3.OperationalError, match="readonly"):
        db.data._execute("DELETE FROM a", ())
    assert db.data.query("SELECT COUNT(*) FROM a") == [(1,)]


def test_sqlite_dump(tmp_path):
    db = import_sql(SQLITE_DUMP)
    assert db.dialect == "sqlite" and not db.import_warnings, db.import_warnings
    assert [t.name for t in db.tables] == ["t1"], "internal sqlite tables are skipped"
    t = db.table("t1")
    assert t.column("id").is_identity and not t.column("id").nullable and t.column("other").data_type == ""
    assert db.data.query('SELECT name FROM t1 ORDER BY id') == [("a;b",), ("c'd",)]
    assert db.routines[0].kind == "trigger" and "DELETE FROM t1" in db.routines[0].definition


def test_security_metadata_false_without_grants():
    db = import_sql("CREATE TABLE a (b int);")
    assert db.security_metadata is False and db.grants == [] and db.data is None


@pytest.mark.parametrize("sql,fragment", [
    ("CREATE TABLE ok (id int); CREATE TABLE broken (id int, name; SELECT 1;", "could not parse"),
    ("CREATE TABLE ok (id int); THIS IS NOT SQL AT ALL;", "unrecognized"),
    ("CREATE TABLE ok (id int); CREATE TABLE ct AS SELECT 1;", "without a column list"),
    ("CREATE TABLE ok (id int); INSERT INTO missing VALUES (1);", "was not created"),
    ("CREATE TABLE ok (id int); INSERT INTO ok SELECT 1;", "without a VALUES"),
    ("CREATE TABLE ok (id int); INSERT INTO ok VALUES (1,;", "row data not loaded"),
    ("CREATE TABLE ok (id int); ALTER TABLE missing ADD COLUMN b int;", "was not created"),
])
def test_unparseable_statements_warn_and_continue(sql, fragment):
    db = import_sql(sql)
    assert db.table("ok") is not None
    assert any(fragment in w for w in db.import_warnings), db.import_warnings


def test_warnings_never_show_passwords():
    db = import_sql("CREATE USER 'a'@'%' IDENTIFIED BY 'plaintext_pw' ;;; CREATE ROLE broken((( PASSWORD 'other_pw';", dialect="mysql")
    assert not any("plaintext_pw" in w or "other_pw" in w for w in db.import_warnings)


def test_row_length_mismatch_skipped():
    db = import_sql("CREATE TABLE a (b int, c int); INSERT INTO a VALUES (1,2),(3);")
    assert db.data.query("SELECT COUNT(*) FROM a") == [(1,)]
    assert any("row skipped" in w for w in db.import_warnings)


def test_expressions_stored_as_text_with_warning():
    db = import_sql("CREATE TABLE a (b text); INSERT INTO a VALUES (now());", dialect="postgres")
    assert db.data.query("SELECT b FROM a") == [("now()",)]
    assert any("expressions" in w for w in db.import_warnings)


def test_conditional_comment_unwrapped_only_when_executable():
    statements = [s.text for s in split_statements("/*!40000 ALTER TABLE t DISABLE KEYS */; /* plain ; note */ SELECT 1;", "mysql")]
    assert statements == ["ALTER TABLE t DISABLE KEYS", "SELECT 1"]


def test_alter_add_forms_mysql():
    db = import_sql("""CREATE TABLE `t` (`a` int, `b` int, `c` int);
        ALTER TABLE `t` ADD PRIMARY KEY (`a`), ADD KEY `ix_b` (`b`), ADD UNIQUE KEY `ux_c` (`c`),
          ADD CONSTRAINT `fk` FOREIGN KEY (`b`) REFERENCES `t` (`a`) ON DELETE RESTRICT;
        ALTER TABLE `t` MODIFY `c` varchar(10) NOT NULL, ADD COLUMN `d` date;""", dialect="mysql")
    t = db.table("t")
    assert t.primary_key == ["a"] and not t.column("a").nullable
    assert [i.name for i in t.indexes] == ["ix_b", "ux_c"] and t.foreign_keys[0].on_delete == "RESTRICT"
    assert t.column("c").data_type == "varchar(10)" and not t.column("c").nullable and t.column("d").data_type == "date"
    assert not db.import_warnings, db.import_warnings


def test_import_sql_from_file_utf16_and_gzip(tmp_path):
    path = tmp_path / "dump.sql"
    path.write_bytes("CREATE TABLE `é` (`a` int);".encode("utf-16"))
    assert import_sql(str(path)).table("é") is not None
    gz = tmp_path / "dump.sql.gz"
    gz.write_bytes(gzip.compress(b"CREATE TABLE a (b int);"))
    db = import_sql(gz)
    assert db.table("a") is not None and db.name == "dump.sql"
    with pytest.raises(FileNotFoundError):
        import_sql("missing_file.sql")


def test_import_sql_name_and_dialect_override():
    db = import_sql("CREATE TABLE a (b int);", dialect="postgresql", name="custom")
    assert db.dialect == "postgres" and db.name == "custom"


# --------------------------------------------------------------------------------------------------------------------
# CSV
# --------------------------------------------------------------------------------------------------------------------


def write(tmp_path, name, text, encoding="utf-8"):
    path = tmp_path / name
    path.write_bytes(text.encode(encoding))
    return path


def test_csv_infers_types_conservatively(tmp_path):
    path = write(tmp_path, "people data.csv", textwrap.dedent("""\
        id,zip,amount,active,joined,seen,mixed,note
        1,01234,1.50,true,2024-01-31,2024-01-31 10:00:00,1,hello
        2,99999,2,false,2024-02-29,2024-02-01T10:00:00,two,
        3,10001,,true,,2024-03-01 10:00:00,3,"multi
        line"
        """))
    db = import_csv(path)
    assert db.source == "csv" and db.name == "people data"
    t = db.table("people_data")
    types = {c.name: c.data_type for c in t.columns}
    assert types == {"id": "bigint", "zip": "text", "amount": "double precision", "active": "boolean", "joined": "date",
                     "seen": "timestamp", "mixed": "text", "note": "text"}
    assert t.row_count == 3
    rows = db.data.query('SELECT id, zip, amount, active, note FROM people_data ORDER BY id')
    assert rows[0] == (1, "01234", 1.5, 1, "hello") and rows[2][2] is None and rows[2][4] == "multi\nline"
    assert db.data.dialect == "sqlite"
    with pytest.raises(ReadOnlyViolation):
        db.data.query("DROP TABLE people_data")


@pytest.mark.parametrize("delimiter", [",", ";", "\t", "|"])
def test_csv_sniffs_delimiter(tmp_path, delimiter):
    db = import_csv(write(tmp_path, "d.csv", f"a{delimiter}b\n1{delimiter}2\n3{delimiter}4\n"))
    assert [c.name for c in db.table("d").columns] == ["a", "b"]


def test_csv_semicolon_with_decimal_commas(tmp_path):
    db = import_csv(write(tmp_path, "d.csv", "a;b\n1,5;2\n3,5;4\n"))
    assert [c.name for c in db.table("d").columns] == ["a", "b"]
    assert db.table("d").column("a").data_type == "text"


def test_csv_messy_file(tmp_path):
    path = write(tmp_path, "messy.csv", "﻿name,,name,score\nann,1,x,9\n\n,,,\nbob,2\ncat,3,y,8,extra\n", encoding="utf-8")
    db = import_csv(path)
    t = db.table("messy")
    assert [c.name for c in t.columns] == ["name", "column_2", "name_2", "score", "column_5"]
    assert t.row_count == 3
    warnings = " ".join(db.import_warnings)
    for fragment in ("blank header", "duplicate header", "short row", "more fields"):
        assert fragment in warnings, db.import_warnings
    assert db.data.query('SELECT score FROM messy WHERE name = ?', ("bob",)) == [(None,)]


def test_csv_encodings(tmp_path):
    latin = write(tmp_path, "l.csv", "name,x\ncafé,1\n", encoding="latin-1")
    assert import_csv(latin).data.query("SELECT name FROM l") == [("café",)]
    wide = write(tmp_path, "w.csv", "name,x\ncafé,1\n", encoding="utf-16")
    assert import_csv(wide).data.query("SELECT name FROM w") == [("café",)]


def test_csv_empty_and_headerless(tmp_path):
    empty = import_csv(write(tmp_path, "e.csv", ""))
    assert empty.tables == [] and "empty" in empty.import_warnings[0]
    headerless = import_csv(write(tmp_path, "h.csv", "1,2\n3,4\n"))
    assert [c.name for c in headerless.table("h").columns] == ["column_1", "column_2"]
    assert headerless.table("h").row_count == 2
    assert any("no header" in w for w in headerless.import_warnings)


def test_csv_directory(tmp_path):
    (tmp_path / "sub").mkdir()
    write(tmp_path, "a.csv", "x\n1\n")
    write(tmp_path, "b.tsv", "y\tz\n1\t2\n")
    write(tmp_path, "notes.md", "not data")
    db = import_csv(tmp_path, name="many")
    assert db.name == "many" and sorted(t.name for t in db.tables) == ["a", "b"]


def test_csv_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        import_csv(tmp_path / "nope.csv")


# --------------------------------------------------------------------------------------------------------------------
# Excel
# --------------------------------------------------------------------------------------------------------------------


def test_excel_one_table_per_sheet(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    import datetime as dt
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sales Data"
    ws.append(["id", "amount", "when", "ok", "mixed", None])
    ws.append([1, 1.5, dt.datetime(2024, 1, 1), True, 1, None])
    ws.append([2, 2.5, dt.datetime(2024, 1, 2), False, "two", None])
    ws.append([None, None, None, None, None, None])
    second = wb.create_sheet("Empty")
    third = wb.create_sheet("NoHeader")
    third.append([1, "a"])
    third.append([2, "b"])
    del second
    path = tmp_path / "book.xlsx"
    wb.save(path)
    db = import_excel(path)
    assert db.source == "excel" and db.name == "book"
    t = db.table("Sales_Data")
    assert {c.name: c.data_type for c in t.columns} == {"id": "bigint", "amount": "double precision", "when": "timestamp",
                                                        "ok": "boolean", "mixed": "text"}
    assert t.row_count == 2
    rows = db.data.query('SELECT id, amount, "when", ok FROM Sales_Data ORDER BY id')
    assert rows == [(1, 1.5, "2024-01-01T00:00:00", 1), (2, 2.5, "2024-01-02T00:00:00", 0)]
    assert db.table("NoHeader").row_count == 2
    assert any("Empty" in w for w in db.import_warnings)


# --------------------------------------------------------------------------------------------------------------------
# Metadata, logs, pipelines
# --------------------------------------------------------------------------------------------------------------------


def test_metadata_round_trip(tmp_path, pg_db):
    target = tmp_path / "meta.json"
    export_metadata(pg_db, target)
    loaded = import_metadata(target)
    assert loaded.name == pg_db.name and loaded.dialect == "postgres" and loaded.data is None
    assert [t.name for t in loaded.tables] == [t.name for t in pg_db.tables]
    assert loaded.table("orders").foreign_keys[0].on_delete == "CASCADE"
    assert loaded.table("customers").column("id").is_identity
    assert loaded.grants == pg_db.grants and loaded.policies == pg_db.policies
    assert loaded.security_metadata and loaded.settings == pg_db.settings
    assert "data" not in json.loads(target.read_text(encoding="utf-8"))


def test_metadata_tolerates_unknown_and_bad_entries(tmp_path):
    path = write(tmp_path, "m.json", json.dumps({
        "name": "x",
        "tables": [{"name": "t", "columns": [{"name": "c", "data_type": "int", "extra": 1}, {"data_type": "int"}], "weird": True}, "nonsense"],
        "views": "bad",
    }))
    db = import_metadata(path)
    assert [c.name for c in db.table("t").columns] == ["c"]
    text = " ".join(db.import_warnings)
    assert "unknown field 'extra'" in text and "missing required field 'name'" in text and "weird" in text and "expected an object" in text
    assert db.source == "metadata" and db.dialect == "generic" and not db.security_metadata


def test_metadata_rejects_other_formats(tmp_path):
    with pytest.raises(ValueError):
        import_metadata(write(tmp_path, "a.json", json.dumps({"format": "something-else"})))
    with pytest.raises(ValueError):
        import_metadata(write(tmp_path, "b.json", "[1, 2]"))


def test_query_log_text(tmp_path):
    db = Database(name="x", dialect="postgres")
    path = write(tmp_path, "log.sql", "-- note\nSELECT 1;\nSELECT ';' FROM t;\nSELECT 1;\n")
    assert load_query_log(db, path) is db
    assert {(q.sql, q.calls) for q in db.query_stats} == {("SELECT 1", 2), ("SELECT ';' FROM t", 1)}


def test_query_log_json(tmp_path):
    db = Database(name="x")
    path = write(tmp_path, "log.json", json.dumps([
        {"sql": "SELECT 1", "calls": 4, "mean_ms": 2.5, "plan": {"Node": "Seq"}},
        {"sql": "SELECT 2"},
        {"calls": 1},
        {"sql": "SELECT 3", "calls": "many"},
    ]))
    load_query_log(db, path)
    assert len(db.query_stats) == 2
    first = db.query_stats[0]
    assert (first.calls, first.mean_ms, first.total_ms) == (4, 2.5, 10.0) and json.loads(first.plan) == {"Node": "Seq"}
    assert len(db.import_warnings) == 2


def test_query_log_bad_json_warns(tmp_path):
    db = Database(name="x")
    load_query_log(db, write(tmp_path, "log.json", "[not json"))
    assert db.query_stats == [] and "invalid JSON" in db.import_warnings[0]


PIPELINE_YAML = """
pipelines:
  - name: daily_load
    schedule: "0 2 * * *"
    owner: data-team
    retries: 3
    idempotent: true
    quality_checks: [row_count]
    steps:
      - name: stage
        kind: extract
        sources: [crm.orders]
        targets: [stage.orders]
        write_mode: overwrite
      - name: merge
        sql: "MERGE INTO dw.orders USING stage.orders ON id"
        write_mode: merge
        merge_keys: [id]
        incremental_column: updated_at
  - owner: nobody
"""


def test_load_pipelines(tmp_path):
    db = Database(name="x")
    path = write(tmp_path, "p.yaml", PIPELINE_YAML)
    assert load_pipelines(db, path) is db
    assert len(db.pipelines) == 1
    job = db.pipelines[0]
    assert (job.name, job.schedule, job.retries, job.idempotent, job.source_file) == ("daily_load", "0 2 * * *", 3, True, str(path))
    assert job.steps[0].kind == "extract" and job.steps[0].targets == ["stage.orders"]
    assert job.steps[1].merge_keys == ["id"] and job.steps[1].incremental_column == "updated_at"
    assert any("missing required field 'name'" in w for w in db.import_warnings)


def test_load_single_job_and_bad_yaml(tmp_path):
    db = Database(name="x")
    load_pipelines(db, write(tmp_path, "one.yaml", "name: solo\nsteps: []\n"))
    assert db.pipelines[0].name == "solo"
    load_pipelines(db, write(tmp_path, "bad.yaml", "a: [unterminated"))
    assert any("invalid YAML" in w for w in db.import_warnings)


# --------------------------------------------------------------------------------------------------------------------
# load_source
# --------------------------------------------------------------------------------------------------------------------


def test_load_source_dispatch(tmp_path):
    import sqlite3
    sql = write(tmp_path, "d.sql", "CREATE TABLE a (b int);")
    assert load_source(sql, name="n").name == "n"
    assert load_source(sql, dialect="mysql").dialect == "mysql"
    assert load_source(write(tmp_path, "c.csv", "a,b\n1,2\n")).source == "csv"
    assert load_source(tmp_path / "c.csv").table("c") is not None
    db_path = tmp_path / "live.sqlite"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE s (a int)")
    conn.close()
    assert load_source(db_path).source == "live"
    assert load_source(f"sqlite:///{db_path.as_posix()}", name="x").name == "x"
    meta = tmp_path / "m.json"
    export_metadata(Database(name="m"), meta)
    assert load_source(meta).name == "m"
    disguised = tmp_path / "unnamed"
    disguised.write_bytes(db_path.read_bytes())
    assert load_source(disguised).source == "live"
    with pytest.raises(ValueError):
        load_source(write(tmp_path, "x.bin", "abc"))
    with pytest.raises(FileNotFoundError):
        load_source(tmp_path / "nope.csv")


def test_load_source_excel(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    wb = openpyxl.Workbook()
    wb.active.append(["a"])
    wb.active.append([1])
    path = tmp_path / "x.xlsx"
    wb.save(path)
    assert load_source(path).source == "excel"
