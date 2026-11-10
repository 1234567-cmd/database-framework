"""Health scoring: deductions, not-assessed categories, the critical cap and confidence."""
import math

import pytest

from dbintel.findings import CATEGORIES, Finding, FindingKind, Severity
from dbintel.rules.engine import RunCoverage
from dbintel.scoring import CATEGORY_WEIGHTS, CRITICAL_DEFECT_CAP, KIND_FACTOR, SEVERITY_POINTS, assess_health, grade


CATALOG = [{"id": "R1", "category": "data_integrity"}, {"id": "R2", "category": "data_integrity"}, {"id": "R3", "category": "security"},
           {"id": "R4", "category": "performance"}, {"id": "R5", "category": "performance"}]


def finding(rule, severity=Severity.MEDIUM, kind=FindingKind.CONFIRMED_DEFECT, confidence=1.0, table="t") -> Finding:
    return Finding(id=f"{rule}-{table}", rule_id=rule, title=f"title {rule}", severity=severity, kind=kind, category=dict((r["id"], r["category"]) for r in CATALOG)[rule],
                   database="d", table=table, column=None, evidence="e", root_cause="r", business_impact="b", technical_impact="t", standards=["X"],
                   standard_statements={"X": "s"}, recommended_solution="s", complexity="low", migration_requirements="m", risks="r", validation_strategy="v", confidence=confidence)


def coverage(executed, skipped=None, errors=None) -> RunCoverage:
    return RunCoverage(executed=list(executed), skipped=dict(skipped or {}), errors=dict(errors or {}))


def category(result, name):
    return next(c for c in result.categories if c.category == name)


def test_grades():
    assert [grade(95), grade(90), grade(80), grade(75), grade(65), grade(60), grade(50), grade(40), grade(10), grade(None)] == ["A", "A", "B", "B", "C", "C", "D", "D", "F", "not assessed"]


def test_deduction_uses_worst_severity_kind_confidence_and_sqrt_count():
    items = [finding("R1", Severity.HIGH, FindingKind.CONFIRMED_DEFECT, 0.8, "a"), finding("R1", Severity.MEDIUM, FindingKind.CONFIRMED_DEFECT, 1.0, "b"),
             finding("R1", Severity.LOW, FindingKind.CONFIRMED_DEFECT, 1.0, "c"), finding("R1", Severity.LOW, FindingKind.CONFIRMED_DEFECT, 1.0, "d")]
    result = assess_health(items, coverage(["R1", "R2", "R3"]), CATALOG)
    cat = category(result, "data_integrity")
    expected_points = round(12.0 * 1.0 * 0.8 * math.sqrt(4), 2)
    assert cat.deductions[0].points == expected_points and cat.deductions[0].count == 4
    assert cat.score == round(100 - expected_points, 1) and cat.grade == grade(cat.score)
    assert cat.rules_executed == 2 and cat.confidence == 1.0


@pytest.mark.parametrize("kind,factor", [(FindingKind.CONFIRMED_DEFECT, 1.0), (FindingKind.CONTEXT_DEPENDENT, 0.5), (FindingKind.OPTIONAL_IMPROVEMENT, 0.25)])
def test_kind_factor_scales_deductions(kind, factor):
    result = assess_health([finding("R1", Severity.CRITICAL, kind)], coverage(["R1", "R3"]), CATALOG)
    assert category(result, "data_integrity").deductions[0].points == pytest.approx(SEVERITY_POINTS[Severity.CRITICAL] * factor)
    assert KIND_FACTOR[kind] == factor


def test_informational_findings_do_not_deduct():
    result = assess_health([finding("R1", Severity.INFO, FindingKind.CONFIRMED_DEFECT)], coverage(["R1", "R3"]), CATALOG)
    assert category(result, "data_integrity").deductions == [] and category(result, "data_integrity").score == 100.0


def test_category_without_any_executed_rule_is_not_assessed_and_excluded_from_overall():
    result = assess_health([finding("R3", Severity.LOW)], coverage(["R3"], {"R1": "input not available: data", "R2": "input not available: data", "R4": "not applicable to workload OLAP"}, {"R5": "boom"}), CATALOG)
    integrity = category(result, "data_integrity")
    assert integrity.score is None and integrity.grade == "not assessed" and integrity.confidence == 0.0 and integrity.rules_skipped == 2
    assert category(result, "performance").score is None
    expected = category(result, "security").score
    assert result.overall == expected, "only assessed categories count toward overall"


def test_no_rules_at_all_gives_not_assessed_overall():
    result = assess_health([], coverage([]), CATALOG)
    assert result.overall is None and result.grade == "not assessed" and result.confidence == 0.0 and all(c.score is None for c in result.categories)


def test_confirmed_critical_caps_overall():
    result = assess_health([finding("R3", Severity.CRITICAL, FindingKind.CONFIRMED_DEFECT, 0.1)], coverage(["R1", "R3", "R4"]), CATALOG)
    assert result.capped and result.overall == CRITICAL_DEFECT_CAP and result.grade == "F"[:0] + grade(CRITICAL_DEFECT_CAP)
    assert category(result, "security").score > CRITICAL_DEFECT_CAP, "the category score itself is not capped"


def test_context_dependent_critical_does_not_cap():
    result = assess_health([finding("R3", Severity.CRITICAL, FindingKind.CONTEXT_DEPENDENT)], coverage(["R1", "R3", "R4"]), CATALOG)
    assert not result.capped and result.overall > CRITICAL_DEFECT_CAP


def test_cap_applies_only_if_score_would_exceed_it():
    bad = [finding("R3", Severity.CRITICAL, FindingKind.CONFIRMED_DEFECT, 1.0, f"t{i}") for i in range(30)]
    bad += [finding("R1", Severity.CRITICAL, FindingKind.CONFIRMED_DEFECT, 1.0, f"t{i}") for i in range(30)]
    bad += [finding("R4", Severity.CRITICAL, FindingKind.CONFIRMED_DEFECT, 1.0, f"t{i}") for i in range(30)]
    result = assess_health(bad, coverage(["R1", "R3", "R4"]), CATALOG)
    assert result.overall < CRITICAL_DEFECT_CAP and not result.capped and category(result, "security").score == 0.0


def test_confidence_reflects_skipped_input_rules_only():
    missing_input = assess_health([], coverage(["R1", "R3", "R4"], {"R2": "input not available: data", "R5": "input not available: query_stats"}), CATALOG)
    assert category(missing_input, "data_integrity").confidence == 0.5
    disabled = assess_health([], coverage(["R1", "R3", "R4"], {"R2": "disabled by configuration"}), CATALOG)
    assert category(disabled, "data_integrity").confidence == 1.0, "a disabled rule does not lower confidence"


def test_errors_count_against_confidence_and_are_listed():
    result = assess_health([], coverage(["R1", "R3"], errors={"R2": "boom"}), CATALOG)
    cat = category(result, "data_integrity")
    assert cat.confidence == 0.5 and cat.rules_skipped == 1 and "R2: check failed" in cat.skipped_reasons


def test_overall_confidence_is_weighted_over_all_categories():
    result = assess_health([], coverage(["R1", "R2", "R3", "R4", "R5"]), CATALOG)
    total = sum(CATEGORY_WEIGHTS.values())
    expected = round(sum(CATEGORY_WEIGHTS[c] * 1.0 for c in ("data_integrity", "security", "performance")) / total, 2)
    assert result.confidence == expected, "categories never run contribute no confidence"


def test_every_category_is_scored():
    result = assess_health([], coverage([]), CATALOG)
    assert [c.category for c in result.categories] == list(CATEGORIES)
    assert result.method and "framework judgment" in result.method


def test_distributions_count_findings():
    items = [finding("R1", Severity.CRITICAL), finding("R3", Severity.LOW, FindingKind.OPTIONAL_IMPROVEMENT, 1.0, "z")]
    result = assess_health(items, coverage(["R1", "R3"]), CATALOG)
    assert result.severity_distribution == {"critical": 1, "low": 1} and result.kind_distribution == {"confirmed_defect": 1, "optional_improvement": 1}


def test_score_never_negative():
    bad = [finding("R3", Severity.CRITICAL, FindingKind.CONFIRMED_DEFECT, 1.0, f"t{i}") for i in range(500)]
    assert assess_health(bad, coverage(["R3"]), CATALOG).categories[3].score == 0.0
