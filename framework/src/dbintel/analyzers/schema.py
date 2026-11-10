"""Schema analyzer: structure, normalization, data types and naming.

Check functions find facts only. All text, thresholds and name lists come from ``rules/catalog/10_schema.yaml``.
Sampled row values are used to decide whether a finding holds. They are never copied into evidence.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from typing import Any, Iterable, Iterator, Optional

from ..config import Profile
from ..findings import Fix
from ..model import Column, Database, ForeignKey, Table
from ..rules.engine import Hit, check, iter_tables

TEXT_FAMILIES = ("text", "char")
NUMERIC_FAMILIES = ("decimal", "float", "money", "int")


# ----------------------------------------------------------------------------------------------------------------
# Shared helpers
# ----------------------------------------------------------------------------------------------------------------
def snake(name: str) -> str:
    """Normalize an identifier to lowercase words separated by single underscores."""
    text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", "_", name.strip())
    text = re.sub(r"[^A-Za-z0-9]+", "_", text)
    return re.sub(r"_+", "_", text).strip("_").lower()


def tokens(name: str) -> list[str]:
    return [p for p in snake(name).split("_") if p]


def matches(name: str, patterns: Iterable[str]) -> bool:
    return any(re.search(p, name, re.I) for p in patterns)


def singular(name: str, irregular: Optional[dict] = None) -> str:
    """Singular form of a lowercase table name, using its last word."""
    parts = name.lower().split("_")
    last = parts[-1]
    if irregular and last in irregular:
        last = irregular[last]
    elif last.endswith("ies") and len(last) > 3:
        last = last[:-3] + "y"
    elif re.search(r"(ss|sh|ch|x|z)es$", last):
        last = last[:-2]
    elif last.endswith("s") and not last.endswith(("ss", "us", "is")):
        last = last[:-1]
    return "_".join(parts[:-1] + [last])


def tables_in_scope(db: Database, profile: Profile, params: dict) -> Iterator[Table]:
    exempt = {x.lower() for x in params.get("exempt_tables", [])}
    patterns = params.get("exempt_table_patterns", [])
    for t in iter_tables(db, profile):
        if t.name.lower() not in exempt and not matches(t.name, patterns):
            yield t


def make_fix(op: str, table: Optional[Table], column: Optional[str] = None, **params: Any) -> Fix:
    return Fix(op, table.fqname if table else None, column, params)


def manual(table: Optional[Table], description: str, column: Optional[str] = None) -> Fix:
    return make_fix("manual", table, column, description=description)


def is_generated(c: Column) -> bool:
    raw = f"{c.data_type} {c.default or ''}".lower()
    return c.is_identity or "serial" in raw or "nextval" in raw or "auto_increment" in raw


def is_unsigned(c: Column) -> bool:
    return "unsigned" in c.data_type.lower()


def fk_column_names(t: Table) -> set[str]:
    return {c.lower() for fk in t.foreign_keys for c in fk.columns}


def key_column_names(t: Table) -> set[str]:
    return {c.lower() for c in t.primary_key} | fk_column_names(t)


def ref_target(db: Database, t: Table, fk: ForeignKey) -> Optional[Table]:
    return db.table(fk.ref_table, fk.ref_schema or t.schema) or db.table(fk.ref_table)


def qualified(db: Database, t: Table) -> str:
    q = db.data.quote
    return f"{q(t.schema)}.{q(t.name)}" if t.schema else q(t.name)


def sample_limit(profile: Profile, params: dict) -> int:
    return int(min(profile.data_sample_limit, params.get("sample_limit", 20000)))


def run_query(db: Database, sql: str) -> Optional[list[tuple]]:
    """Run a read-only query. A failure means the data could not be verified, so callers fall back."""
    if db.data is None:
        return None
    try:
        return db.data.query(sql)
    except Exception:  # noqa: BLE001 - permissions, dialect gaps and timeouts must not stop the assessment
        return None


def sample(db: Database, profile: Profile, params: dict, t: Table, column: str) -> Optional[list[Any]]:
    """Up to the configured number of non-null values, or None when row data cannot be read."""
    if db.data is None:
        return None
    q = db.data.quote
    rows = run_query(db, f"SELECT {q(column)} FROM {qualified(db, t)} WHERE {q(column)} IS NOT NULL "
                         f"LIMIT {sample_limit(profile, params)}")
    return None if rows is None else [r[0] for r in rows]


def _unverified(db: Database, values: list[str], params: dict) -> str:
    """Say why contents were not checked: no row data at all is different from too small a sample."""
    if db.data is None:
        return "row data was not available to verify."
    return f"only {len(values)} non-null value(s) were sampled, fewer than the {params['min_samples']} needed to verify."


def text_values(values: list[Any]) -> list[str]:
    return [v.decode("utf-8", "replace") if isinstance(v, (bytes, bytearray)) else str(v) for v in values]


def share(values: list[str], pattern: str) -> float:
    rx = re.compile(pattern, re.I)
    return sum(1 for v in values if rx.search(v.strip())) / len(values) if values else 0.0


def by_dialect(mapping: dict, db: Database) -> Optional[str]:
    return mapping.get(db.dialect, mapping.get("default"))


def is_money(c: Column, profile: Profile, params: dict) -> bool:
    words = set(tokens(c.name))
    return bool(words & {p.lower() for p in profile.money_name_patterns}) \
        and not words & {x.lower() for x in params["exclude_tokens"]}


def multi_currency(db: Database, profile: Profile, params: dict) -> Optional[str]:
    """Why this database holds several currencies, or None. ``params.multi_currency`` overrides the inference."""
    explicit = params.get("multi_currency")
    if explicit is not None:
        return "configured as multi-currency" if explicit else None
    if profile.multi_company:
        return "the profile is multi-company"
    for t in db.tables:
        if t.name.lower() in {x.lower() for x in params["currency_tables"]}:
            return f"table {t.fqname} exists"
        for c in t.columns:
            if matches(c.name, params["currency_column_patterns"]):
                return f"column {t.fqname}.{c.name} exists"
    return None


def uniform_or_each(items: list, total: int, params: dict, summary: str) -> Iterator[Hit]:
    """Report a convention that a whole database follows once, instead of once per table."""
    if len(items) >= params["uniform_min_count"] and len(items) / max(total, 1) >= params["uniform_ratio"]:
        yield Hit(evidence=summary, vars={"scope": "database"}, data={"tables": [i.table for i in items]},
                  fix=Fix("manual", None, None, {"description": "Decide whether to adopt the standard name or record "
                                                               "the existing uniform convention as an exception."}))
    else:
        yield from items


# ----------------------------------------------------------------------------------------------------------------
# Keys and references
# ----------------------------------------------------------------------------------------------------------------
@check("schema.missing_primary_key")
def missing_primary_key(db, profile, params):
    if not profile.system_of_record:
        return
    for t in tables_in_scope(db, profile, params):
        if t.primary_key:
            continue
        unique = [u for u in t.unique_keys()
                  if u and all(t.column(c) is not None and not t.column(c).nullable for c in u)]
        if unique:
            fix = make_fix("add_primary_key", t, columns=list(unique[0]))
            detail = f"; a NOT NULL unique key on ({', '.join(unique[0])}) could be promoted"
        else:
            fix = make_fix("add_surrogate_primary_key", t)
            detail = "; no NOT NULL unique key exists"
        yield Hit(table=t.fqname, evidence=f"Table {t.fqname} declares no primary key{detail}.", fix=fix)


def _reference_stems(name: str, params: dict) -> list[tuple[str, bool]]:
    """Possible parent names for a reference column, each flagged when it drops a role qualifier."""
    words = tokens(name)
    if len(words) < 2 or words[-1] not in params["reference_suffixes"]:
        return []
    stem = words[:-1]
    return [("_".join(stem[i:]), i > 0) for i in range(len(stem))]


def _find_parent(db: Database, t: Table, stem: str, irregular: dict) -> Optional[Table]:
    candidates = {stem, stem + "s", stem + "es"} | ({stem[:-1] + "ies"} if stem.endswith("y") else set())
    candidates |= {k for k, v in irregular.items() if v == stem}
    found = [o for o in db.tables if snake(o.name) in candidates and o is not t]
    same_schema = [o for o in found if (o.schema or "") == (t.schema or "")]
    return (same_schema or found or [None])[0]


def _single_key(t: Table) -> Optional[str]:
    if len(t.primary_key) == 1:
        return t.primary_key[0]
    return next((u[0] for u in t.unique_keys() if len(u) == 1), None)


def _compatible(a: Column, b: Column) -> bool:
    fa, fb = a.type.family, b.type.family
    return fa == fb or (fa in TEXT_FAMILIES and fb in TEXT_FAMILIES)


@check("schema.missing_foreign_key")
def missing_foreign_key(db, profile, params):
    if not profile.system_of_record:
        return
    for t in tables_in_scope(db, profile, params):
        if t.partition_columns and db.dialect == "mysql":
            continue  # InnoDB does not support foreign keys on partitioned tables (INT-002 engine note)
        fk_cols = fk_column_names(t)
        names = {c.name.lower() for c in t.columns}
        for c in t.columns:
            low = c.name.lower()
            if low in fk_cols or matches(c.name, params["exclude_column_patterns"]):
                continue
            if t.primary_key == [c.name] and singular(snake(t.name)) == "_".join(tokens(c.name)[:-1]):
                continue
            stems = _reference_stems(c.name, params)
            if not stems or f"{'_'.join(tokens(c.name)[:-1])}_type" in names:
                continue
            for stem, role_qualified in stems:
                parent = _find_parent(db, t, stem, params["irregular_plurals"])
                key = _single_key(parent) if parent else None
                pk_col = parent.column(key) if key else None
                if pk_col is None or not _compatible(c, pk_col):
                    continue
                confidence = params["role_confidence"] if role_qualified else params["base_confidence"]
                detail = f"Column {t.fqname}.{c.name} ({c.data_type}) looks like a reference to " \
                         f"{parent.fqname}.{key} ({pk_col.data_type}) but no foreign key is declared."
                verified = _verify_reference(db, profile, params, t, c.name, parent, key)
                if verified is not None:
                    total, matched = verified
                    if total >= params["min_verify_rows"]:
                        ratio = matched / total
                        if ratio < params["min_match_ratio"]:
                            break  # the values do not behave like references to this table
                        detail += f" In {total} sampled non-null rows, {matched} ({ratio:.1%}) exist in the parent."
                        if ratio >= params["strong_match_ratio"]:
                            confidence = params["verified_confidence"]
                yield Hit(table=t.fqname, column=c.name, evidence=detail, confidence=confidence,
                          vars={"ref_table": parent.fqname, "ref_column": key},
                          fix=make_fix("add_foreign_key", t, c.name, columns=[c.name], ref_table=parent.fqname,
                                       ref_columns=[key]))
                break


def _verify_reference(db, profile, params, t, column, parent, key) -> Optional[tuple[int, int]]:
    if db.data is None:
        return None
    q = db.data.quote
    rows = run_query(db, f"SELECT COUNT(*), COALESCE(SUM(CASE WHEN EXISTS (SELECT 1 FROM {qualified(db, parent)} p "
                         f"WHERE p.{q(key)} = s.v) THEN 1 ELSE 0 END), 0) FROM (SELECT {q(column)} AS v FROM "
                         f"{qualified(db, t)} WHERE {q(column)} IS NOT NULL LIMIT {sample_limit(profile, params)}) s")
    return (int(rows[0][0]), int(rows[0][1] or 0)) if rows else None


def _type_label(c: Column) -> str:
    return re.sub(r"\s+", " ", c.data_type.strip().lower())


def _width_key(c: Column) -> tuple:
    ti = c.type
    family = "text" if ti.family in TEXT_FAMILIES else ti.family
    return family, ti.bits, ti.length, ti.precision, ti.scale, is_unsigned(c)


def _plain_type(c: Column, serial_map: dict) -> str:
    raw = re.sub(r"\s*auto_increment", "", c.data_type.strip(), flags=re.I)
    return serial_map.get(raw.lower(), raw)


@check("schema.fk_type_mismatch")
def fk_type_mismatch(db, profile, params):
    for t in tables_in_scope(db, profile, params):
        for fk in t.foreign_keys:
            parent = ref_target(db, t, fk)
            if parent is None or len(fk.columns) != len(fk.ref_columns):
                continue
            for child_name, parent_name in zip(fk.columns, fk.ref_columns):
                child, target = t.column(child_name), parent.column(parent_name)
                if child is None or target is None or child.type.family == "other" or target.type.family == "other":
                    continue
                if _width_key(child) != _width_key(target):
                    new_type = _plain_type(target, params["serial_types"])
                    yield Hit(table=t.fqname, column=child.name,
                              evidence=f"{t.fqname}.{child.name} is {_type_label(child)} but references "
                                       f"{parent.fqname}.{target.name} of type {_type_label(target)}.",
                              vars={"ref_table": parent.fqname, "ref_column": target.name, "problem": "type"},
                              fix=make_fix("alter_column_type", t, child.name, new_type=new_type))
                elif child.type.family in TEXT_FAMILIES and child.charset and target.charset and (
                        child.charset.lower() != target.charset.lower()
                        or (child.collation or "").lower() != (target.collation or "").lower()):
                    yield Hit(table=t.fqname, column=child.name,
                              evidence=f"{t.fqname}.{child.name} uses {child.charset}/{child.collation} but references "
                                       f"{parent.fqname}.{target.name} using {target.charset}/{target.collation}.",
                              vars={"ref_table": parent.fqname, "ref_column": target.name, "problem": "collation"},
                              fix=manual(t, "Convert both columns to the same character set and collation.", child.name))


@check("schema.nullable_primary_key")
def nullable_primary_key(db, profile, params):
    for t in iter_tables(db, profile):
        for name in t.primary_key:
            c = t.column(name)
            if c is not None and c.nullable:
                yield Hit(table=t.fqname, column=c.name,
                          evidence=f"Primary key column {t.fqname}.{c.name} is declared nullable.",
                          fix=make_fix("set_not_null", t, c.name))


@check("schema.composite_fk_partially_nullable")
def composite_fk_partially_nullable(db, profile, params):
    for t in tables_in_scope(db, profile, params):
        for fk in t.foreign_keys:
            cols = [t.column(c) for c in fk.columns]
            if len(cols) < 2 or any(c is None for c in cols):
                continue
            nullable = [c.name for c in cols if c.nullable]
            if nullable and len(nullable) < len(cols):
                yield Hit(table=t.fqname, column=nullable[0],
                          evidence=f"Composite foreign key ({', '.join(fk.columns)}) to {fk.ref_table} has nullable "
                                   f"column(s) {', '.join(nullable)}. Under MATCH SIMPLE a NULL in any column skips the check.",
                          fix=make_fix("set_not_null", t, nullable[0]))


@check("schema.nullable_fk_without_nulls")
def nullable_fk_without_nulls(db, profile, params):
    for t in tables_in_scope(db, profile, params):
        for fk in t.foreign_keys:
            for name in fk.columns:
                c = t.column(name)
                if c is None or not c.nullable:
                    continue
                q = db.data.quote
                rows = run_query(db, f"SELECT COUNT(*), COUNT({q(c.name)}) FROM {qualified(db, t)}")
                if not rows or int(rows[0][0]) < params["min_rows"] or int(rows[0][0]) != int(rows[0][1]):
                    continue
                yield Hit(table=t.fqname, column=c.name,
                          evidence=f"Foreign key column {t.fqname}.{c.name} is nullable but all {int(rows[0][0])} rows "
                                   f"have a value.",
                          fix=make_fix("set_not_null", t, c.name))


@check("schema.fk_no_explicit_actions")
def fk_no_explicit_actions(db, profile, params):
    for t in tables_in_scope(db, profile, params):
        for fk in t.foreign_keys:
            missing = [label for label, value in (("ON DELETE", fk.on_delete), ("ON UPDATE", fk.on_update)) if not value]
            if missing:
                yield Hit(table=t.fqname, column=fk.columns[0] if fk.columns else None,
                          evidence=f"Foreign key {fk.name or '(unnamed)'} on ({', '.join(fk.columns)}) to {fk.ref_table} "
                                   f"does not state {' or '.join(missing)}.",
                          vars={"fk": fk.name or ",".join(fk.columns)},
                          fix=manual(t, "Choose the delete and update action for this relationship.",
                                     fk.columns[0] if fk.columns else None))


# ----------------------------------------------------------------------------------------------------------------
# Normalization
# ----------------------------------------------------------------------------------------------------------------
@check("schema.repeating_columns")
def repeating_columns(db, profile, params):
    if not profile.system_of_record:
        return
    for t in tables_in_scope(db, profile, params):
        groups: dict[str, list[tuple[int, Column]]] = defaultdict(list)
        for c in t.columns:
            m = re.match(r"^(.*?[a-z])_?(\d+)$", snake(c.name))
            if m:
                groups[m.group(1).rstrip("_")].append((int(m.group(2)), c))
        for base, items in groups.items():
            numbers = sorted(n for n, _ in items)
            if len(items) < params["min_group"] or len(base) < params["min_base_length"] \
                    or base in params["exempt_bases"]:
                continue
            if numbers[0] not in (0, 1) or numbers != list(range(numbers[0], numbers[0] + len(numbers))):
                continue
            if len({c.type.family for _, c in items}) != 1:
                continue
            names = [c.name for _, c in sorted(items, key=lambda x: x[0])]
            yield Hit(table=t.fqname, column=names[0], vars={"group": base},
                      evidence=f"Numbered column group in {t.fqname}: {', '.join(names)}.", data={"columns": names},
                      fix=manual(t, f"Move {', '.join(names)} to a child table with one row per value.", names[0]))


@check("schema.delimited_list")
def delimited_list(db, profile, params):
    if not profile.system_of_record:
        return
    atomic = params["atomic_list_pattern"]
    for t in tables_in_scope(db, profile, params):
        for c in t.columns:
            if c.type.family not in TEXT_FAMILIES or (c.type.length or 9999) < params["min_length"]:
                continue
            words = set(tokens(c.name))
            if words & set(params["exclude_tokens"]):
                continue
            named = matches(c.name, params["name_patterns"])
            values = text_values(sample(db, profile, params, t, c.name) or [])
            if db.data is None or len(values) < params["min_samples"]:
                if named:
                    yield Hit(table=t.fqname, column=c.name, kind="context_dependent",
                              confidence=params["name_only_confidence"],
                              evidence=f"Column {t.fqname}.{c.name} ({c.data_type}) has a list-like name; "
                                       f"{_unverified(db, values, params)}",
                              fix=manual(t, f"Check the contents of {c.name}; if it holds lists, move them to a child "
                                            f"table.", c.name))
                continue
            usable = [v for v in values if not re.match(params["thousands_pattern"], v.strip())]
            ratio = share(usable, atomic)
            if ratio >= params["min_ratio"]:
                yield Hit(table=t.fqname, column=c.name, kind="confirmed_defect", confidence=params["verified_confidence"],
                          evidence=f"{ratio:.0%} of {len(usable)} sampled values in {t.fqname}.{c.name} are delimited "
                                   f"lists of short tokens.",
                          fix=manual(t, f"Move the list in {c.name} to a child table with one row per value.", c.name))


@check("schema.redundant_attribute")
def redundant_attribute(db, profile, params):
    generic = {x.lower() for x in params["generic_columns"]}
    audit = {n.lower() for group in profile.audit_columns for n in group}
    excluded = {x.lower() for x in params["exclude_tokens"]}
    for t in tables_in_scope(db, profile, params):
        keys = key_column_names(t)
        for fk in t.foreign_keys:
            parent = ref_target(db, t, fk)
            if parent is None or len(fk.columns) != 1 or parent is t:
                continue
            parent_keys = key_column_names(parent)
            for c in t.columns:
                low = c.name.lower()
                if low in keys or low in generic or low in audit or set(tokens(low)) & excluded:
                    continue
                other = parent.column(c.name)
                if other is None or low in parent_keys or c.is_generated or not _compatible(c, other):
                    continue
                confidence = params["base_confidence"]
                detail = f"{c.name} is stored in both {t.fqname} and its parent {parent.fqname}, related through " \
                         f"{fk.columns[0]}."
                ratio_info = _equal_ratio(db, profile, params, t, c.name, fk, parent)
                if ratio_info is not None and ratio_info[0] >= params["min_rows"]:
                    total, equal = ratio_info
                    ratio = equal / total
                    if ratio < params["min_equal_ratio"]:
                        continue  # the child value differs, so it is a snapshot or a different fact
                    detail += f" {equal} of {total} sampled joined rows hold the same value ({ratio:.1%})."
                    confidence = params["verified_confidence"]
                yield Hit(table=t.fqname, column=c.name, evidence=detail, confidence=confidence,
                          vars={"parent": parent.fqname},
                          fix=manual(t, f"Keep {c.name} in {parent.fqname} only, or maintain the copy through one "
                                        f"controlled mechanism and record why.", c.name))


def _equal_ratio(db, profile, params, t, column, fk, parent) -> Optional[tuple[int, int]]:
    if db.data is None:
        return None
    q = db.data.quote
    rows = run_query(db, f"SELECT COUNT(*), COALESCE(SUM(CASE WHEN c.v = p.{q(column)} THEN 1 ELSE 0 END), 0) FROM "
                         f"(SELECT {q(fk.columns[0])} AS k, {q(column)} AS v FROM {qualified(db, t)} "
                         f"WHERE {q(column)} IS NOT NULL LIMIT {sample_limit(profile, params)}) c "
                         f"JOIN {qualified(db, parent)} p ON c.k = p.{q(fk.ref_columns[0])}")
    return (int(rows[0][0]), int(rows[0][1] or 0)) if rows else None


@check("schema.functional_dependency")
def functional_dependency(db, profile, params):
    for t in tables_in_scope(db, profile, params):
        unique_single = {u[0].lower() for u in t.unique_keys() if len(u) == 1}
        fk_cols = fk_column_names(t)
        for det in t.columns:
            words = tokens(det.name)
            if len(words) < 2 or words[-1] not in params["determinant_suffixes"] or det.name.lower() in unique_single:
                continue
            prefix = "_".join(words[:-1]) + "_"
            for dep in t.columns:
                low = snake(dep.name)
                if dep is det or not low.startswith(prefix) or dep.type.family not in TEXT_FAMILIES:
                    continue
                if low in fk_cols or set(tokens(low)) & set(params["exclude_tokens"]):
                    continue
                result = _dependency(db, profile, params, t, det.name, dep.name)
                if result is None:
                    continue
                determinants, rows = result
                yield Hit(table=t.fqname, column=dep.name, vars={"determinant": det.name},
                          confidence=params["verified_confidence"],
                          evidence=f"In {rows} sampled rows of {t.fqname}, each of {determinants} {det.name} values maps "
                                   f"to one {dep.name} value, so {dep.name} depends on {det.name}, not on the key.",
                          fix=manual(t, f"Move {dep.name} to the table identified by {det.name} and join to it.", dep.name))


def _dependency(db, profile, params, t, det, dep) -> Optional[tuple[int, int]]:
    q = db.data.quote
    rows = run_query(db, f"SELECT {q(det)}, {q(dep)} FROM {qualified(db, t)} WHERE {q(det)} IS NOT NULL AND {q(dep)} "
                         f"IS NOT NULL LIMIT {sample_limit(profile, params)}")
    if not rows:
        return None
    seen: dict[Any, set] = defaultdict(set)
    for a, b in rows:
        seen[a].add(b)
    if len(seen) < params["min_determinants"] or len(rows) < len(seen) * params["min_repeat"]:
        return None
    conflicting = sum(1 for v in seen.values() if len(v) > 1)
    if conflicting / len(seen) > params["max_violation_ratio"]:
        return None
    if len({next(iter(v)) for v in seen.values()}) < 2:
        return None
    return len(seen), len(rows)


# ----------------------------------------------------------------------------------------------------------------
# Data types
# ----------------------------------------------------------------------------------------------------------------
@check("schema.money_float")
def money_float(db, profile, params):
    for t in tables_in_scope(db, profile, params):
        for c in t.columns:
            if c.type.family == "float" and is_money(c, profile, params):
                yield Hit(table=t.fqname, column=c.name, evidence=f"{t.fqname}.{c.name} is {c.data_type}, a binary "
                          f"floating-point type, and its name indicates a monetary value.",
                          fix=make_fix("alter_column_type", t, c.name, new_type=params["target_type"]))


@check("schema.money_proprietary")
def money_proprietary(db, profile, params):
    for t in tables_in_scope(db, profile, params):
        for c in t.columns:
            if c.type.family == "money":
                yield Hit(table=t.fqname, column=c.name, evidence=f"{t.fqname}.{c.name} uses the proprietary type "
                          f"{c.data_type}.", fix=make_fix("alter_column_type", t, c.name, new_type=params["target_type"]))


@check("schema.money_low_scale")
def money_low_scale(db, profile, params):
    for t in tables_in_scope(db, profile, params):
        for c in t.columns:
            ti = c.type
            if ti.family != "decimal" or ti.scale is None or ti.scale >= params["min_scale"]:
                continue
            if not is_money(c, profile, params):
                continue
            precision = (ti.precision or 18) + (params["min_scale"] - ti.scale)
            yield Hit(table=t.fqname, column=c.name,
                      evidence=f"{t.fqname}.{c.name} is {c.data_type}, with scale {ti.scale}, below {params['min_scale']}.",
                      fix=make_fix("alter_column_type", t, c.name, new_type=f"decimal({precision},{params['min_scale']})"))


@check("schema.money_multicurrency_scale")
def money_multicurrency_scale(db, profile, params):
    reason = multi_currency(db, profile, params)
    if not reason:
        return
    for t in tables_in_scope(db, profile, params):
        for c in t.columns:
            ti = c.type
            if ti.family != "decimal" or ti.scale is None or ti.scale >= params["min_scale"]:
                continue
            if not is_money(c, profile, params):
                continue
            precision = (ti.precision or 18) + (params["min_scale"] - ti.scale)
            yield Hit(table=t.fqname, column=c.name,
                      evidence=f"{t.fqname}.{c.name} is {c.data_type}. Multi-currency context: {reason}.",
                      fix=make_fix("alter_column_type", t, c.name, new_type=f"decimal({precision},{params['min_scale']})"))


@check("schema.amount_without_currency")
def amount_without_currency(db, profile, params):
    reason = multi_currency(db, profile, params)
    if not reason:
        return
    patterns = params["currency_column_patterns"]
    for t in tables_in_scope(db, profile, params):
        amounts = [c.name for c in t.columns if c.type.family in ("decimal", "float", "money")
                   and is_money(c, profile, params)]
        if not amounts or any(matches(c.name, patterns) for c in t.columns):
            continue
        parents = [ref_target(db, t, fk) for fk in t.foreign_keys]
        if any(p is not None and any(matches(c.name, patterns) for c in p.columns) for p in parents):
            continue  # the currency is carried by the parent row, as with order lines and orders
        yield Hit(table=t.fqname, column=amounts[0],
                  evidence=f"{t.fqname} has amount column(s) {', '.join(amounts)} but neither it nor a referenced "
                           f"parent has a currency column. Multi-currency context: {reason}.",
                  data={"columns": amounts},
                  fix=make_fix("add_column", t, params["currency_column"], type=params["currency_type"], nullable=True,
                               default=None))


@check("schema.timestamp_without_zone")
def timestamp_without_zone(db, profile, params):
    if db.dialect in params["exempt_dialects"]:
        return
    for t in tables_in_scope(db, profile, params):
        for c in t.columns:
            if c.type.family != "datetime" or not matches(c.name, params["instant_patterns"]):
                continue
            base = c.data_type.strip().lower().split("(")[0].strip()
            if db.dialect in params["utc_normalizing"] and base in params["utc_normalizing"][db.dialect]:
                continue
            if c.comment and re.search(r"\butc\b", c.comment, re.I):
                continue
            target = by_dialect(params["target_types"], db)
            fix = make_fix("alter_column_type", t, c.name, new_type=target) if target else \
                manual(t, f"Document the UTC convention for {c.name}, or move it to a UTC-normalizing type.", c.name)
            yield Hit(table=t.fqname, column=c.name, fix=fix,
                      evidence=f"{t.fqname}.{c.name} is {c.data_type}, which stores no time zone, and its name "
                               f"indicates an instant.")


@check("schema.date_as_text")
def date_as_text(db, profile, params):
    if db.dialect in params["exempt_dialects"]:
        return
    for t in tables_in_scope(db, profile, params):
        for c in t.columns:
            if c.type.family not in TEXT_FAMILIES or not matches(c.name, params["name_patterns"]) \
                    or set(tokens(c.name)) & set(params["exclude_tokens"]):
                continue
            is_instant = matches(c.name, params["instant_patterns"])
            new_type = by_dialect(params["instant_types" if is_instant else "date_types"], db)
            fix = make_fix("alter_column_type", t, c.name, new_type=new_type)
            values = text_values(sample(db, profile, params, t, c.name) or [])
            if db.data is None or len(values) < params["min_samples"]:
                yield Hit(table=t.fqname, column=c.name, kind="context_dependent",
                          confidence=params["name_only_confidence"], fix=fix,
                          evidence=f"{t.fqname}.{c.name} is {c.data_type} and its name indicates a date; "
                                   f"{_unverified(db, values, params)}")
                continue
            ratio = share(values, params["value_pattern"])
            if ratio >= params["min_ratio"]:
                yield Hit(table=t.fqname, column=c.name, kind="confirmed_defect",
                          confidence=params["verified_confidence"], fix=fix,
                          evidence=f"{ratio:.0%} of {len(values)} sampled values in {t.fqname}.{c.name} "
                                   f"({c.data_type}) are dates or date-times.")


@check("schema.number_as_text")
def number_as_text(db, profile, params):
    for t in tables_in_scope(db, profile, params):
        for c in t.columns:
            words = set(tokens(c.name))
            if c.type.family not in TEXT_FAMILIES or words & set(params["exclude_tokens"]):
                continue
            if not words & (set(params["quantity_tokens"]) | {p.lower() for p in profile.money_name_patterns}):
                continue
            values = text_values(sample(db, profile, params, t, c.name) or [])
            if len(values) < params["min_samples"]:
                continue
            if share(values, params["number_pattern"]) < params["min_ratio"]:
                continue
            if share(values, params["leading_zero_pattern"]) > params["max_leading_zero_ratio"]:
                continue  # leading zeros mean a code, which TYP-028 says stays text
            integral = share(values, params["integer_pattern"]) >= 1.0
            new_type = params["integer_type"] if integral else params["decimal_type"]
            yield Hit(table=t.fqname, column=c.name,
                      evidence=f"All or nearly all of {len(values)} sampled values in {t.fqname}.{c.name} ({c.data_type}) "
                               f"are numeric.",
                      fix=make_fix("alter_column_type", t, c.name, new_type=new_type))


@check("schema.boolean_as_int_or_char")
def boolean_as_int_or_char(db, profile, params):
    if db.dialect in params["exempt_dialects"]:
        return
    target = by_dialect(params["target_types"], db)
    for t in tables_in_scope(db, profile, params):
        for c in t.columns:
            ti = c.type
            if not matches(c.name, params["name_patterns"]):
                continue
            if ti.family == "int":
                if db.dialect in params["tinyint_accepted_dialects"] and ti.bits == 8:
                    continue  # TYP-021 engine note accepts tinyint on MySQL
            elif not (ti.family in TEXT_FAMILIES and (ti.length or 99) <= params["max_char_length"]):
                continue
            values = sample(db, profile, params, t, c.name)
            if values is not None and len({str(v).strip().lower() for v in values}) > 2:
                continue
            fix = make_fix("alter_column_type", t, c.name, new_type=target) if ti.family == "int" else \
                manual(t, f"Map the stored codes in {c.name} to true and false, then change the type to {target}.", c.name)
            yield Hit(table=t.fqname, column=c.name, fix=fix, evidence=f"{t.fqname}.{c.name} is {c.data_type} but its "
                      f"name indicates a yes-or-no attribute.")


@check("schema.enum_prefer_lookup")
def enum_prefer_lookup(db, profile, params):
    for t in tables_in_scope(db, profile, params):
        for c in t.columns:
            if c.type.family == "enum" and len(c.type.values) >= params["min_values"]:
                yield Hit(table=t.fqname, column=c.name, evidence=f"{t.fqname}.{c.name} is a native enumeration with "
                          f"{len(c.type.values)} values.",
                          fix=manual(t, f"Decide whether the values of {c.name} can change; if so, use a reference table.",
                                     c.name))


@check("schema.json_in_text")
def json_in_text(db, profile, params):
    if db.dialect in params["exempt_dialects"]:
        return
    target = by_dialect(params["target_types"], db)
    for t in tables_in_scope(db, profile, params):
        for c in t.columns:
            if c.type.family != "text":
                continue
            explicit = matches(c.name, params["explicit_patterns"])
            candidate = explicit or matches(c.name, params["likely_patterns"])
            if not candidate:
                continue
            fix = make_fix("alter_column_type", t, c.name, new_type=target)
            values = text_values(sample(db, profile, params, t, c.name) or [])
            if db.data is None or len(values) < params["min_samples"]:
                if explicit:
                    yield Hit(table=t.fqname, column=c.name, kind="context_dependent", fix=fix,
                              confidence=params["name_only_confidence"],
                              evidence=f"{t.fqname}.{c.name} is {c.data_type} and its name indicates JSON; "
                                       f"{_unverified(db, values, params)}")
                continue
            parsed = sum(1 for v in values if _is_json(v))
            ratio = parsed / len(values)
            if ratio >= params["min_ratio"]:
                yield Hit(table=t.fqname, column=c.name, kind="confirmed_defect", fix=fix,
                          confidence=params["verified_confidence"],
                          evidence=f"{ratio:.0%} of {len(values)} sampled values in {t.fqname}.{c.name} parse as JSON "
                                   f"documents.")


def _is_json(value: str) -> bool:
    text = value.strip()
    if not text or text[0] not in "{[":
        return False
    try:
        json.loads(text)
    except (ValueError, RecursionError):
        return False
    return True


@check("schema.uuid_as_text")
def uuid_as_text(db, profile, params):
    target = by_dialect(params["target_types"], db)
    for t in tables_in_scope(db, profile, params):
        for c in t.columns:
            ti = c.type
            if ti.family not in TEXT_FAMILIES or (ti.length is not None and ti.length not in params["lengths"]):
                continue
            named = matches(c.name, params["name_patterns"])
            maybe = matches(c.name, params["candidate_patterns"])
            if not named and not (maybe and ti.length in params["lengths"]):
                continue
            fix = make_fix("alter_column_type", t, c.name, new_type=target) if target else \
                manual(t, f"Store {c.name} in binary(16) or the engine's native UUID form, and update readers.", c.name)
            values = text_values(sample(db, profile, params, t, c.name) or [])
            if len(values) >= params["min_samples"]:
                ratio = share(values, params["value_pattern"])
                if ratio >= params["min_ratio"]:
                    yield Hit(table=t.fqname, column=c.name, kind="confirmed_defect", fix=fix,
                              confidence=params["verified_confidence"],
                              evidence=f"{ratio:.0%} of {len(values)} sampled values in {t.fqname}.{c.name} "
                                       f"({c.data_type}) are UUIDs stored as text.")
            elif named:
                yield Hit(table=t.fqname, column=c.name, kind="context_dependent", fix=fix,
                          confidence=params["name_only_confidence"],
                          evidence=f"{t.fqname}.{c.name} is {c.data_type} and its name indicates a UUID; "
                                   f"{_unverified(db, values, params)}")


@check("schema.key_32bit")
def key_32bit(db, profile, params):
    for t in tables_in_scope(db, profile, params):
        if len(t.primary_key) != 1 or (t.row_count or 0) and t.row_count <= params["bounded_lookup_rows"]:
            continue
        if matches(t.name, params["lookup_name_patterns"]):
            continue
        c = t.column(t.primary_key[0])
        if c is None or c.type.family != "int" or (c.type.bits or 64) > 32 or not is_generated(c):
            continue
        new_type = "bigint unsigned" if is_unsigned(c) else "bigint"
        yield Hit(table=t.fqname, column=c.name, evidence=f"Generated primary key {t.fqname}.{c.name} is {c.data_type} "
                  f"({c.type.bits}-bit).", fix=make_fix("alter_column_type", t, c.name, new_type=new_type))


@check("schema.nullable_by_default")
def nullable_by_default(db, profile, params):
    for t in tables_in_scope(db, profile, params):
        keys = key_column_names(t)
        body = [c for c in t.columns if c.name.lower() not in keys and not c.is_generated]
        if len(body) < params["min_columns"]:
            continue
        nullable = [c.name for c in body if c.nullable]
        ratio = len(nullable) / len(body)
        if ratio >= params["min_ratio"]:
            yield Hit(table=t.fqname, data={"columns": nullable},
                      evidence=f"{len(nullable)} of {len(body)} non-key columns in {t.fqname} are nullable ({ratio:.0%}).",
                      fix=manual(t, "Review which columns have a documented meaning for NULL and set the rest NOT NULL."))


@check("schema.same_name_type_mismatch")
def same_name_type_mismatch(db, profile, params):
    generic = {x.lower() for x in params["generic_columns"]}
    seen: dict[str, list[tuple[Table, Column]]] = defaultdict(list)
    for t in tables_in_scope(db, profile, params):
        for c in t.columns:
            if c.name.lower() not in generic and c.type.family != "other":
                seen[c.name.lower()].append((t, c))

    def signature(c: Column) -> tuple:
        ti = c.type
        family = "text" if ti.family in TEXT_FAMILIES else ti.family
        length = ti.length if params["compare_text_length"] and family == "text" else None
        return family, ti.bits, length, is_unsigned(c)

    for name, items in seen.items():
        if len(items) < params["min_tables"] or not matches(name, params["name_patterns"]):
            continue
        counts = Counter(signature(c) for _, c in items)
        if len(counts) < 2:
            continue
        common, top = counts.most_common(1)[0]
        tie = sum(1 for v in counts.values() if v == top) > 1
        reference = next(c for _, c in items if signature(c) == common)
        for t, c in items:
            if signature(c) == common and not tie:
                continue
            fix = manual(t, f"Decide the single type for {c.name} across all tables.", c.name) if tie else \
                make_fix("alter_column_type", t, c.name, new_type=_plain_type(reference, params["serial_types"]))
            yield Hit(table=t.fqname, column=c.name, fix=fix,
                      vars={"usual_type": reference.data_type},
                      evidence=f"{t.fqname}.{c.name} is {c.data_type}, while {name} is {reference.data_type} in "
                               f"{top} of {len(items)} tables.")


@check("schema.polymorphic_reference")
def polymorphic_reference(db, profile, params):
    for t in tables_in_scope(db, profile, params):
        names = {snake(c.name): c for c in t.columns}
        fks = fk_column_names(t)
        for low, c in names.items():
            m = re.match(params["id_pattern"], low)
            if not m or c.name.lower() in fks:
                continue
            base = m.group(1)
            partner = next((names[f"{base}_{s}"] for s in params["type_suffixes"] if f"{base}_{s}" in names), None)
            if partner is None or partner.type.family not in TEXT_FAMILIES + ("enum", "int"):
                continue
            if _find_parent(db, t, base, params["irregular_plurals"]) is not None:
                continue  # the id resolves to a real table, so the type column classifies it
            yield Hit(table=t.fqname, column=c.name, vars={"type_column": partner.name},
                      evidence=f"{t.fqname} pairs {partner.name} with {c.name}, and no table named for {base} exists.",
                      fix=manual(t, f"Replace {partner.name} and {c.name} with one nullable foreign key per parent, or "
                                    f"an exclusive supertype.", c.name))


@check("schema.eav_shape")
def eav_shape(db, profile, params):
    for t in tables_in_scope(db, profile, params):
        low = {snake(c.name): c for c in t.columns}
        keys = [n for n in low if matches(n, params["attribute_patterns"])]
        values = [n for n in low if matches(n, params["value_patterns"])]
        if not keys or not values or len(t.columns) > params["max_columns"]:
            continue
        entity = [n for n in low if n.endswith("_id") and n not in keys and low[n].name not in t.primary_key]
        if not entity and not t.foreign_keys:
            continue  # a plain key and value table is configuration, not EAV
        yield Hit(table=t.fqname, column=low[values[0]].name, vars={"attribute": low[keys[0]].name},
                  evidence=f"{t.fqname} has attribute column {low[keys[0]].name}, value column {low[values[0]].name} and "
                           f"entity reference(s) {', '.join(entity) or 'through a foreign key'}.",
                  fix=manual(t, "Promote attributes that are filtered, aggregated, keyed or monetary to typed columns."))


@check("schema.god_table")
def god_table(db, profile, params):
    for t in tables_in_scope(db, profile, params):
        if len(t.columns) > params["max_columns"]:
            yield Hit(table=t.fqname, evidence=f"{t.fqname} has {len(t.columns)} columns; the limit is {params['max_columns']}.",
                      fix=manual(t, "Review the table for independent groups of attributes that belong in other tables."))


@check("schema.charset_mixture")
def charset_mixture(db, profile, params):
    """Non-Unicode encodings, and tables that differ from the dominant character set or collation."""
    non_unicode = {x.lower() for x in params["non_unicode_charsets"]}
    usage: list[tuple[Table, Optional[Column], str, Optional[str]]] = []
    for t in tables_in_scope(db, profile, params):
        for c in t.columns:
            if c.type.family in TEXT_FAMILIES:
                charset = c.charset or t.charset
                if charset:
                    usage.append((t, c, charset.lower(), (c.collation or t.collation or "").lower() or None))
    if not usage:
        return
    dominant_charset = Counter(u[2] for u in usage).most_common(1)[0][0]
    dominant_collation = Counter(u[3] for u in usage if u[3]).most_common(1)
    dominant_collation = dominant_collation[0][0] if dominant_collation else None
    reported: set[tuple[str, str]] = set()
    for t, c, charset, collation in usage:
        if charset in non_unicode and (t.fqname, "unicode") not in reported:
            reported.add((t.fqname, "unicode"))
            yield Hit(table=t.fqname, column=c.name, vars={"problem": "non-Unicode"},
                      evidence=f"{t.fqname} has text stored in non-Unicode encoding {charset}.",
                      fix=manual(t, "Convert the table to the database's approved Unicode encoding."))
        if charset != dominant_charset and charset not in non_unicode and (t.fqname, "charset") not in reported:
            reported.add((t.fqname, "charset"))
            yield Hit(table=t.fqname, column=c.name, vars={"problem": "charset"},
                      evidence=f"{t.fqname} uses character set {charset}, while most text columns use {dominant_charset}.",
                      fix=manual(t, f"Convert the table to {dominant_charset}."))
        if collation and dominant_collation and collation != dominant_collation \
                and charset == dominant_charset and (t.fqname, "collation") not in reported:
            reported.add((t.fqname, "collation"))
            yield Hit(table=t.fqname, column=c.name, vars={"problem": "collation"},
                      evidence=f"{t.fqname} uses collation {collation}, while most text columns use {dominant_collation}.",
                      fix=manual(t, f"Convert the table to collation {dominant_collation}."))


def _is_association(t: Table) -> bool:
    return len(t.foreign_keys) >= 2 and len(t.columns) <= len(fk_column_names(t)) + 1 + len(t.primary_key)


@check("schema.missing_audit_columns")
def missing_audit_columns(db, profile, params):
    if not profile.system_of_record:
        return
    for t in tables_in_scope(db, profile, params):
        if profile.is_audit_exempt(t.name) or (params["exempt_association_tables"] and _is_association(t)):
            continue
        for group in profile.audit_columns:
            if not group or any(t.has_column(n) for n in group):
                continue
            name = group[0]
            is_time = name.endswith(("_at", "_on"))
            yield Hit(table=t.fqname, column=name,
                      evidence=f"{t.fqname} has none of the required audit column(s): {', '.join(group)}.",
                      fix=make_fix("add_column", t, name, type=by_dialect(params["time_types"], db) if is_time else params["actor_type"],
                                   nullable=True, default=params["time_default"] if is_time else None))


@check("schema.table_no_relationships")
def table_no_relationships(db, profile, params):
    if len(db.tables) < params["min_tables"]:
        return
    for t in tables_in_scope(db, profile, params):
        if t.foreign_keys or db.referencing(t):
            continue
        if any(len(w := tokens(c.name)) > 1 and w[-1] in params["reference_suffixes"] for c in t.columns):
            continue  # reference-like columns are reported by the missing foreign key rule
        yield Hit(table=t.fqname, evidence=f"{t.fqname} has no declared foreign keys in either direction and no "
                  f"reference-like columns.", fix=manual(t, "Confirm whether the table is standalone, or retire it."))


@check("schema.status_without_check")
def status_without_check(db, profile, params):
    for t in tables_in_scope(db, profile, params):
        fks = fk_column_names(t)
        for c in t.columns:
            if c.type.family not in TEXT_FAMILIES or not matches(c.name, params["name_patterns"]) or c.name.lower() in fks:
                continue
            if any(c.name.lower() in (ck.expression or "").lower() for ck in t.checks):
                continue
            values = sample(db, profile, params, t, c.name)
            if values is None:
                yield Hit(table=t.fqname, column=c.name, confidence=params["name_only_confidence"],
                          evidence=f"{t.fqname}.{c.name} ({c.data_type}) has no CHECK constraint or foreign key.",
                          fix=manual(t, f"Constrain {c.name} with a CHECK or a reference table.", c.name))
                continue
            distinct = sorted({str(v) for v in values})
            if not distinct or len(distinct) > params["max_distinct"] \
                    or not all(re.match(params["value_pattern"], v) for v in distinct):
                continue
            quoted = ", ".join("'" + v.replace("'", "''") + "'" for v in distinct)
            yield Hit(table=t.fqname, column=c.name, confidence=params["verified_confidence"],
                      evidence=f"{t.fqname}.{c.name} has {len(distinct)} distinct values in {len(values)} sampled rows and "
                               f"no CHECK constraint or foreign key.",
                      fix=make_fix("add_check", t, c.name, expression=f"{c.name} IN ({quoted})",
                                   name=f"check_{t.name}_{c.name}"))


@check("schema.unbounded_varchar")
def unbounded_varchar(db, profile, params):
    for t in tables_in_scope(db, profile, params):
        columns = []
        for c in t.columns:
            base = c.data_type.strip().lower().split("(")[0].strip()
            unbounded = base in params["varchar_types"] and (c.type.length is None)
            if unbounded and not set(tokens(c.name)) & set(params["free_text_tokens"]):
                columns.append(c.name)
        if columns:
            yield Hit(table=t.fqname, data={"columns": columns},
                      evidence=f"{t.fqname} has unbounded varchar column(s) with no stated reason: {', '.join(columns)}.",
                      fix=manual(t, "Record each length as a business limit or a storage choice, or add a content rule."))


# ----------------------------------------------------------------------------------------------------------------
# Naming
# ----------------------------------------------------------------------------------------------------------------
def _identifiers(db, profile, params) -> Iterator[tuple[Table, Optional[Column], str]]:
    for t in tables_in_scope(db, profile, params):
        yield t, None, t.name
        for c in t.columns:
            yield t, c, c.name


def _rename(t: Table, c: Optional[Column], new_name: str) -> Fix:
    if c is not None:
        return make_fix("rename_column", t, c.name, new_name=new_name)
    return make_fix("rename_table", t, new_name=new_name)


def _where(t: Table, c: Optional[Column]) -> str:
    return f"Column {t.fqname}.{c.name}" if c is not None else f"Table {t.fqname}"


def _engines(db: Database, profile: Profile, words: dict) -> list[str]:
    selected = {e.lower() for e in profile.target_engines}
    if db.dialect in words:
        selected.add(db.dialect)
    return sorted(selected & set(words))


@check("schema.reserved_word")
def reserved_word(db, profile, params):
    words_by_engine = {k: {w.lower() for w in v} for k, v in params["reserved_words"].items()}
    engines = _engines(db, profile, words_by_engine)
    every = set().union(*(words_by_engine[e] for e in engines)) if engines else set()
    for t, c, name in _identifiers(db, profile, params):
        low = name.lower()
        hit_engines = [e for e in engines if low in words_by_engine[e]]
        if hit_engines:
            suffix = params["column_suffix"]
            if c is None:
                new_name = low + "s" if low + "s" not in every and db.table(low + "s") is None else low + params["table_suffix"]
            else:
                new_name = low + suffix
            yield Hit(table=t.fqname, column=c.name if c else None, fix=_rename(t, c, new_name),
                      vars={"identifier": name, "engines": ", ".join(hit_engines)},
                      evidence=f"{_where(t, c)} uses the name {name}, a reserved word in {', '.join(hit_engines)} "
                               f"(checked against a curated subset of each engine's list).")
    for t in tables_in_scope(db, profile, params):
        for dialect, prefixes in params["reserved_table_prefixes"].items():
            if dialect in engines or dialect == db.dialect:
                for prefix in prefixes:
                    if t.name.lower().startswith(prefix):
                        yield Hit(table=t.fqname, fix=_rename(t, None, t.name[len(prefix):]),
                                  vars={"identifier": t.name, "engines": dialect},
                                  evidence=f"Table {t.fqname} uses the reserved prefix {prefix} of {dialect}.")


@check("schema.identifier_characters")
def identifier_characters(db, profile, params):
    pattern = re.compile(params["allowed_pattern"])
    for t, c, name in _identifiers(db, profile, params):
        if not pattern.match(name):
            fixed = re.sub(r"[^A-Za-z0-9_]+", "_", name).strip("_")
            if not re.match(r"^[A-Za-z]", fixed):
                fixed = params["fallback_prefix"] + fixed
            yield Hit(table=t.fqname, column=c.name if c else None, fix=_rename(t, c, snake(fixed)),
                      vars={"identifier": name},
                      evidence=f"{_where(t, c)} is named {name!r}, which contains characters outside ASCII letters, "
                               f"digits and underscores, or does not start with a letter.")


@check("schema.identifier_case")
def identifier_case(db, profile, params):
    allowed = re.compile(params["allowed_pattern"])
    style = re.compile(params["style_pattern"])
    for t, c, name in _identifiers(db, profile, params):
        if allowed.match(name) and not style.match(name):
            yield Hit(table=t.fqname, column=c.name if c else None, fix=_rename(t, c, snake(name)),
                      vars={"identifier": name},
                      evidence=f"{_where(t, c)} is named {name}, which is not lowercase with single underscores.")


@check("schema.identifier_length")
def identifier_length(db, profile, params):
    limit = int(params.get("limit") or profile.identifier_limit)
    for t, c, name in _identifiers(db, profile, params):
        if len(name) > limit:
            yield Hit(table=t.fqname, column=c.name if c else None, fix=_rename(t, c, name[:limit].rstrip("_")),
                      vars={"identifier": name},
                      evidence=f"{_where(t, c)} has a {len(name)}-character name; the limit is {limit}.")


@check("schema.identifier_quoting_collision")
def identifier_quoting_collision(db, profile, params):
    tables_by_name: dict[str, list[Table]] = defaultdict(list)
    for t in tables_in_scope(db, profile, params):
        tables_by_name[f"{(t.schema or '').lower()}.{t.name.lower()}"].append(t)
        by_lower: dict[str, list[Column]] = defaultdict(list)
        for c in t.columns:
            by_lower[c.name.lower()].append(c)
        for cols in by_lower.values():
            if len(cols) > 1:
                names = [c.name for c in cols]
                yield Hit(table=t.fqname, column=names[0], vars={"names": ",".join(names)},
                          evidence=f"Columns {', '.join(names)} in {t.fqname} differ only by letter case.",
                          fix=manual(t, "Rename the columns so they are distinct without relying on quoting.", names[0]))
    for tables in tables_by_name.values():
        if len(tables) > 1:
            names = [t.name for t in tables]
            yield Hit(table=tables[0].fqname, vars={"names": ",".join(names)},
                      evidence=f"Tables {', '.join(names)} differ only by letter case.",
                      fix=manual(tables[0], "Rename the tables so they are distinct without relying on quoting."))


def _looks_plural(word: str, params: dict) -> bool:
    if word in params["plural_words"]:
        return True
    return word.endswith("s") and not word.endswith(tuple(params["singular_endings"]))


@check("schema.table_plural_naming")
def table_plural_naming(db, profile, params):
    want_plural = profile.table_plural if params.get("plural") is None else bool(params["plural"])
    scope = list(tables_in_scope(db, profile, params))
    hits: list[Hit] = []
    uncountable = {x.lower() for x in params["uncountable_words"]}
    for t in scope:
        last = tokens(t.name)[-1] if tokens(t.name) else ""
        if not last or last in uncountable:
            continue
        plural = _looks_plural(last, params)
        if plural == want_plural:
            continue
        if want_plural:
            new_name = t.name + ("es" if re.search(r"(sh|ch|x|z)$", t.name, re.I) else "s")
            if re.search(r"[^aeiou]y$", t.name, re.I):
                new_name = t.name[:-1] + "ies"
        else:
            new_name = singular(t.name, params["irregular_plurals"])
        hits.append(Hit(table=t.fqname, fix=_rename(t, None, new_name), vars={"expected": new_name},
                        evidence=f"Table {t.fqname} is {'plural' if plural else 'singular'}; the convention is "
                                 f"{'plural' if want_plural else 'singular'}."))
    summary = f"{len(hits)} of {len(scope)} tables are {'singular' if want_plural else 'plural'}, the opposite of the " \
              f"configured convention, so the schema is uniform but differs from it."
    yield from uniform_or_each(hits, len(scope), params, summary)


@check("schema.type_prefix")
def type_prefix(db, profile, params):
    for t, c, name in _identifiers(db, profile, params):
        low = name.lower()
        prefixes = params["column_prefixes"] if c is not None else params["table_prefixes"]
        prefix = next((p for p in prefixes if low.startswith(p) and len(low) > len(p)), None)
        if prefix:
            yield Hit(table=t.fqname, column=c.name if c else None, fix=_rename(t, c, low[len(prefix):]),
                      vars={"identifier": name},
                      evidence=f"{_where(t, c)} is named {name}, with the type prefix {prefix}.")


@check("schema.pk_naming")
def pk_naming(db, profile, params):
    scope = [t for t in tables_in_scope(db, profile, params) if len(t.primary_key) == 1]
    hits: list[Hit] = []
    fk_map = {(t.name.lower(), c) for t in db.tables for c in fk_column_names(t)}
    for t in scope:
        expected = f"{singular(snake(t.name), params['irregular_plurals'])}_id"
        name = t.primary_key[0]
        if snake(name) == expected or (t.name.lower(), name.lower()) in fk_map:
            continue
        c = t.column(name)
        if c is None or not (is_generated(c) or c.type.family in ("int", "uuid")):
            continue
        hits.append(Hit(table=t.fqname, column=name, fix=make_fix("rename_column", t, name, new_name=expected),
                        vars={"expected": expected}, evidence=f"Primary key {t.fqname}.{name} is not named {expected}."))
    summary = f"{len(hits)} of {len(scope)} single-column primary keys do not use the <entity_singular>_id form; the " \
              f"naming is uniform across the database."
    yield from uniform_or_each(hits, len(scope), params, summary)


@check("schema.fk_naming")
def fk_naming(db, profile, params):
    for t in tables_in_scope(db, profile, params):
        for fk in t.foreign_keys:
            if len(fk.columns) != 1 or fk.ref_table.lower() == t.name.lower():
                continue
            name = snake(fk.columns[0])
            expected = f"{singular(snake(fk.ref_table), params['irregular_plurals'])}_id"
            ref_column = snake(fk.ref_columns[0]) if fk.ref_columns else "id"
            natural = f"{singular(snake(fk.ref_table), params['irregular_plurals'])}_{ref_column}"
            if name in (expected, ref_column, natural) or name.endswith((f"_{expected}", f"_{natural}")):
                continue
            yield Hit(table=t.fqname, column=fk.columns[0], vars={"expected": expected},
                      fix=make_fix("rename_column", t, fk.columns[0], new_name=expected),
                      evidence=f"{t.fqname}.{fk.columns[0]} references {fk.ref_table} but is not named {expected} or "
                               f"<role>_{expected}.")


@check("schema.constraint_naming")
def constraint_naming(db, profile, params):
    for t in tables_in_scope(db, profile, params):
        bad: list[str] = []
        if t.primary_key_name and t.primary_key_name.upper() not in params["exempt_names"] \
                and not re.match(params["pk_pattern"], t.primary_key_name, re.I):
            bad.append(t.primary_key_name)
        bad += [fk.name for fk in t.foreign_keys if fk.name and not re.match(params["fk_pattern"], fk.name, re.I)]
        for idx in t.indexes:
            if not idx.name or idx.primary or idx.name.upper() in params["exempt_names"]:
                continue
            pattern = params["unique_pattern"] if idx.unique else params["index_pattern"]
            if not re.match(pattern, idx.name, re.I):
                bad.append(idx.name)
        bad += [ck.name for ck in t.checks if ck.name and not re.match(params["check_pattern"], ck.name, re.I)]
        if bad:
            yield Hit(table=t.fqname, data={"names": bad},
                      evidence=f"{t.fqname} has {len(bad)} constraint or index name(s) outside the standard forms: "
                               f"{', '.join(bad[:params['max_listed']])}.",
                      fix=manual(t, "Rename constraints and indexes to the standard pk_, fk_, unique_, check_ and index_ "
                                    "forms in a planned change."))


@check("schema.boolean_naming")
def boolean_naming(db, profile, params):
    for t in tables_in_scope(db, profile, params):
        for c in t.columns:
            if c.type.family == "bool" and not re.match(params["allowed_pattern"], c.name, re.I):
                yield Hit(table=t.fqname, column=c.name, fix=make_fix("rename_column", t, c.name, new_name=f"is_{snake(c.name)}"),
                          evidence=f"Boolean column {t.fqname}.{c.name} does not use the is_ or has_ form.")


@check("schema.temporal_naming")
def temporal_naming(db, profile, params):
    audit = {n.lower() for group in profile.audit_columns for n in group}
    for t in tables_in_scope(db, profile, params):
        for c in t.columns:
            family, low = c.type.family, snake(c.name)
            if low in audit:
                continue
            stem = re.sub(params["strip_suffix_pattern"], "", low) or low
            if family in ("datetime", "timestamptz") and not re.search(params["instant_pattern"], low):
                expected = f"{stem}_at"
                label = "instant"
            elif family == "date" and not re.search(params["date_pattern"], low):
                expected = f"{stem}_date"
                label = "calendar date"
            else:
                continue
            yield Hit(table=t.fqname, column=c.name, fix=make_fix("rename_column", t, c.name, new_name=expected),
                      vars={"expected": expected, "label": label},
                      evidence=f"{t.fqname}.{c.name} holds a {label} ({c.data_type}) and is not named in the {expected} form.")
