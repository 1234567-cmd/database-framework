"""Data quality checks. Every check reads through ``db.data`` only, uses generic SQL and honours the sample limit.

Findings never propose deleting records: duplicates, orphans and financial differences use a manual repair plan.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

from ..model import Column, Database, Table
from ..rules.engine import Hit, check, iter_tables
from .security import compile_any, manual, mask_value, matches, read_limit, safe_query, sample_column, table_ref

_GROUPABLE = {"int", "decimal", "float", "money", "text", "char", "bool", "date", "datetime", "timestamptz", "time",
              "uuid", "enum"}
_NUMERIC = {"int", "decimal", "float", "money"}
_DATES = {"date", "datetime", "timestamptz"}
_TEXT = {"text", "char"}
_DUP_PLAN = ("Review the duplicates with the data owner, choose the surviving record, and repoint references. "
             "Do not delete financial or business records without an approved repair plan.")
_ORPHAN_PLAN = ("Identify each orphan's correct parent or restore the missing parent. Do not delete records "
                "automatically; financial and business records are preserved.")


def _sampled(db: Database, t: Table, columns: list[str], limit: int, where: str = "") -> str:
    cols = ", ".join(db.data.quote(c) for c in columns)
    clause = f" WHERE {where}" if where else ""
    return f"(SELECT {cols} FROM {table_ref(db, t)}{clause} LIMIT {int(limit)}) s"


def _lit(value: str) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def _groupable(t: Table) -> list[Column]:
    return [c for c in t.columns if c.type.family in _GROUPABLE]


def _table_stats(db: Database, t: Table, limit: int) -> Optional[tuple[int, dict[str, tuple[int, int]]]]:
    """Row count, and for each groupable column (non-null count, distinct count), over the sample."""
    cols = _groupable(t)
    if not cols:
        return None
    q = db.data.quote
    exprs = ["COUNT(*)"] + [f"COUNT({q(c.name)}), COUNT(DISTINCT {q(c.name)})" for c in cols]
    rows = safe_query(db, f"SELECT {', '.join(exprs)} FROM {_sampled(db, t, [c.name for c in cols], limit)}", t.fqname)
    if not rows:
        return None
    row = rows[0]
    return int(row[0]), {c.name: (int(row[1 + 2 * i]), int(row[2 + 2 * i])) for i, c in enumerate(cols)}


def _duplicate_groups(db: Database, t: Table, columns: list[str], limit: int, where: str = "") -> Optional[tuple[int, int, int]]:
    """(distinct groups, groups with duplicates, rows in those groups) over the sample."""
    group = ", ".join(db.data.quote(c) for c in columns)
    sql = (f"SELECT COUNT(*), SUM(CASE WHEN cnt > 1 THEN 1 ELSE 0 END), SUM(CASE WHEN cnt > 1 THEN cnt ELSE 0 END) "
           f"FROM (SELECT COUNT(*) AS cnt FROM {_sampled(db, t, columns, limit, where)} GROUP BY {group}) g")
    rows = safe_query(db, sql, t.fqname)
    if not rows:
        return None
    return int(rows[0][0] or 0), int(rows[0][1] or 0), int(rows[0][2] or 0)


def _key_columns(t: Table) -> set[str]:
    keys = {c.lower() for key in t.unique_keys() for c in key}
    return keys


def _tenant_scope(t: Table, profile) -> list[str]:
    scope = []
    if t.has_column(profile.tenant_column):
        scope.append(profile.tenant_column)
    if profile.multi_company and t.has_column(profile.company_column):
        scope.append(profile.company_column)
    return scope


@check("data_quality.empty_tables")
def empty_tables(db, profile, params):
    for t in iter_tables(db, profile):
        rows = safe_query(db, f"SELECT COUNT(*) FROM (SELECT 1 AS x FROM {table_ref(db, t)} LIMIT 1) s", t.fqname)
        if rows and int(rows[0][0]) == 0:
            yield Hit(table=t.fqname, evidence=f"Table {t.fqname} has no rows.")


@check("data_quality.exact_duplicates")
def exact_duplicates(db, profile, params):
    limit = read_limit(profile, params, 100000)
    audit = {n.lower() for group in profile.audit_columns for n in group}
    for t in iter_tables(db, profile):
        pk = {c.lower() for c in t.primary_key}
        cols = [c.name for c in _groupable(t)
                if c.name.lower() not in pk and not c.is_identity and c.name.lower() not in audit]
        if len(cols) < int(params.get("min_columns", 2)):
            continue
        res = _duplicate_groups(db, t, cols, limit)
        if not res or res[1] == 0:
            continue
        keyed = bool(t.unique_keys())
        yield Hit(table=t.fqname, evidence=f"{res[1]} duplicate groups covering {res[2]} rows in the sample, comparing "
                                           f"{len(cols)} columns" + (" and excluding the key." if keyed else "."),
                  kind="context_dependent" if keyed else "confirmed_defect", data={"groups": res[1], "rows": res[2]},
                  fix=manual(t.fqname, None, _DUP_PLAN))


@check("data_quality.natural_key_duplicates")
def natural_key_duplicates(db, profile, params):
    limit = read_limit(profile, params, 100000)
    name_rx, exclude = compile_any(params.get("name_patterns", [])), compile_any(params.get("exclude_patterns", []))
    min_ratio = float(params.get("min_distinct_ratio", 0.8))
    for t in iter_tables(db, profile):
        keys = _key_columns(t)
        fk_cols = {c.lower() for fk in t.foreign_keys for c in fk.columns}
        scope = _tenant_scope(t, profile)
        for c in _groupable(t):
            low = c.name.lower()
            if not matches(name_rx, low) or matches(exclude, low) or low in keys or low in fk_cols or c.is_generated:
                continue
            q = db.data.quote(c.name)
            res = _duplicate_groups(db, t, scope + [c.name], limit, f"{q} IS NOT NULL")
            if not res or res[1] == 0:
                continue
            nonnull = res[0] + res[2] - res[1]
            if res[0] / max(nonnull, 1) < min_ratio:  # repeats by design, for example a status code
                continue
            yield Hit(table=t.fqname, column=c.name,
                      evidence=f"{res[1]} values repeat across {res[2]} rows in the sample"
                               + (f", within {', '.join(scope)}." if scope else "."),
                      fix=manual(t.fqname, c.name, _DUP_PLAN), data={"groups": res[1], "rows": res[2]})


@check("data_quality.unenforced_key_duplicates")
def unenforced_key_duplicates(db, profile, params):
    limit = read_limit(profile, params, 100000)
    for t in iter_tables(db, profile):
        for key in t.unique_keys():
            where = " AND ".join(f"{db.data.quote(c)} IS NOT NULL" for c in key)
            res = _duplicate_groups(db, t, list(key), limit, where)
            if res and res[1]:
                yield Hit(table=t.fqname, column=key[0] if len(key) == 1 else None, vars={"key_columns": ", ".join(key)},
                          evidence=f"Declared key ({', '.join(key)}) has {res[1]} duplicated values across {res[2]} rows.",
                          fix=manual(t.fqname, None, _DUP_PLAN), data={"groups": res[1], "rows": res[2]})


@check("data_quality.high_null_rate")
def high_null_rate(db, profile, params):
    limit = read_limit(profile, params, 100000)
    max_ratio, min_rows = float(params.get("max_null_ratio", 0.5)), int(params.get("min_rows", 100))
    exclude = compile_any(params.get("exclude_patterns", []))
    for t in iter_tables(db, profile):
        stats = _table_stats(db, t, limit)
        if not stats or stats[0] < min_rows:
            continue
        for c in _groupable(t):
            nonnull = stats[1][c.name][0]
            ratio = 1 - nonnull / stats[0]
            if c.nullable and ratio > max_ratio and not matches(exclude, c.name):
                yield Hit(table=t.fqname, column=c.name, evidence=f"{ratio:.0%} of {stats[0]} sampled rows are NULL.",
                          vars={"null_ratio": f"{ratio:.0%}"})


@check("data_quality.mandatory_looking_nulls")
def mandatory_looking_nulls(db, profile, params):
    limit = read_limit(profile, params, 100000)
    name_rx, exclude = compile_any(params.get("name_patterns", [])), compile_any(params.get("exclude_patterns", []))
    max_ratio = float(params.get("max_null_ratio", 0.2))
    for t in iter_tables(db, profile):
        candidates = [c for c in _groupable(t) if matches(name_rx, c.name) and not matches(exclude, c.name)]
        if not candidates:
            continue
        stats = _table_stats(db, t, limit)
        if not stats or stats[0] == 0:
            continue
        for c in candidates:
            nulls = stats[0] - stats[1][c.name][0]
            if nulls and nulls / stats[0] <= max_ratio:
                yield Hit(table=t.fqname, column=c.name, evidence=f"{nulls} of {stats[0]} sampled rows are NULL in a "
                                                                  "column that looks mandatory.",
                          fix=manual(t.fqname, c.name, "Populate the missing values with the data owner, then add NOT NULL."),
                          data={"nulls": nulls})


def _orphans(db: Database, child: Table, child_cols: list[str], parent: Table, parent_cols: list[str],
             limit: int) -> Optional[tuple[int, int]]:
    q = db.data.quote
    where = " AND ".join(f"{q(c)} IS NOT NULL" for c in child_cols)
    join = " AND ".join(f"c.{q(a)} = p.{q(b)}" for a, b in zip(child_cols, parent_cols))
    inner = f"(SELECT {', '.join(q(c) for c in child_cols)} FROM {table_ref(db, child)} WHERE {where} LIMIT {int(limit)}) c"
    sql = (f"SELECT COUNT(*), SUM(CASE WHEN p.{q(parent_cols[0])} IS NULL THEN 1 ELSE 0 END) "
           f"FROM {inner} LEFT JOIN {table_ref(db, parent)} p ON {join}")
    rows = safe_query(db, sql, child.fqname)
    if not rows:
        return None
    return int(rows[0][0] or 0), int(rows[0][1] or 0)


@check("data_quality.orphans_declared")
def orphans_declared(db, profile, params):
    limit = read_limit(profile, params, 100000)
    for t in iter_tables(db, profile):
        for fk in t.foreign_keys:
            parent = db.table(fk.ref_table, fk.ref_schema) or db.table(fk.ref_table)
            if parent is None or not fk.ref_columns:
                continue
            res = _orphans(db, t, fk.columns, parent, fk.ref_columns, limit)
            if res and res[1]:
                yield Hit(table=t.fqname, column=fk.columns[0], vars={"ref_table": parent.fqname, "basis": "declared foreign key"},
                          evidence=f"{res[1]} of {res[0]} sampled references have no parent in {parent.fqname}.",
                          fix=manual(t.fqname, fk.columns[0], _ORPHAN_PLAN), data={"orphans": res[1], "sampled": res[0]})


def _candidate_parent(db: Database, base: str) -> Optional[Table]:
    names = [base, base + "s", base + "es"]
    if base.endswith("y"):
        names.append(base[:-1] + "ies")
    for name in names:
        table = db.table(name)
        if table is not None:
            return table
    return None


def _compatible(a: Column, b: Column) -> bool:
    fa, fb = a.type.family, b.type.family
    return fa == fb or {fa, fb} <= _TEXT or {fa, fb} <= {"int", "decimal"}


@check("data_quality.orphans_inferred")
def orphans_inferred(db, profile, params):
    limit = read_limit(profile, params, 100000)
    suffix = params.get("reference_suffix", "_id")
    strong = float(params.get("strong_match_ratio", 0.9))
    floor = float(params.get("min_match_ratio", 0.5))
    for t in iter_tables(db, profile):
        declared = {c.lower() for fk in t.foreign_keys for c in fk.columns}
        for c in t.columns:
            low = c.name.lower()
            if not low.endswith(suffix) or low in declared or low == suffix.lstrip("_") or [low] == [k.lower() for k in t.primary_key]:
                continue
            base = low[: -len(suffix)]
            parent = _candidate_parent(db, base)
            if parent is None or parent is t or len(parent.primary_key) != 1:
                continue
            pk = parent.column(parent.primary_key[0])
            if pk is None or pk.name.lower() not in ("id", low) or not _compatible(c, pk):
                continue
            res = _orphans(db, t, [c.name], parent, [pk.name], limit)
            if not res or not res[0] or not res[1]:
                continue
            ratio = 1 - res[1] / res[0]
            if ratio < floor:  # most values do not resolve: the guess itself is probably wrong
                continue
            is_strong = ratio >= strong
            yield Hit(table=t.fqname, column=c.name,
                      vars={"ref_table": parent.fqname, "basis": "strong inference" if is_strong else "weak inference"},
                      kind="confirmed_defect" if is_strong else "context_dependent", confidence=0.85 if is_strong else 0.5,
                      evidence=f"{res[1]} of {res[0]} sampled values of {c.name} have no match in {parent.fqname}.{pk.name}; "
                               f"{ratio:.0%} resolve, and no foreign key is declared.",
                      fix=manual(t.fqname, c.name, _ORPHAN_PLAN), data={"orphans": res[1], "sampled": res[0]})


def _valid_date(text: str) -> bool:
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            datetime.strptime(text[:19], fmt)
            return True
        except ValueError:
            continue
    return False


@check("data_quality.invalid_formats")
def invalid_formats(db, profile, params):
    limit = read_limit(profile, params)
    max_bad = float(params.get("max_invalid_ratio", 0.5))
    formats = [(f, compile_any(f.get("name_patterns", [])), compile_any(f.get("exclude_patterns", [])),
                re.compile(f["regex"]) if f.get("regex") else None) for f in params.get("formats", [])]
    for t in iter_tables(db, profile):
        for c in t.columns:
            if c.type.family not in _TEXT:
                continue
            for fmt, name_rx, exclude, rx in formats:
                if not matches(name_rx, c.name) or matches(exclude, c.name):
                    continue
                values = [str(v).strip() for v in (sample_column(db, t, c.name, limit) or []) if str(v).strip()]
                if not values:
                    break
                bad = [v for v in values if not (rx.fullmatch(v) if rx else _valid_date(v))]
                if bad and len(bad) / len(values) <= max_bad:
                    shown = bad[:3] if fmt.get("safe_examples") else [mask_value(v) for v in bad[:3]]
                    yield Hit(table=t.fqname, column=c.name, vars={"format_name": fmt["name"]},
                              evidence=f"{len(bad)} of {len(values)} sampled values fail {fmt['name']}; "
                                       f"examples: {', '.join(shown)}.",
                              fix=manual(t.fqname, c.name, "Correct the values with the data owner, then add validation at write."),
                              data={"invalid": len(bad), "sampled": len(values)})
                break


@check("data_quality.negative_values")
def negative_values(db, profile, params):
    limit = read_limit(profile, params, 100000)
    name_rx = compile_any(params.get("non_negative_patterns", []))
    exclude = compile_any(params.get("exclude_patterns", []))
    for t in iter_tables(db, profile):
        for c in t.columns:
            if c.type.family not in _NUMERIC or not matches(name_rx, c.name) or matches(exclude, c.name):
                continue
            q = db.data.quote(c.name)
            rows = safe_query(db, f"SELECT COUNT(*) FROM {_sampled(db, t, [c.name], limit)} WHERE {q} < 0", t.fqname)
            if rows and rows[0][0]:
                yield Hit(table=t.fqname, column=c.name, evidence=f"{rows[0][0]} sampled rows have a negative value.",
                          fix=manual(t.fqname, c.name, "Confirm whether negatives are valid here; correct them, then add a CHECK."),
                          data={"negative": int(rows[0][0])})


@check("data_quality.future_dates")
def future_dates(db, profile, params):
    limit = read_limit(profile, params, 100000)
    name_rx = compile_any(params.get("name_patterns", []))
    cutoff = (datetime.now(timezone.utc) + timedelta(days=int(params.get("tolerance_days", 1)))).strftime("%Y-%m-%d %H:%M:%S")
    for t in iter_tables(db, profile):
        for c in t.columns:
            if c.type.family not in _DATES or not matches(name_rx, c.name):
                continue
            q = db.data.quote(c.name)
            rows = safe_query(db, f"SELECT COUNT(*) FROM {_sampled(db, t, [c.name], limit)} WHERE {q} > {_lit(cutoff)}", t.fqname)
            if rows and rows[0][0]:
                yield Hit(table=t.fqname, column=c.name, evidence=f"{rows[0][0]} sampled rows are dated after {cutoff} UTC.",
                          fix=manual(t.fqname, c.name, "Find the writer producing these dates and correct the values."),
                          data={"future": int(rows[0][0])})


@check("data_quality.end_before_start")
def end_before_start(db, profile, params):
    limit = read_limit(profile, params, 100000)
    for t in iter_tables(db, profile):
        for start, end in params.get("column_pairs", []):
            s_col, e_col = t.column(start), t.column(end)
            if s_col is None or e_col is None:
                continue
            q = db.data.quote
            sql = (f"SELECT COUNT(*) FROM {_sampled(db, t, [s_col.name, e_col.name], limit)} "
                   f"WHERE {q(e_col.name)} < {q(s_col.name)}")
            rows = safe_query(db, sql, t.fqname)
            if rows and rows[0][0]:
                yield Hit(table=t.fqname, column=e_col.name, vars={"start_column": s_col.name},
                          evidence=f"{rows[0][0]} sampled rows have {e_col.name} before {s_col.name}.",
                          fix=manual(t.fqname, e_col.name, f"Correct the rows, then add a CHECK that {e_col.name} >= {s_col.name}."),
                          data={"invalid": int(rows[0][0])})


@check("data_quality.casing_variants")
def casing_variants(db, profile, params):
    limit = read_limit(profile, params, 100000)
    max_distinct = int(params.get("max_distinct", 200))
    exclude = compile_any(params.get("exclude_patterns", []))
    for t in iter_tables(db, profile):
        for c in t.columns:
            if c.type.family not in _TEXT or matches(exclude, c.name) or (c.type.length or 0) > int(params.get("max_length", 255)):
                continue
            q = db.data.quote(c.name)
            sql = f"SELECT {q}, COUNT(*) FROM {_sampled(db, t, [c.name], limit, f'{q} IS NOT NULL')} GROUP BY {q} LIMIT {max_distinct + 1}"
            rows = safe_query(db, sql, f"{t.fqname}.{c.name}")
            if not rows or len(rows) > max_distinct:
                continue
            groups: dict[str, list[str]] = {}
            for value, _ in rows:
                groups.setdefault(" ".join(str(value).split()).casefold(), []).append(str(value))
            variants = {k: v for k, v in groups.items() if len(v) > 1}
            if variants:
                sample = ", ".join("/".join(mask_value(x) for x in v[:3]) for v in list(variants.values())[:2])
                yield Hit(table=t.fqname, column=c.name, evidence=f"{len(variants)} values appear in several spellings of "
                                                                  f"case or whitespace; masked: {sample}.",
                          fix=manual(t.fqname, c.name, "Agree the canonical form, normalize the values and validate at write."),
                          data={"variant_groups": len(variants)})


@check("data_quality.constant_columns")
def constant_columns(db, profile, params):
    limit = read_limit(profile, params, 100000)
    min_rows = int(params.get("min_rows", 100))
    exclude = compile_any(params.get("exclude_patterns", []))
    for t in iter_tables(db, profile):
        stats = _table_stats(db, t, limit)
        if not stats or stats[0] < min_rows:
            continue
        skip = {profile.tenant_column.lower(), profile.company_column.lower()}
        for c in _groupable(t):
            nonnull, distinct = stats[1][c.name]
            if distinct == 1 and nonnull == stats[0] and c.name.lower() not in skip and not matches(exclude, c.name):
                yield Hit(table=t.fqname, column=c.name, evidence=f"All {stats[0]} sampled rows hold one value.")


# ---- financial integrity ----

def _dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value if value is not None else 0))
    except InvalidOperation:
        return Decimal(0)


def _first(t: Table, names: list[str], families: Optional[set[str]] = None) -> Optional[Column]:
    for name in names:
        col = t.column(name)
        if col is not None and (families is None or col.type.family in families):
            return col
    return None


def _posted_filter(db: Database, t: Table, alias: str, params: dict) -> Optional[str]:
    status = _first(t, params.get("status_columns", []), _TEXT | {"enum"})
    if status is None:
        return None
    values = ", ".join(_lit(str(v).lower()) for v in params.get("posted_values", []))
    return f"LOWER({alias}.{db.data.quote(status.name)}) IN ({values})"


@check("financial.ledger_imbalance")
def ledger_imbalance(db, profile, params):
    limit = read_limit(profile, params, 100000)
    name_rx = compile_any(params.get("journal_table_patterns", []))
    tolerance = Decimal(str(params.get("tolerance", 0.005)))
    for t in iter_tables(db, profile):
        debit = _first(t, params.get("debit_columns", []), _NUMERIC)
        credit = _first(t, params.get("credit_columns", []), _NUMERIC)
        if not matches(name_rx, t.name) or debit is None or credit is None:
            continue
        group = _first(t, params.get("journal_id_columns", []))
        if group is None:
            continue
        q = db.data.quote
        conds, joins, known = [], "", False
        line_filter = _posted_filter(db, t, "x", params)
        if line_filter:
            conds.append(line_filter)
            known = True
        else:
            for fk in t.foreign_keys:
                header = db.table(fk.ref_table)
                if header is None or [c.lower() for c in fk.columns] != [group.name.lower()]:
                    continue
                head_filter = _posted_filter(db, header, "h", params)
                if head_filter:
                    joins = f" JOIN {table_ref(db, header)} h ON x.{q(group.name)} = h.{q(fk.ref_columns[0])}"
                    conds.append(head_filter)
                    known = True
                    break
        where = f" WHERE {' AND '.join(conds)}" if conds else ""
        g = q(group.name)
        # Whole journals are sampled, never a slice of rows, so a partial journal cannot look unbalanced.
        sql = (f"SELECT x.{g}, SUM(COALESCE(x.{q(debit.name)}, 0)), SUM(COALESCE(x.{q(credit.name)}, 0)) "
               f"FROM {table_ref(db, t)} x JOIN (SELECT DISTINCT {g} FROM {table_ref(db, t)} WHERE {g} IS NOT NULL "
               f"LIMIT {int(limit)}) s ON x.{g} = s.{g}{joins}{where} GROUP BY x.{g}")
        rows = safe_query(db, sql, t.fqname)
        if not rows:
            continue
        bad = [(r[0], _dec(r[1]) - _dec(r[2])) for r in rows if abs(_dec(r[1]) - _dec(r[2])) > tolerance]
        if bad:
            sample = ", ".join(f"{k} (difference {d})" for k, d in bad[:3])
            scope = "posted journals" if known else "journals, with posting status not detectable, so drafts may be included"
            yield Hit(table=t.fqname, column=debit.name, vars={"journal_column": group.name},
                      evidence=f"{len(bad)} of {len(rows)} {scope} do not balance: {sample}.",
                      confidence=0.95 if known else 0.7, data={"unbalanced": len(bad), "checked": len(rows)},
                      fix=manual(t.fqname, None, "Investigate each journal with finance and correct through reversing "
                                                 "or correcting entries. Do not edit or delete posted entries."))


@check("financial.document_totals")
def document_totals(db, profile, params):
    limit = read_limit(profile, params, 100000)
    doc_rx, line_rx = compile_any(params.get("document_table_patterns", [])), compile_any(params.get("line_table_patterns", []))
    tolerance = Decimal(str(params.get("tolerance", 0.01)))
    q_lines = params.get("line_amount_columns", [])
    for header in iter_tables(db, profile):
        if not matches(doc_rx, header.name) or matches(line_rx, header.name) or len(header.primary_key) != 1:
            continue
        posted = _posted_filter(db, header, "d", params)
        total = _first(header, params.get("net_total_columns", []), _NUMERIC)
        if total is None and not any(header.has_column(c) for c in params.get("adjustment_columns", [])):
            total = _first(header, params.get("gross_total_columns", []), _NUMERIC)
        if posted is None or total is None:
            continue
        pk = header.primary_key[0]
        q = db.data.quote
        for line, fk in db.referencing(header):
            amount = _first(line, q_lines, _NUMERIC)
            if not matches(line_rx, line.name) or amount is None or len(fk.columns) != 1:
                continue
            sql = (f"SELECT h.{q(pk)}, h.{q(total.name)}, SUM(COALESCE(l.{q(amount.name)}, 0)) FROM "
                   f"(SELECT d.{q(pk)}, d.{q(total.name)} FROM {table_ref(db, header)} d WHERE {posted} LIMIT {int(limit)}) h "
                   f"JOIN {table_ref(db, line)} l ON l.{q(fk.columns[0])} = h.{q(pk)} GROUP BY h.{q(pk)}, h.{q(total.name)}")
            rows = safe_query(db, sql, header.fqname)
            if not rows:
                continue
            bad = [(r[0], _dec(r[1]) - _dec(r[2])) for r in rows if abs(_dec(r[1]) - _dec(r[2])) > tolerance]
            if bad:
                sample = ", ".join(f"{k} (difference {d})" for k, d in bad[:3])
                yield Hit(table=header.fqname, column=total.name, vars={"line_table": line.fqname},
                          evidence=f"{len(bad)} of {len(rows)} posted documents differ from {line.fqname}: {sample}.",
                          data={"mismatched": len(bad), "checked": len(rows)},
                          fix=manual(header.fqname, total.name, "Reconcile each document with finance; correct through "
                                                                "credit or adjusting documents, not by editing posted records."))


@check("financial.document_number_gaps")
def document_number_gaps(db, profile, params):
    limit = read_limit(profile, params, 100000)
    table_rx, name_rx = compile_any(params.get("document_table_patterns", [])), compile_any(params.get("number_column_patterns", []))
    exclude = compile_any(params.get("exclude_table_patterns", []))
    split = re.compile(params.get("number_regex", r"^(.*?)(\d+)$"))
    for t in iter_tables(db, profile):
        if not matches(table_rx, t.name) or matches(exclude, t.name):
            continue
        fk_cols = {c.lower() for fk in t.foreign_keys for c in fk.columns}
        cols = [c for c in t.columns if matches(name_rx, c.name) and c.name.lower() not in fk_cols
                and c.type.family in _TEXT | {"int", "decimal"}]
        if not cols:
            continue
        total = safe_query(db, f"SELECT COUNT(*) FROM {table_ref(db, t)}", t.fqname)
        if not total:
            continue
        if int(total[0][0]) > limit:  # a slice of a sequence would show false gaps
            db.import_warnings.append(f"Document number gap check skipped for {t.fqname}: more rows than the sample limit.")
            continue
        scope = _tenant_scope(t, profile)
        for c in cols:
            select = ", ".join(db.data.quote(x) for x in scope + [c.name])
            rows = safe_query(db, f"SELECT {select} FROM {table_ref(db, t)} WHERE {db.data.quote(c.name)} IS NOT NULL", t.fqname)
            series: dict[tuple, set[int]] = {}
            for row in rows or []:
                m = split.match(str(row[-1]).strip())
                if m:
                    series.setdefault((*row[:-1], m.group(1)), set()).add(int(m.group(2)))
            gaps = {k: (max(v) - min(v) + 1 - len(v)) for k, v in series.items()}
            missing = {k: g for k, g in gaps.items() if g > 0}
            if missing:
                sample = ", ".join(f"series {k[-1] or '(none)'}: {g} missing" for k, g in list(missing.items())[:3])
                yield Hit(table=t.fqname, column=c.name, evidence=f"{sum(missing.values())} number gaps; {sample}.",
                          data={"gaps": sum(missing.values()), "series": len(missing)},
                          fix=manual(t.fqname, c.name, "Requires legal review: record the reason for each gap for the "
                                                       "applicable jurisdiction. Do not renumber issued documents."))
