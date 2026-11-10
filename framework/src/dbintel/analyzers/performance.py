"""Performance and scalability analyzer: index design, query patterns, execution plans and key capacity.

Check functions find facts only. All text, thresholds and name lists come from ``rules/catalog/20_performance.yaml``.
SQL is parsed with sqlglot. A statement that does not parse is skipped, never guessed at with regular expressions.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Iterator, Optional

import sqlglot
from sqlglot import exp

from ..model import Column, Database, QueryStat, Table
from ..rules.engine import Hit, check, iter_tables
from .schema import is_generated, is_unsigned, make_fix, manual, matches, qualified, run_query, tables_in_scope, tokens

_DIALECTS = {"postgres": "postgres", "mysql": "mysql", "sqlite": "sqlite"}
_COMPARE = (exp.EQ, exp.NEQ, exp.GT, exp.GTE, exp.LT, exp.LTE)
_RANGE = (exp.GT, exp.GTE, exp.LT, exp.LTE, exp.Between)
_ARITHMETIC = (exp.Add, exp.Sub, exp.Mul, exp.Div, exp.Mod, exp.DPipe)


# ----------------------------------------------------------------------------------------------------------------
# SQL helpers
# ----------------------------------------------------------------------------------------------------------------
@lru_cache(maxsize=4096)
def _parse(sql: str, dialect: Optional[str]) -> Optional[exp.Expression]:
    text = re.sub(r"\(\s*\.\.\.\s*\)", "(?)", sql.replace("%s", "?"))
    try:
        return sqlglot.parse_one(text, read=dialect)
    except Exception:  # noqa: BLE001 - logs contain fragments and vendor syntax that no parser fully covers
        return None


def fingerprint(sql: str) -> str:
    """Query text with literals removed, safe to put in evidence and stable across parameter values."""
    text = re.sub(r"'(?:[^']|'')*'", "?", sql)
    text = re.sub(r"\b\d+(\.\d+)?\b", "?", text)
    text = re.sub(r"\s+", " ", text).strip()
    return re.sub(r"(\?\s*,\s*)+\?", "?", text)


def _digest(sql: str) -> str:
    return hashlib.sha256(fingerprint(sql).lower().encode("utf-8")).hexdigest()[:10]


def _snippet(sql: str, limit: int = 200) -> str:
    text = fingerprint(sql)
    return text if len(text) <= limit else text[:limit] + "..."


@dataclass
class Query:
    stat: QueryStat
    tree: exp.Expression
    tables: dict[str, Table]  # lower-cased alias or name to model table
    cte_names: set[str]

    @property
    def single_table(self) -> Optional[Table]:
        distinct = {id(t): t for t in self.tables.values()}
        return next(iter(distinct.values())) if len(distinct) == 1 else None

    def resolve(self, col: exp.Column) -> tuple[Optional[Table], Optional[Column]]:
        name = col.name
        if col.table:
            t = self.tables.get(col.table.lower())
            return (t, t.column(name)) if t is not None else (None, None)
        distinct = {id(t): t for t in self.tables.values()}
        holders = [t for t in distinct.values() if t.has_column(name)]
        return (holders[0], holders[0].column(name)) if len(holders) == 1 else (None, None)


def _queries(db: Database) -> Iterator[Query]:
    dialect = _DIALECTS.get(db.dialect)
    for stat in db.query_stats:
        tree = _parse(stat.sql, dialect)
        if not isinstance(tree, (exp.Select, exp.Update, exp.Delete)):
            continue
        cte_names = {c.alias.lower() for c in tree.find_all(exp.CTE)}
        tables: dict[str, Table] = {}
        for node in tree.find_all(exp.Table):
            if node.name.lower() in cte_names:
                continue
            t = db.table(node.name, node.db or None)
            if t is not None:
                tables[(node.alias or node.name).lower()] = t
                tables.setdefault(node.name.lower(), t)
        yield Query(stat, tree, tables, cte_names)


def _leaves(node: Optional[exp.Expression]) -> Iterator[exp.Expression]:
    """Comparison leaves of a boolean expression, looking through AND, OR, NOT and parentheses."""
    if node is None:
        return
    if isinstance(node, (exp.And, exp.Or)):
        yield from _leaves(node.left)
        yield from _leaves(node.right)
    elif isinstance(node, (exp.Paren, exp.Not)):
        yield from _leaves(node.this)
    else:
        yield node


def _where_leaves(tree: exp.Expression) -> Iterator[exp.Expression]:
    for where in tree.find_all(exp.Where):
        yield from _leaves(where.this)


def _sides(leaf: exp.Expression) -> tuple[Optional[exp.Expression], Optional[exp.Expression]]:
    """Column-bearing side first, so ``5 = col`` is treated like ``col = 5``."""
    left, right = leaf.this if isinstance(leaf.this, exp.Expression) else None, leaf.args.get("expression")
    if left is not None and right is not None and not left.find(exp.Column) and right.find(exp.Column):
        return right, left
    return left, right


def _has_expression_index(t: Optional[Table], col: exp.Column) -> bool:
    if t is None:
        return False
    return any("(" in c and col.name.lower() in c.lower() for i in t.indexes for c in i.columns)


def _context(q: Query, params: dict) -> Optional[str]:
    """Filter out trivial queries, so query-pattern rules report only ones that matter."""
    if q.stat.calls < params.get("min_calls", 1) or q.stat.total_ms < params.get("min_total_ms", 0):
        return None
    return _snippet(q.stat.sql)


def _hit(q: Query, evidence: str, table: Optional[Table] = None, **kw: Any) -> Hit:
    t = table or q.single_table
    return Hit(table=t.fqname if t else None, evidence=evidence, vars={"query": _digest(q.stat.sql), **kw.pop("vars", {})},
               data={"sql": _snippet(q.stat.sql, 1000), "calls": q.stat.calls, "total_ms": q.stat.total_ms}, **kw)


def _reads_base_table(q: Query) -> bool:
    """True when the outermost FROM names a real table, not only a CTE or a subquery."""
    source = q.tree.args.get("from_") or q.tree.args.get("from")
    return isinstance(source, exp.From) and isinstance(source.this, exp.Table)         and source.this.name.lower() not in q.cte_names


def _rewrite_fix(t: Optional[Table], description: str):
    return manual(t, description)


def _large_enough(t: Optional[Table], stat: QueryStat, min_rows: int) -> bool:
    if stat.rows is not None and stat.rows >= min_rows:
        return True
    return t is not None and t.row_count is not None and t.row_count >= min_rows


# ----------------------------------------------------------------------------------------------------------------
# Index design
# ----------------------------------------------------------------------------------------------------------------
@check("perf.fk_without_index")
def fk_without_index(db, profile, params):
    if db.dialect in params["auto_index_dialects"]:
        return
    for t in tables_in_scope(db, profile, params):
        if t.row_count is not None and t.row_count < params["min_rows"]:
            continue
        for fk in t.foreign_keys:
            if fk.columns and not t.index_leading(fk.columns):
                columns = list(fk.columns)
                yield Hit(table=t.fqname, column=columns[0],
                          evidence=f"Foreign key ({', '.join(columns)}) on {t.fqname} to {fk.ref_table} has no index "
                                   f"leading with these columns.",
                          vars={"columns": ",".join(columns), "ref_table": fk.ref_table},
                          fix=make_fix("add_index", t, columns[0], columns=columns, unique=False))


def _same_kind(a, b) -> bool:
    return (a.method or "").lower() == (b.method or "").lower() and (a.where or "") == (b.where or "")


@check("perf.redundant_index")
def redundant_index(db, profile, params):
    for t in tables_in_scope(db, profile, params):
        keys = list(t.indexes)
        low = lambda cols: [c.lower() for c in cols]  # noqa: E731
        for idx in keys:
            if idx.primary or idx.unique or idx.is_constraint or not idx.name or idx.where or idx.include:
                continue
            cols = low(idx.columns)
            covering = None
            if t.primary_key and low(t.primary_key)[: len(cols)] == cols and not idx.method:
                covering = "the primary key"
            for other in keys:
                if other is idx or not _same_kind(idx, other):
                    continue
                other_cols = low(other.columns)
                if other_cols[: len(cols)] != cols:
                    continue
                if len(other_cols) == len(cols):
                    # Two identical indexes: keep the unique or constrained one, otherwise keep the first by name.
                    keep_other = other.unique or other.is_constraint or other.primary or (other.name or "") < idx.name
                    if keep_other:
                        covering = f"index {other.name}"
                        break
                else:
                    covering = f"index {other.name} ({', '.join(other.columns)})"
                    break
            if covering:
                yield Hit(table=t.fqname, vars={"index": idx.name},
                          evidence=f"Index {idx.name} on ({', '.join(idx.columns)}) in {t.fqname} is covered by {covering}.",
                          fix=make_fix("drop_index", t, name=idx.name))


@check("perf.too_many_indexes")
def too_many_indexes(db, profile, params):
    for t in tables_in_scope(db, profile, params):
        secondary = [i for i in t.indexes if not i.primary]
        if len(secondary) > params["max_indexes"]:
            yield Hit(table=t.fqname, evidence=f"{t.fqname} has {len(secondary)} secondary indexes; the limit is "
                      f"{params['max_indexes']}.", fix=manual(t, "Review each index against a named query or constraint."))


@check("perf.wide_index")
def wide_index(db, profile, params):
    for t in tables_in_scope(db, profile, params):
        for idx in t.indexes:
            if idx.primary or not idx.name:
                continue
            width = 0
            unknown = False
            for name in idx.columns:
                c = t.column(name)
                if c is None:
                    unknown = True
                    continue
                ti = c.type
                width += ti.length if ti.family in ("text", "char") and ti.length else 8
            too_many = len(idx.columns) > params["max_columns"]
            too_wide = not unknown and width > params["max_bytes"]
            if too_many or too_wide:
                yield Hit(table=t.fqname, vars={"index": idx.name},
                          evidence=f"Index {idx.name} on {t.fqname} has {len(idx.columns)} columns and an estimated key "
                                   f"width of {width} characters or bytes.",
                          fix=manual(t, f"Confirm which query needs {idx.name}, and narrow it if possible."))


@check("perf.low_selectivity_index")
def low_selectivity_index(db, profile, params):
    for t in tables_in_scope(db, profile, params):
        if t.row_count is not None and t.row_count < params["min_rows"]:
            continue
        fk_cols = {c.lower() for fk in t.foreign_keys for c in fk.columns}
        for idx in t.indexes:
            if idx.primary or idx.unique or idx.where or idx.is_constraint or not idx.name or len(idx.columns) != 1:
                continue
            column = t.column(idx.columns[0])
            if column is None or column.name.lower() in fk_cols:
                continue
            q = db.data.quote
            limit = int(min(profile.data_sample_limit, params["sample_limit"]))
            rows = run_query(db, f"SELECT s.v, COUNT(*) FROM (SELECT {q(column.name)} AS v FROM {qualified(db, t)} "
                                 f"LIMIT {limit}) s GROUP BY s.v")
            if not rows:
                continue
            total = sum(int(r[1]) for r in rows)
            distinct = len(rows)
            top_share = max(int(r[1]) for r in rows) / total if total else 0.0
            if total < params["min_rows"] or distinct > params["max_distinct"] or distinct / total > params["max_ratio"]:
                continue
            if top_share > params["max_top_share"]:
                continue  # a skewed column can make the index useful for finding the rare values
            yield Hit(table=t.fqname, column=column.name, vars={"index": idx.name},
                      evidence=f"Index {idx.name} on {t.fqname}.{column.name} has {distinct} distinct values in {total} "
                               f"sampled rows; the most common value is {top_share:.0%} of rows.",
                      fix=make_fix("drop_index", t, name=idx.name))


# ----------------------------------------------------------------------------------------------------------------
# Query patterns
# ----------------------------------------------------------------------------------------------------------------
@check("perf.missing_index_for_query")
def missing_index_for_query(db, profile, params):
    found: dict[tuple[str, tuple[str, ...]], dict] = {}
    for q in _queries(db):
        if q.stat.calls < params["min_calls"] or q.stat.mean_ms < params["min_mean_ms"]:
            continue
        per_table: dict[str, dict] = {}
        for leaf in list(_where_leaves(q.tree)) + _join_leaves(q.tree):
            if not isinstance(leaf, (exp.EQ, exp.In) + _RANGE):
                continue
            left, right = _sides(leaf)
            if not isinstance(left, exp.Column):
                continue
            if isinstance(right, exp.Expression) and right.find(exp.Column) and not _is_join_eq(leaf):
                continue
            t, column = q.resolve(left)
            if t is None or column is None or column.type.family in params["skip_families"]:
                continue
            slot = per_table.setdefault(t.fqname, {"table": t, "eq": [], "range": []})
            bucket = "eq" if isinstance(leaf, (exp.EQ, exp.In)) else "range"
            if column.name not in slot[bucket]:
                slot[bucket].append(column.name)
        for slot in per_table.values():
            t = slot["table"]
            if t.row_count is not None and t.row_count < params["min_rows"]:
                continue
            columns = (slot["eq"] + slot["range"][:1])[: params["max_columns"]]
            if not columns or t.index_leading([columns[0]]):
                continue
            key = (t.fqname, tuple(c.lower() for c in columns))
            entry = found.setdefault(key, {"table": t, "columns": columns, "calls": 0, "total": 0.0, "sql": q.stat.sql})
            entry["calls"] += q.stat.calls
            entry["total"] += q.stat.total_ms
    for entry in found.values():
        t, columns = entry["table"], entry["columns"]
        confidence = params["confidence_known_size"] if t.row_count is not None else params["confidence_unknown_size"]
        yield Hit(table=t.fqname, column=columns[0], confidence=confidence, vars={"columns": ",".join(columns)},
                  evidence=f"Queries filter or join {t.fqname} on ({', '.join(columns)}) with no index leading on "
                           f"{columns[0]}: {entry['calls']} calls, {entry['total']:.0f} ms total, for example: "
                           f"{_snippet(entry['sql'])}",
                  data={"sql": _snippet(entry["sql"], 1000), "calls": entry["calls"]},
                  fix=make_fix("add_index", t, columns[0], columns=columns, unique=False))


def _join_leaves(tree: exp.Expression) -> list[exp.Expression]:
    out: list[exp.Expression] = []
    for join in tree.find_all(exp.Join):
        out.extend(_leaves(join.args.get("on")))
    return out


def _is_join_eq(leaf: exp.Expression) -> bool:
    return isinstance(leaf, exp.EQ) and isinstance(leaf.this, exp.Column) and isinstance(leaf.args.get("expression"), exp.Column)


@check("perf.non_sargable_predicate")
def non_sargable_predicate(db, profile, params):
    for q in _queries(db):
        snippet = _context(q, params)
        if snippet is None:
            continue
        seen: set[str] = set()
        for leaf in _where_leaves(q.tree):
            reason = None
            column: Optional[exp.Column] = None
            if isinstance(leaf, (exp.Like, exp.ILike)):
                pattern = leaf.args.get("expression")
                if isinstance(pattern, exp.Literal) and pattern.is_string and pattern.this.startswith("%") \
                        and isinstance(leaf.this, exp.Column):
                    column, reason = leaf.this, "a leading wildcard"
            if reason is None and isinstance(leaf, _COMPARE + (exp.In, exp.Between, exp.Like, exp.ILike)):
                left, _right = _sides(leaf)
                if isinstance(left, (exp.Func, _ARITHMETIC)) and not isinstance(left, exp.AggFunc):
                    column = left.find(exp.Column)
                    if column is not None:
                        reason = "a function or expression wrapping the column"
            if reason is None or column is None:
                continue
            t, _ = q.resolve(column)
            if _has_expression_index(t, column) or f"{column.name}:{reason}" in seen:
                continue
            seen.add(f"{column.name}:{reason}")
            yield _hit(q, f"Predicate on {column.name} uses {reason}, which prevents ordinary index use. Query: {snippet}",
                       table=t, column=column.name,
                       fix=_rewrite_fix(t, f"Rewrite the predicate on {column.name} so the column stands alone, or add a "
                                           f"matching expression index."))


@check("perf.select_star")
def select_star(db, profile, params):
    for q in _queries(db):
        if not isinstance(q.tree, exp.Select) or not any(e.is_star for e in q.tree.expressions):
            continue
        if not _reads_base_table(q):
            continue  # selecting from a CTE or subquery only
        snippet = _context(q, params)
        if snippet is None:
            continue
        yield _hit(q, f"SELECT * returns every column. Query: {snippet}",
                   fix=_rewrite_fix(q.single_table, "Name the columns this query needs."))


@check("perf.offset_pagination")
def offset_pagination(db, profile, params):
    for q in _queries(db):
        if not isinstance(q.tree, exp.Select):
            continue
        offset = q.tree.args.get("offset")
        value = offset.expression if offset is not None else None
        if value is None:
            continue
        snippet = _context(q, params)
        if snippet is None:
            continue
        fix = _rewrite_fix(q.single_table, "Use keyset pagination on an indexed, unique ordering.")
        if isinstance(value, exp.Literal) and not value.is_string:
            amount = int(float(value.this))
            if amount >= params["min_offset"]:
                yield _hit(q, f"OFFSET {amount} scans and discards rows. Query: {snippet}", fix=fix)
        elif params["flag_parameterized"] and isinstance(value, (exp.Placeholder, exp.Parameter)):
            yield _hit(q, f"Parameterized OFFSET can become deep; the value is unknown. Query: {snippet}", fix=fix,
                       confidence=params["parameterized_confidence"], severity=params["parameterized_severity"])


def _literal_kind(node: exp.Expression) -> Optional[str]:
    if isinstance(node, exp.Neg):
        node = node.this
    if isinstance(node, exp.Literal):
        return "string" if node.is_string else "number"
    return None


def _is_numeric_text(node: exp.Expression, pattern: str) -> bool:
    return isinstance(node, exp.Literal) and bool(re.match(pattern, node.this.strip()))


@check("perf.implicit_conversion")
def implicit_conversion(db, profile, params):
    for q in _queries(db):
        snippet = _context(q, params)
        if snippet is None:
            continue
        reported: set[str] = set()
        for leaf in _where_leaves(q.tree):
            if isinstance(leaf, _COMPARE):
                left, right = _sides(leaf)
                literals = [right]
            elif isinstance(leaf, exp.In):
                left, literals = leaf.this, list(leaf.expressions)
            else:
                continue
            if not isinstance(left, exp.Column) or not literals:
                continue
            t, column = q.resolve(left)
            if t is None or column is None or column.name in reported:
                continue
            family = column.type.family
            kinds = {_literal_kind(x) for x in literals if isinstance(x, exp.Expression)}
            problem = None
            if family in ("text", "char") and "number" in kinds and "string" not in kinds:
                problem = "a text column compared with a number"
            elif family in ("int", "decimal", "float") and "string" in kinds and "number" not in kinds:
                if not all(_is_numeric_text(x, params["numeric_text_pattern"]) for x in literals):
                    problem = "a numeric column compared with non-numeric text"
            elif family in ("date", "datetime", "timestamptz") and kinds == {"number"}:
                problem = "a date column compared with a number"
            if problem is None:
                continue
            reported.add(column.name)
            yield _hit(q, f"{t.fqname}.{column.name} ({column.data_type}) is {problem}. Query: {snippet}",
                       table=t, column=column.name,
                       fix=_rewrite_fix(t, f"Compare {column.name} with a value of matching type."))


@check("perf.unbounded_result")
def unbounded_result(db, profile, params):
    for q in _queries(db):
        tree = q.tree
        if not isinstance(tree, exp.Select) or tree.args.get("limit") is not None or tree.args.get("where") is not None:
            continue
        if tree.args.get("group") is not None or tree.find(exp.AggFunc) is not None or tree.args.get("joins"):
            continue
        t = q.single_table
        if t is None or not _reads_base_table(q) or not _large_enough(t, q.stat, params["min_rows"]):
            continue
        snippet = _context(q, params)
        if snippet is None:
            continue
        yield _hit(q, f"Query reads all of {t.fqname} with no WHERE or LIMIT. Query: {snippet}",
                   fix=_rewrite_fix(t, "Add a filter or a limit, and page through results with a keyset."))


@check("perf.n_plus_one")
def n_plus_one(db, profile, params):
    groups: dict[str, list[QueryStat]] = {}
    for stat in db.query_stats:
        groups.setdefault(fingerprint(stat.sql).lower(), []).append(stat)
    examples = {fingerprint(q.stat.sql).lower(): q for q in _queries(db)}
    for key, stats in groups.items():
        q = examples.get(key)
        if q is None or not isinstance(q.tree, exp.Select):
            continue
        calls = sum(s.calls for s in stats)
        rows = [s.rows for s in stats if s.rows is not None]
        if calls < params["min_calls"]:
            continue
        if q.tree.args.get("joins") or q.tree.find(exp.AggFunc) is not None or q.tree.args.get("group") is not None:
            continue
        leaves = list(_where_leaves(q.tree))
        if len(leaves) != 1 or not isinstance(leaves[0], (exp.EQ, exp.In)):
            continue
        left, _ = _sides(leaves[0])
        if not isinstance(left, exp.Column):
            continue
        if isinstance(leaves[0], exp.In) and len(leaves[0].expressions) != 1:
            continue
        if rows and sum(rows) / calls > params["max_rows_per_call"]:
            continue
        t = q.single_table
        if t is None:
            continue
        yield _hit(q, f"The same keyed lookup ran {calls} times on {t.fqname} by {left.name}. Query: {_snippet(q.stat.sql)}",
                   table=t, column=left.name, vars={"calls": calls},
                   fix=_rewrite_fix(t, f"Fetch the rows in one join, or a batched query on {left.name}."))


@check("perf.expensive_query")
def expensive_query(db, profile, params):
    grand_total = sum(s.total_ms for s in db.query_stats)
    if grand_total <= 0:
        return
    ranked = sorted(db.query_stats, key=lambda s: s.total_ms, reverse=True)
    for stat in ranked[: params["max_hits"]]:
        share = stat.total_ms / grand_total
        if stat.total_ms < params["min_total_ms"] or share < params["min_share"]:
            continue
        yield Hit(evidence=f"Query used {stat.total_ms:.0f} ms total over {stat.calls} calls ({share:.0%} of observed time): "
                           f"{_snippet(stat.sql)}",
                  vars={"query": _digest(stat.sql)}, data={"sql": _snippet(stat.sql, 1000), "calls": stat.calls},
                  fix=manual(None, "Inspect the execution plan and tune the query or its indexes."))


# ----------------------------------------------------------------------------------------------------------------
# Execution plans
# ----------------------------------------------------------------------------------------------------------------
@dataclass
class PlanNode:
    kind: str  # seq | sort
    relation: Optional[str] = None
    rows: Optional[int] = None
    external: bool = False


def parse_plan(plan: Optional[str]) -> list[PlanNode]:
    """Normalize PostgreSQL or MySQL EXPLAIN output in JSON, text or tabular form."""
    text = (plan or "").strip()
    if not text:
        return []
    if text[0] in "[{":
        try:
            data = json.loads(text)
        except ValueError:
            return []
        out: list[PlanNode] = []
        _walk_json_plan(data, out)
        return out
    return _parse_text_plan(text)


def _walk_json_plan(node: Any, out: list[PlanNode]) -> None:
    if isinstance(node, list):
        for item in node:
            _walk_json_plan(item, out)
        return
    if not isinstance(node, dict):
        return
    node_type = node.get("Node Type")
    if node_type == "Seq Scan":
        out.append(PlanNode("seq", node.get("Relation Name"), _int(node.get("Plan Rows"))))
    elif node_type == "Sort":
        external = "external" in str(node.get("Sort Method", "")).lower() or "Disk" in str(node.get("Sort Space Type", ""))
        out.append(PlanNode("sort", None, _int(node.get("Plan Rows")), external))
    table = node.get("table")
    if isinstance(table, dict) and "access_type" in table:
        if str(table.get("access_type")).upper() == "ALL":
            out.append(PlanNode("seq", table.get("table_name"), _int(table.get("rows_examined_per_scan"))))
    if node.get("using_filesort") is True:
        source = table if isinstance(table, dict) else node
        out.append(PlanNode("sort", source.get("table_name"), _int(source.get("rows_examined_per_scan"))))
    for value in node.values():
        if isinstance(value, (dict, list)):
            _walk_json_plan(value, out)


def _int(value: Any) -> Optional[int]:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _parse_text_plan(text: str) -> list[PlanNode]:
    out: list[PlanNode] = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = re.search(r"Seq Scan on\s+\"?([\w.]+)\"?.*?rows=(\d+)", line)
        if m:
            out.append(PlanNode("seq", m.group(1), int(m.group(2))))
            continue
        m = re.search(r"(?:^|->\s*)\s*Sort\s+\(.*?rows=(\d+)", line)
        if m:
            external = any("external" in later for later in lines[i + 1 : i + 4])
            out.append(PlanNode("sort", None, int(m.group(1)), external))
            continue
        m = re.search(r"Table scan on\s+`?([\w.]+)`?.*?rows=(\d+)", line)
        if m:
            out.append(PlanNode("seq", m.group(1), int(m.group(2))))
    out.extend(_parse_mysql_table_plan(lines))
    return out


def _parse_mysql_table_plan(lines: list[str]) -> list[PlanNode]:
    out: list[PlanNode] = []
    header: Optional[list[str]] = None
    record: dict[str, str] = {}
    for line in lines:
        if re.match(r"^\s*\*+\s*\d+\.\s*row\s*\*+", line):
            _emit_mysql_row(record, out)
            record = {}
            continue
        m = re.match(r"^\s*(table|type|rows|Extra)\s*:\s*(.*)$", line, re.I)
        if m:
            record[m.group(1).lower()] = m.group(2).strip()
            continue
        if line.startswith("+"):
            continue
        cells = [c.strip() for c in (line.strip().strip("|").split("|") if "|" in line else line.split("\t"))]
        lowered = [c.lower() for c in cells]
        if "table" in lowered and "type" in lowered and "rows" in lowered:
            header = lowered
            continue
        if header and len(cells) == len(header):
            _emit_mysql_row(dict(zip(header, cells)), out)
    _emit_mysql_row(record, out)
    return out


def _emit_mysql_row(row: dict[str, str], out: list[PlanNode]) -> None:
    if not row:
        return
    table = row.get("table")
    rows = _int(row.get("rows"))
    if (row.get("type") or "").upper() == "ALL":
        out.append(PlanNode("seq", table, rows))
    if "using filesort" in (row.get("extra") or "").lower():
        out.append(PlanNode("sort", table, rows))


def _plan_target(db: Database, name: Optional[str]) -> Optional[Table]:
    if not name:
        return None
    return db.table(name.split(".")[-1])


@check("perf.plan_seq_scan")
def plan_seq_scan(db, profile, params):
    seen: set[tuple[str, str]] = set()
    for stat in db.query_stats:
        for node in parse_plan(stat.plan):
            if node.kind != "seq":
                continue
            t = _plan_target(db, node.relation)
            rows = node.rows if node.rows is not None else (t.row_count if t else None)
            if t is not None and t.row_count is not None:
                rows = max(rows or 0, t.row_count)
            if rows is None or rows < params["min_rows"]:
                continue
            key = (node.relation or "", _digest(stat.sql))
            if key in seen:
                continue
            seen.add(key)
            yield Hit(table=t.fqname if t else None, vars={"query": _digest(stat.sql), "relation": node.relation},
                      evidence=f"Plan shows a full scan of {node.relation} ({rows} rows). Query: {_snippet(stat.sql)}",
                      data={"sql": _snippet(stat.sql, 1000), "plan_rows": rows},
                      fix=manual(t, "Add a suitable index or a more selective predicate for this query."))


@check("perf.plan_filesort")
def plan_filesort(db, profile, params):
    seen: set[str] = set()
    for stat in db.query_stats:
        for node in parse_plan(stat.plan):
            if node.kind != "sort":
                continue
            t = _plan_target(db, node.relation)
            rows = node.rows if node.rows is not None else (t.row_count if t else None)
            if not node.external and (rows is None or rows < params["min_rows"]):
                continue
            key = _digest(stat.sql)
            if key in seen:
                continue
            seen.add(key)
            detail = "an external (disk) sort" if node.external else f"a sort of {rows} rows"
            yield Hit(table=t.fqname if t else None, vars={"query": key}, data={"sql": _snippet(stat.sql, 1000)},
                      evidence=f"Plan performs {detail}. Query: {_snippet(stat.sql)}",
                      fix=manual(t, "Add an index matching the ORDER BY, or reduce the rows being sorted."))


# ----------------------------------------------------------------------------------------------------------------
# Scalability
# ----------------------------------------------------------------------------------------------------------------
def _max_value(c: Column) -> Optional[int]:
    bits = c.type.bits
    if bits is None:
        return None
    return 2 ** bits - 1 if is_unsigned(c) else 2 ** (bits - 1) - 1


def _key_usage(db: Database, t: Table, c: Column) -> tuple[Optional[int], str]:
    """Current key value and where it came from: AUTO_INCREMENT info, then row data, then the row count."""
    counters = db.settings.get("auto_increment") or {}
    value = counters.get(t.fqname, counters.get(t.name))
    if value is not None:
        return int(value), "AUTO_INCREMENT counter"
    if db.data is not None:
        q = db.data.quote
        rows = run_query(db, f"SELECT MAX({q(c.name)}) FROM {qualified(db, t)}")
        if rows and rows[0][0] is not None:
            return int(rows[0][0]), "MAX of the key"
    if t.row_count is not None:
        return int(t.row_count), "row count (a lower bound)"
    return None, ""


@check("perf.key_near_exhaustion")
def key_near_exhaustion(db, profile, params):
    for t in tables_in_scope(db, profile, params):
        if len(t.primary_key) != 1:
            continue
        c = t.column(t.primary_key[0])
        if c is None or c.type.family != "int" or (c.type.bits or 64) > params["max_bits"] or not is_generated(c):
            continue
        current, source = _key_usage(db, t, c)
        maximum = _max_value(c)
        if current is None or not maximum:
            continue
        ratio = current / maximum
        if ratio < params["warn_ratio"]:
            continue
        severity = "critical" if ratio >= params["critical_ratio"] else None
        new_type = "bigint unsigned" if is_unsigned(c) else "bigint"
        yield Hit(table=t.fqname, column=c.name, severity=severity, vars={"ratio": f"{ratio:.0%}"},
                  evidence=f"{t.fqname}.{c.name} ({c.data_type}) is at {current} of a maximum {maximum} ({ratio:.1%}), "
                           f"from the {source}.",
                  data={"current": current, "maximum": maximum},
                  fix=make_fix("alter_column_type", t, c.name, new_type=new_type))


def _partition_columns(t: Table) -> list[str]:
    found: list[str] = []
    for entry in t.partition_columns:
        for word in re.findall(r"[A-Za-z_]\w*", entry):
            c = t.column(word)
            if c is not None and c.name not in found:
                found.append(c.name)
    return found


@check("perf.partition_key_not_in_unique")
def partition_key_not_in_unique(db, profile, params):
    enforced = {d.lower() for d in params["enforcing_dialects"]}
    for t in tables_in_scope(db, profile, params):
        partition = _partition_columns(t)
        if not partition:
            continue
        lowered = {p.lower() for p in partition}
        for key in t.unique_keys():
            if not key or lowered <= {c.lower() for c in key}:
                continue
            missing = [p for p in partition if p.lower() not in {c.lower() for c in key}]
            yield Hit(table=t.fqname, column=missing[0], vars={"key": ",".join(key)},
                      kind="confirmed_defect" if db.dialect in enforced else "context_dependent",
                      evidence=f"Unique key ({', '.join(key)}) on partitioned table {t.fqname} does not include "
                               f"partition column(s) {', '.join(missing)}.",
                      fix=manual(t, f"Add {', '.join(missing)} to the key, or record the engine's documented alternative."))


@check("perf.large_table_unpartitioned")
def large_table_unpartitioned(db, profile, params):
    for t in tables_in_scope(db, profile, params):
        if t.partition_columns or t.row_count is None or t.row_count < params["min_rows"]:
            continue
        temporal = [c.name for c in t.columns if c.type.family in ("date", "datetime", "timestamptz")]
        if not temporal:
            continue
        yield Hit(table=t.fqname, vars={"temporal": ",".join(temporal[:3])},
                  evidence=f"{t.fqname} has about {t.row_count} rows, no partitioning, and date column(s) "
                           f"{', '.join(temporal[:3])}.",
                  fix=manual(t, "Assess whether retention, maintenance or query pruning on a dominant filter justifies "
                                "partitioning."))


@check("perf.uuid_clustered_innodb")
def uuid_clustered_innodb(db, profile, params):
    if db.dialect not in params["dialects"]:
        return
    for t in tables_in_scope(db, profile, params):
        if not t.primary_key or (t.engine or "innodb").lower() != "innodb":
            continue
        c = t.column(t.primary_key[0])
        if c is None:
            continue
        ti = c.type
        looks_uuid = ti.family == "uuid" or (ti.family in ("text", "char") and ti.length in params["text_lengths"]
                                             and bool({w.lower() for w in tokens(c.name)} & set(params["name_tokens"])))
        if ti.family == "binary" and ti.length == 16 and matches(c.name, params["binary_name_patterns"]):
            looks_uuid = True
        if looks_uuid:
            yield Hit(table=t.fqname, column=c.name,
                      evidence=f"Primary key {t.fqname}.{c.name} ({c.data_type}) appears to hold UUIDs and is the InnoDB "
                               f"clustered key. Whether they are random cannot be read from the schema.",
                      fix=manual(t, "If the UUIDs are random, use a time-ordered version or a 64-bit key.", c.name))
