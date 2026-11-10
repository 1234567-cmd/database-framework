"""Entity-relationship diagrams: Mermaid text, and inline SVG of our own so that reports work offline."""
from __future__ import annotations

import copy
import html
import math
import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional, Sequence

from ..findings import Finding
from ..migrate._sql import apply_fix_effect
from ..migrate.generator import MigrationPlan
from ..model import Column, Database, ForeignKey, Table

MAX_TABLES_PER_DIAGRAM = 20
MAX_SVG_COLUMNS = 14
_MERMAID_KEYWORDS = {"erdiagram", "title", "acctitle", "accdescr", "direction", "style", "classdef", "class", "one", "many",
                     "zero", "only", "to", "optionally", "u", "pk", "fk", "uk", "tb", "bt", "lr", "rl"}
_PLAIN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass
class Relation:
    source: str  # table with the foreign key
    target: str  # referenced table
    columns: list[str]
    ref_columns: list[str]
    proposed: bool = False


@dataclass
class ErDiagram:
    title: str
    tables: list[Table]
    relations: list[Relation]
    external: list[str] = field(default_factory=list)  # tables shown as stubs because another diagram owns them
    changed_columns: dict[str, dict[str, str]] = field(default_factory=dict)  # table to column to "added" | "changed"
    notes: list[str] = field(default_factory=list)

    @property
    def mermaid(self) -> str:
        return render_mermaid(self)

    @property
    def svg(self) -> str:
        return render_svg(self)

    def to_dict(self) -> dict[str, Any]:
        return {"title": self.title, "tables": [t.name for t in self.tables], "external": self.external, "notes": self.notes,
                "relations": [r.__dict__ for r in self.relations], "mermaid": self.mermaid}


# --- Mermaid escaping --------------------------------------------------------

def mermaid_entity(name: str) -> str:
    """Return a safe entity token: a bare word when possible, otherwise a quoted name without unsafe characters."""
    if _PLAIN.match(name) and name.lower() not in _MERMAID_KEYWORDS:
        return name
    cleaned = re.sub(r'["\\\n\r\t<>{}|%;#]', "_", name).strip()
    return f'"{cleaned or "unnamed"}"'


def mermaid_attribute(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]", "_", name)
    if not re.match(r"^[A-Za-z_]", cleaned):
        cleaned = "c_" + cleaned
    return cleaned or "unnamed"


def mermaid_type(raw: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", raw or "unknown").strip("_")
    cleaned = re.sub(r"_+", "_", cleaned)
    if not re.match(r"^[A-Za-z_]", cleaned):
        cleaned = "t_" + cleaned
    return cleaned or "unknown"


def mermaid_text(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r'["\\<>{}|%#;]', "'", text or "")).strip()


def _key_marks(table: Table, column: Column) -> str:
    marks = []
    low = column.name.lower()
    if low in {c.lower() for c in table.primary_key}:
        marks.append("PK")
    if any(low in {c.lower() for c in fk.columns} for fk in table.foreign_keys):
        marks.append("FK")
    return ", ".join(marks)


def render_mermaid(diagram: ErDiagram) -> str:
    lines = ["erDiagram"]
    if diagram.title:
        lines.insert(0, f"%% {mermaid_text(diagram.title)}")
    for note in diagram.notes:
        lines.insert(1 if diagram.title else 0, f"%% {mermaid_text(note)}")
    aliases: dict[str, str] = {}
    used: set[str] = set()

    def entity(name: str) -> str:
        if name.lower() in aliases:
            return aliases[name.lower()]
        token = mermaid_entity(name)
        base, n = token, 2
        while token in used:
            token = (base[:-1] + f"_{n}\"") if base.startswith('"') else f"{base}_{n}"
            n += 1
        used.add(token)
        aliases[name.lower()] = token
        return token

    for table in diagram.tables:
        lines.append(f"    {entity(table.name)} {{")
        changed = diagram.changed_columns.get(table.name.lower(), {})
        for column in table.columns:
            attr = mermaid_attribute(column.name)
            comment = []
            if attr != column.name:
                comment.append(mermaid_text(column.name))
            state = changed.get(column.name.lower())
            if state:
                comment.append(f"proposed: {state}")
            parts = [mermaid_type(column.data_type), attr]
            marks = _key_marks(table, column)
            if marks:
                parts.append(marks)
            if comment:
                parts.append(f'"{mermaid_text("; ".join(comment))}"')
            lines.append("        " + " ".join(parts))
        lines.append("    }")
    for name in diagram.external:
        lines.append(f"    {entity(name)} {{")
        lines.append('        external stub "see the diagram that holds this table"')
        lines.append("    }")
    for rel in diagram.relations:
        label = mermaid_text(",".join(rel.columns)) or "fk"
        if rel.proposed:
            label += " (proposed)"
        lines.append(f'    {entity(rel.target)} ||--o{{ {entity(rel.source)} : "{label}"')
    return "\n".join(lines) + "\n"


# --- splitting ---------------------------------------------------------------

def _relations_of(tables: Iterable[Table], proposed_keys: Optional[set[tuple]] = None) -> list[Relation]:
    relations = []
    proposed_keys = proposed_keys or set()
    for table in tables:
        for fk in table.foreign_keys:
            key = (table.name.lower(), tuple(c.lower() for c in fk.columns), fk.ref_table.lower())
            relations.append(Relation(table.name, fk.ref_table, list(fk.columns), list(fk.ref_columns), key in proposed_keys))
    return relations


def components(tables: Sequence[Table]) -> list[list[Table]]:
    """Connected components of the foreign key graph, largest first. Single tables come last."""
    by_name = {t.name.lower(): t for t in tables}
    parent = {n: n for n in by_name}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for table in tables:
        for fk in table.foreign_keys:
            ref = fk.ref_table.lower()
            if ref in by_name:
                parent[find(table.name.lower())] = find(ref)
    groups: dict[str, list[Table]] = {}
    for name, table in by_name.items():
        groups.setdefault(find(name), []).append(table)
    return sorted(groups.values(), key=lambda g: (-len(g), min(t.name.lower() for t in g)))


def _degree(table: Table, tables: Sequence[Table]) -> int:
    low = table.name.lower()
    return len(table.foreign_keys) + sum(1 for t in tables for fk in t.foreign_keys if fk.ref_table.lower() == low)


def _split_component(group: list[Table], limit: int) -> list[list[Table]]:
    """Break a large component into neighbourhoods around its most connected tables."""
    if len(group) <= limit:
        return [group]
    by_name = {t.name.lower(): t for t in group}
    links: dict[str, set[str]] = {n: set() for n in by_name}
    for table in group:
        for fk in table.foreign_keys:
            ref = fk.ref_table.lower()
            if ref in by_name and ref != table.name.lower():
                links[table.name.lower()].add(ref)
                links[ref].add(table.name.lower())
    remaining = dict(by_name)
    parts: list[list[Table]] = []
    while remaining:
        seed = max(sorted(remaining), key=lambda n: _degree(remaining[n], group))
        part: list[str] = []
        queue = [seed]
        while queue and len(part) < limit:
            current = queue.pop(0)
            if current in remaining and current not in part:
                part.append(current)
                queue.extend(sorted(n for n in links[current] if n in remaining and n not in part))
        parts.append([remaining.pop(n) for n in part])
    return parts


def _domain_title(part: Sequence[Table], tables: Sequence[Table]) -> str:
    hub = max(sorted(part, key=lambda t: t.name.lower()), key=lambda t: _degree(t, tables))
    return hub.name


def split_tables(tables: Sequence[Table], limit: int = MAX_TABLES_PER_DIAGRAM) -> list[list[Table]]:
    parts: list[list[Table]] = []
    singles: list[Table] = []
    for group in components(list(tables)):
        if len(group) == 1:
            singles.append(group[0])
        else:
            parts.extend(_split_component(group, limit))
    for i in range(0, len(singles), limit):
        parts.append(singles[i:i + limit])
    return parts


def _build(tables: Sequence[Table], title: str, limit: int, proposed_keys: Optional[set[tuple]] = None,
           changed: Optional[dict[str, dict[str, str]]] = None, notes: Optional[list[str]] = None) -> list[ErDiagram]:
    parts = split_tables(tables, limit)
    if not parts:
        return [ErDiagram(title, [], [], notes=notes or [])]
    out: list[ErDiagram] = []
    for i, part in enumerate(parts, start=1):
        names = {t.name.lower() for t in part}
        relations = [r for r in _relations_of(part, proposed_keys)]
        external = sorted({r.target for r in relations if r.target.lower() not in names}, key=str.lower)
        sub = title
        if len(parts) > 1:
            label = _domain_title(part, tables) if len(part) > 1 else part[0].name
            sub = f"{title} ({i} of {len(parts)}: around {label})"
        out.append(ErDiagram(sub, list(part), relations, external, changed or {}, list(notes or [])))
    return out


def current_diagrams(db: Database, limit: int = MAX_TABLES_PER_DIAGRAM) -> list[ErDiagram]:
    return _build(db.tables, f"Current schema of {db.name}", limit)


def proposed_database(db: Database, findings: Sequence[Finding], plan: MigrationPlan) -> tuple[list[Table], set[tuple], dict[str, dict[str, str]], list[str]]:
    """Apply the effect of each executable, non-refused plan step to a copy of the tables."""
    tables = {t.fqname.lower(): copy.deepcopy(t) for t in db.tables}
    short = {t.name.lower(): k for k, t in zip(tables, db.tables)}
    by_id = {f.id: f for f in findings}
    original_columns = {t.name.lower(): {c.name.lower(): c.data_type for c in t.columns} for t in db.tables}
    original_fks = {(t.name.lower(), tuple(c.lower() for c in fk.columns), fk.ref_table.lower()) for t in db.tables for fk in t.foreign_keys}
    notes: list[str] = []
    skipped = 0
    for step in plan.steps:
        if step.manual or step.refused_reason:
            skipped += 1
            continue
        for fid in step.finding_ids:
            f = by_id.get(fid)
            if f is None or f.fix is None or f.fix.op == "manual":
                continue
            ref = (f.fix.table or f.table or "").lower()
            table = tables.get(ref) or tables.get(short.get(ref.split(".")[-1], ""))
            if table is None:
                continue
            apply_fix_effect(table, f.fix.op, f.fix.column or f.column, dict(f.fix.params or {}))
    if skipped:
        notes.append(f"{skipped} manual or refused plan step(s) are not shown as applied.")
    changed: dict[str, dict[str, str]] = {}
    proposed_keys: set[tuple] = set()
    for table in tables.values():
        before = original_columns.get(table.name.lower(), {})
        for column in table.columns:
            low = column.name.lower()
            if low not in before:
                changed.setdefault(table.name.lower(), {})[low] = "added"
            elif before[low] != column.data_type:
                changed.setdefault(table.name.lower(), {})[low] = "changed"
        for fk in table.foreign_keys:
            key = (table.name.lower(), tuple(c.lower() for c in fk.columns), fk.ref_table.lower())
            if key not in original_fks:
                proposed_keys.add(key)
    return list(tables.values()), proposed_keys, changed, notes


def proposed_diagrams(db: Database, findings: Sequence[Finding], plan: MigrationPlan, limit: int = MAX_TABLES_PER_DIAGRAM) -> list[ErDiagram]:
    tables, keys, changed, notes = proposed_database(db, findings, plan)
    return _build(tables, f"Proposed schema of {db.name}", limit, keys, changed, notes)


# --- inline SVG --------------------------------------------------------------

_ROW = 18
_HEADER = 26
_GAP_X = 80
_GAP_Y = 46
_CHAR = 6.7


def _x(text: Any) -> str:
    return html.escape(str(text), quote=True)


def _clip(text: str, chars: int) -> str:
    return text if len(text) <= chars else text[:max(chars - 1, 1)] + "…"


def _box_height(table: Optional[Table]) -> int:
    if table is None:
        return _HEADER + _ROW
    shown = min(len(table.columns), MAX_SVG_COLUMNS) + (1 if len(table.columns) > MAX_SVG_COLUMNS else 0)
    return _HEADER + max(shown, 1) * _ROW + 6


def _box_width(table: Optional[Table], name: str) -> int:
    chars = len(name) + 2
    if table is not None:
        for column in table.columns[:MAX_SVG_COLUMNS]:
            chars = max(chars, len(column.name) + len(column.data_type) + 8)
    return int(max(180, min(chars, 46) * _CHAR + 16))


def _clamp(value: int, start: int, length: int, margin: int = 10) -> int:
    return max(start + margin, min(value, start + length - margin))


def _key(mark: str) -> str:
    return f'<tspan class="er-key">{mark}</tspan> ' if mark else ""


def render_svg(diagram: ErDiagram) -> str:
    """Draw the diagram as a grid of table boxes joined by lines. Every piece of text is escaped."""
    names: list[tuple[str, Optional[Table]]] = [(t.name, t) for t in diagram.tables] + [(n, None) for n in diagram.external]
    if not names:
        return '<p class="muted">This diagram has no tables.</p>'
    columns = max(1, math.ceil(math.sqrt(len(names))))
    widths = [max(_box_width(t, n) for n, t in names[c::columns]) for c in range(columns)]
    xs = [20 + sum(widths[:c]) + _GAP_X * c for c in range(columns)]
    rows = [names[i:i + columns] for i in range(0, len(names), columns)]
    heights = [max(_box_height(t) for _, t in row) for row in rows]
    ys = [20 + sum(heights[:r]) + _GAP_Y * r for r in range(len(rows))]
    boxes: dict[str, tuple[int, int, int, int]] = {}
    body: list[str] = []
    for r, row in enumerate(rows):
        for c, (name, table) in enumerate(row):
            x, y, width, height = xs[c], ys[r], widths[c], _box_height(table)
            boxes[name.lower()] = (x, y, width, height)
            cls = "er-box er-stub" if table is None else "er-box"
            label = _clip(name, int((width - 12) / _CHAR))
            body.append(f'<g class="{cls}"><title>{_x(name)}</title>'
                        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="4" class="er-frame"/>'
                        f'<rect x="{x}" y="{y}" width="{width}" height="{_HEADER}" rx="4" class="er-head"/>'
                        f'<text x="{x + 8}" y="{y + 18}" class="er-title">{_x(label)}</text>')
            if table is None:
                body.append(f'<text x="{x + 8}" y="{y + _HEADER + 14}" class="er-col">(shown in another diagram)</text>')
            else:
                changed = diagram.changed_columns.get(table.name.lower(), {})
                for i, column in enumerate(table.columns[:MAX_SVG_COLUMNS]):
                    marks = _key_marks(table, column).replace(", ", "/")
                    text = _clip(f"{column.name}  {column.data_type}", int((width - 40) / _CHAR))
                    state = changed.get(column.name.lower())
                    cls_col = "er-col er-new" if state else "er-col"
                    tip = f"{column.name} {column.data_type}" + (f" (proposed: {state})" if state else "")
                    body.append(f'<text x="{x + 8}" y="{y + _HEADER + 14 + i * _ROW}" class="{cls_col}"><title>{_x(tip)}</title>{_key(marks)}{_x(text)}</text>')
                if len(table.columns) > MAX_SVG_COLUMNS:
                    body.append(f'<text x="{x + 8}" y="{y + _HEADER + 14 + MAX_SVG_COLUMNS * _ROW}" class="er-col er-more">+{len(table.columns) - MAX_SVG_COLUMNS} more columns</text>')
            body.append("</g>")
    lines: list[str] = []
    for index, rel in enumerate(diagram.relations):
        src, dst = boxes.get(rel.source.lower()), boxes.get(rel.target.lower())
        if src is None or dst is None:
            continue
        lines.append(_edge(rel, src, dst, index))
    width = xs[-1] + widths[-1] + 20
    height = ys[-1] + heights[-1] + 20
    return (f'<svg xmlns="http://www.w3.org/2000/svg" class="er" viewBox="0 0 {width} {height}" role="img" '
            f'aria-label="{_x(diagram.title)}" width="{width}" height="{height}">'
            f'<defs><marker id="er-one" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
            f'<path d="M0 0 L8 4 L0 8 z" class="er-arrow"/></marker></defs>'
            + "".join(lines) + "".join(body) + "</svg>")


def _edge(rel: Relation, src: tuple[int, int, int, int], dst: tuple[int, int, int, int], index: int = 0) -> str:
    """Curved connector. Each edge is shifted a little so that parallel lines and their labels do not sit on top of each other."""
    shift = (index % 5 - 2) * 11
    sx, sy, sw, sh = src
    dx, dy, dw, dh = dst
    if rel.source.lower() == rel.target.lower():
        x, y = sx + sw, sy + sh // 2
        path = f"M{x} {y} C {x + 40} {y - 30}, {x + 40} {y + 30}, {x} {y + 12}"
        tx, ty = x + 34, y
    else:
        if sx + sw < dx:
            x1, x2 = sx + sw, dx
        elif dx + dw < sx:
            x1, x2 = sx, dx + dw
        else:
            x1, x2 = sx + sw // 2, dx + dw // 2
        if x1 in (sx + sw, sx):
            y1, y2 = _clamp(sy + sh // 2 + shift, sy, sh), _clamp(dy + dh // 2 + shift, dy, dh)
            mid = (x1 + x2) // 2
            path = f"M{x1} {y1} C {mid} {y1}, {mid} {y2}, {x2} {y2}"
            tx, ty = (2 * x1 + x2) // 3, y1 - 5
        else:
            y1, y2 = (sy + sh, dy) if sy < dy else (sy, dy + dh)
            x1, x2 = _clamp(x1 + shift * 2, sx, sw), _clamp(x2 + shift * 2, dx, dw)
            mid = (y1 + y2) // 2
            path = f"M{x1} {y1} C {x1} {mid}, {x2} {mid}, {x2} {y2}"
            tx, ty = x1 + 4, (2 * y1 + y2) // 3
    cls = "er-line er-proposed" if rel.proposed else "er-line"
    label = _clip(",".join(rel.columns), 28)
    tip = f"{rel.source}({','.join(rel.columns)}) references {rel.target}({','.join(rel.ref_columns)})" + (" - proposed" if rel.proposed else "")
    return (f'<g class="{cls}"><title>{_x(tip)}</title><path d="{path}" fill="none" marker-end="url(#er-one)"/>'
            f'<text x="{tx}" y="{ty}" class="er-label">{_x(label)}</text></g>')


SVG_CSS = """
svg.er { max-width: 100%; height: auto; font: 12px ui-monospace, Consolas, monospace; }
.er-frame { fill: var(--surface); stroke: var(--line); }
.er-head { fill: var(--head); stroke: var(--line); }
.er-title { font-weight: 600; fill: var(--text); }
.er-col { fill: var(--text); }
.er-new { fill: var(--good); font-weight: 600; }
.er-more { fill: var(--muted); font-style: italic; }
.er-key { fill: var(--accent); font-weight: 600; }
.er-stub .er-frame { stroke-dasharray: 4 3; }
.er-line path { stroke: var(--muted); stroke-width: 1.2; }
.er-proposed path { stroke: var(--good); stroke-dasharray: 5 3; }
.er-arrow { fill: var(--muted); }
.er-label { fill: var(--muted); font-size: 10px; text-anchor: middle; }
"""
