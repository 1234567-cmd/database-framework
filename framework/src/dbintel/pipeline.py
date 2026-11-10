"""The end-to-end assessment workflow.

Steps: 1 import or connect, 2 extract metadata, 3 analyze inputs, 4 run rules, 5 classify and score, 6 explain root
causes, 7 recommend, 8 show before and after, 9 generate proposed SQL, 10 report. ``assess`` performs steps 1 to 9 and
writes nothing; step 10 is ``reporting.write_reports``. The source is only ever read.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Optional, Sequence, Union

from .config import Profile, load_profile
from .connectors import Connector, redact_url
from .connectors.base import ConnectorError
from .findings import Finding
from .importers import load_pipelines, load_query_log, load_source
from .importers._common import Sandbox
from .migrate.generator import MigrationPlan, generate_plan
from .migrate.safety import plan_hash
from .model import Database
from .recommend import Recommendation, RootCauseGroup, build_recommendations, root_cause_groups
from .rules.engine import RuleEngine, RunCoverage, available_capabilities, load_catalog, load_standards
from .scoring import HealthAssessment, assess_health

PathLike = Union[str, "os.PathLike[str]"]

# Stages reported through the optional ``progress`` callback of ``assess``, in the order they run.
ASSESSMENT_STAGES = ("import_and_extract", "analyze_inputs", "run_rules", "classify_and_score", "explain_root_causes",
                     "generate_proposed_sql", "recommend_before_and_after", "lineage_and_limitations")
ProgressCallback = Callable[[str, str, float], None]


@dataclass
class Assessment:
    db: Database
    findings: list[Finding]
    coverage: RunCoverage
    health: HealthAssessment
    plan: MigrationPlan
    recommendations: list[Recommendation]
    root_cause_groups: list[RootCauseGroup]
    lineage: dict[str, Any]
    timing: dict[str, float] = field(default_factory=dict)
    profile: Profile = field(default_factory=Profile)
    source_label: str = ""
    capabilities: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    @property
    def plan_hash(self) -> str:
        return plan_hash(self.plan)


class _Timer:
    def __init__(self, progress: Optional[ProgressCallback] = None) -> None:
        self.timing: dict[str, float] = {}
        self._start = time.perf_counter()
        self._last = self._start
        self._progress = progress

    def begin(self, step: str) -> None:
        if self._progress:
            self._progress(step, "start", 0.0)

    def mark(self, step: str) -> None:
        now = time.perf_counter()
        self.timing[step] = round(now - self._last, 4)
        self._last = now
        if self._progress:
            self._progress(step, "done", self.timing[step])

    def finish(self) -> dict[str, float]:
        self.timing["total"] = round(time.perf_counter() - self._start, 4)
        return self.timing


def _as_profile(profile: Union[Profile, PathLike, None]) -> Profile:
    if isinstance(profile, Profile):
        return profile
    return load_profile(profile)


def _as_list(value: Union[PathLike, Sequence[PathLike], None]) -> list[PathLike]:
    if value is None:
        return []
    if isinstance(value, (str, os.PathLike)):
        return [value]
    return list(value)


def _label(source: Any) -> str:
    if isinstance(source, Database):
        return f"model:{source.name}"
    return redact_url(os.fspath(source))


def _close_live(db: Database) -> None:
    """Close a live connection. An imported ``Sandbox`` is private and in memory, so it stays open for ``migrate test``."""
    data = db.data
    if isinstance(data, Connector) and not isinstance(data, Sandbox):
        try:
            data.close()
        except (ConnectorError, OSError):
            pass
        db.data = None


def _short(name: str) -> str:
    return name.split(".")[-1].lower()


def build_lineage(db: Database) -> dict[str, Any]:
    """Object-level data flow from views, routines, triggers and pipeline manifests. Foreign keys are not data flow."""
    known = {t.name.lower() for t in db.tables} | {v.name.lower() for v in db.views}
    edges: list[dict[str, str]] = []
    gaps: list[str] = []

    def add(source: str, target: str, via: str, kind: str) -> None:
        edge = {"source": source, "target": target, "via": via, "kind": kind,
                "source_known": str(_short(source) in known).lower(), "target_known": str(_short(target) in known).lower()}
        if edge not in edges:
            edges.append(edge)

    for view in db.views:
        if not view.references:
            gaps.append(f"View {view.fqname} has no recorded source tables.")
        for ref in view.references:
            add(ref, view.fqname, view.fqname, "materialized_view" if view.materialized else "view")
    for routine in db.routines:
        if routine.kind == "trigger" and routine.table:
            add(routine.table, routine.name, routine.name, "trigger")
        for ref in routine.references:
            if routine.kind != "trigger" or _short(ref) != _short(routine.table or ""):
                add(ref, routine.name, routine.name, f"{routine.kind}_reference")
    for job in db.pipelines:
        for step in job.steps:
            via = f"{job.name}.{step.name}"
            if not step.sources and not step.targets:
                gaps.append(f"Pipeline step {via} declares no sources or targets.")
            elif not step.targets:
                gaps.append(f"Pipeline step {via} declares no targets.")
            elif not step.sources:
                gaps.append(f"Pipeline step {via} declares no sources.")
            for source in step.sources:
                for target in step.targets:
                    add(source, target, via, "pipeline")
    nodes = sorted({e["source"] for e in edges} | {e["target"] for e in edges})
    notes = ["Lineage is at object level. Column-level lineage is not derived."]
    if not db.pipelines:
        notes.append("No pipeline manifest was supplied, so pipeline lineage is absent.")
    return {"edges": edges, "nodes": nodes, "gaps": gaps, "notes": notes}


def limitations_for(db: Database, coverage: RunCoverage, app_source_dir: Optional[str]) -> list[str]:
    """Plain statements of what this particular assessment could not see."""
    notes: list[str] = []
    if db.data is None and db.source not in ("live",):
        notes.append("No row data was available, so rules needing data were skipped.")
    if not db.security_metadata:
        notes.append("Roles and grants were not available, so privilege rules were skipped.")
    if not db.query_stats:
        notes.append("No query workload was available, so query-level performance rules were skipped.")
    if not db.pipelines:
        notes.append("No pipeline manifest was supplied, so pipeline rules were skipped.")
    if db.source != "live":
        notes.append("The source is an import, not a live server: runtime settings, recovery configuration and "
                     "real row counts may be absent or different from production.")
    if not app_source_dir:
        notes.append("No application source was supplied, so application impact was not evaluated.")
    if coverage.errors:
        notes.append(f"{len(coverage.errors)} rule(s) failed to run and are listed under coverage.")
    notes.append("Findings are heuristic. Severity and scores are guidance for review, not certification.")
    notes.append("Proposed SQL is untested against your data and must be reviewed before use.")
    return notes


def assess(source: Union[PathLike, Database], profile: Union[Profile, PathLike, None] = None, dialect: Optional[str] = None,
           name: Optional[str] = None, password_env: Optional[str] = None, query_log: Union[PathLike, Sequence[PathLike], None] = None,
           pipelines: Union[PathLike, Sequence[PathLike], None] = None, app_source_dir: Optional[PathLike] = None,
           target_dialect: Optional[str] = None, progress: Optional[ProgressCallback] = None) -> Assessment:
    """Assess ``source`` (a connection URL, a file or directory path, or a ``Database``) and return an ``Assessment``.

    Writes nothing and never changes the source. Live connections are read-only and closed before returning.
    ``progress``, if given, is called as ``progress(stage, "start" | "done", seconds)`` for each of ``ASSESSMENT_STAGES``.
    An exception it raises propagates and stops the assessment.
    """
    timer = _Timer(progress)
    active = _as_profile(profile)
    timer.begin("import_and_extract")
    if isinstance(source, Database):
        db = source
        if name:
            db.name = name
    else:
        db = load_source(source, dialect=dialect, name=name, password_env=password_env)
    label = _label(source)
    timer.mark("import_and_extract")
    try:
        timer.begin("analyze_inputs")
        for log_path in _as_list(query_log):
            load_query_log(db, log_path)
        for manifest in _as_list(pipelines):
            load_pipelines(db, manifest)
        timer.mark("analyze_inputs")
        timer.begin("run_rules")
        engine = RuleEngine(active)
        capabilities = sorted(available_capabilities(db))
        findings, coverage = engine.run(db)
        timer.mark("run_rules")
        timer.begin("classify_and_score")
        health = assess_health(findings, coverage, engine.catalog)
        timer.mark("classify_and_score")
        timer.begin("explain_root_causes")
        causes = root_cause_groups(findings)
        timer.mark("explain_root_causes")
        timer.begin("generate_proposed_sql")
        plan = generate_plan(db, findings, target_dialect, profile=active)
        timer.mark("generate_proposed_sql")
        timer.begin("recommend_before_and_after")
        app_dir = os.fspath(app_source_dir) if app_source_dir else None
        recommendations = build_recommendations(db, findings, plan, app_dir, profile=active)
        timer.mark("recommend_before_and_after")
        timer.begin("lineage_and_limitations")
        lineage = build_lineage(db)
        limitations = limitations_for(db, coverage, app_dir)
        timer.mark("lineage_and_limitations")
    finally:
        _close_live(db)
    return Assessment(db=db, findings=findings, coverage=coverage, health=health, plan=plan, recommendations=recommendations,
                      root_cause_groups=causes, lineage=lineage, timing=timer.finish(), profile=active, source_label=label,
                      capabilities=capabilities, limitations=limitations)
