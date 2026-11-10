import pytest

from dbintel.findings import Finding, FindingKind, Fix, Severity
from dbintel.migrate import generate_plan
from dbintel.model import Column, Database, ForeignKey, Index, PipelineJob, PipelineStep, Routine, Table, View
from dbintel.recommend import build_recommendations, root_cause_groups


def finding(op, table, column=None, fid=None, severity=Severity.HIGH, kind=FindingKind.CONFIRMED_DEFECT, category="schema_quality",
            confidence=0.9, complexity="low", root_cause="Missing key.", rule="R-1", **params):
    return Finding(id=fid or f"F-{op}-{table}-{column}", rule_id=rule, title=f"{op} on {table}", severity=severity, kind=kind, category=category,
                   database="shop", table=table, column=column, evidence="evidence text", root_cause=root_cause, business_impact="b",
                   technical_impact="t", standards=[], standard_statements={}, recommended_solution="s", complexity=complexity,
                   migration_requirements="m", risks="r", validation_strategy="Check the outcome.", confidence=confidence,
                   fix=Fix(op, table, column, params) if op else None)


def model():
    customers = Table("customers", columns=[Column("id", "int", False), Column("email", "varchar(100)", True), Column("legacy", "text", True)],
                      primary_key=["id"], row_count=5, indexes=[Index("ix_customers_email", ["email"])])
    orders = Table("orders", columns=[Column("id", "int", False), Column("customer_id", "int", True), Column("amount", "decimal(10,2)", True)],
                   primary_key=["id"], row_count=5, foreign_keys=[ForeignKey("fk_o_c", ["customer_id"], "customers", ["id"])])
    db = Database("shop", "postgres", "live", tables=[customers, orders])
    db.views += [View("v_mail", "SELECT c.email, c.id FROM customers c"),
                 View("v_star", "SELECT * FROM customers"),
                 View("v_unrelated", "SELECT id FROM orders"),
                 View("v_broken", "SELECT legacy FROM customers WHERE ??? bad syntax here"),
                 View("v_join", "SELECT email, amount FROM customers JOIN orders ON customers.id = orders.customer_id")]
    db.routines += [Routine("touch_customers", kind="procedure", definition="-- customers legacy\nUPDATE customers SET email = NULL"),
                    Routine("uses_legacy", kind="function", definition="SELECT legacy FROM customers"),
                    Routine("unrelated", definition="SELECT 1"),
                    Routine("trg_cust", kind="trigger", table="customers", definition="BEGIN NULL; END")]
    db.pipelines.append(PipelineJob("nightly", steps=[PipelineStep("load", sql="INSERT INTO stats SELECT * FROM customers", sources=["customers"])]))
    return db


def recommend(findings, app_dir=None, db=None):
    db = db or model()
    return build_recommendations(db, findings, generate_plan(db, findings), app_dir)


def test_groups_per_table():
    recs = recommend([finding("set_not_null", "customers", "email"), finding("add_index", "customers", None, fid="B", columns=["legacy"]),
                      finding("add_index", "orders", None, fid="C", columns=["amount"])])
    assert len(recs) == 2 and {r.table for r in recs} == {"customers", "orders"}
    assert next(r for r in recs if r.table == "customers").finding_ids == ["B", "F-set_not_null-customers-email"]


def test_tableless_finding_grouped_by_concern():
    recs = recommend([finding(None, None, category="security", fid="G")])
    assert len(recs) == 1 and recs[0].table is None and "security" in recs[0].title


def test_recommendation_fields_are_populated():
    rec = recommend([finding("set_not_null", "customers", "email")])[0]
    assert "email" in rec.existing_structure and "evidence text" in rec.weakness
    assert "NOT NULL" in rec.recommended_structure and "NOT NULL" in rec.before_after["after"]
    assert "NOT NULL" not in rec.before_after["before"].split("email", 1)[1].split("\n", 1)[0]
    assert "SET NOT NULL" in rec.proposed_sql
    assert rec.rollback and rec.validation_tests and rec.business_logic_notes


def test_foreign_key_dependency_detected():
    rec = recommend([finding("add_index", "customers", None, columns=["legacy"])])[0]
    kinds = {(d["kind"], d["object"]) for d in rec.data_dependencies}
    assert ("foreign_key_in", "orders.fk_o_c") in kinds


def test_outgoing_foreign_key_listed():
    rec = recommend([finding("add_index", "orders", None, columns=["amount"])])[0]
    assert any(d["kind"] == "foreign_key_out" for d in rec.data_dependencies)


def test_view_dependencies_parsed_with_columns():
    rec = recommend([finding("set_not_null", "customers", "email")])[0]
    by_name = {d["object"]: d for d in rec.data_dependencies}
    assert by_name["v_mail"]["method"] == "sqlglot" and by_name["v_mail"]["columns"] == ["email"]
    assert "v_unrelated" not in by_name
    assert by_name["v_star"]["select_star"] is True
    assert by_name["v_join"]["possible_columns"] == ["email"]


def test_unparseable_view_falls_back_to_text_search():
    rec = recommend([finding("set_not_null", "customers", "legacy")])[0]
    broken = next(d for d in rec.data_dependencies if d["object"] == "v_broken")
    assert broken["method"] == "text_search" and "legacy" in broken["columns"]


def test_routine_dependencies_found():
    rec = recommend([finding("set_not_null", "customers", "legacy")])[0]
    by_name = {d["object"]: d for d in rec.data_dependencies}
    assert "uses_legacy" in by_name and "legacy" in by_name["uses_legacy"]["columns"]
    assert "touch_customers" in by_name and "legacy" not in by_name["touch_customers"]["columns"]
    assert "unrelated" not in by_name
    assert "trg_cust" in by_name


def test_pipeline_dependency_found():
    rec = recommend([finding("add_index", "customers", None, columns=["legacy"])])[0]
    assert any(d["kind"] == "pipeline" and d["object"] == "nightly.load" for d in rec.data_dependencies)


def test_no_application_source_states_not_evaluated():
    rec = recommend([finding("add_index", "orders", None, columns=["amount"])])[0]
    assert rec.application_impact_evaluated is False and rec.requires_review is True
    assert rec.application_dependencies[0]["status"] == "not_evaluated"
    assert "not evaluated" in rec.application_dependencies[0]["message"].lower()


def test_missing_app_dir_is_not_evaluated(tmp_path):
    rec = recommend([finding("add_index", "orders", None, columns=["amount"])], str(tmp_path / "missing"))[0]
    assert rec.application_impact_evaluated is False and rec.requires_review


def test_app_scan_reports_file_and_line(tmp_path):
    (tmp_path / "svc.py").write_text("x = 1\nq = 'select * from customers where email = 1'\n", encoding="utf-8")
    (tmp_path / "no_table.py").write_text("email = 'x'\n", encoding="utf-8")
    rec = recommend([finding("set_not_null", "customers", "email")], str(tmp_path))[0]
    assert rec.application_impact_evaluated is True
    assert any(d["file"] == "svc.py" and d["line"] == 2 and d["kind"] == "table" for d in rec.application_dependencies)
    assert any(d["match"] == "email" and d["file"] == "svc.py" for d in rec.application_dependencies)
    assert not any(d.get("file") == "no_table.py" for d in rec.application_dependencies)


def test_app_scan_skips_vendor_binary_and_large_files(tmp_path):
    vendor = tmp_path / "node_modules"
    vendor.mkdir()
    (vendor / "lib.js").write_text("customers", encoding="utf-8")
    (tmp_path / "image.png").write_bytes(b"customers")
    (tmp_path / "data.bin2").write_bytes(b"\x00customers")
    (tmp_path / "big.txt").write_text("customers\n" * 200000, encoding="utf-8")
    rec = recommend([finding("add_index", "customers", None, columns=["legacy"])], str(tmp_path))[0]
    skipped = rec.application_scan["files_skipped"]
    assert skipped["vendor_or_build_directory"] == 1 and skipped["binary_extension"] == 1
    assert skipped["binary_content"] == 1 and skipped["over_size_limit"] == 1
    assert rec.application_dependencies[0]["status"] == "scanned_no_match"
    assert "does not rule out" in rec.application_dependencies[0]["message"]


def test_priority_explained_and_monotonic():
    high = recommend([finding("add_index", "orders", None, fid="H", severity=Severity.CRITICAL, columns=["amount"])])[0]
    low = recommend([finding("add_index", "orders", None, fid="L", severity=Severity.LOW, columns=["amount"])])[0]
    assert high.priority_score > low.priority_score and high.priority < low.priority
    assert any("severity" in r for r in high.priority_rationale)
    assert any("Confidence" in r for r in high.priority_rationale)
    assert any("Complexity" in r for r in high.priority_rationale)
    assert any("depend" in r for r in high.priority_rationale)


def test_priority_reflects_kind_confidence_and_complexity():
    base = dict(fid="A", columns=["amount"])
    confirmed = recommend([finding("add_index", "orders", None, **base)])[0].priority_score
    optional = recommend([finding("add_index", "orders", None, kind=FindingKind.OPTIONAL_IMPROVEMENT, **base)])[0].priority_score
    low_conf = recommend([finding("add_index", "orders", None, confidence=0.4, **base)])[0].priority_score
    hard = recommend([finding("add_index", "orders", None, complexity="high", **base)])[0].priority_score
    assert confirmed > optional and confirmed > low_conf and confirmed > hard


def test_many_dependencies_lower_score():
    db = model()
    db2 = model()
    db2.views += [View(f"v{i}", "SELECT id FROM orders") for i in range(6)]
    f = finding("add_index", "orders", None, columns=["amount"])
    assert recommend([f], db=db)[0].priority_score > recommend([f], db=db2)[0].priority_score


def test_requires_review_for_context_dependent_and_manual():
    rec = recommend([finding("add_index", "orders", None, kind=FindingKind.CONTEXT_DEPENDENT, columns=["amount"])])[0]
    assert rec.requires_review
    assert any("context dependent" in n for n in rec.business_logic_notes)


def test_no_review_only_when_everything_is_clean(tmp_path):
    db = Database("x", "postgres", "live", tables=[Table("lonely", columns=[Column("a", "int", True)], row_count=1)])
    (tmp_path / "x.py").write_text("hello\n", encoding="utf-8")
    f = finding("add_index", "lonely", None, columns=["a"])
    rec = build_recommendations(db, [f], generate_plan(db, [f]), str(tmp_path))[0]
    assert rec.requires_review is False and rec.application_impact_evaluated is True


def test_after_structure_excludes_manual_steps():
    db = model()
    f = finding("alter_column_type", "orders", "amount", fid="T", new_type="decimal(5,1)")
    f2 = finding("manual", "orders", None, fid="M", description="ask")
    rec = build_recommendations(db, [f, f2], generate_plan(db, [f, f2]))[0]
    assert "decimal(5,1)" in rec.before_after["after"]
    assert "Deferred" in rec.recommended_structure and "M " in rec.recommended_structure.replace("M (manual)", "M ")
    assert "MANUAL" in rec.proposed_sql


def test_irreversible_step_stated_in_rollback():
    db = model()
    db.table("orders").row_count = 0
    f = finding("alter_column_type", "orders", "amount", new_type="decimal(5,1)")
    rec = build_recommendations(db, [f], generate_plan(db, [f]))[0]
    assert "NOT reversible" in rec.rollback


def test_data_migration_describes_expand_contract():
    db = model()
    f = finding("alter_column_type", "orders", "id", new_type="bigint")
    rec = build_recommendations(db, [f], generate_plan(db, [f]))[0]
    assert "expand" in rec.data_migration and "contract" in rec.data_migration


def test_data_migration_when_none_needed():
    rec = recommend([finding("add_index", "orders", None, columns=["amount"])])[0]
    assert "does not change existing data" in rec.data_migration


def test_financial_note_on_rename():
    db = Database("x", "postgres", "live", tables=[Table("payments", columns=[Column("a", "int", True)], row_count=1)])
    f = finding("rename_column", "payments", "a", new_name="b")
    rec = build_recommendations(db, [f], generate_plan(db, [f]))[0]
    assert any("financial" in n for n in rec.business_logic_notes) and rec.requires_review


def test_business_note_never_assumes():
    rec = recommend([finding("add_index", "orders", None, columns=["amount"])])[0]
    assert "No business rule was inferred" in rec.business_logic_notes[0]


def test_root_cause_groups_cluster_across_tables():
    fs = [finding("add_primary_key", "a", None, fid="1", root_cause="Table a has no primary key.", columns=["x"]),
          finding("add_primary_key", "b", None, fid="2", root_cause="Table b has no primary key.", columns=["y"]),
          finding("add_primary_key", "c", None, fid="3", root_cause="Table c has no primary key.", columns=["z"]),
          finding("set_not_null", "a", "q", fid="4", root_cause="Column q in a allows NULL.")]
    groups = root_cause_groups(fs)
    assert len(groups) == 2 and groups[0].count == 3 and groups[0].systemic
    assert groups[0].tables == ["a", "b", "c"] and "convention" in groups[0].note
    assert groups[0].shared_fix_ops == ["add_primary_key"]
    assert not groups[1].systemic


def test_root_cause_groups_separate_categories():
    fs = [finding(None, "a", fid="1", category="security", root_cause="Same."), finding(None, "a", fid="2", category="performance", root_cause="Same.")]
    assert len(root_cause_groups(fs)) == 2


def test_findings_without_steps_handled():
    rec = recommend([finding(None, "orders", fid="X")])[0]
    assert rec.proposed_sql.startswith("-- No SQL") and "No SQL" in rec.rollback or "no rollback" in rec.rollback.lower()
