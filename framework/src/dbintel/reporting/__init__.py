"""Reports: JSON, Markdown and self-contained HTML, plus ER diagrams and proposed migration files."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Union

from ..migrate.writer import write_migration_files
from .content import build_report
from .er import current_diagrams, proposed_diagrams
from .html_report import render_html
from .json_report import render_json
from .markdown_report import render_markdown

FORMATS = {"json": ("report.json", render_json), "md": ("report.md", render_markdown), "markdown": ("report.md", render_markdown),
           "html": ("report.html", render_html)}
DEFAULT_FORMATS = ("html", "md", "json")


def write_reports(assessment: Any, out_dir: Union[str, Path], formats: Iterable[str] = DEFAULT_FORMATS) -> dict[str, Path]:
    """Write the chosen reports, Mermaid sources and proposed migration files under ``out_dir``. Nothing is applied."""
    wanted = list(formats)
    unknown = [f for f in wanted if f not in FORMATS]
    if unknown:
        raise ValueError(f"Unknown report formats: {unknown}. Known: {sorted(FORMATS)}")
    base = Path(out_dir)
    base.mkdir(parents=True, exist_ok=True)
    data = build_report(assessment)
    out: dict[str, Path] = {}
    for fmt in wanted:
        filename, render = FORMATS[fmt]
        path = base / filename
        path.write_text(render(assessment, data), encoding="utf-8")
        out[fmt] = path
    er_dir = base / "er"
    er_dir.mkdir(exist_ok=True)
    for label, diagrams in (("current", data["er"]["current"]), ("proposed", data["er"]["proposed"])):
        for index, diagram in enumerate(diagrams, start=1):
            (er_dir / f"{label}_{index:02d}.mmd").write_text(diagram["mermaid"], encoding="utf-8")
    out["er"] = er_dir
    write_migration_files(assessment.plan, base / "migrations")
    out["migrations"] = base / "migrations"
    return out


__all__ = ["FORMATS", "build_report", "current_diagrams", "proposed_diagrams", "render_html", "render_json", "render_markdown", "write_reports"]
