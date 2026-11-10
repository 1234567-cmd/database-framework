"""Saved runs on disk and the read-only queries the interface makes against them.

A run is a directory ``reports/ui_runs/<run id>`` holding the existing masked report files plus a small
``summary.json`` copied from ``report.json``. Run ids and table names never reach a file path unvalidated.
"""
from __future__ import annotations

import json
import re
import secrets
import shutil
import threading
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any, Iterable, Optional

from ..reporting.er import mermaid_attribute, mermaid_entity, mermaid_text, mermaid_type

RUN_ID_RE = re.compile(r"^\d{8}-\d{6}-[0-9a-f]{6}$")
PARTIAL_PREFIX = ".partial-"
REPORT_FILES = {"json": ("report.json", "application/json; charset=utf-8"),
                "md": ("report.md", "text/markdown; charset=utf-8"),
                "html": ("report.html", "text/html; charset=utf-8")}
SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3, "informational": 4}
KIND_RANK = {"confirmed_defect": 0, "context_dependent": 1, "optional_improvement": 2}
MAX_PAGE_SIZE = 200
ER_NODE_LIMIT = 60
ER_ALL_TABLES_LIMIT = 30
COMPARE_LIST_LIMIT = 2000
SUMMARY_FILE = "summary.json"


class StoreError(Exception):
    """A request could not be served from the saved runs; the message is safe to show."""

    def __init__(self, message: str, status: int = 404, code: str = "not_found"):
        super().__init__(message)
        self.status = status
        self.code = code


def confidence_band(value: float) -> str:
    return "high" if value >= 0.8 else "medium" if value >= 0.5 else "low"


def _csv_set(value: Optional[str]) -> set[str]:
    return {v.strip().lower() for v in (value or "").split(",") if v.strip()}


def _int_param(value: Optional[str], default: int, minimum: int, maximum: int) -> int:
    try:
        number = int(value) if value not in (None, "") else default
    except ValueError:
        return default
    return max(minimum, min(number, maximum))


def _page(items: list, params: dict[str, str], default_size: int = 50) -> dict[str, Any]:
    size = _int_param(params.get("size"), default_size, 1, MAX_PAGE_SIZE)
    total = len(items)
    pages = max(1, (total + size - 1) // size)
    page = _int_param(params.get("page"), 1, 1, pages)
    start = (page - 1) * size
    return {"items": items[start:start + size], "total": total, "page": page, "size": size, "pages": pages}


def _short(name: Optional[str]) -> str:
    return (name or "").split(".")[-1].lower()


class LoadedRun:
    """A parsed report with the indexes that make filtering, drill-down and comparison fast."""

    def __init__(self, run_id: str, directory: Path, report: dict[str, Any]):
        self.id = run_id
        self.dir = directory
        self.report = report
        self.findings: list[dict[str, Any]] = []
        self.finding_meta: dict[str, dict[str, Any]] = {}
        for kind_rows in (report.get("findings") or {}).values():
            for f in kind_rows:
                self.findings.append(f)
                self.finding_meta[f["id"]] = {
                    "sev": SEVERITY_RANK.get(f.get("severity"), 9), "kind": KIND_RANK.get(f.get("kind"), 9),
                    "band": confidence_band(float(f.get("confidence") or 0)), "table": (f.get("table") or "").lower(),
                    "text": " ".join(str(f.get(k) or "") for k in ("id", "rule_id", "title", "table", "column", "category", "evidence",
                                                                     "root_cause", "recommended_solution")).lower()}
        self.findings.sort(key=lambda f: self.default_key(f))
        self.finding_by_id = {f["id"]: f for f in self.findings}
        self.recommendations: list[dict[str, Any]] = list(report.get("recommendations") or [])
        self.rec_by_id = {r["id"]: r for r in self.recommendations}
        self.rec_by_finding: dict[str, list[dict[str, Any]]] = {}
        for rec in self.recommendations:
            for fid in rec.get("finding_ids") or []:
                self.rec_by_finding.setdefault(fid, []).append(rec)
        migration = report.get("migration") or {}
        self.steps: list[dict[str, Any]] = sorted(migration.get("steps") or [], key=lambda s: s.get("order", 0))
        self.step_by_id = {s["id"]: s for s in self.steps}
        self.steps_by_finding: dict[str, list[dict[str, Any]]] = {}
        for step in self.steps:
            for fid in step.get("finding_ids") or []:
                self.steps_by_finding.setdefault(fid, []).append(step)
        architecture = report.get("architecture") or {}
        self.tables: list[dict[str, Any]] = list(architecture.get("tables") or [])
        self.relations: list[dict[str, Any]] = list(architecture.get("relations") or [])
        self.table_by_name: dict[str, dict[str, Any]] = {}
        for table in self.tables:
            self.table_by_name[table["name"].lower()] = table
            self.table_by_name.setdefault(_short(table["name"]), table)
        self.table_findings: dict[str, list[dict[str, Any]]] = {}
        for f in self.findings:
            target = self.table_by_name.get((f.get("table") or "").lower())
            if target is not None:
                self.table_findings.setdefault(target["name"], []).append(f)

    def default_key(self, f: dict[str, Any]) -> tuple:
        meta = self.finding_meta[f["id"]]
        return meta["kind"], meta["sev"], -float(f.get("confidence") or 0), f["id"]

    def resolve_table(self, name: Optional[str]) -> Optional[dict[str, Any]]:
        if not name:
            return None
        return self.table_by_name.get(name.lower()) or self.table_by_name.get(_short(name))


class RunStore:
    def __init__(self, runs_dir: Path, cache_size: int = 3):
        self.root = Path(runs_dir)
        self.root.mkdir(parents=True, exist_ok=True)
        self.cache_size = cache_size
        self._cache: "OrderedDict[str, LoadedRun]" = OrderedDict()
        self._lock = threading.Lock()
        self._clean_partials()

    # --- ids and paths --------------------------------------------------

    def run_dir(self, run_id: str) -> Path:
        """Return the directory of a saved run, or refuse. A traversal attempt can never pass ``RUN_ID_RE``."""
        if not isinstance(run_id, str) or not RUN_ID_RE.match(run_id):
            raise StoreError("That run does not exist.", 404, "not_found")
        path = self.root / run_id
        try:
            resolved = path.resolve(strict=True)
        except OSError:
            raise StoreError("That run does not exist.", 404, "not_found") from None
        if resolved.parent != self.root.resolve() or not resolved.is_dir():
            raise StoreError("That run does not exist.", 404, "not_found")
        return resolved

    def new_run_id(self) -> str:
        return time.strftime("%Y%m%d-%H%M%S-") + secrets.token_hex(3)

    def partial_dir(self, run_id: str) -> Path:
        return self.root / f"{PARTIAL_PREFIX}{run_id}"

    def _clean_partials(self) -> None:
        for child in self.root.iterdir():
            if child.name.startswith(PARTIAL_PREFIX):
                shutil.rmtree(child, ignore_errors=True)

    # --- listing and deleting -------------------------------------------

    def list_runs(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for child in self.root.iterdir():
            if child.is_dir() and RUN_ID_RE.match(child.name):
                summary = self.read_summary(child)
                if summary is not None:
                    out.append(summary)
        out.sort(key=lambda s: s["id"], reverse=True)
        return out

    def read_summary(self, directory: Path) -> Optional[dict[str, Any]]:
        path = directory / SUMMARY_FILE
        try:
            summary = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        if not isinstance(summary, dict) or summary.get("id") != directory.name:
            return None
        return summary

    def invalidate(self, run_id: str) -> None:
        with self._lock:
            self._cache.pop(run_id, None)

    def delete(self, run_id: str) -> None:
        directory = self.run_dir(run_id)
        self.invalidate(run_id)
        shutil.rmtree(directory, ignore_errors=False)

    # --- loading --------------------------------------------------------

    def load(self, run_id: str) -> LoadedRun:
        directory = self.run_dir(run_id)
        with self._lock:
            cached = self._cache.get(run_id)
            if cached is not None:
                self._cache.move_to_end(run_id)
                return cached
            path = directory / "report.json"
            try:
                report = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                raise StoreError("This run has no readable report.json.", 404, "not_found") from None
            run = LoadedRun(run_id, directory, report)
            self._cache[run_id] = run
            while len(self._cache) > self.cache_size:
                self._cache.popitem(last=False)
            return run

    def export_path(self, run_id: str, fmt: str) -> tuple[Path, str, str]:
        if fmt not in REPORT_FILES:
            raise StoreError("Unknown export format.", 404, "not_found")
        filename, ctype = REPORT_FILES[fmt]
        directory = self.run_dir(run_id)
        path = directory / filename
        if not path.is_file():
            raise StoreError(f"This run has no {filename}.", 404, "not_found")
        return path, ctype, f"dbintel_{run_id}_{filename}"


# --- run header ----------------------------------------------------------

def run_overview(run: LoadedRun) -> dict[str, Any]:
    r = run.report
    migration = {k: v for k, v in (r.get("migration") or {}).items() if k not in ("steps", "destructive", "refused", "unaddressed_findings", "satisfied_findings")}
    migration["unaddressed_count"] = len((r.get("migration") or {}).get("unaddressed_findings") or [])
    migration["satisfied_count"] = len((r.get("migration") or {}).get("satisfied_findings") or [])
    coverage = {k: v for k, v in (r.get("coverage") or {}).items() if k.endswith("count") or k == "capabilities"}
    return {"id": run.id, "generated_at": r.get("generated_at"), "source": r.get("source"), "profile": r.get("profile"), "summary": r.get("summary"),
            "health": r.get("health"), "distribution": r.get("distribution"), "findings_total": r.get("findings_total"),
            "import_warnings": r.get("import_warnings") or [], "limitations": r.get("limitations") or [],
            "root_cause_groups_count": len(r.get("root_cause_groups") or []), "recommendations_count": len(run.recommendations),
            "migration": migration, "coverage": coverage, "table_count": len(run.tables), "timing": r.get("timing") or {},
            "lineage_edges": len((r.get("lineage") or {}).get("edges") or [])}


SECTIONS = {"roadmap": "roadmap", "lineage": "lineage", "architecture": "architecture", "coverage": "coverage",
            "limitations": None, "root_causes": "root_cause_groups", "timing": "timing"}


def run_section(run: LoadedRun, name: str) -> Any:
    if name not in SECTIONS:
        raise StoreError("Unknown section.", 404, "not_found")
    report = run.report
    if name == "limitations":
        return {"limitations": report.get("limitations") or [], "import_warnings": report.get("import_warnings") or [],
                "source": report.get("source"), "generated_at": report.get("generated_at"), "profile": report.get("profile"), "timing": report.get("timing") or {}}
    if name == "architecture":
        arch = report.get("architecture") or {}
        return {k: v for k, v in arch.items() if k != "proposed"}
    return report.get(SECTIONS[name])


# --- findings ------------------------------------------------------------

_ROW_FIELDS = ("id", "rule_id", "title", "severity", "kind", "category", "database", "table", "column", "confidence", "provisional_standard")
_SORT_KEYS = {"severity": lambda run, f: run.finding_meta[f["id"]]["sev"], "kind": lambda run, f: run.finding_meta[f["id"]]["kind"],
              "confidence": lambda run, f: float(f.get("confidence") or 0), "rule": lambda run, f: f.get("rule_id") or "",
              "table": lambda run, f: (f.get("table") or "￿").lower(), "category": lambda run, f: f.get("category") or "",
              "title": lambda run, f: (f.get("title") or "").lower(), "id": lambda run, f: f["id"]}
_FACETS = ("severity", "kind", "category", "rule", "table", "confidence")


def finding_row(f: dict[str, Any]) -> dict[str, Any]:
    return {k: f.get(k) for k in _ROW_FIELDS}


def _finding_filters(params: dict[str, str]) -> dict[str, set[str]]:
    filters = {name: _csv_set(params.get(name)) for name in _FACETS}
    return {k: v for k, v in filters.items() if v}


def _matches(run: LoadedRun, f: dict[str, Any], filters: dict[str, set[str]], skip: Optional[str] = None) -> bool:
    meta = run.finding_meta[f["id"]]
    values = {"severity": f.get("severity"), "kind": f.get("kind"), "category": f.get("category"), "rule": f.get("rule_id"),
              "table": meta["table"], "confidence": meta["band"]}
    for name, wanted in filters.items():
        if name != skip and str(values[name] or "").lower() not in wanted:
            return False
    return True


def query_findings(run: LoadedRun, params: dict[str, str]) -> dict[str, Any]:
    filters = _finding_filters(params)
    terms = [t for t in (params.get("q") or "").lower().split() if t]
    provisional = params.get("provisional") == "1"
    candidates = run.findings
    if terms:
        candidates = [f for f in candidates if all(t in run.finding_meta[f["id"]]["text"] for t in terms)]
    if provisional:
        candidates = [f for f in candidates if f.get("provisional_standard")]
    matched = [f for f in candidates if _matches(run, f, filters)]
    sort = params.get("sort") or "default"
    descending = params.get("order") == "desc"
    if sort in _SORT_KEYS:
        key = _SORT_KEYS[sort]
        matched = sorted(matched, key=lambda f: (key(run, f), run.default_key(f)), reverse=descending)
    elif descending:
        matched = list(reversed(matched))
    page = _page(matched, params)
    page["items"] = [finding_row(f) for f in page["items"]]
    facets: dict[str, dict[str, int]] = {}
    for name in _FACETS:
        counts: dict[str, int] = {}
        for f in candidates:
            if _matches(run, f, filters, skip=name):
                meta = run.finding_meta[f["id"]]
                value = {"severity": f.get("severity"), "kind": f.get("kind"), "category": f.get("category"), "rule": f.get("rule_id"),
                         "table": f.get("table") or "", "confidence": meta["band"]}[name]
                if value:
                    counts[value] = counts.get(value, 0) + 1
        facets[name] = dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))
    page["facets"] = facets
    page["applied"] = {"q": params.get("q") or "", **{k: sorted(v) for k, v in filters.items()}, "sort": sort, "order": params.get("order") or "asc"}
    page["default_view"] = not filters and not terms and not provisional and sort == "default"
    return page


def finding_detail(run: LoadedRun, finding_id: str) -> dict[str, Any]:
    finding = run.finding_by_id.get(finding_id)
    if finding is None:
        raise StoreError("That finding does not exist in this run.")
    return {"finding": finding,
            "recommendations": [{"id": r["id"], "title": r["title"], "priority": r["priority"]} for r in run.rec_by_finding.get(finding_id, [])],
            "steps": [{"id": s["id"], "title": s["title"], "order": s.get("order"), "manual": s.get("manual")} for s in run.steps_by_finding.get(finding_id, [])]}


# --- tables --------------------------------------------------------------

_TABLE_SORT = {"name": lambda t: t["name"].lower(), "columns": lambda t: t["columns"], "foreign_keys": lambda t: t["foreign_keys"],
               "referenced_by": lambda t: t["referenced_by"], "indexes": lambda t: t["indexes"], "findings": lambda t: t["findings"],
               "rows": lambda t: t["row_count"] if t["row_count"] is not None else -1}


def _severity_counts(findings: Iterable[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for f in findings:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1
    return counts


def _table_row(run: LoadedRun, t: dict[str, Any]) -> dict[str, Any]:
    findings = run.table_findings.get(t["name"], [])
    return {"name": t["name"], "columns": t["columns"], "primary_key": t["primary_key"], "foreign_keys": t["foreign_keys"],
            "referenced_by": t["referenced_by"], "indexes": t["indexes"], "row_count": t["row_count"], "financial": t.get("financial"),
            "findings": len(findings), "severity_counts": _severity_counts(findings)}


def query_tables(run: LoadedRun, params: dict[str, str]) -> dict[str, Any]:
    terms = [t for t in (params.get("q") or "").lower().split() if t]
    rows = [_table_row(run, t) for t in run.tables if all(term in t["name"].lower() for term in terms)]
    sort = params.get("sort") or "name"
    key = _TABLE_SORT.get(sort, _TABLE_SORT["name"])
    rows.sort(key=lambda t: (key(t), t["name"].lower()), reverse=params.get("order") == "desc")
    page = _page(rows, params)
    page["total_tables"] = len(run.tables)
    return page


def table_names(run: LoadedRun) -> list[str]:
    return sorted((t["name"] for t in run.tables), key=str.lower)


def table_detail(run: LoadedRun, name: str) -> dict[str, Any]:
    table = run.resolve_table(name)
    if table is None:
        raise StoreError("That table does not exist in this run.")
    short = _short(table["name"])
    fq = table["name"].lower()
    out_rel, in_rel = [], []
    for rel in run.relations:
        source = run.resolve_table(rel["from"])
        target = run.resolve_table(rel["to"])
        item = {**rel, "from_resolved": source["name"] if source else rel["from"], "to_resolved": target["name"] if target else None}
        if source is table:
            out_rel.append(item)
        if target is table:
            in_rel.append(item)
    fk_columns = {c.lower(): rel["to"] for rel in out_rel for c in rel["columns"]}
    pk_columns = {c.lower() for c in table["primary_key"]}
    column_findings: dict[str, int] = {}
    for f in run.table_findings.get(table["name"], []):
        if f.get("column"):
            column_findings[f["column"].lower()] = column_findings.get(f["column"].lower(), 0) + 1
    columns = [{**c, "pk": c["name"].lower() in pk_columns, "fk_to": fk_columns.get(c["name"].lower()), "findings": column_findings.get(c["name"].lower(), 0)}
               for c in table.get("column_list") or []]
    indexes = table.get("index_list")
    dependencies: list[dict[str, str]] = []
    for edge in (run.report.get("lineage") or {}).get("edges") or []:
        if _short(edge.get("source")) == short or edge.get("source", "").lower() == fq:
            dependencies.append({"direction": "feeds", "object": edge.get("target"), "via": edge.get("via"), "kind": edge.get("kind")})
        elif _short(edge.get("target")) == short or edge.get("target", "").lower() == fq:
            dependencies.append({"direction": "fed by", "object": edge.get("source"), "via": edge.get("via"), "kind": edge.get("kind")})
    findings = run.table_findings.get(table["name"], [])
    return {"name": table["name"], "comment": table.get("comment"), "row_count": table.get("row_count"), "rls_enabled": table.get("rls_enabled"),
            "financial": table.get("financial"), "primary_key": table["primary_key"], "primary_key_name": table.get("primary_key_name"),
            "columns": columns, "indexes": indexes, "indexes_available": indexes is not None, "checks": table.get("check_list") or [],
            "unique_keys": [i for i in indexes or [] if i.get("unique")], "relations_out": out_rel, "relations_in": in_rel,
            "dependencies": dependencies, "findings": [finding_row(f) for f in findings], "severity_counts": _severity_counts(findings)}


# --- ER views ------------------------------------------------------------

def _er_tables(run: LoadedRun, mode: str) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], dict[str, dict[str, str]], list[str]]:
    """Return tables keyed by canonical name, all relations, changed-column states and notes for the mode."""
    arch = run.report.get("architecture") or {}
    tables = {t["name"]: {"name": t["name"], "column_list": t.get("column_list") or [], "primary_key": t.get("primary_key") or []} for t in run.tables}
    relations = [{**r, "proposed": False} for r in run.relations]
    changed: dict[str, dict[str, str]] = {}
    notes: list[str] = []
    if mode == "proposed":
        proposed = arch.get("proposed") or {}
        for t in proposed.get("tables") or []:
            base = run.resolve_table(t["name"])
            if base is not None:
                tables[base["name"]] = {"name": base["name"], "column_list": t.get("column_list") or [], "primary_key": base.get("primary_key") or []}
        relations += [{**r, "proposed": True} for r in proposed.get("relations") or []]
        for short_name, cols in (proposed.get("columns_changed") or {}).items():
            base = run.resolve_table(short_name)
            if base is not None:
                changed[base["name"]] = cols
        notes += list(proposed.get("notes") or [])
    return tables, relations, changed, notes


def _er_node(run: LoadedRun, table: dict[str, Any], changed: dict[str, dict[str, str]], relations: list[dict[str, Any]], focus: Optional[str]) -> dict[str, Any]:
    name = table["name"]
    states = changed.get(name, {})
    fk_cols = {c.lower() for r in relations if run.resolve_table(r["from"]) is not None and run.resolve_table(r["from"])["name"] == name for c in r["columns"]}
    pk = {c.lower() for c in table["primary_key"]}
    columns = [{"name": c["name"], "type": c["type"], "pk": c["name"].lower() in pk, "fk": c["name"].lower() in fk_cols, "state": states.get(c["name"].lower())}
               for c in table["column_list"]]
    return {"name": name, "short": _short(name), "label": name, "columns": columns, "external": False, "focus": name == focus,
            "changed": bool(states), "findings": len(run.table_findings.get(name, []))}


def er_view(run: LoadedRun, params: dict[str, str]) -> dict[str, Any]:
    report = run.report
    arch = report.get("architecture") or {}
    proposed_available = isinstance(arch.get("proposed"), dict)
    mode = "proposed" if params.get("mode") == "proposed" else "current"
    notes: list[str] = []
    if mode == "proposed" and not proposed_available:
        mode = "current"
        notes.append("This run was saved before the proposed schema was recorded, so only the current schema can be shown.")
    diagrams = (report.get("er") or {}).get(mode) or []
    diagram_list = [{"index": i, "title": d.get("title"), "size": len(d.get("tables") or [])} for i, d in enumerate(diagrams)]
    tables, relations, changed, mode_notes = _er_tables(run, mode)
    notes += mode_notes
    edges_all: list[dict[str, Any]] = []
    for rel in relations:
        source = run.resolve_table(rel["from"])
        target = run.resolve_table(rel["to"])
        if source is None:
            continue
        edges_all.append({"source": source["name"], "target": target["name"] if target else rel["to"], "target_known": target is not None,
                          "columns": rel.get("columns") or [], "ref_columns": rel.get("ref_columns") or [], "proposed": rel.get("proposed", False), "name": rel.get("name")})
    focus_name = None
    if params.get("focus"):
        focused = run.resolve_table(params["focus"])
        if focused is None:
            raise StoreError("That table does not exist in this run.")
        focus_name = focused["name"]
    truncated = False
    selection: list[str]
    selected_diagram: Optional[int] = None
    if focus_name:
        hops = _int_param(params.get("hops"), 1, 1, 2)
        neighbours: dict[str, set[str]] = {}
        for e in edges_all:
            if e["target_known"]:
                neighbours.setdefault(e["source"], set()).add(e["target"])
                neighbours.setdefault(e["target"], set()).add(e["source"])
        ordered = [focus_name]
        frontier = [focus_name]
        for _ in range(hops):
            next_frontier: list[str] = []
            for name in frontier:
                for other in sorted(neighbours.get(name, ())):
                    if other not in ordered and other not in next_frontier:
                        next_frontier.append(other)
            ordered.extend(next_frontier)
            frontier = next_frontier
        if len(ordered) > ER_NODE_LIMIT:
            truncated = True
            ordered = ordered[:ER_NODE_LIMIT]
        selection = ordered
    else:
        diagram = params.get("diagram")
        if diagram == "all" and len(tables) <= ER_NODE_LIMIT:
            selection = list(tables)
        elif diagram not in (None, "", "all") or len(tables) > ER_ALL_TABLES_LIMIT:
            index = _int_param(diagram if diagram not in ("all",) else None, 0, 0, max(len(diagrams) - 1, 0))
            selected_diagram = index
            names = (diagrams[index].get("tables") if diagrams else []) or []
            resolved = [run.resolve_table(n) for n in names]
            selection = [t["name"] for t in resolved if t is not None][:ER_NODE_LIMIT]
            if len(names) > ER_NODE_LIMIT:
                truncated = True
        else:
            selection = list(tables)
    chosen = set(selection)
    nodes = [_er_node(run, tables[n], changed, relations, focus_name) for n in selection if n in tables]
    externals: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []
    for e in edges_all:
        if e["source"] in chosen and e["target"] in chosen:
            edges.append(e)
        elif e["source"] in chosen and focus_name is None and not e["target_known"]:
            externals.setdefault(e["target"], {"name": e["target"], "label": e["target"], "short": _short(e["target"]), "columns": [], "external": True, "focus": False, "changed": False, "findings": 0})
            edges.append(e)
        elif e["source"] in chosen and selected_diagram is not None and e["target"] not in chosen and e["target_known"]:
            externals.setdefault(e["target"], {"name": e["target"], "label": e["target"], "short": _short(e["target"]), "columns": [], "external": True, "focus": False, "changed": False, "findings": 0})
            edges.append(e)
    return {"mode": mode, "proposed_available": proposed_available, "nodes": nodes + list(externals.values()), "edges": edges, "diagrams": diagram_list,
            "selected_diagram": selected_diagram, "focus": focus_name, "total_tables": len(tables), "truncated": truncated, "notes": notes,
            "node_limit": ER_NODE_LIMIT}


def er_mermaid(run: LoadedRun, params: dict[str, str]) -> tuple[str, str]:
    mode = "proposed" if params.get("mode") == "proposed" else "current"
    diagrams = (run.report.get("er") or {}).get(mode) or []
    if params.get("focus"):
        view = er_view(run, {**params, "mode": mode})
        focus = view["focus"] or "table"
        lines = [f"%% {mermaid_text(f'{mode.title()} schema around {focus}')}", "erDiagram"]
        tokens: dict[str, str] = {}
        for node in view["nodes"]:
            token = mermaid_entity(node["name"])
            while token in tokens.values():
                token = f'{token[:-1]}_x"' if token.startswith('"') else f"{token}_x"
            tokens[node["name"]] = token
            lines.append(f"    {token} {{")
            if node["external"]:
                lines.append('        external stub "see the diagram that holds this table"')
            for col in node["columns"]:
                marks = ", ".join(m for m, on in (("PK", col["pk"]), ("FK", col["fk"])) if on)
                parts = [mermaid_type(col["type"]), mermaid_attribute(col["name"])]
                if marks:
                    parts.append(marks)
                if col.get("state"):
                    parts.append(f'"proposed: {mermaid_text(col["state"])}"')
                lines.append("        " + " ".join(parts))
            lines.append("    }")
        for edge in view["edges"]:
            if edge["source"] in tokens and edge["target"] in tokens:
                label = mermaid_text(",".join(edge["columns"])) or "fk"
                if edge["proposed"]:
                    label += " (proposed)"
                lines.append(f'    {tokens[edge["target"]]} ||--o{{ {tokens[edge["source"]]} : "{label}"')
        return "\n".join(lines) + "\n", f"er_{mode}_focus.mmd"
    if not diagrams:
        raise StoreError("This run has no ER diagrams.")
    index = _int_param(params.get("diagram"), 0, 0, len(diagrams) - 1)
    return diagrams[index].get("mermaid") or "", f"er_{mode}_{index + 1:02d}.mmd"


# --- recommendations and migration ---------------------------------------

_REC_SUMMARY = ("id", "title", "priority", "priority_score", "table", "requires_review", "application_impact_evaluated")


def query_recommendations(run: LoadedRun, params: dict[str, str]) -> dict[str, Any]:
    terms = [t for t in (params.get("q") or "").lower().split() if t]
    wanted = _csv_set(params.get("priority"))
    rows: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    for rec in run.recommendations:
        counts[rec["priority"]] = counts.get(rec["priority"], 0) + 1
        haystack = " ".join(str(rec.get(k) or "") for k in ("id", "title", "table", "weakness")).lower()
        if (not terms or all(t in haystack for t in terms)) and (not wanted or rec["priority"].lower() in wanted):
            rows.append(rec)
    rows.sort(key=lambda r: (r["priority"], -float(r.get("priority_score") or 0), r["id"]))
    page = _page(rows, params)
    page["items"] = [{**{k: r.get(k) for k in _REC_SUMMARY}, "findings": len(r.get("finding_ids") or [])} for r in page["items"]]
    page["priorities"] = dict(sorted(counts.items()))
    return page


def recommendation_detail(run: LoadedRun, rec_id: str) -> dict[str, Any]:
    rec = run.rec_by_id.get(rec_id)
    if rec is None:
        raise StoreError("That recommendation does not exist in this run.")
    findings = [finding_row(run.finding_by_id[f]) for f in rec.get("finding_ids") or [] if f in run.finding_by_id]
    steps = [{"id": s["id"], "title": s["title"], "order": s.get("order"), "manual": s.get("manual")} for s in run.steps if rec["id"] in {r["id"] for fid in s.get("finding_ids") or [] for r in run.rec_by_finding.get(fid, [])}]
    return {"recommendation": rec, "findings": findings, "steps": steps}


_STEP_FLAGS = {"destructive": lambda s: bool(s.get("destructive")), "irreversible": lambda s: not s.get("reversible", True) and not s.get("manual"),
               "refused": lambda s: bool(s.get("refused_reason")), "data_repair": lambda s: bool(s.get("requires_data_repair")),
               "manual": lambda s: bool(s.get("manual")), "breaking": lambda s: bool(s.get("breaking"))}
_STEP_ROW = ("id", "order", "title", "op", "table", "column", "manual", "destructive", "reversible", "data_loss_risk", "lock_risk",
             "requires_backup", "requires_data_repair", "refused_reason", "breaking", "phase_label")


def query_steps(run: LoadedRun, params: dict[str, str]) -> dict[str, Any]:
    terms = [t for t in (params.get("q") or "").lower().split() if t]
    table_filter = (params.get("table") or "").lower().strip()
    flags = [name for name in _csv_set(params.get("flags")) if name in _STEP_FLAGS]
    matched: list[dict[str, Any]] = []
    for step in run.steps:
        haystack = " ".join(str(step.get(k) or "") for k in ("id", "title", "op", "table", "column", "manual_description")).lower()
        if (not terms or all(t in haystack for t in terms)) and (not table_filter or table_filter in str(step.get("table") or "").lower()) \
                and all(_STEP_FLAGS[f](step) for f in flags):
            matched.append(step)
    counts = {name: sum(1 for s in run.steps if rule(s)) for name, rule in _STEP_FLAGS.items()}
    page = _page(matched, params)
    page["items"] = [{k: s.get(k) for k in _STEP_ROW} for s in page["items"]]
    page["flag_counts"] = counts
    page["total_steps"] = len(run.steps)
    return page


def step_detail(run: LoadedRun, step_id: str) -> dict[str, Any]:
    step = run.step_by_id.get(step_id)
    if step is None:
        raise StoreError("That migration step does not exist in this run.")
    rec_ids = {r["id"] for fid in step.get("finding_ids") or [] for r in run.rec_by_finding.get(fid, [])}
    return {"step": step, "findings": [finding_row(run.finding_by_id[f]) for f in step.get("finding_ids") or [] if f in run.finding_by_id],
            "recommendations": [{"id": r["id"], "title": r["title"], "priority": r["priority"]} for r in run.recommendations if r["id"] in rec_ids]}


# --- comparison ----------------------------------------------------------

def _minimal(f: dict[str, Any]) -> dict[str, Any]:
    return {"id": f["id"], "severity": f.get("severity"), "kind": f.get("kind"), "title": f.get("title"), "table": f.get("table"), "column": f.get("column"), "rule_id": f.get("rule_id")}


def compare_runs(a: LoadedRun, b: LoadedRun) -> dict[str, Any]:
    a_ids, b_ids = set(a.finding_by_id), set(b.finding_by_id)
    new = [b.finding_by_id[i] for i in b_ids - a_ids]
    resolved = [a.finding_by_id[i] for i in a_ids - b_ids]
    changed = []
    for fid in a_ids & b_ids:
        before, after = a.finding_by_id[fid], b.finding_by_id[fid]
        if before.get("severity") != after.get("severity") or before.get("kind") != after.get("kind"):
            changed.append({"id": fid, "title": after.get("title"), "table": after.get("table"), "before": {"severity": before.get("severity"), "kind": before.get("kind")},
                            "after": {"severity": after.get("severity"), "kind": after.get("kind")}})
    new.sort(key=lambda f: b.default_key(f))
    resolved.sort(key=lambda f: a.default_key(f))
    changed.sort(key=lambda c: c["id"])

    def categories(run: LoadedRun) -> dict[str, dict[str, Any]]:
        return {c["category"]: c for c in (run.report.get("health") or {}).get("categories") or []}

    a_cat, b_cat = categories(a), categories(b)
    category_changes = []
    for name in sorted(set(a_cat) | set(b_cat)):
        before, after = a_cat.get(name, {}).get("score"), b_cat.get(name, {}).get("score")
        delta = None if before is None or after is None else round(after - before, 1)
        category_changes.append({"category": name, "before": before, "after": after, "delta": delta,
                                 "before_confidence": a_cat.get(name, {}).get("confidence"), "after_confidence": b_cat.get(name, {}).get("confidence")})

    def header(run: LoadedRun) -> dict[str, Any]:
        h = run.report.get("health") or {}
        return {"id": run.id, "name": (run.report.get("source") or {}).get("name"), "generated_at": run.report.get("generated_at"), "overall": h.get("overall"),
                "grade": h.get("grade"), "confidence": h.get("confidence"), "findings_total": run.report.get("findings_total")}

    ah, bh = header(a), header(b)
    overall_delta = None if ah["overall"] is None or bh["overall"] is None else round(bh["overall"] - ah["overall"], 1)
    return {"a": ah, "b": bh, "overall_delta": overall_delta, "category_changes": category_changes,
            "new": [_minimal(f) for f in new[:COMPARE_LIST_LIMIT]], "resolved": [_minimal(f) for f in resolved[:COMPARE_LIST_LIMIT]],
            "changed": changed[:COMPARE_LIST_LIMIT], "new_count": len(new), "resolved_count": len(resolved), "changed_count": len(changed),
            "unchanged_count": len(a_ids & b_ids) - len(changed), "list_limit": COMPARE_LIST_LIMIT}


def build_summary(run_id: str, report: dict[str, Any]) -> dict[str, Any]:
    source = report.get("source") or {}
    health = report.get("health") or {}
    summary = report.get("summary") or {}
    return {"id": run_id, "name": source.get("name"), "dialect": source.get("dialect"), "source_label": source.get("label"), "source_kind": source.get("kind"),
            "generated_at": report.get("generated_at"), "overall": health.get("overall"), "grade": health.get("grade"), "confidence": health.get("confidence"),
            "capped": health.get("capped"), "findings_total": report.get("findings_total"), "critical": summary.get("critical"), "high": summary.get("high"),
            "confirmed_defects": summary.get("confirmed_defects"), "tables": summary.get("tables"), "plan_hash": (report.get("migration") or {}).get("plan_hash")}
