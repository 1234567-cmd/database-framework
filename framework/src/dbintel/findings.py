"""Finding records produced by the rule engine."""
from __future__ import annotations

import enum
from dataclasses import asdict, dataclass, field
from typing import Any, Optional


class Severity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "informational"

    @property
    def rank(self) -> int:
        return ["critical", "high", "medium", "low", "informational"].index(self.value)


class FindingKind(str, enum.Enum):
    CONFIRMED_DEFECT = "confirmed_defect"
    OPTIONAL_IMPROVEMENT = "optional_improvement"
    CONTEXT_DEPENDENT = "context_dependent"


CATEGORIES = ("schema_quality", "data_integrity", "performance", "security", "data_quality", "scalability",
              "maintainability", "data_engineering_readiness", "governance", "reliability_recovery")


@dataclass
class Fix:
    """Machine-readable remediation. The migration generator turns ``op`` into SQL."""
    op: str
    table: Optional[str] = None
    column: Optional[str] = None
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class Finding:
    id: str
    rule_id: str
    title: str
    severity: Severity
    kind: FindingKind
    category: str
    database: str
    table: Optional[str]
    column: Optional[str]
    evidence: str
    root_cause: str
    business_impact: str
    technical_impact: str
    standards: list[str]
    standard_statements: dict[str, str]
    recommended_solution: str
    complexity: str
    migration_requirements: str
    risks: str
    validation_strategy: str
    confidence: float = 0.9
    provisional_standard: bool = False
    fix: Optional[Fix] = None
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["severity"] = self.severity.value
        d["kind"] = self.kind.value
        return d
