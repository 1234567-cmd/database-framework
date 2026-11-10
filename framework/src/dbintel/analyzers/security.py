"""Security and tenant-isolation checks. Checks only find facts; all text and thresholds live in the catalog.

Raw values read from sampled columns never leave this module unmasked: evidence uses ``mask_value`` or counts only.
"""
from __future__ import annotations

import re
from typing import Any, Iterable, Optional

from ..findings import Fix
from ..model import Column, Database, Table
from ..rules.engine import Hit, check, iter_tables

_TEXT = {"text", "char"}
_NUMERIC_ID = {"int", "decimal"}


# ---- shared helpers (also used by data_quality) ----

def mask_value(value: Any) -> str:
    """Return a masked form of a value. Safe to place in evidence."""
    text = "" if value is None else str(value)
    if "@" in text:
        local, _, domain = text.partition("@")
        tld = domain.rsplit(".", 1)[-1] if "." in domain else ""
        return f"{local[:1]}***@***.{tld}" if tld else f"{local[:1]}***@***"
    if len(text) <= 6:
        return "***"
    return "***" + text[-2:]


def is_luhn_valid(number: str) -> bool:
    digits = [int(d) for d in number if d.isdigit()]
    if not digits:
        return False
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d = d * 2 - 9 if d > 4 else d * 2
        total += d
    return total % 10 == 0


def looks_like_pan(value: Any, min_len: int = 13, max_len: int = 19) -> bool:
    text = re.sub(r"[ -]", "", str(value))
    if not text.isdigit() or not min_len <= len(text) <= max_len or len(set(text)) == 1:
        return False
    return is_luhn_valid(text)


def compile_any(patterns: Iterable[str]) -> Optional[re.Pattern]:
    joined = "|".join(f"(?:{p})" for p in patterns)
    return re.compile(joined, re.I) if joined else None


def matches(rx: Optional[re.Pattern], text: str) -> bool:
    return bool(rx and rx.search(text))


def read_limit(profile, params: dict, default: int = 1000) -> int:
    return max(1, min(int(profile.data_sample_limit), int(params.get("sample_limit", default))))


def table_ref(db: Database, table: Table) -> str:
    q = db.data.quote
    return f"{q(table.schema)}.{q(table.name)}" if table.schema else q(table.name)


def safe_query(db: Database, sql: str, where: str) -> Optional[list[tuple]]:
    """Run a read query. A failure is recorded by exception type only, so that no data reaches the report."""
    try:
        return db.data.query(sql)
    except Exception as exc:  # one unreadable table must not lose the assessment
        note = f"Data check skipped for {where}: {type(exc).__name__}"
        if note not in db.import_warnings:
            db.import_warnings.append(note)
        return None


def sample_column(db: Database, table: Table, column: str, limit: int) -> Optional[list[Any]]:
    """Up to ``limit`` non-null values of a column, or None when the column could not be read."""
    q = db.data.quote(column)
    rows = safe_query(db, f"SELECT {q} FROM {table_ref(db, table)} WHERE {q} IS NOT NULL LIMIT {int(limit)}",
                      f"{table.fqname}.{column}")
    return None if rows is None else [r[0] for r in rows]


def manual(table: Optional[str], column: Optional[str], description: str) -> Fix:
    return Fix("manual", table, column, {"description": description})


# ---- role helpers ----

def _is_admin(name: str, params: dict) -> bool:
    return matches(compile_any(params.get("admin_role_patterns", [])), name)


def _is_runtime(name: str, params: dict) -> bool:
    explicit = {r.lower() for r in params.get("runtime_roles", [])}
    if explicit:
        return name.lower() in explicit
    if _is_admin(name, params):
        return False
    return matches(compile_any(params.get("runtime_role_patterns", [])), name)


def _priv(privilege: str) -> str:
    return " ".join(privilege.upper().split())


def _scope(table: Optional[str]) -> Optional[str]:
    return None if table in (None, "*") else table


@check("security.runtime_role_privileges")
def runtime_role_privileges(db, profile, params):
    for role in db.roles:
        if role.superuser and _is_runtime(role.name, params):
            yield Hit(evidence=f"Role {role.name} matches the runtime role patterns and has superuser rights.",
                      vars={"role": role.name, "privilege": "SUPERUSER"}, severity="critical",
                      fix=manual(None, None, f"Remove superuser from {role.name} and connect the application "
                                             "with a least-privilege role."))
    ddl = {_priv(p) for p in params.get("ddl_privileges", [])}
    for g in db.grants:
        if _is_runtime(g.grantee, params) and _priv(g.privilege) in ddl:
            target = _scope(g.table)
            yield Hit(table=target, evidence=f"Role {g.grantee} holds {_priv(g.privilege)} on {g.table or 'the database'}.",
                      vars={"role": g.grantee, "privilege": _priv(g.privilege)},
                      fix=Fix("revoke_grant", target, None, {"grantee": g.grantee, "privilege": g.privilege}))


@check("security.broad_grants")
def broad_grants(db, profile, params):
    ignored = {_priv(p) for p in params.get("ignored_privileges", [])}
    for g in db.grants:
        priv = _priv(g.privilege)
        public = g.grantee.upper() == "PUBLIC"
        if _is_admin(g.grantee, params) and not public:
            continue
        everything = priv in ("ALL", "ALL PRIVILEGES")
        wildcard = g.table in (None, "*")
        reasons = [label for flag, label in ((public, "granted to PUBLIC"), (everything, "ALL privileges"),
                                             (wildcard, "wildcard scope"), (g.grantable, "grant option")) if flag]
        if not reasons or (not everything and not g.grantable and priv in ignored):
            continue
        strong = public or everything
        fix = (Fix("revoke_grant", _scope(g.table), None, {"grantee": g.grantee, "privilege": g.privilege})
               if strong or wildcard else
               manual(_scope(g.table), None, f"Remove the grant option from {g.grantee} on {g.table}."))
        yield Hit(table=_scope(g.table),
                  evidence=f"{g.grantee} holds {priv} on {g.table or 'the database'}: {', '.join(reasons)}.",
                  vars={"grantee": g.grantee, "privilege": priv, "reason": ", ".join(reasons)},
                  severity=None if strong else "medium", kind=None if strong else "context_dependent", fix=fix)


@check("security.weak_logins")
def weak_logins(db, profile, params):
    for role in db.roles:
        if not role.can_login:
            continue
        if role.password_set is False:
            yield Hit(evidence=f"Login role {role.name} has no password set.",
                      vars={"role": role.name, "issue": "no password"},
                      fix=manual(None, None, f"Set a credential for {role.name} or disable its login."))
        if role.host == "%":
            yield Hit(evidence=f"Login role {role.name} may connect from any host ('%').",
                      vars={"role": role.name, "issue": "any host"}, severity="medium", kind="context_dependent",
                      fix=manual(None, None, f"Restrict the host of {role.name} to the application network."))


# ---- tenancy ----

def tenant_tables(db: Database, profile) -> list[Table]:
    return [t for t in iter_tables(db, profile) if not profile.is_tenant_exempt(t.name)]


def _tenant_type(db: Database, profile, params: dict) -> str:
    parent = db.table("tenants")
    if parent is not None and len(parent.primary_key) == 1:
        col = parent.column(parent.primary_key[0])
        if col is not None:
            return col.data_type
    return params.get("tenant_column_type", "bigint")


@check("security.tenant_column_missing")
def tenant_column_missing(db, profile, params):
    tenant = profile.tenant_column
    ctype = _tenant_type(db, profile, params)
    for t in tenant_tables(db, profile):
        if not t.has_column(tenant):
            yield Hit(table=t.fqname, column=tenant, evidence=f"Table {t.fqname} has no {tenant} column.",
                      fix=Fix("add_column", t.fqname, tenant, {"type": ctype, "nullable": True, "default": None}))


@check("security.tenant_column_nullable")
def tenant_column_nullable(db, profile, params):
    for t in tenant_tables(db, profile):
        col = t.column(profile.tenant_column)
        if col is not None and col.nullable:
            yield Hit(table=t.fqname, column=col.name, evidence=f"{t.fqname}.{col.name} allows NULL.",
                      fix=Fix("set_not_null", t.fqname, col.name, {}))


@check("security.tenant_not_in_primary_key")
def tenant_not_in_primary_key(db, profile, params):
    tenant = profile.tenant_column.lower()
    for t in tenant_tables(db, profile):
        if t.has_column(tenant) and t.primary_key and tenant not in {c.lower() for c in t.primary_key}:
            yield Hit(table=t.fqname, column=profile.tenant_column,
                      evidence=f"Primary key of {t.fqname} is ({', '.join(t.primary_key)}), without {tenant}.",
                      fix=manual(t.fqname, profile.tenant_column,
                                 f"Rebuild the primary key of {t.fqname} to include {tenant}; plan dependent keys."))


@check("security.tenant_not_in_unique_key")
def tenant_not_in_unique_key(db, profile, params):
    tenant = profile.tenant_column.lower()
    global_rx = compile_any(params.get("global_unique_patterns", []))
    for t in tenant_tables(db, profile):
        if not t.has_column(tenant):
            continue
        for idx in t.indexes:
            cols = [c.lower() for c in idx.columns]
            if not idx.unique or idx.primary or idx.where or tenant in cols:
                continue
            if all(matches(global_rx, c) for c in cols):
                continue
            yield Hit(table=t.fqname, column=idx.columns[0],
                      evidence=f"Unique key {idx.name or idx.columns} on {t.fqname} does not include {tenant}.",
                      vars={"key_columns": ", ".join(idx.columns)},
                      fix=Fix("add_index", t.fqname, None, {"columns": [profile.tenant_column] + idx.columns, "unique": True}))


@check("security.fk_can_cross_tenants")
def fk_can_cross_tenants(db, profile, params):
    tenant = profile.tenant_column.lower()
    for t in tenant_tables(db, profile):
        if not t.has_column(tenant):
            continue
        for fk in t.foreign_keys:
            ref = db.table(fk.ref_table, fk.ref_schema) or db.table(fk.ref_table)
            if ref is None or profile.is_tenant_exempt(ref.name) or not ref.has_column(tenant):
                continue
            if tenant in {c.lower() for c in fk.columns}:
                continue
            ref_cols = [profile.tenant_column] + fk.ref_columns
            want = {c.lower() for c in ref_cols}
            composite = any({c.lower() for c in key} == want for key in ref.unique_keys())
            fix = (Fix("add_foreign_key", t.fqname, None, {"columns": [profile.tenant_column] + fk.columns,
                                                           "ref_table": ref.fqname, "ref_columns": ref_cols})
                   if composite else
                   manual(t.fqname, fk.columns[0], f"Add a unique key on {ref.fqname} ({', '.join(ref_cols)}), then "
                                                   f"replace this foreign key with one that includes {tenant}."))
            yield Hit(table=t.fqname, column=fk.columns[0],
                      evidence=f"Foreign key {t.fqname}({', '.join(fk.columns)}) -> {ref.fqname}"
                               f"({', '.join(fk.ref_columns)}) does not include {tenant}.",
                      vars={"ref_table": ref.fqname, "fk_columns": ", ".join(fk.columns)}, fix=fix)


@check("security.rls_missing")
def rls_missing(db, profile, params):
    if db.dialect != "postgres":
        return
    for t in tenant_tables(db, profile):
        if t.rls_enabled is False and t.has_column(profile.tenant_column):
            yield Hit(table=t.fqname, evidence=f"Row-level security is not enabled on {t.fqname}.",
                      vars={"issue": "not enabled"},
                      fix=Fix("enable_rls", t.fqname, None, {"tenant_column": profile.tenant_column}))
        elif t.rls_enabled is True and db.security_metadata and not any(
                p.table.lower() == t.name.lower() for p in db.policies):
            yield Hit(table=t.fqname, evidence=f"Row-level security is enabled on {t.fqname} but no policy exists.",
                      vars={"issue": "no policy"},
                      fix=manual(t.fqname, None, f"Create a tenant policy on {t.fqname}."))


@check("security.rls_bypass_principals")
def rls_bypass_principals(db, profile, params):
    if db.dialect != "postgres" or not any(t.rls_enabled for t in tenant_tables(db, profile)):
        return
    for role in db.roles:
        if not (role.bypass_rls or role.superuser):
            continue
        why = "superuser" if role.superuser else "BYPASSRLS"
        if _is_runtime(role.name, params):
            yield Hit(evidence=f"Runtime role {role.name} can bypass row-level security ({why}).",
                      vars={"role": role.name, "reason": why}, severity="critical", kind="confirmed_defect",
                      fix=manual(None, None, f"Remove {why} from {role.name}."))
        else:
            yield Hit(evidence=f"Role {role.name} can bypass row-level security ({why}); record it in the design.",
                      vars={"role": role.name, "reason": why}, severity="informational", kind="context_dependent")


@check("security.per_tenant_objects")
def per_tenant_objects(db, profile, params):
    rx = compile_any(params.get("per_tenant_patterns", []))
    for t in iter_tables(db, profile):
        if matches(rx, t.name):
            yield Hit(table=t.fqname, evidence=f"Table name {t.name} looks specific to one tenant.",
                      vars={"object_kind": "table"},
                      fix=manual(t.fqname, None, "Move per-tenant data to the shared table with a tenant identifier."))
        for c in t.columns:
            if matches(rx, c.name):
                yield Hit(table=t.fqname, column=c.name, evidence=f"Column {t.fqname}.{c.name} looks specific to one tenant.",
                          vars={"object_kind": "column"},
                          fix=manual(t.fqname, c.name, "Move tenant-specific fields to a custom-data structure."))


@check("security.company_column_missing")
def company_column_missing(db, profile, params):
    if not profile.multi_company:
        return
    shared = compile_any(params.get("shared_master_patterns", []))
    ctype = params.get("company_column_type", "bigint")
    for t in tenant_tables(db, profile):
        if t.has_column(profile.company_column) or profile.is_audit_exempt(t.name) or matches(shared, t.name):
            continue
        yield Hit(table=t.fqname, column=profile.company_column,
                  evidence=f"Table {t.fqname} has no {profile.company_column} column in a multi-company profile.",
                  fix=Fix("add_column", t.fqname, profile.company_column, {"type": ctype, "nullable": True, "default": None}))


# ---- sensitive data ----

def _category(name: str, params: dict) -> Optional[str]:
    if matches(compile_any(params.get("exclude_name_patterns", [])), name):
        return None
    for category, patterns in params.get("sensitive_name_patterns", {}).items():
        if matches(compile_any(patterns), name):
            return category
    return None


@check("security.sensitive_by_name")
def sensitive_by_name(db, profile, params):
    for t in iter_tables(db, profile):
        for c in t.columns:
            if c.type.family == "bool":
                continue
            category = _category(c.name, params)
            if category:
                yield Hit(table=t.fqname, column=c.name, evidence=f"Column name suggests {category} data.",
                          vars={"data_category": category},
                          fix=manual(t.fqname, c.name, f"Classify {c.name} ({category}) and record its required protections."))


def _text_columns(table: Table) -> Iterable[Column]:
    return (c for c in table.columns if c.type.family in _TEXT)


@check("security.sensitive_by_sampling")
def sensitive_by_sampling(db, profile, params):
    limit = read_limit(profile, params)
    detectors = [(d["category"], re.compile(d["regex"])) for d in params.get("detectors", [])]
    min_ratio = float(params.get("min_match_ratio", 0.5))
    min_matches = int(params.get("min_matches", 1))
    for t in iter_tables(db, profile):
        for c in _text_columns(t):
            values = sample_column(db, t, c.name, limit)
            if not values:
                continue
            for category, rx in detectors:
                found = [v for v in values if rx.fullmatch(str(v).strip())]
                if len(found) >= min_matches and len(found) / len(values) >= min_ratio:
                    examples = ", ".join(mask_value(v) for v in found[:2])
                    yield Hit(table=t.fqname, column=c.name, vars={"data_category": category},
                              evidence=f"{len(found)} of {len(values)} sampled values look like {category}; "
                                       f"masked examples: {examples}.",
                              data={"sampled": len(values), "matched": len(found)},
                              fix=manual(t.fqname, c.name, f"Classify {c.name} ({category}) and protect it accordingly."))


@check("security.forbidden_card_columns")
def forbidden_card_columns(db, profile, params):
    rx = compile_any(params.get("forbidden_patterns", []))
    payment = compile_any(params.get("payment_table_patterns", []))
    pin = compile_any(params.get("bare_pin_patterns", []))
    for t in iter_tables(db, profile):
        for c in t.columns:
            if c.type.family != "bool" and (matches(rx, c.name) or (matches(payment, t.name) and matches(pin, c.name))):
                yield Hit(table=t.fqname, column=c.name,
                          evidence=f"Column name {c.name} suggests card authentication data.",
                          fix=manual(t.fqname, c.name, "Confirm the content and, after legal review, stop storing it "
                                                       "and plan its controlled removal."))


@check("security.card_numbers")
def card_numbers(db, profile, params):
    limit = read_limit(profile, params)
    name_rx = compile_any(params.get("card_name_patterns", []))
    exclude = compile_any(params.get("exclude_name_patterns", []))
    min_ratio = float(params.get("min_match_ratio", 0.5))
    for t in iter_tables(db, profile):
        for c in t.columns:
            if c.type.family not in _TEXT | _NUMERIC_ID or matches(exclude, c.name):
                continue
            named = matches(name_rx, c.name)
            values = sample_column(db, t, c.name, limit) if db.data is not None else None
            if values:
                pans = [v for v in values if looks_like_pan(v)]
                if pans and len(pans) / len(values) >= min_ratio:
                    yield Hit(table=t.fqname, column=c.name, vars={"basis": "sampled values"},
                              evidence=f"{len(pans)} of {len(values)} sampled values pass the Luhn check for a card "
                                       f"number; masked example: {mask_value(pans[0])}.",
                              confidence=0.9, data={"sampled": len(values), "matched": len(pans)},
                              fix=manual(t.fqname, c.name, "After legal review, tokenize or render the stored values unreadable."))
            elif named:
                yield Hit(table=t.fqname, column=c.name, vars={"basis": "column name"},
                          evidence=f"Column name {c.name} suggests a card number; no values could be sampled.",
                          confidence=0.5,
                          fix=manual(t.fqname, c.name, "Confirm the content and, after legal review, tokenize it."))


@check("security.password_storage")
def password_storage(db, profile, params):
    limit = read_limit(profile, params)
    name_rx = compile_any(params.get("password_name_patterns", []))
    exclude = compile_any(params.get("exclude_name_patterns", []))
    hashed = compile_any(params.get("hash_shapes", []))
    digest = compile_any(params.get("fast_digest_shapes", []))
    min_ratio = float(params.get("min_plaintext_ratio", 0.01))
    for t in iter_tables(db, profile):
        for c in _text_columns(t):
            if not matches(name_rx, c.name) or matches(exclude, c.name):
                continue
            values = [v for v in (sample_column(db, t, c.name, limit) or []) if str(v)]
            if not values:
                continue
            not_hashed = [v for v in values if not matches(hashed, str(v))]
            digests = [v for v in not_hashed if matches(digest, str(v))]
            plain = len(not_hashed) - len(digests)
            if plain / len(values) >= min_ratio:
                yield Hit(table=t.fqname, column=c.name, vars={"shape": "plaintext"}, severity="critical",
                          kind="confirmed_defect",
                          evidence=f"{plain} of {len(values)} sampled values do not match any password-hash shape.",
                          fix=manual(t.fqname, c.name, "Rehash at next login or force a reset with a password-hashing algorithm."))
            elif digests:
                yield Hit(table=t.fqname, column=c.name, vars={"shape": "fast digest"}, severity="high",
                          kind="context_dependent",
                          evidence=f"{len(digests)} of {len(values)} sampled values look like an unsalted fast digest.",
                          fix=manual(t.fqname, c.name, "Migrate to a password-hashing algorithm such as Argon2id or bcrypt."))


@check("security.sensitive_unencrypted")
def sensitive_unencrypted(db, profile, params):
    wanted = set(params.get("categories", []))
    opaque = re.compile(params.get("opaque_value_regex", r"^[A-Za-z0-9+/=_:.-]{24,}$"))
    min_opaque = float(params.get("min_opaque_ratio", 0.9))
    limit = read_limit(profile, params)
    encrypted_name = compile_any(params.get("encrypted_name_patterns", []))
    for t in iter_tables(db, profile):
        for c in t.columns:
            category = _category(c.name, params)
            if category not in wanted or c.type.family not in _TEXT | _NUMERIC_ID or matches(encrypted_name, c.name):
                continue
            if db.data is not None:
                values = sample_column(db, t, c.name, limit) or []
                if values and sum(1 for v in values if opaque.match(str(v))) / len(values) >= min_opaque:
                    continue
            yield Hit(table=t.fqname, column=c.name, vars={"data_category": category},
                      evidence=f"Column {c.name} ({category}) has type {c.data_type} and no encryption signal.",
                      fix=manual(t.fqname, c.name, "Decide on column or application encryption from the threat model."))


@check("security.audit_tables_writable")
def audit_tables_writable(db, profile, params):
    rx = compile_any(params.get("audit_table_patterns", []))
    write = {_priv(p) for p in params.get("write_privileges", [])}
    audit_tables = [t for t in iter_tables(db, profile) if matches(rx, t.name)]
    for g in db.grants:
        if not _is_runtime(g.grantee, params) or _priv(g.privilege) not in write:
            continue
        for t in audit_tables:
            if g.table in (None, "*") or g.table.lower() == t.name.lower():
                yield Hit(table=t.fqname, evidence=f"Runtime role {g.grantee} holds {_priv(g.privilege)} on audit table {t.fqname}.",
                          vars={"grantee": g.grantee, "privilege": _priv(g.privilege)},
                          fix=Fix("revoke_grant", t.fqname, None, {"grantee": g.grantee, "privilege": g.privilege}))


@check("security.settings")
def settings(db, profile, params):
    current = {str(k).lower(): v for k, v in db.settings.items()}
    for item in params.get("settings", []):
        if item.get("dialects") and db.dialect not in item["dialects"]:
            continue
        key = item["setting"].lower()
        if key in current and str(current[key]).strip().lower() in {str(v).lower() for v in item["bad_values"]}:
            yield Hit(evidence=f"Setting {item['setting']} is {current[key]}.",
                      vars={"setting": item["setting"], "issue": item.get("issue", "unsafe value")},
                      severity=item.get("severity"),
                      fix=manual(None, None, item.get("remedy", f"Review the setting {item['setting']}.")))
