"""Explainable database health assessment.

Each category starts at 100 and loses points per rule. Repeats of one rule across many objects grow with the square
root of the count, so one convention gap cannot erase a score on its own. Categories with no executed rule are reported
as not assessed and are excluded, never counted as healthy.
"""
from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from typing import Optional

from .findings import CATEGORIES, Finding, FindingKind, Severity
from .rules.engine import RunCoverage

SEVERITY_POINTS = {Severity.CRITICAL: 25.0, Severity.HIGH: 12.0, Severity.MEDIUM: 5.0, Severity.LOW: 1.5, Severity.INFO: 0.0}
KIND_FACTOR = {FindingKind.CONFIRMED_DEFECT: 1.0, FindingKind.CONTEXT_DEPENDENT: 0.5, FindingKind.OPTIONAL_IMPROVEMENT: 0.25}
CATEGORY_WEIGHTS = {"schema_quality": 14, "data_integrity": 16, "performance": 10, "security": 16, "data_quality": 12,
                    "scalability": 6, "maintainability": 6, "data_engineering_readiness": 6, "governance": 6,
                    "reliability_recovery": 8}
CRITICAL_DEFECT_CAP = 59.0


@dataclass
class Deduction:
    rule_id: str
    title: str
    count: int
    points: float


@dataclass
class CategoryScore:
    category: str
    score: Optional[float]
    grade: str
    confidence: float
    rules_executed: int
    rules_skipped: int
    deductions: list[Deduction] = field(default_factory=list)
    skipped_reasons: list[str] = field(default_factory=list)


@dataclass
class HealthAssessment:
    overall: Optional[float]
    grade: str
    confidence: float
    capped: bool
    categories: list[CategoryScore]
    severity_distribution: dict[str, int]
    kind_distribution: dict[str, int]
    method: str

    def to_dict(self) -> dict:
        return asdict(self)


def grade(score: Optional[float]) -> str:
    if score is None:
        return "not assessed"
    for floor, label in ((90, "A"), (75, "B"), (60, "C"), (40, "D")):
        if score >= floor:
            return label
    return "F"


def _input_gap(reason: str) -> bool:
    return reason.startswith("input not available")


def assess_health(findings: list[Finding], coverage: RunCoverage, catalog: list[dict]) -> HealthAssessment:
    category_of = {r["id"]: r["category"] for r in catalog}
    per_rule: dict[str, list[Finding]] = defaultdict(list)
    for f in findings:
        per_rule[f.rule_id].append(f)

    results: list[CategoryScore] = []
    for cat in CATEGORIES:
        rule_ids = [r for r, c in category_of.items() if c == cat]
        executed = [r for r in rule_ids if r in coverage.executed]
        gaps = {r: coverage.skipped[r] for r in rule_ids if r in coverage.skipped and _input_gap(coverage.skipped[r])}
        errors = [r for r in rule_ids if r in coverage.errors]
        considered = len(executed) + len(gaps) + len(errors)
        deductions: list[Deduction] = []
        for rid in executed:
            group = per_rule.get(rid, [])
            if not group:
                continue
            worst = max(SEVERITY_POINTS[f.severity] * KIND_FACTOR[f.kind] * f.confidence for f in group)
            points = round(worst * math.sqrt(len(group)), 2)
            if points > 0:
                deductions.append(Deduction(rid, group[0].title, len(group), points))
        deductions.sort(key=lambda d: -d.points)
        score = round(max(0.0, 100.0 - sum(d.points for d in deductions)), 1) if executed else None
        confidence = round(len(executed) / considered, 2) if considered else 0.0
        reasons = sorted(set(gaps.values())) + [f"{r}: check failed" for r in errors]
        results.append(CategoryScore(cat, score, grade(score), confidence, len(executed), len(gaps) + len(errors), deductions, reasons))

    assessed = [c for c in results if c.score is not None]
    total_weight = sum(CATEGORY_WEIGHTS[c.category] for c in assessed)
    overall = round(sum(c.score * CATEGORY_WEIGHTS[c.category] for c in assessed) / total_weight, 1) if assessed else None
    capped = False
    if overall is not None and overall > CRITICAL_DEFECT_CAP and any(
            f.severity is Severity.CRITICAL and f.kind is FindingKind.CONFIRMED_DEFECT for f in findings):
        overall, capped = CRITICAL_DEFECT_CAP, True
    weight_all = sum(CATEGORY_WEIGHTS.values())
    confidence = round(sum(c.confidence * CATEGORY_WEIGHTS[c.category] for c in results) / weight_all, 2)
    method = ("Each category starts at 100. A rule deducts its worst finding's severity points (critical 25, high 12, "
              "medium 5, low 1.5, informational 0), multiplied by kind (defect 1, context-dependent 0.5, optional 0.25), "
              "finding confidence, and the square root of the number of findings. Overall is a weighted average of "
              f"assessed categories, capped at {CRITICAL_DEFECT_CAP:g} if a confirmed critical defect exists. Confidence is "
              "the share of applicable rules that could actually run. These weights are a framework judgment, not a "
              "published standard.")
    return HealthAssessment(overall, grade(overall), confidence, capped, results,
                            dict(Counter(f.severity.value for f in findings)), dict(Counter(f.kind.value for f in findings)), method)
