"""End-to-end assessment of every sample against its expected_findings.yaml, plus parse checks of the samples."""
import json
from pathlib import Path

import pytest
import yaml

from dbintel.config import Profile, load_profile
from dbintel.findings import CATEGORIES, FindingKind, Severity
from dbintel.importers import import_sql, load_pipelines, load_query_log, load_source
from dbintel.model import Database, QueryStat, Table, Column
from dbintel.pipeline import Assessment, assess, build_lineage

SAMPLES = Path(__file__).resolve().parent.parent / "samples"
EXPECTED_FILES = {"erp": "erp_mysql.expected_findings.yaml", "saas": "saas_postgres.expected_findings.yaml", "clean": "clean_postgres.expected_findings.yaml",
                  "csv": "csv/expected_findings.yaml", "excel": "excel/expected_findings.yaml"}


def spec_for(key):
    return yaml.safe_load((SAMPLES / EXPECTED_FILES[key]).read_text(encoding="utf-8"))


def run_spec(spec) -> Assessment:
    kw = {}
    for field in ("query_log", "pipelines"):
        if spec.get(field):
            kw[field] = str(SAMPLES / spec[field])
    return assess(SAMPLES / spec["source"], profile=str(SAMPLES / spec["profile"]) if spec.get("profile") else None, name=spec.get("name"), **kw)


@pytest.fixture(scope="module")
def assessments():
    return {key: run_spec(spec_for(key)) for key in EXPECTED_FILES}


def matches(f, item):
    if f.rule_id != item["rule"]:
        return False
    if "table" in item and f.table != item["table"]:
        return False
    if "column" in item and f.column != item["column"]:
        return False
    if "evidence_contains" in item and item["evidence_contains"] not in f.evidence:
        return False
    return True


@pytest.mark.parametrize("key", list(EXPECTED_FILES))
def test_expected_findings_are_detected_with_the_right_severity(assessments, key):
    spec, assessment = spec_for(key), assessments[key]
    for item in spec.get("expected") or []:
        hits = [f for f in assessment.findings if matches(f, item)]
        assert hits, f"{key}: expected finding not reported: {item}"
        assert any(f.severity.value == item["severity"] for f in hits), f"{key}: wrong severity for {item}: {[f.severity.value for f in hits]}"
        if "kind" in item:
            assert any(f.kind.value == item["kind"] and f.severity.value == item["severity"] for f in hits), f"{key}: wrong kind for {item}"


@pytest.mark.parametrize("key", list(EXPECTED_FILES))
def test_listed_false_positives_are_absent(assessments, key):
    for item in spec_for(key).get("absent") or []:
        offenders = [f for f in assessments[key].findings if matches(f, item)]
        assert not offenders, f"{key}: false positive {item}: {[(f.table, f.column, f.evidence) for f in offenders]}"


def test_clean_sample_has_no_critical_or_high_confirmed_defect(assessments):
    spec = spec_for("clean")
    limit = Severity(spec["no_confirmed_at_or_above"]).rank
    assessment = assessments["clean"]
    blocking = [f for f in assessment.findings if f.kind is FindingKind.CONFIRMED_DEFECT and f.severity.rank <= limit]
    assert not blocking, [(f.rule_id, f.table, f.column) for f in blocking]
    assert assessment.health.overall is not None and assessment.health.overall >= spec["minimum_overall_score"]
    assert not assessment.health.capped


def test_erp_score_is_capped_and_reports_data_rule_coverage(assessments):
    erp = assessments["erp"]
    assert erp.health.capped and erp.health.overall == 59.0
    assert "data" in erp.capabilities and "query_stats" in erp.capabilities and "pipelines" in erp.capabilities
    assert not erp.coverage.errors, erp.coverage.errors


def test_dump_data_checks_reach_schema_qualified_tables(assessments):
    """PostgreSQL dumps name tables as public.x. Rows must still be reachable, not silently skipped."""
    saas = assessments["saas"]
    assert not [w for w in saas.db.import_warnings if "Data check skipped" in w], saas.db.import_warnings
    assert any(f.rule_id == "SECA-005" for f in saas.findings), "email sampling needs row access"


def test_rule_executed_only_when_inputs_exist(assessments):
    saas = assessments["saas"]
    assert saas.coverage.skipped["PERF-004"].startswith("input not available"), saas.coverage.skipped["PERF-004"]
    assert any(reason.startswith("not applicable") for reason in assessments["clean"].coverage.skipped.values())


def test_csv_sources_do_not_claim_declared_schema_defects(assessments):
    for key in ("csv", "excel"):
        assert "declared_schema" not in assessments[key].capabilities
        assert assessments[key].coverage.skipped["SCH-001"].startswith("input not available: declared_schema")
        assert "SCH-001" not in {f.rule_id for f in assessments[key].findings}


def test_identity_columns_are_numbered_when_omitted_from_inserts(assessments):
    """Clean sample inserts omit generated keys; children must still resolve to parents, so DQ-007 stays silent."""
    assert not [f for f in assessments["clean"].findings if f.rule_id == "DQ-007"]


def test_assessment_structure(assessments):
    a = assessments["erp"]
    assert isinstance(a, Assessment)
    for step in ("import_and_extract", "run_rules", "classify_and_score", "generate_proposed_sql", "recommend_before_and_after", "total"):
        assert step in a.timing
    assert a.timing["total"] >= a.timing["run_rules"]
    assert a.plan.steps and a.recommendations and a.root_cause_groups
    assert len(a.health.categories) == len(CATEGORIES)


def test_lineage_comes_from_the_pipeline_manifest(assessments):
    edges = {(e["source"], e["target"]) for e in assessments["erp"].lineage["edges"]}
    assert ("orders", "stg_orders") in edges and ("stg_orders", "fact_sales") in edges


def test_lineage_records_gaps():
    db = Database("x", tables=[Table("t", columns=[Column("a", "int")])])
    from dbintel.model import PipelineJob, PipelineStep
    db.pipelines.append(PipelineJob("job", steps=[PipelineStep("nothing"), PipelineStep("load", sources=["t"])]))
    gaps = build_lineage(db)["gaps"]
    assert any("declares no sources or targets" in g for g in gaps) and any("no targets" in g for g in gaps)


def test_assess_accepts_a_database_object_and_a_profile_object():
    db = import_sql(SAMPLES / "clean_postgres.sql")
    a = assess(db, profile=Profile(), name="renamed")
    assert a.db.name == "renamed" and a.source_label == "model:renamed"


def test_identifier_escaping_does_not_crash_the_pipeline():
    db = Database("odd db", dialect="postgres", source="metadata", tables=[Table("my table", columns=[Column("a b", "int"), Column("<x>", "text")])])
    a = assess(db)
    assert not a.coverage.errors, a.coverage.errors


# --- samples are parseable -----------------------------------------------------

@pytest.mark.parametrize("name,dialect,tables", [("erp_mysql.sql", "mysql", 11), ("saas_postgres.sql", "postgres", 6), ("clean_postgres.sql", "postgres", 7)])
def test_sql_samples_parse_without_warnings(name, dialect, tables):
    db = import_sql(SAMPLES / name)
    assert db.dialect == dialect and len(db.tables) == tables
    assert db.import_warnings == [], db.import_warnings
    assert all(t.row_count is not None for t in db.tables)


def test_csv_excel_query_log_and_pipeline_samples_load():
    csv_db = load_source(SAMPLES / "csv")
    assert {t.name for t in csv_db.tables} == {"customers", "orders"} and not csv_db.import_warnings
    book = load_source(SAMPLES / "excel" / "sales_book.xlsx")
    assert {t.name for t in book.tables} == {"customers", "orders"} and not book.import_warnings
    target = import_sql(SAMPLES / "erp_mysql.sql")
    load_query_log(target, SAMPLES / "query_log.json")
    assert len(target.query_stats) == 6 and all(isinstance(q, QueryStat) for q in target.query_stats)
    load_pipelines(target, SAMPLES / "pipelines.yaml")
    assert len(target.pipelines) == 2 and not target.import_warnings
    assert all(q.mean_ms > 0 for q in target.query_stats)


@pytest.mark.parametrize("name", ["erp.yaml", "saas.yaml", "clean.yaml"])
def test_profile_samples_load(name):
    profile = load_profile(SAMPLES / "profiles" / name)
    assert profile.workload == "OLTP"


def test_excel_script_is_reproducible(tmp_path, monkeypatch):
    import importlib.util
    pytest.importorskip("openpyxl")
    spec = importlib.util.spec_from_file_location("make_excel_sample", SAMPLES / "make_excel_sample.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    copy = tmp_path / "make_excel_sample.py"
    copy.write_text((SAMPLES / "make_excel_sample.py").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(module, "__file__", str(copy))
    path = module.main()
    assert path.parent == tmp_path / "excel" and load_source(path).table("orders").row_count == 3


def test_sample_data_is_marked_fictional():
    for name in ("erp_mysql.sql", "saas_postgres.sql", "clean_postgres.sql"):
        assert "FICTIONAL" in (SAMPLES / name).read_text(encoding="utf-8")


def test_query_log_json_is_valid():
    entries = json.loads((SAMPLES / "query_log.json").read_text(encoding="utf-8"))
    assert all({"sql", "calls", "mean_ms"} <= set(e) for e in entries)
