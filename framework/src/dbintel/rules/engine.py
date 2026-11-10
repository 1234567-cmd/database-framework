"""Configurable rule engine.

Rule definitions live in ``rules/catalog/*.yaml``. Python check functions only find facts and return ``Hit`` objects.
Text, severity, standards, scope and parameters come from the catalog and can be overridden by a profile.
"""
from __future__ import annotations

import hashlib
import importlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

import yaml

from ..config import Profile
from ..findings import CATEGORIES, Finding, FindingKind, Fix, Severity
from ..model import Database

CATALOG_DIR = Path(__file__).parent / "catalog"
REGISTRY_PATH = Path(__file__).parent.parent / "data" / "rule_registry.json"
_CHECKS: dict[str, Callable] = {}
REQUIRED_KEYS = {"id", "check", "title", "category", "severity", "kind", "standards", "root_cause", "business_impact",
                 "technical_impact", "solution", "complexity", "migration", "risks", "validation"}
CAPABILITIES = {"data", "security_metadata", "query_stats", "pipelines", "live", "declared_schema"}
INFERRED_SCHEMA_SOURCES = {"csv", "excel"}  # columns and types here are guessed from cell values, so absent keys prove nothing
ANALYZERS = ("schema", "performance", "security", "data_quality", "data_engineering")


def check(name: str) -> Callable:
    """Register a check function with signature ``f(db, profile, params) -> Iterable[Hit]``."""
    def deco(fn: Callable) -> Callable:
        existing = _CHECKS.get(name)
        if existing is not None and existing.__qualname__ != fn.__qualname__:
            raise ValueError(f"Duplicate check name: {name}")
        _CHECKS[name] = fn
        return fn
    return deco


@dataclass
class Hit:
    table: Optional[str] = None
    column: Optional[str] = None
    evidence: str = ""
    vars: dict[str, Any] = field(default_factory=dict)  # extra template values
    severity: Optional[str] = None
    kind: Optional[str] = None
    confidence: Optional[float] = None
    fix: Optional[Fix] = None
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class RunCoverage:
    executed: list[str] = field(default_factory=list)
    skipped: dict[str, str] = field(default_factory=dict)  # rule id to reason
    errors: dict[str, str] = field(default_factory=dict)


class _Safe(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def load_standards() -> dict[str, dict]:
    return {r["id"]: r for r in json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))}


def load_catalog(directory: Path = CATALOG_DIR) -> list[dict]:
    rules: list[dict] = []
    for f in sorted(directory.glob("*.yaml")):
        rules.extend(yaml.safe_load(f.read_text(encoding="utf-8")) or [])
    return rules


def _load_analyzers() -> None:
    for mod in ANALYZERS:
        importlib.import_module(f"dbintel.analyzers.{mod}")


def available_capabilities(db: Database) -> set[str]:
    caps: set[str] = set()
    if db.data is not None:
        caps.add("data")
    if db.security_metadata:
        caps.add("security_metadata")
    if db.query_stats:
        caps.add("query_stats")
    if db.pipelines:
        caps.add("pipelines")
    if db.source == "live":
        caps.add("live")
    if db.source not in INFERRED_SCHEMA_SOURCES:
        caps.add("declared_schema")
    return caps


class RuleEngine:
    def __init__(self, profile: Optional[Profile] = None, catalog: Optional[list[dict]] = None):
        _load_analyzers()
        self.profile = profile or Profile()
        self.catalog = catalog if catalog is not None else load_catalog()
        self.standards = load_standards()
        self.validate_catalog()

    def validate_catalog(self) -> None:
        seen: set[str] = set()
        for rule in self.catalog:
            rid = rule.get("id", "?")
            missing = REQUIRED_KEYS - set(rule)
            if missing:
                raise ValueError(f"Rule {rid} is missing {sorted(missing)}")
            if rid in seen:
                raise ValueError(f"Duplicate rule id {rid}")
            seen.add(rid)
            if rule["check"] not in _CHECKS:
                raise ValueError(f"Rule {rid} names unknown check {rule['check']}")
            if rule["category"] not in CATEGORIES:
                raise ValueError(f"Rule {rid} has unknown category {rule['category']}")
            Severity(rule["severity"])
            FindingKind(rule["kind"])
            for sid in rule["standards"]:
                if sid not in self.standards:
                    raise ValueError(f"Rule {rid} cites unknown standard {sid}")
                if self.standards[sid]["status"] == "superseded":
                    raise ValueError(f"Rule {rid} cites superseded standard {sid}")
            bad = set(rule.get("requires", [])) - CAPABILITIES
            if bad:
                raise ValueError(f"Rule {rid} requires unknown capability {sorted(bad)}")

    def _applies(self, rule: dict) -> Optional[str]:
        over = self.profile.rule_override(rule["id"])
        if not over.get("enabled", rule.get("enabled", True)):
            return "disabled by configuration"
        workloads = rule.get("workloads")
        if workloads and self.profile.workload not in workloads:
            return f"not applicable to workload {self.profile.workload}"
        tenancy = rule.get("tenancy")
        if tenancy and self.profile.tenancy not in tenancy:
            return f"not applicable to tenancy {self.profile.tenancy}"
        return None

    def run(self, db: Database) -> tuple[list[Finding], RunCoverage]:
        coverage = RunCoverage()
        findings: dict[str, Finding] = {}
        caps = available_capabilities(db)
        for rule in self.catalog:
            reason = self._applies(rule)
            missing = set(rule.get("requires", [])) - caps
            if not reason and missing:
                reason = "input not available: " + ", ".join(sorted(missing))
            if reason:
                coverage.skipped[rule["id"]] = reason
                continue
            over = self.profile.rule_override(rule["id"])
            params = {**rule.get("params", {}), **over.get("params", {})}
            try:
                hits = list(_CHECKS[rule["check"]](db, self.profile, params))
            except Exception as exc:  # one failing check must not lose the whole assessment
                coverage.errors[rule["id"]] = f"{type(exc).__name__}: {exc}"
                continue
            coverage.executed.append(rule["id"])
            for hit in hits:
                if hit.table and self.profile.is_excluded(hit.table.split(".")[-1]):
                    continue
                f = self._finding(db, rule, over, hit)
                findings[f.id] = f
        ordered = sorted(findings.values(), key=lambda f: (f.severity.rank, f.rule_id, f.table or "", f.column or ""))
        return ordered, coverage

    def _finding(self, db: Database, rule: dict, over: dict, hit: Hit) -> Finding:
        values = _Safe(table=hit.table or "(database)", column=hit.column or "(none)", database=db.name,
                       evidence=hit.evidence, **hit.vars)
        text = lambda key: str(rule[key]).strip().format_map(values)
        key = f"{db.name}|{rule['id']}|{hit.table}|{hit.column}|{sorted(hit.vars.items(), key=str)}"
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:8]
        sids = rule["standards"]
        return Finding(
            id=f"{rule['id']}-{digest}", rule_id=rule["id"], title=text("title"),
            severity=Severity(over.get("severity") or hit.severity or rule["severity"]),
            kind=FindingKind(over.get("kind") or hit.kind or rule["kind"]),
            category=rule["category"], database=db.name, table=hit.table, column=hit.column, evidence=hit.evidence,
            root_cause=text("root_cause"), business_impact=text("business_impact"),
            technical_impact=text("technical_impact"), standards=list(sids),
            standard_statements={s: self.standards[s]["statement"] for s in sids},
            recommended_solution=text("solution"), complexity=rule["complexity"],
            migration_requirements=text("migration"), risks=text("risks"), validation_strategy=text("validation"),
            confidence=hit.confidence if hit.confidence is not None else float(rule.get("confidence", 0.9)),
            provisional_standard=any(self.standards[s]["status"] == "provisional" for s in sids),
            fix=hit.fix, data=hit.data)


def iter_tables(db: Database, profile: Profile) -> Iterable:
    return (t for t in db.tables if not profile.is_excluded(t.name))
