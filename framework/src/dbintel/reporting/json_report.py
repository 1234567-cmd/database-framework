"""JSON report."""
from __future__ import annotations

import json
from typing import Any

from .content import build_report


def render_json(assessment: Any, data: dict | None = None) -> str:
    report = data if data is not None else build_report(assessment)
    return json.dumps(report, indent=2, sort_keys=False, default=str, ensure_ascii=False) + "\n"
