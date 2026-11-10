"""Safety properties end to end: the source is never changed, writes are rejected, and only an approved sandbox can run a plan.

The PostgreSQL tests start a real server with pgserver in a temporary directory, as tests/test_connectors.py does.
"""
import hashlib
import inspect
import shutil
import sqlite3
from pathlib import Path

import pytest

import dbintel.cli
from dbintel.connectors import ConnectorError, ReadOnlyViolation, open_connector
from dbintel.migrate.generator import MigrationPlan
from dbintel.migrate.safety import ApprovalRequired, plan_hash
from dbintel.migrate.sandbox import SandboxRefused, test_plan_in_sandbox
from dbintel.pipeline import assess

SAMPLES = Path(__file__).resolve().parent.parent / "samples"
SAAS_SQL = SAMPLES / "saas_postgres.sql"
SAAS_PROFILE = str(SAMPLES / "profiles" / "saas.yaml")
MAJOR = {"TENA-001", "TENA-003", "TENA-006", "TENA-007", "SCH-020"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --- file sources ---------------------------------------------------------------

@pytest.mark.parametrize("name", ["erp_mysql.sql", "saas_postgres.sql", "clean_postgres.sql", "excel/sales_book.xlsx", "csv/customers.csv"])
def test_assess_does_not_change_source_files(name):
    path = SAMPLES / name
    before = sha(path)
    assess(path)
    assert sha(path) == before


def _sqlite_source(path: Path) -> Path:
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE customers (id INTEGER PRIMARY KEY, email TEXT);
        CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER, amount REAL);
        INSERT INTO customers VALUES (1, 'a@example.com');
        INSERT INTO orders VALUES (1, 1, 9.99), (2, 7, 1.5);
    """)
    conn.commit()
    conn.close()
    return path


def test_assess_leaves_a_sqlite_file_byte_identical_and_closes_the_connector(tmp_path):
    db_file = _sqlite_source(tmp_path / "shop.db")
    before = sha(db_file)
    assessment = assess(db_file)
    assert sha(db_file) == before
    assert assessment.db.data is None, "the live connector is closed and released"
    with sqlite3.connect(db_file) as conn:
        assert conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 2


def test_connector_is_closed_when_a_rule_step_crashes(tmp_path, monkeypatch):
    db_file = _sqlite_source(tmp_path / "shop.db")
    from dbintel import pipeline

    def boom(*a, **k):
        raise RuntimeError("generator failed")

    captured = {}
    real_open = pipeline.load_source

    def spy(*a, **k):
        db = real_open(*a, **k)
        captured["conn"] = db.data
        return db

    monkeypatch.setattr(pipeline, "load_source", spy)
    monkeypatch.setattr(pipeline, "generate_plan", boom)
    with pytest.raises(RuntimeError):
        assess(db_file)
    with pytest.raises(ConnectorError):
        captured["conn"].query("SELECT 1 FROM orders")


def test_assess_writes_nothing_to_the_source_directory(tmp_path):
    db_file = _sqlite_source(tmp_path / "shop.db")
    listed = sorted(p.name for p in tmp_path.iterdir())
    assess(db_file)
    assert sorted(p.name for p in tmp_path.iterdir()) == listed


# --- read-only enforcement --------------------------------------------------------

@pytest.mark.parametrize("statement", ["INSERT INTO orders VALUES (3, 1, 1.0)", "DELETE FROM orders", "DROP TABLE orders", "UPDATE orders SET amount = 0",
                                       "SELECT 1; DELETE FROM orders", "CREATE TABLE t (a INT)"])
def test_sqlite_connector_rejects_writes(tmp_path, statement):
    url = f"sqlite:///{_sqlite_source(tmp_path / 'shop.db').as_posix()}"
    with open_connector(url) as conn:
        with pytest.raises(ReadOnlyViolation):
            conn.query(statement)


def test_sqlite_read_only_is_also_enforced_by_the_driver(tmp_path):
    url = f"sqlite:///{_sqlite_source(tmp_path / 'shop.db').as_posix()}"
    with open_connector(url) as conn:
        with pytest.raises(sqlite3.OperationalError, match="readonly|query_only|read-only"):
            conn._execute("DELETE FROM orders", ())


def test_passwords_never_appear_in_the_report_source_label():
    from dbintel.pipeline import _label
    assert "s3cret" not in _label("postgresql://app:s3cret@db.example/shop") and _label("postgresql://app:s3cret@db.example/shop").startswith("postgresql://app:***@")


def test_no_public_path_applies_a_plan_to_a_source():
    import dbintel.migrate as migrate
    import dbintel.reporting as reporting
    import dbintel.pipeline as pipeline_module
    names = {n for mod in (migrate, reporting, pipeline_module) for n in dir(mod)}
    assert not [n for n in names if n.lower().startswith(("apply_plan", "apply_migration", "execute_plan", "run_migration"))]
    assert "connect" not in inspect.signature(assess).parameters and "apply" not in inspect.signature(assess).parameters
    for path in (Path(dbintel.__file__).parent).rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if path.name == "sandbox.py":
            continue
        assert "up_script" not in text or path.name in {"writer.py", "generator.py", "content.py", "engine.py"}, path


def test_cli_never_opens_a_write_connection():
    source = inspect.getsource(dbintel.cli)
    assert "psycopg" not in source and "pymysql" not in source and "sqlite3" not in source
    assert "write_migration_files" not in source, "the CLI only reaches migration files through write_reports"


# --- approval --------------------------------------------------------------------

def test_sandbox_requires_exact_plan_hash():
    assessment = assess(SAMPLES / "clean_postgres.sql")
    for token in (None, "", "x", assessment.plan_hash[:-1]):
        with pytest.raises(ApprovalRequired):
            test_plan_in_sandbox(assessment.db, assessment.plan, token)
    report = test_plan_in_sandbox(assessment.db, assessment.plan, assessment.plan_hash)
    assert report.plan_hash == assessment.plan_hash


def test_changing_a_plan_invalidates_its_token():
    assessment = assess(SAMPLES / "clean_postgres.sql")
    token = assessment.plan_hash
    assessment.plan.steps[0].title += " tampered"
    with pytest.raises(ApprovalRequired):
        test_plan_in_sandbox(assessment.db, assessment.plan, token)


def test_sandbox_default_target_is_a_private_temp_file_not_the_source(tmp_path):
    db_file = _sqlite_source(tmp_path / "shop.db")
    before = sha(db_file)
    assessment = assess(db_file)
    from dbintel.importers import load_source
    source_db = load_source(db_file)
    try:
        test_plan_in_sandbox(source_db, assessment.plan, assessment.plan_hash)
    finally:
        source_db.data.close()
    assert sha(db_file) == before


def test_sandbox_refuses_unlisted_host_and_unprefixed_database():
    assessment = assess(SAMPLES / "clean_postgres.sql")
    token = assessment.plan_hash
    def fail_connect(url):  # pragma: no cover - must never be reached
        raise AssertionError("no connection may be opened")
    with pytest.raises(SandboxRefused, match="allow_hosts"):
        test_plan_in_sandbox(None, assessment.plan, token, scratch_url="postgresql://u@prod.example/dbintel_sandbox_a", allow_hosts=[], connect=fail_connect)
    with pytest.raises(SandboxRefused, match="must begin with"):
        test_plan_in_sandbox(None, assessment.plan, token, scratch_url="postgresql://u@127.0.0.1/shop", allow_hosts=["127.0.0.1"], connect=fail_connect)
    with pytest.raises(SandboxRefused, match="password"):
        test_plan_in_sandbox(None, assessment.plan, token, scratch_url="postgresql://u:pw@127.0.0.1/dbintel_sandbox_a", allow_hosts=["127.0.0.1"], connect=fail_connect)


# --- real PostgreSQL -------------------------------------------------------------

@pytest.fixture(scope="module")
def pg(tmp_path_factory):
    """A throwaway PostgreSQL server holding the SaaS sample. Skips when pgserver or psycopg are unavailable."""
    pgserver = pytest.importorskip("pgserver")
    psycopg = pytest.importorskip("psycopg")
    pgdata = tmp_path_factory.mktemp("pgdata_e2e")
    server = pgserver.get_server(pgdata, cleanup_mode="stop")
    admin_uri = server.get_uri()
    base = admin_uri.replace("postgres:@", "postgres@").rsplit("/", 1)[0]
    with psycopg.connect(admin_uri, autocommit=True) as admin:
        admin.execute("CREATE DATABASE saas")
        admin.execute("CREATE DATABASE clean_demo")
    server.psql("\\c saas\n" + SAAS_SQL.read_text(encoding="utf-8"))
    server.psql("\\c clean_demo\n" + (SAMPLES / "clean_postgres.sql").read_text(encoding="utf-8"))
    yield {"server": server, "base": base, "admin": admin_uri, "psycopg": psycopg, "url": f"{base}/saas"}
    server.cleanup()
    shutil.rmtree(pgdata, ignore_errors=True)


def recreate_scratch(pg):
    """Build a scratch copy of the sample under the reserved dbintel_sandbox_ name. The source database is never used."""
    psycopg = pg["psycopg"]
    with psycopg.connect(pg["admin"], autocommit=True) as admin:
        admin.execute('DROP DATABASE IF EXISTS "dbintel_sandbox_e2e"')
        admin.execute('CREATE DATABASE "dbintel_sandbox_e2e"')
    sql = SAAS_SQL.read_text(encoding="utf-8").replace("CREATE ROLE app_user LOGIN;", "")
    pg["server"].psql("\\c dbintel_sandbox_e2e\n" + sql)
    return psycopg.connect(f"{pg['base']}/dbintel_sandbox_e2e", autocommit=True)


@pytest.fixture(scope="module")
def live_assessment(pg):
    return assess(pg["url"], profile=SAAS_PROFILE, name="saas_live")


def test_live_assess_reads_postgres_through_the_read_only_connector(pg, live_assessment):
    a = live_assessment
    assert a.db.source == "live" and a.db.dialect == "postgres" and a.db.data is None, "closed after assess"
    assert not a.coverage.errors, a.coverage.errors
    assert {"data", "live", "security_metadata"} <= set(a.capabilities)


def test_live_postgres_finds_the_same_major_issues_as_the_dump(live_assessment):
    dump = assess(SAAS_SQL, profile=SAAS_PROFILE, name="saas_demo")
    live_rules, dump_rules = {f.rule_id for f in live_assessment.findings}, {f.rule_id for f in dump.findings}
    assert MAJOR <= live_rules and MAJOR <= dump_rules
    table = lambda findings: {(f.rule_id, (f.table or "").split(".")[-1], f.column) for f in findings if f.rule_id in MAJOR}
    assert table(live_assessment.findings) == table(dump.findings), "live and dump agree on the major tenant findings"
    # A live server reports GRANT ALL as individual privileges, so the same over-grant shows up per table as SECA-001.
    excess = [f for f in live_assessment.findings if f.rule_id == "SECA-001" and "app_user" in f.evidence and "TRUNCATE" in f.evidence]
    assert len(excess) == 6 and all(f.severity.value == "high" and f.kind.value == "confirmed_defect" for f in excess)
    assert any(f.rule_id == "SECA-002" and "PUBLIC" in f.evidence for f in live_assessment.findings)
    assert live_assessment.health.capped


def test_live_postgres_row_counts_and_schema_unchanged_by_assess(pg, live_assessment):
    psycopg = pg["psycopg"]
    with psycopg.connect(pg["url"], autocommit=True) as conn:
        assert conn.execute("SELECT count(*) FROM public.users").fetchone()[0] == 6
        assert conn.execute("SELECT count(*) FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'tasks' AND column_name = 'tenant_id'").fetchone()[0] == 0


@pytest.mark.parametrize("statement", ["INSERT INTO public.tenants (id, name, plan, created_at) VALUES (9, 'x', 'p', now())", "DELETE FROM public.users", "DROP TABLE public.comments", "SELECT 1; DELETE FROM public.users"])
def test_live_connector_rejects_writes(pg, statement):
    with open_connector(pg["url"]) as conn:
        with pytest.raises(ReadOnlyViolation):
            conn.query(statement)
        with pytest.raises(ConnectorError, match="read-only"):
            conn.query("SELECT pg_catalog.set_config('transaction_read_only', 'off', false)")
    with pg["psycopg"].connect(pg["url"], autocommit=True) as check:
        assert check.execute("SELECT count(*) FROM public.users").fetchone()[0] == 6


def test_live_server_itself_refuses_writes_on_the_connector_session(pg):
    with open_connector(pg["url"]) as conn:
        with pytest.raises(Exception, match="read-only"):
            conn._execute("DELETE FROM public.users", ())


def test_live_clean_sample_has_no_blocking_defects(pg):
    a = assess(f"{pg['base']}/clean_demo", profile=str(SAMPLES / "profiles" / "clean.yaml"), name="clean_live")
    blocking = [f for f in a.findings if f.kind.value == "confirmed_defect" and f.severity.value in ("critical", "high") and not f.rule_id.startswith("SECA-")]
    assert not blocking, [(f.rule_id, f.table, f.column, f.evidence) for f in blocking]


def _scratch_url(pg):
    return f"{pg['base']}/dbintel_sandbox_e2e"


def _host(pg):
    from urllib.parse import urlsplit
    return urlsplit(pg["base"]).hostname


def _prepare_repaired_scratch(pg):
    """Load the sample and repair the NULL tenant the sample contains, as a DBA would before running these steps."""
    conn = recreate_scratch(pg)
    conn.execute("UPDATE public.users SET tenant_id = 1 WHERE tenant_id IS NULL")
    return conn


def test_generated_plan_runs_up_and_down_on_real_postgres(pg, live_assessment):
    conn = _prepare_repaired_scratch(pg)
    try:
        before = conn.execute("SELECT count(*) FROM information_schema.columns WHERE table_schema = 'public'").fetchone()[0]
    finally:
        conn.close()
    a = live_assessment
    report = test_plan_in_sandbox(a.db, a.plan, a.plan_hash, scratch_url=_scratch_url(pg), allow_hosts=[_host(pg)],
                                  connect=lambda url: pg["psycopg"].connect(url, autocommit=True))
    failed = [(r.step_id, r.title, r.reason) for r in report.results if r.status == "failed"]
    assert not failed, failed
    assert report.isolated and report.engine == "postgres-scratch"
    executed = [r for r in report.results if r.status == "passed"]
    assert len(executed) >= 40, f"too few steps actually ran: {len(executed)}"
    for result in executed:
        step = next(s for s in a.plan.steps if s.id == result.step_id)
        if step.reversible and step.down_sql:
            assert result.rollback == "passed", (step.id, result.reason)
            assert result.schema_restored is True, step.id
    assert before > 0, "the scratch database really held the schema"


def _reversible_only(plan):
    """A plan of the executable steps whose rollback restores everything, closed over dependencies."""
    kept = {s.id: s for s in plan.steps if not s.manual and s.reversible and s.down_sql}
    changed = True
    while changed:
        changed = False
        for sid, step in list(kept.items()):
            if any(need not in kept for need in step.depends_on):
                del kept[sid]
                changed = True
    return MigrationPlan(database=plan.database, source_dialect=plan.source_dialect, dialect=plan.dialect, steps=[s for s in plan.steps if s.id in kept],
                         notes=list(plan.notes), unaddressed_findings=list(plan.unaddressed_findings), satisfied_findings=list(plan.satisfied_findings), backup_recommendation=plan.backup_recommendation)


def test_full_rollback_restores_schema_on_real_postgres(pg, live_assessment):
    subset = _reversible_only(live_assessment.plan)
    assert len(subset.steps) >= 20, "enough reversible steps to be a meaningful proof"
    conn = _prepare_repaired_scratch(pg)
    conn.close()
    report = test_plan_in_sandbox(live_assessment.db, subset, plan_hash(subset), scratch_url=_scratch_url(pg), allow_hosts=[_host(pg)],
                                  connect=lambda url: pg["psycopg"].connect(url, autocommit=True))
    assert report.overall == "passed", [(r.step_id, r.status, r.reason) for r in report.results if r.status != "passed"]
    assert report.schema_restored is True, report.schema_restored_reason


def test_unrepaired_data_blocks_steps_on_real_postgres_instead_of_failing_midway(pg, live_assessment):
    recreate_scratch(pg).close()
    a = live_assessment
    report = test_plan_in_sandbox(a.db, a.plan, a.plan_hash, scratch_url=_scratch_url(pg), allow_hosts=[_host(pg)],
                                  connect=lambda url: pg["psycopg"].connect(url, autocommit=True))
    blocked = [r for r in report.results if r.status == "failed"]
    assert blocked and all("Precheck failed" in r.reason for r in blocked), [(r.step_id, r.reason) for r in blocked]
    tenant = {r.title for r in blocked}
    assert any("tenant_id" in title for title in tenant)


def test_sandbox_refuses_the_source_database_itself(pg, live_assessment):
    a = live_assessment
    with pytest.raises(SandboxRefused):
        test_plan_in_sandbox(a.db, a.plan, a.plan_hash, scratch_url=pg["url"], allow_hosts=[_host(pg)], connect=lambda url: pg["psycopg"].connect(url, autocommit=True))
