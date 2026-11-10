import yaml

from dbintel.analyzers.data_engineering import build_lineage
from dbintel.config import Profile
from dbintel.findings import Fix
from dbintel.model import Column, Database, Index, PipelineJob, PipelineStep, Table, View
from dbintel.rules.engine import CATALOG_DIR, RuleEngine

DW = Profile(workload="data_warehouse")


def catalog():
    rules = []
    for name in ("50_data_engineering.yaml", "60_governance.yaml"):
        rules += yaml.safe_load((CATALOG_DIR / name).read_text(encoding="utf-8"))
    return rules


def run(db, profile=None):
    findings, coverage = RuleEngine(profile or DW, catalog=catalog()).run(db)
    assert not coverage.errors, coverage.errors
    return findings


def by_rule(findings, rule):
    return [f for f in findings if f.rule_id == rule]


def good_job(**kw):
    step = PipelineStep("load", kind="load", sql="MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET a = s.a",
                        sources=["s"], targets=["t"], write_mode="merge", merge_keys=["id"])
    defaults = dict(owner="team", retries=3, idempotent=True, records_run_metadata=True, emits_lineage=True, quality_checks=["uniqueness"])
    return PipelineJob("job", **{"steps": [step], **defaults, **kw})


def pipeline_db(*jobs, **kw):
    return Database("t", tables=[Table("t", columns=[Column("id", "bigint", False), Column("updated_at", "timestamp", False)], primary_key=["id"])],
                    pipelines=list(jobs), **kw)


def step_job(step, **kw):
    return good_job(steps=[step], **kw)


# ---- catalog ----

def test_catalog_is_valid():
    RuleEngine(DW, catalog=catalog())


# ---- clean ----

def test_clean_pipeline_has_no_pipeline_findings():
    f = run(pipeline_db(good_job()), DW)
    assert not [x for x in f if x.rule_id.startswith("DE-")]


# ---- idempotency ----

def test_plain_insert_select_append_is_defect():
    step = PipelineStep("load", sql="INSERT INTO t SELECT * FROM s", sources=["s"], targets=["t"], write_mode="append")
    hit = by_rule(run(pipeline_db(step_job(step, idempotent=None))), "DE-001")[0]
    assert hit.kind.value == "confirmed_defect" and hit.table == "t" and hit.fix.op == "manual"
    assert hit.standards == ["PIP-001"]


def test_idempotent_flag_dedupe_merge_and_prior_delete_are_clean():
    cases = [
        (PipelineStep("load", sql="INSERT INTO t SELECT * FROM s", targets=["t"], write_mode="append"), True),
        (PipelineStep("load", sql="INSERT INTO t SELECT * FROM s WHERE NOT EXISTS (SELECT 1 FROM t WHERE t.id = s.id)", targets=["t"], write_mode="append"), None),
        (PipelineStep("load", sql="INSERT INTO t SELECT * FROM s", targets=["t"], write_mode="append", merge_keys=["id"]), None),
    ]
    for step, flag in cases:
        assert not by_rule(run(pipeline_db(step_job(step, idempotent=flag))), "DE-001")
    delete = PipelineStep("clear", sql="DELETE FROM t WHERE day = '2024-01-01'", targets=["t"])
    insert = PipelineStep("load", sql="INSERT INTO t SELECT * FROM s", targets=["t"], write_mode="append")
    assert not by_rule(run(pipeline_db(good_job(steps=[delete, insert], idempotent=None))), "DE-001")


def test_on_conflict_is_clean():
    step = PipelineStep("load", sql="INSERT INTO t SELECT * FROM s ON CONFLICT (id) DO NOTHING", targets=["t"], write_mode="append")
    assert not by_rule(run(pipeline_db(step_job(step, idempotent=None), dialect="postgres")), "DE-001")


def test_append_without_sql_is_context_dependent():
    step = PipelineStep("load", targets=["t"], write_mode="append")
    assert by_rule(run(pipeline_db(step_job(step, idempotent=None))), "DE-001")[0].kind.value == "context_dependent"


def test_values_insert_is_not_flagged():
    step = PipelineStep("load", sql="INSERT INTO t VALUES (1)", targets=["t"])
    assert not by_rule(run(pipeline_db(step_job(step, idempotent=None))), "DE-001")


def test_unparseable_templated_sql_falls_back_to_text():
    step = PipelineStep("load", sql="INSERT INTO t SELECT a, {{ ds }} FROM s WHERE d = {{ ds }}", targets=["t"], write_mode="append")
    assert by_rule(run(pipeline_db(step_job(step, idempotent=None))), "DE-001")


def test_oltp_profile_downgrades_out_of_scope_standard_to_context():
    step = PipelineStep("load", sql="INSERT INTO t SELECT * FROM s", targets=["t"], write_mode="append")
    hit = by_rule(run(pipeline_db(step_job(step, idempotent=None)), Profile()), "DE-001")[0]
    assert hit.kind.value == "context_dependent" and "scoped to" in hit.evidence


# ---- atomic overwrite ----

def test_truncate_insert_is_not_atomic():
    step = PipelineStep("load", sql="TRUNCATE TABLE t; INSERT INTO t SELECT id FROM s", targets=["t"], write_mode="overwrite")
    hit = by_rule(run(pipeline_db(step_job(step))), "DE-002")[0]
    assert hit.kind.value == "confirmed_defect"


def test_swap_or_transaction_is_atomic():
    for sql in ("BEGIN; TRUNCATE TABLE t; INSERT INTO t SELECT id FROM s; COMMIT;",
                "CREATE OR REPLACE TABLE t AS SELECT id FROM s"):
        step = PipelineStep("load", sql=sql, targets=["t"], write_mode="overwrite")
        assert not by_rule(run(pipeline_db(step_job(step))), "DE-002")


def test_overwrite_without_sql_is_context_dependent():
    step = PipelineStep("load", targets=["t"], write_mode="overwrite")
    assert by_rule(run(pipeline_db(step_job(step))), "DE-002")[0].kind.value == "context_dependent"


# ---- merge and extract ----

def test_merge_without_keys():
    step = PipelineStep("load", targets=["t"], write_mode="merge")
    assert by_rule(run(pipeline_db(step_job(step))), "DE-003")


def test_merge_statement_with_on_clause_is_clean():
    step = PipelineStep("load", sql="MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET a = s.a", targets=["t"], write_mode="merge")
    assert not by_rule(run(pipeline_db(step_job(step))), "DE-003")


def test_extract_without_incremental_column():
    step = PipelineStep("ex", kind="extract", sql="SELECT id FROM orders", sources=["orders"], targets=["st"], write_mode="append")
    hit = by_rule(run(pipeline_db(step_job(step)), Profile()), "DE-004")[0]
    assert hit.table == "orders"


def test_extract_with_watermark_filter_is_clean():
    step = PipelineStep("ex", kind="extract", sql="SELECT id FROM orders WHERE updated_at > :wm", sources=["orders"], write_mode="append")
    assert not by_rule(run(pipeline_db(step_job(step)), Profile()), "DE-004")
    step = PipelineStep("ex", kind="extract", sql="SELECT id FROM orders", sources=["orders"], write_mode="append", incremental_column="updated_at")
    assert not by_rule(run(pipeline_db(step_job(step)), Profile()), "DE-004")


# ---- schema-only readiness ----

def test_schema_only_readiness_runs_without_pipelines():
    t = Table("orders", columns=[Column("id", "bigint", False)])
    findings, coverage = RuleEngine(Profile(), catalog=catalog()).run(Database("t", tables=[t]))
    assert not coverage.errors
    assert {"DE-005", "DE-006"} <= {f.rule_id for f in findings}
    assert "DE-001" in coverage.skipped and "pipelines" in coverage.skipped["DE-001"]
    no_key = by_rule(findings, "DE-006")[0]
    assert no_key.kind.value == "context_dependent" and no_key.confidence == 0.5


def test_change_column_fix_and_exempt():
    t = Table("orders", columns=[Column("id", "bigint", False), Column("note", "text")], primary_key=["id"])
    hit = by_rule(run(Database("t", tables=[t]), Profile()), "DE-005")[0]
    assert hit.column == "updated_at" and hit.fix.op == "add_column"
    assert hit.fix.params == {"type": "timestamp", "nullable": True, "default": None}
    clean = Table("orders", columns=[Column("id", "bigint", False), Column("updated_at", "timestamp")], primary_key=["id"])
    assert not by_rule(run(Database("t", tables=[clean]), Profile()), "DE-005")


def test_table_with_unique_not_null_key_is_cdc_ready():
    t = Table("o", columns=[Column("a", "bigint", False)], indexes=[Index("u", ["a"], unique=True)])
    assert not by_rule(run(Database("t", tables=[t]), Profile()), "DE-006")
    nullable = Table("o", columns=[Column("a", "bigint", True)], indexes=[Index("u", ["a"], unique=True)])
    assert by_rule(run(Database("t", tables=[nullable]), Profile()), "DE-006")


def test_cdc_step_confirms_defect():
    t = Table("orders", columns=[Column("id", "bigint", False)])
    step = PipelineStep("debezium", kind="extract", sources=["orders"], targets=["topic"])
    db = Database("t", tables=[t], pipelines=[good_job(steps=[step])])
    hit = by_rule(run(db, Profile()), "DE-006")[0]
    assert hit.kind.value == "confirmed_defect" and hit.fix.op == "manual"


def test_logical_replication_setting_is_a_context_signal():
    t = Table("orders", columns=[Column("id", "bigint", False)])
    db = Database("t", tables=[t], settings={"wal_level": "logical"})
    assert "logical change capture" in by_rule(run(db, Profile()), "DE-006")[0].evidence


# ---- job-level metadata ----

def test_job_metadata_gaps_and_unknown_is_context():
    job = PipelineJob("j", owner=None, retries=None, records_run_metadata=False, emits_lineage=None, quality_checks=[])
    f = run(pipeline_db(job))
    assert by_rule(f, "DE-007")[0].kind.value == "optional_improvement"
    assert by_rule(f, "DE-008")[0].kind.value == "context_dependent"
    assert by_rule(f, "DE-009") and by_rule(f, "DE-010") and by_rule(f, "DE-011")
    assert all(x.fix.op == "manual" for x in f if x.rule_id in {"DE-007", "DE-008", "DE-009", "DE-010", "DE-011"})


# ---- money ----

def test_float_money_in_schema_and_cast():
    t = Table("fact", columns=[Column("amount", "double precision"), Column("note", "text"), Column("ratio", "float")])
    step = PipelineStep("l", sql="SELECT CAST(x AS DOUBLE) AS total_price FROM s", targets=["t"], write_mode="merge", merge_keys=["id"])
    db = Database("t", tables=[t], pipelines=[good_job(steps=[step])])
    hits = by_rule(run(db), "DE-012")
    assert {(h.column) for h in hits} == {"amount", "total_price"}


def test_float_money_not_checked_on_oltp():
    t = Table("fact", columns=[Column("amount", "double precision")])
    assert not by_rule(run(Database("t", tables=[t]), Profile()), "DE-012")


# ---- lineage ----

def test_build_lineage_from_sql_declared_and_views():
    job = PipelineJob("j", steps=[
        PipelineStep("a", sql="INSERT INTO mart.f SELECT * FROM stg.o JOIN stg.c ON o.id = c.id"),
        PipelineStep("b", sources=["raw.x"], targets=["stg.x"]),
        PipelineStep("c", sql="CREATE TABLE d AS WITH u AS (SELECT * FROM src) SELECT * FROM u"),
    ])
    db = Database("t", pipelines=[job], views=[View("v", "SELECT * FROM a JOIN b ON a.id = b.id")])
    edges = build_lineage(db)
    pairs = {(e["source"], e["target"]) for e in edges}
    assert {("stg.o", "mart.f"), ("stg.c", "mart.f"), ("raw.x", "stg.x"), ("src", "d"), ("a", "v"), ("b", "v")} <= pairs
    assert ("u", "d") not in pairs
    assert {e["origin"] for e in edges} == {"sql", "declared"}


def test_build_lineage_excludes_self_edges_and_is_empty_without_input():
    assert build_lineage(Database("t")) == []
    job = PipelineJob("j", steps=[PipelineStep("a", sql="INSERT INTO t SELECT id FROM t")])
    assert build_lineage(Database("t", pipelines=[job])) == []


def test_lineage_uses_view_references_when_definition_is_missing():
    edges = build_lineage(Database("t", views=[View("v", "", references=["base"])]))
    assert [(e["source"], e["origin"]) for e in edges] == [("base", "declared")]


def test_lineage_gap_when_sql_reads_undeclared_source():
    step = PipelineStep("l", sql="INSERT INTO t SELECT a FROM s JOIN other ON s.id = other.id", sources=["s"], targets=["t"], write_mode="merge", merge_keys=["id"])
    hit = by_rule(run(pipeline_db(step_job(step))), "DE-013")[0]
    assert "other" in hit.evidence


def test_lineage_gap_when_nothing_declared():
    assert by_rule(run(pipeline_db(step_job(PipelineStep("l", kind="transform")))), "DE-013")


# ---- SELECT * and view dependency ----

def test_select_star_steps_and_views_but_not_count():
    step = PipelineStep("l", sql="INSERT INTO t SELECT * FROM s", targets=["t"], write_mode="merge", merge_keys=["id"])
    db = pipeline_db(step_job(step))
    db.views.append(View("v", "SELECT * FROM t"))
    assert len(by_rule(run(db), "DE-014")) == 2
    ok = PipelineStep("l", sql="INSERT INTO t SELECT COUNT(*) AS c FROM s", targets=["t"], write_mode="merge", merge_keys=["id"])
    assert not by_rule(run(pipeline_db(step_job(ok))), "DE-014")


def test_view_dependencies():
    step = PipelineStep("l", sources=["vw_sales"], targets=["t"], write_mode="merge", merge_keys=["id"])
    db = pipeline_db(step_job(step))
    db.views += [View("vw_sales", "SELECT id FROM vw_base"), View("vw_base", "SELECT id FROM t")]
    hits = by_rule(run(db), "DE-015")
    assert len(hits) == 2


def test_view_rules_are_context_on_oltp():
    db = Database("t", views=[View("v", "SELECT * FROM t")])
    assert by_rule(run(db, Profile()), "DE-014")[0].kind.value == "context_dependent"


# ---- governance ----

def gov_table(**kw):
    return Table("orders", columns=[Column("id", "bigint", False)], primary_key=["id"], **kw)


def test_comment_checks_and_sqlite_is_unsupported():
    db = Database("t", dialect="postgres", tables=[gov_table()])
    f = run(db)
    assert by_rule(f, "GVN-001") and by_rule(f, "GVN-002")
    assert not by_rule(run(Database("t", dialect="sqlite", tables=[gov_table()])), "GVN-001")


def test_owner_and_classification_markers_are_found_in_comments():
    t = gov_table(comment="owner: finance; classification: internal")
    f = run(Database("t", dialect="postgres", tables=[t]))
    assert not by_rule(f, "GVN-003") and not by_rule(f, "GVN-004") and not by_rule(f, "GVN-001")
    f = run(Database("t", dialect="postgres", tables=[gov_table()]))
    assert by_rule(f, "GVN-003")[0].confidence == 0.5 and by_rule(f, "GVN-004")[0].kind.value == "context_dependent"


def test_audit_and_retention_structures_and_legal_text():
    f = run(Database("t", tables=[gov_table()]))
    assert by_rule(f, "GVN-005")
    retention = by_rule(f, "GVN-006")[0]
    assert retention.kind.value == "context_dependent" and "requires legal review" in retention.recommended_solution.lower()
    tables = [gov_table(), Table("audit_log", columns=[Column("id", "bigint", False)], primary_key=["id"]),
              Table("retention_schedule", columns=[Column("id", "bigint", False)], primary_key=["id"])]
    f = run(Database("t", tables=tables))
    assert not by_rule(f, "GVN-005") and not by_rule(f, "GVN-006")


def test_retention_skipped_when_not_system_of_record():
    assert not by_rule(run(Database("t", tables=[gov_table()]), Profile(system_of_record=False)), "GVN-006")


def test_migration_history():
    assert by_rule(run(Database("t", tables=[gov_table()])), "GVN-007")
    tables = [gov_table(), Table("flyway_schema_history", columns=[Column("id", "bigint", False)], primary_key=["id"])]
    assert not by_rule(run(Database("t", tables=tables)), "GVN-007")


# ---- reliability ----

def live(settings, dialect="postgres", tables=None):
    return Database("t", dialect=dialect, source="live", settings=settings, tables=tables or [gov_table()])


def test_recovery_off_is_low_confidence():
    hit = by_rule(run(live({"archive_mode": "off"}), Profile()), "REL-001")[0]
    assert hit.kind.value == "context_dependent" and hit.confidence == 0.4 and "cannot prove" in hit.technical_impact


def test_recovery_on_is_informational_and_never_claims_a_backup():
    hit = by_rule(run(live({"archive_mode": "on", "wal_level": "replica"}), Profile()), "REL-002")[0]
    assert hit.severity.value == "informational" and hit.confidence == 0.4 and "cannot prove" in hit.evidence


def test_recovery_mysql_settings_and_requires_live():
    assert by_rule(run(live({"log_bin": "OFF"}, dialect="mysql"), Profile()), "REL-001")
    findings, coverage = RuleEngine(Profile(), catalog=catalog()).run(Database("t", tables=[gov_table()], settings={"archive_mode": "off"}))
    assert "REL-001" in coverage.skipped


def test_replica_and_history_are_not_backup_substitutes():
    hit = by_rule(run(live({"hot_standby": "on"}), Profile()), "REL-003")[0]
    assert hit.severity.value == "informational"
    tables = [gov_table(), Table("orders_history", columns=[Column("id", "bigint", False)], primary_key=["id"])]
    assert by_rule(run(Database("t", tables=tables), Profile()), "REL-003")
    assert not by_rule(run(Database("t", tables=[gov_table()]), Profile()), "REL-003")


# ---- fix ops ----

def test_only_known_fix_ops_are_used():
    allowed = {"add_column", "set_not_null", "add_foreign_key", "add_index", "add_check", "enable_rls", "revoke_grant", "manual"}
    step = PipelineStep("l", sql="TRUNCATE TABLE t; INSERT INTO t SELECT id FROM s", targets=["t"], write_mode="overwrite")
    f = run(pipeline_db(step_job(step)))
    assert all(isinstance(x.fix, Fix) and x.fix.op in allowed for x in f if x.fix)
