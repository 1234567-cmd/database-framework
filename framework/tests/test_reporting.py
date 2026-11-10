"""Report content, accuracy against the assessment, escaping, masking, offline HTML and ER diagrams."""
import json
import re
from collections import Counter
from pathlib import Path

import pytest
import yaml

from dbintel.findings import CATEGORIES
from dbintel.model import Column, Database, ForeignKey, Table
from dbintel.pipeline import assess
from dbintel.reporting import FORMATS, build_report, render_html, render_json, render_markdown, write_reports
from dbintel.reporting.er import ErDiagram, MAX_TABLES_PER_DIAGRAM, current_diagrams, mermaid_attribute, mermaid_entity, proposed_database, proposed_diagrams, render_mermaid, render_svg, split_tables

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


@pytest.fixture(scope="module")
def erp():
    return assess(SAMPLES / "erp_mysql.sql", profile=str(SAMPLES / "profiles" / "erp.yaml"), query_log=str(SAMPLES / "query_log.json"), pipelines=str(SAMPLES / "pipelines.yaml"), name="erp_demo")


@pytest.fixture(scope="module")
def saas():
    return assess(SAMPLES / "saas_postgres.sql", profile=str(SAMPLES / "profiles" / "saas.yaml"), name="saas_demo")


@pytest.fixture(scope="module")
def reports(erp, tmp_path_factory):
    out = tmp_path_factory.mktemp("rep")
    written = write_reports(erp, out)
    return {"out": out, "written": written, "json": json.loads(written["json"].read_text(encoding="utf-8")), "md": written["md"].read_text(encoding="utf-8"), "html": written["html"].read_text(encoding="utf-8")}


# --- accuracy: every count is compared with the assessment --------------------

def test_json_counts_match_assessment(erp, reports):
    d = reports["json"]
    assert d["findings_total"] == len(erp.findings) and sum(len(v) for v in d["findings"].values()) == len(erp.findings)
    sev, kind, cat = Counter(f.severity.value for f in erp.findings), Counter(f.kind.value for f in erp.findings), Counter(f.category for f in erp.findings)
    assert d["distribution"]["severity"] == {s: sev.get(s, 0) for s in d["distribution"]["severity"]}
    assert d["distribution"]["kind"] == {k: kind.get(k, 0) for k in d["distribution"]["kind"]}
    assert d["distribution"]["category"] == {c: cat.get(c, 0) for c in CATEGORIES}
    assert len(d["recommendations"]) == len(erp.recommendations) and len(d["root_cause_groups"]) == len(erp.root_cause_groups)
    c = d["coverage"]
    assert c["rules_executed_count"] == len(erp.coverage.executed) and c["skipped_count"] == len(erp.coverage.skipped) and c["errors_count"] == len(erp.coverage.errors)
    assert len(c["rules_executed"]) == len(erp.coverage.executed) and len(c["skipped"]) == len(erp.coverage.skipped)
    m = d["migration"]
    assert m["total_steps"] == len(erp.plan.steps) and m["executable_steps"] == len(erp.plan.executable_steps) and m["manual_steps"] == len(erp.plan.manual_steps)
    assert m["destructive_steps"] == sum(1 for s in erp.plan.steps if s.destructive) and len(m["destructive"]) == m["destructive_steps"]
    assert m["refused_steps"] == sum(1 for s in erp.plan.steps if s.refused_reason) and len(m["refused"]) == m["refused_steps"]
    assert m["plan_hash"] == erp.plan_hash and d["summary"]["plan_hash"] == erp.plan_hash
    assert len(d["lineage"]["edges"]) == len(erp.lineage["edges"])
    assert d["summary"]["tables"] == len(erp.db.tables) and d["architecture"]["tables"].__len__() == len(erp.db.tables)
    assert len(d["architecture"]["relations"]) == sum(len(t.foreign_keys) for t in erp.db.tables)


def test_health_section_matches(erp, reports):
    h = reports["json"]["health"]
    assert h["overall"] == erp.health.overall and h["grade"] == erp.health.grade and h["confidence"] == erp.health.confidence and h["capped"] == erp.health.capped
    assert len(h["categories"]) == 10 and {c["category"] for c in h["categories"]} == set(CATEGORIES)
    for cat, source in zip(h["categories"], erp.health.categories):
        assert cat["score"] == source.score and cat["grade"] == source.grade and cat["confidence"] == source.confidence and len(cat["deductions"]) == len(source.deductions)
    assert h["method"] and h["weights"]


def test_markdown_counts_match(erp, reports):
    md = reports["md"]
    kinds = Counter(f.kind.value for f in erp.findings)
    assert f"## Findings ({len(erp.findings)})" in md
    assert f"### Confirmed defects ({kinds['confirmed_defect']})" in md and f"### Optional improvements ({kinds['optional_improvement']})" in md and f"### Context-dependent items ({kinds['context_dependent']})" in md
    assert f"## Recommendations ({len(erp.recommendations)})" in md and f"## Root cause groups ({len(erp.root_cause_groups)})" in md
    assert f"{len(erp.coverage.executed)} rules executed, {len(erp.coverage.skipped)} skipped, {len(erp.coverage.errors)} errors" in md
    plan = erp.plan
    assert f"{len(plan.steps)} step(s): {len(plan.executable_steps)} executable, {len(plan.manual_steps)} manual, {sum(1 for s in plan.steps if s.destructive)} destructive" in md
    for f in erp.findings:
        assert f.id in md
    for r in erp.recommendations:
        assert r.id in md
    assert md.count("- **Provisional standard:**") == len(erp.findings), "every finding lists all its fields once"


def test_html_counts_match(erp, reports):
    html = reports["html"]
    assert f'<h2>Findings ({len(erp.findings)})</h2>' in html and f'Recommendations ({len(erp.recommendations)})' in html
    assert html.count('id="f-') == len(erp.findings), "each finding is rendered exactly once"
    for r in erp.recommendations:
        assert f'id="r-{r.id}"' in html
    for name in CATEGORIES:
        assert name in html
    assert f'{len(erp.coverage.executed)} rules executed' in html and erp.plan_hash in html
    assert html.count("Provisional standard") == len(erp.findings)


def test_every_finding_field_is_rendered(erp, reports):
    f = next(x for x in erp.findings if x.rule_id == "SCH-020")
    for value in (f.id, f.database, f.table, f.column, f.evidence, f.root_cause, f.business_impact, f.technical_impact, f.recommended_solution, f.complexity, f.migration_requirements, f.risks, f.validation_strategy):
        assert value.replace("<", "&lt;") in reports["md"].replace("`", ""), value
    assert "Provisional standard" in reports["html"]
    item = next(x for x in reports["json"]["findings"]["confirmed_defect"] if x["id"] == f.id)
    assert {"id", "database", "table", "column", "evidence", "root_cause", "business_impact", "technical_impact", "standards", "standard_statements", "recommended_solution", "complexity", "migration_requirements", "risks", "validation_strategy", "confidence", "kind", "provisional_standard"} <= set(item)


def test_findings_are_partitioned_by_kind_without_overlap(reports):
    groups = reports["json"]["findings"]
    ids = [f["id"] for items in groups.values() for f in items]
    assert len(ids) == len(set(ids))
    assert all(f["kind"] == "confirmed_defect" for f in groups["confirmed_defect"])


def test_recommendations_have_required_sections(reports, erp):
    r = reports["json"]["recommendations"][0]
    for key in ("existing_structure", "before_after", "proposed_sql", "application_dependencies", "data_dependencies", "data_migration", "rollback", "validation_tests", "priority", "priority_rationale"):
        assert key in r
    assert reports["md"].count("**Application dependencies:**") == len(erp.recommendations)
    assert reports["html"].count("<h4>Validation tests</h4>") == len(erp.recommendations)


def test_roadmap_places_each_recommendation_once_and_respects_dependencies(reports, erp):
    roadmap = reports["json"]["roadmap"]
    placed = [i["recommendation"] for p in roadmap["phases"] for i in p["items"]]
    assert sorted(placed) == sorted(r.id for r in erp.recommendations) and len(placed) == roadmap["recommendation_count"]
    phase_of = {i["recommendation"]: p["phase"] for p in roadmap["phases"] for i in p["items"]}
    for p in roadmap["phases"]:
        for item in p["items"]:
            for need in item["depends_on"]:
                assert phase_of[need] <= p["phase"], "a dependency cannot be in a later phase"
    assert roadmap["prerequisites"]


def test_architecture_domains_cover_all_tables(reports, saas):
    d = build_report(saas)
    assert {n for domain in d["architecture"]["domains"] for n in domain["tables"]} == {t.fqname for t in saas.db.tables}
    assert any(domain["size"] >= 2 and "domain" in domain["name"] for domain in d["architecture"]["domains"])


def test_import_warnings_and_limitations_are_reported(tmp_path):
    a = assess(SAMPLES / "clean_postgres.sql", profile=str(SAMPLES / "profiles" / "clean.yaml"))
    a.db.import_warnings.append("sample warning for test")
    d = build_report(a)
    assert "sample warning for test" in d["import_warnings"] and d["limitations"]
    assert "sample warning for test" in render_markdown(a) and "sample warning for test" in render_html(a)


def test_write_reports_writes_all_formats_and_migrations(reports, erp):
    out, written = reports["out"], reports["written"]
    assert set(written) >= {"html", "md", "json", "er", "migrations"}
    assert (out / "migrations" / "plan.json").is_file() and (out / "migrations" / "README.md").is_file()
    plan = json.loads((out / "migrations" / "plan.json").read_text(encoding="utf-8"))
    assert plan["plan_hash"] == erp.plan_hash
    assert list((out / "er").glob("current_*.mmd")) and list((out / "er").glob("proposed_*.mmd"))


def test_write_reports_rejects_unknown_format(erp, tmp_path):
    with pytest.raises(ValueError, match="Unknown report formats"):
        write_reports(erp, tmp_path, ["pdf"])


def test_format_list_is_html_md_json():
    assert set(FORMATS) == {"json", "md", "markdown", "html"}


# --- safety ---------------------------------------------------------------------

@pytest.mark.parametrize("key,expected_file", [("erp", "erp_mysql.expected_findings.yaml"), ("saas", "saas_postgres.expected_findings.yaml")])
def test_masking_is_preserved_in_all_formats(request, tmp_path, key, expected_file):
    assessment = request.getfixturevalue(key)
    written = write_reports(assessment, tmp_path)
    secrets = yaml.safe_load((SAMPLES / expected_file).read_text(encoding="utf-8"))["never_in_reports"]
    for fmt in ("html", "md", "json"):
        text = written[fmt].read_text(encoding="utf-8")
        for secret in secrets:
            assert secret not in text, f"{secret} leaked into {fmt}"
    for sql in (tmp_path / "migrations").iterdir():
        for secret in secrets:
            assert secret not in sql.read_text(encoding="utf-8"), f"{secret} leaked into {sql.name}"


def test_card_numbers_in_view_text_are_scrubbed():
    from dbintel.reporting.content import scrub
    data = scrub({"a": "SELECT 4111 1111 1111 1111", "b": ["card 5555-5555-5555-4444", "order 12345678901234567890 or 1234567890123"]})
    assert "4111" not in data["a"] and "5555" not in data["b"][0] and data["a"].endswith("***11")
    assert "12345678901234567890" in data["b"][1] and "1234567890123" in data["b"][1], "numbers that fail the Luhn check are kept"


def test_html_is_self_contained(reports):
    html = reports["html"]
    low = html.lower()
    assert "<script" not in low
    for pattern in ('src="http', "src='http", 'href="http', "href='http", "@import", "url(http", "cdn.", "<link "):
        assert pattern not in low, pattern
    assert "<style>" in low and "<svg" in low


def test_html_escapes_untrusted_names_and_keeps_mermaid_source():
    evil = '<img src=x onerror=alert(1)>'
    db = Database(f"bad{evil}", dialect="postgres", source="metadata", tables=[
        Table(f"t{evil}", columns=[Column(f"c{evil}", "int")], comment="<b>hi</b>"),
        Table("parent", columns=[Column("id", "int")], primary_key=["id"]),
    ])
    db.tables[0].foreign_keys.append(ForeignKey("fk", [f"c{evil}"], "parent", ["id"]))
    a = assess(db)
    html = render_html(a)
    assert evil not in html and "<script" not in html.lower()
    assert "onerror" in html and "&lt;img" in html, "the text stays but is escaped"
    no_fences = re.sub(r"```.*?```", "", render_markdown(a), flags=re.S)
    md = re.sub(r"`[^`]*`", "", no_fences)
    assert "<img" not in md, "outside code spans, HTML in values is neutralized"
    assert "Mermaid source" in html and "erDiagram" in html


# --- ER diagrams -----------------------------------------------------------------

def test_mermaid_names_are_escaped():
    assert mermaid_entity("orders") == "orders"
    assert mermaid_entity("order items") == '"order items"'
    assert mermaid_entity('a"b') == '"a_b"'
    assert mermaid_entity("one") == '"one"', "mermaid keywords are quoted"
    assert mermaid_attribute("first name") == "first_name" and mermaid_attribute("1st").startswith("c_")


def test_mermaid_diagram_is_valid_shape():
    db = Database("d", tables=[Table("orders", columns=[Column("id", "int"), Column("first name", "varchar(20)")], primary_key=["id"]),
                               Table('line "items"', columns=[Column("id", "int"), Column("order_id", "int")], primary_key=["id"], foreign_keys=[ForeignKey("fk", ["order_id"], "orders", ["id"])])])
    text = current_diagrams(db)[0].mermaid
    assert text.startswith("%% Current schema") and "\nerDiagram\n" in text
    assert "varchar_20 first_name" in text and 'first name' in text
    assert 'orders ||--o{ "line _items_" : "order_id"' in text
    assert '"line "items"' not in text


def test_mermaid_marks_keys():
    db = Database("d", tables=[Table("a", columns=[Column("id", "int")], primary_key=["id"])])
    assert "int id PK" in current_diagrams(db)[0].mermaid


def large_schema(size: int) -> Database:
    tables = [Table("hub", columns=[Column("id", "int")], primary_key=["id"])]
    for i in range(size - 1):
        tables.append(Table(f"t{i}", columns=[Column("id", "int"), Column("hub_id", "int")], primary_key=["id"], foreign_keys=[ForeignKey(None, ["hub_id"], "hub", ["id"])]))
    return Database("big", tables=tables)


def test_large_schema_is_split_with_a_limit_and_keeps_every_table():
    db = large_schema(50)
    diagrams = current_diagrams(db)
    assert len(diagrams) > 1
    assert all(len(d.tables) <= MAX_TABLES_PER_DIAGRAM for d in diagrams)
    assert sorted(t.name for d in diagrams for t in d.tables) == sorted(t.name for t in db.tables)
    assert any("external" in d.mermaid or d.external for d in diagrams), "cross-diagram references appear as stubs"
    assert all("of" in d.title for d in diagrams)


def test_isolated_tables_are_batched():
    db = Database("d", tables=[Table(f"s{i}", columns=[Column("id", "int")]) for i in range(45)])
    parts = split_tables(db.tables, 20)
    assert len(parts) == 3 and all(len(p) <= 20 for p in parts)


def test_proposed_diagram_reflects_plan_steps(saas):
    tables, keys, changed, notes = proposed_database(saas.db, saas.findings, saas.plan)
    tasks = next(t for t in tables if t.name == "tasks")
    assert tasks.has_column("tenant_id"), "the proposed schema adds tenant_id from an executable step"
    assert "tenant_id" in changed["tasks"] and changed["tasks"]["tenant_id"] == "added"
    assert notes, "manual and refused steps are noted"
    text = "\n".join(d.mermaid for d in proposed_diagrams(saas.db, saas.findings, saas.plan))
    assert "proposed: added" in text
    original = "\n".join(d.mermaid for d in current_diagrams(saas.db))
    assert "proposed" not in original and "\n        bigint tenant_id" not in original.split("tasks {")[1].split("}")[0]


def test_proposed_diagram_does_not_touch_the_original_model(saas):
    before = [t.name for t in saas.db.tables], [c.name for t in saas.db.tables for c in t.columns]
    proposed_diagrams(saas.db, saas.findings, saas.plan)
    assert before == ([t.name for t in saas.db.tables], [c.name for t in saas.db.tables for c in t.columns])


def test_svg_is_inline_escaped_and_offline():
    db = Database("d", tables=[Table('x<&>"', columns=[Column('a<b', "int")], primary_key=['a<b'])])
    svg = current_diagrams(db)[0].svg
    assert svg.startswith("<svg") and "x&lt;&amp;&gt;&quot;" in svg and "<b</" not in svg and "http://" not in svg.replace("http://www.w3.org/2000/svg", "")


def test_svg_handles_external_stubs_and_empty_diagram():
    db = large_schema(50)
    stubbed = next(d for d in current_diagrams(db) if d.external)
    assert "shown in another diagram" in stubbed.svg
    assert "no tables" in ErDiagram("empty", [], []).svg
