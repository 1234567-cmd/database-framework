"""Destructive-change detection, plan hashing, approval and backup advice."""
from __future__ import annotations

import hashlib
import hmac
import json
import re
from dataclasses import dataclass
from typing import Any, Iterable, Optional, Sequence

import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError

from ._sql import normalize_dialect, quiet_sqlglot, type_change_kind

DEFAULT_FINANCIAL_PATTERNS = ("journal", "ledger", "invoice", "payment")
DESTRUCTIVE = "destructive"
RISKY = "risky"


class ApprovalRequired(PermissionError):
    """The approval token does not match the exact plan."""


@dataclass(frozen=True)
class DestructiveHit:
    kind: str
    severity: str  # destructive | risky
    statement: str
    detail: str = ""
    source: str = "sqlglot"  # sqlglot | fallback

    def to_dict(self) -> dict[str, str]:
        return {"kind": self.kind, "severity": self.severity, "statement": self.statement,
                "detail": self.detail, "source": self.source}


# --- lexing -----------------------------------------------------------------

def _strip_comments(sql: str, backslash: bool = True) -> str:
    """Remove comments but keep the body of executable MySQL comments, which the server runs."""
    out: list[str] = []
    i, n = 0, len(sql)
    while i < n:
        ch = sql[i]
        two = sql[i:i + 2]
        if ch in "'\"`":
            end = _skip_quoted(sql, i, ch, backslash)
            out.append(sql[i:end])
            i = end
        elif ch == "$":
            end = _skip_dollar(sql, i)
            if end:
                out.append(sql[i:end])
                i = end
            else:
                out.append(ch)
                i += 1
        elif two == "--":
            nl = sql.find("\n", i)
            i = n if nl < 0 else nl
        elif two == "/*":
            m = re.match(r"/\*M?!\d*", sql[i:])
            close = sql.find("*/", i + 2)
            if close < 0:  # unterminated: keep the text so that it is still inspected
                out.append(sql[i + 2:])
                break
            if m:
                out.append(" " + _strip_comments(sql[i + m.end():close], backslash) + " ")
            else:
                out.append(" ")
            i = close + 2
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def _skip_quoted(sql: str, start: int, quote_char: str, backslash: bool = True) -> int:
    i, n = start + 1, len(sql)
    while i < n:
        if backslash and sql[i] == "\\" and quote_char == "'":
            i += 2
            continue
        if sql[i] == quote_char:
            if sql[i:i + 2] == quote_char * 2:
                i += 2
                continue
            return i + 1
        i += 1
    return n


_DOLLAR = re.compile(r"\$([A-Za-z_][A-Za-z_0-9]*)?\$")


def _skip_dollar(sql: str, start: int) -> Optional[int]:
    m = _DOLLAR.match(sql, start)
    if not m:
        return None
    close = sql.find(m.group(0), m.end())
    return (close + len(m.group(0))) if close >= 0 else len(sql)


def _mask(clean: str, backslash: bool = True) -> tuple[str, list[str], list[str]]:
    """Blank quoted content so keywords inside strings and identifiers are ignored; return strings and $$ bodies."""
    chars = list(clean)
    strings: list[str] = []
    bodies: list[str] = []
    i, n = 0, len(clean)
    while i < n:
        ch = clean[i]
        if ch in "'\"`":
            end = _skip_quoted(clean, i, ch, backslash)
            if ch == "'":
                strings.append(clean[i + 1:end - 1].replace("''", "'"))
            for j in range(i + 1, max(i + 1, end - 1)):
                chars[j] = " "
            i = end
        elif ch == "$":
            end = _skip_dollar(clean, i)
            if end:
                m = _DOLLAR.match(clean, i)
                bodies.append(clean[m.end():end - len(m.group(0))])
                for j in range(i + 1, end - 1):
                    chars[j] = " "
                i = end
            else:
                i += 1
        else:
            i += 1
    return "".join(chars), strings, bodies


def _split(clean: str, masked: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    start = 0
    for i, ch in enumerate(masked):
        if ch == ";":
            out.append((clean[start:i], masked[start:i]))
            start = i + 1
    out.append((clean[start:], masked[start:]))
    return [(c.strip(), m.strip()) for c, m in out if c.strip()]


def _has_toplevel_where(masked: str) -> bool:
    depth = 0
    upper = masked.upper()
    for i, ch in enumerate(upper):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif depth == 0 and upper.startswith("WHERE", i):
            before = upper[i - 1] if i else " "
            after = upper[i + 5] if i + 5 < len(upper) else " "
            if not (before.isalnum() or before == "_") and not (after.isalnum() or after == "_"):
                return True
    return False


_ALWAYS_TRUE = re.compile(r"\bWHERE\s+(?:TRUE\b|1\s*(?:$|;|\bOR\b)|(\d+|'[^']*')\s*=\s*\1(?:\s|$|;))", re.I)
_OR_TRUE = re.compile(r"\bOR\s+(?:TRUE\b|(\d+|'[^']*')\s*=\s*\1(?:\s|$|;))", re.I)

_RULES: list[tuple[str, str, re.Pattern]] = [(k, s, re.compile(p, re.I | re.S)) for k, s, p in [
    ("drop_table", DESTRUCTIVE, r"\bDROP\s+(?:TEMPORARY\s+)?TABLE\b"),
    ("drop_database", DESTRUCTIVE, r"\bDROP\s+(?:DATABASE|SCHEMA)\b"),
    ("truncate", DESTRUCTIVE, r"^\s*TRUNCATE\b(?!\s*\()|\bTRUNCATE\s+(?:TABLE|PARTITION)\b"),
    ("delete", DESTRUCTIVE, r"\bDELETE\s+FROM\b|^\s*DELETE\b"),
    ("drop_column", DESTRUCTIVE, r"\bDROP\s+COLUMN\b"),
    ("drop_column", DESTRUCTIVE, r"\bALTER\s+TABLE\b.*?\bDROP\s+(?!COLUMN\b|CONSTRAINT\b|INDEX\b|KEY\b|PRIMARY\b|FOREIGN\b|"
                                 r"CHECK\b|PARTITION\b|DEFAULT\b|NOT\b|IDENTITY\b|EXPRESSION\b)(?:IF\s+EXISTS\s+)?[`\"\w]"),
    ("drop_partition", DESTRUCTIVE, r"\bDROP\s+PARTITION\b"),
    ("replace_into", DESTRUCTIVE, r"^\s*REPLACE\s+(?:LOW_PRIORITY\s+|DELAYED\s+)?INTO\b"),
    ("overwrite", DESTRUCTIVE, r"\bINSERT\s+OVERWRITE\b|\bCREATE\s+OR\s+REPLACE\s+TABLE\b"),
    ("merge_delete", DESTRUCTIVE, r"\bMERGE\b.*\bTHEN\s+DELETE\b"),
    ("writable_schema", DESTRUCTIVE, r"\bPRAGMA\s+writable_schema\b"),
    ("drop_view", RISKY, r"\bDROP\s+(?:MATERIALIZED\s+)?VIEW\b"),
    ("drop_index", RISKY, r"\bDROP\s+INDEX\b"),
    ("drop_constraint", RISKY, r"\bDROP\s+(?:CONSTRAINT|PRIMARY\s+KEY|FOREIGN\s+KEY|CHECK)\b"),
    ("drop_routine", RISKY, r"\bDROP\s+(?:FUNCTION|PROCEDURE|TRIGGER|SEQUENCE|TYPE|POLICY)\b"),
    ("rename", RISKY, r"\bRENAME\s+(?:COLUMN|TO|TABLE)\b|\bALTER\s+TABLE\b.*\bRENAME\b"),
    ("disable_protection", RISKY, r"\bDISABLE\s+(?:ROW\s+LEVEL\s+SECURITY|TRIGGER)\b|\bFOREIGN_KEY_CHECKS\s*=\s*0\b|"
                                  r"\bsession_replication_role\b"),
]]

_DYNAMIC_START = re.compile(r"^\s*(?:EXEC(?:UTE)?|PREPARE|DO|CALL|BEGIN)\b", re.I)
_OPAQUE_CALL = re.compile(r"^\s*(?:CALL|EXEC(?:UTE)?)\b", re.I)
_UPDATE_RE = re.compile(r"^\s*(?:WITH\b.*?\b)?UPDATE\b.*?\bSET\b", re.I | re.S)
_IDENT = r"(?:\"[^\"]+\"|`[^`]+`|\[[^\]]+\]|[A-Za-z_][\w$]*)"
_QUAL = rf"{_IDENT}(?:\s*\.\s*{_IDENT})*"
_ALTER_TABLE = re.compile(rf"\bALTER\s+TABLE\s+(?:ONLY\s+)?(?:IF\s+EXISTS\s+)?({_QUAL})", re.I)
_TYPE_BODY = r"(?:[^,()]|\([^)]*\))+"
_TYPE_PATTERNS = [
    re.compile(rf"\bALTER\s+(?:COLUMN\s+)?({_IDENT})\s+(?:SET\s+DATA\s+)?TYPE\s+({_TYPE_BODY}?)(?=\s+USING\b|\s+COLLATE\b|,|$)", re.I | re.S),
    re.compile(rf"\bMODIFY\s+(?:COLUMN\s+)?({_IDENT})\s+({_TYPE_BODY}?)(?=,|$)", re.I | re.S),
    re.compile(rf"\bCHANGE\s+(?:COLUMN\s+)?{_IDENT}\s+({_IDENT})\s+({_TYPE_BODY}?)(?=,|$)", re.I | re.S),
]
_TYPE_TAIL = re.compile(r"\b(?:NOT\s+NULL|NULL|DEFAULT|COMMENT|AUTO_INCREMENT|PRIMARY|UNIQUE|ALGORITHM|LOCK|FIRST|AFTER|"
                        r"COLLATE|CHARACTER\s+SET|REFERENCES|CHECK|ON\s+UPDATE)\b.*$", re.I | re.S)


def _unquote_last(name: str) -> str:
    part = re.split(r"\s*\.\s*(?=(?:[\"`\[]|[A-Za-z_]))", name.strip())[-1]
    return part.strip().strip('"`[]').lower()


def _trim_stmt(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()[:300]


def _type_hits(clean: str, known: dict[str, str], stmt: str) -> list[DestructiveHit]:
    if not re.search(r"\bALTER\s+TABLE\b", clean, re.I):
        return []
    table_m = _ALTER_TABLE.search(clean)
    table = _unquote_last(table_m.group(1)) if table_m else ""
    out: list[DestructiveHit] = []
    for pat in _TYPE_PATTERNS:
        for m in pat.finditer(clean):
            col = _unquote_last(m.group(1))
            new_type = _TYPE_TAIL.sub("", m.group(2)).strip().rstrip(";,").strip()
            if not new_type:
                continue
            old_type = known.get(f"{table}.{col}")
            if old_type is None:
                out.append(DestructiveHit("type_narrowing", DESTRUCTIVE, stmt,
                                          f"Column {col} changes type to {new_type}; the previous type is unknown, so narrowing cannot be ruled out.",
                                          "fallback"))
            else:
                change = type_change_kind(old_type, new_type, "postgres")
                if change == "narrowing":
                    out.append(DestructiveHit("type_narrowing", DESTRUCTIVE, stmt,
                                              f"Column {col} narrows from {old_type} to {new_type}.", "fallback"))
                elif change != "same":
                    out.append(DestructiveHit("type_change", RISKY, stmt,
                                              f"Column {col} changes from {old_type} to {new_type} ({change}).", "fallback"))
    return out


def _regex_hits(clean: str, masked: str, known: dict[str, str]) -> list[DestructiveHit]:
    stmt = _trim_stmt(clean)
    out: list[DestructiveHit] = []
    for kind, severity, pattern in _RULES:
        if pattern.search(masked):
            out.append(DestructiveHit(kind, severity, stmt, source="fallback"))
    if _UPDATE_RE.search(masked):
        if not _has_toplevel_where(masked):
            out.append(DestructiveHit("update_without_where", DESTRUCTIVE, stmt, "UPDATE has no WHERE clause.", "fallback"))
        elif _ALWAYS_TRUE.search(clean) or _OR_TRUE.search(clean):
            out.append(DestructiveHit("update_always_true", DESTRUCTIVE, stmt, "UPDATE has a WHERE clause that is always true.", "fallback"))
    if re.search(r"\bDELETE\b", masked, re.I) and (_ALWAYS_TRUE.search(clean) or _OR_TRUE.search(clean)):
        out.append(DestructiveHit("delete_always_true", DESTRUCTIVE, stmt, "DELETE has a WHERE clause that is always true.", "fallback"))
    out.extend(_type_hits(clean, known, stmt))
    return out


def _ast_hits(clean: str, dialect: Optional[str], known: dict[str, str]) -> list[DestructiveHit]:
    stmt = _trim_stmt(clean)
    tree = None
    for read in ([dialect] if dialect else ["postgres", "mysql", "sqlite", None]):
        try:
            with quiet_sqlglot():
                parsed = sqlglot.parse(clean, read=read)
        except (SqlglotError, Exception):  # sqlglot may raise non-Sqlglot errors on hostile text
            continue
        if parsed and parsed[0] is not None and not isinstance(parsed[0], exp.Command):
            tree = parsed[0]
            break
    if tree is None:
        return []
    out: list[DestructiveHit] = []
    for node in tree.find_all(exp.Drop):
        drop_kind = str(node.args.get("kind") or "").upper()
        if drop_kind in ("DATABASE", "SCHEMA"):
            out.append(DestructiveHit("drop_database", DESTRUCTIVE, stmt))
        elif drop_kind == "TABLE":
            out.append(DestructiveHit("drop_table", DESTRUCTIVE, stmt))
        elif drop_kind == "COLUMN":
            out.append(DestructiveHit("drop_column", DESTRUCTIVE, stmt))
    for node in tree.find_all(exp.TruncateTable):
        out.append(DestructiveHit("truncate", DESTRUCTIVE, stmt))
    for node in tree.find_all(exp.Delete):
        out.append(DestructiveHit("delete", DESTRUCTIVE, stmt))
    for node in tree.find_all(exp.Update):
        if node.args.get("where") is None:
            out.append(DestructiveHit("update_without_where", DESTRUCTIVE, stmt, "UPDATE has no WHERE clause."))
    return out


def detect_destructive(sql: str, dialect: Optional[str] = None,
                       known_types: Optional[dict[str, str]] = None) -> list[DestructiveHit]:
    """Classify destructive and risky statements.

    ``sqlglot`` is tried first; a regular-expression pass over text with strings and comments removed always runs too,
    so unparseable SQL and engine-specific forms are still caught. Executable MySQL comments are expanded and dollar-
    quoted bodies are inspected. ``known_types`` maps ``table.column`` (lowercase) to its current type so that a type
    change can be classified precisely; without it a type change counts as possible narrowing.
    """
    if not sql:
        return []
    read = None if dialect is None else normalize_dialect(dialect)
    known = {k.lower(): v for k, v in (known_types or {}).items()}
    out: list[DestructiveHit] = []
    seen: set[tuple[str, str]] = set()

    def add(hits: Iterable[DestructiveHit]) -> None:
        for hit in hits:
            key = (hit.kind, hit.statement)
            if key not in seen:
                seen.add(key)
                out.append(hit)

    # Engines disagree on whether backslash escapes a quote, so the text is read both ways and the results are combined.
    for backslash in (True, False):
        clean_text = _strip_comments(sql, backslash)
        masked_text, _, _ = _mask(clean_text, backslash)
        for clean, masked in _split(clean_text, masked_text):
            add(_ast_hits(clean, read, known))
            add(_regex_hits(clean, masked, known))
            _, strings, bodies = _mask(clean, backslash)
            for body in bodies:
                for hit in detect_destructive(body, dialect, known_types):
                    add([DestructiveHit("dynamic_sql", hit.severity, _trim_stmt(clean), f"Dollar-quoted body contains {hit.kind}.", "fallback")])
            if _DYNAMIC_START.match(masked):
                for text in strings:
                    for hit in detect_destructive(text, dialect, known_types):
                        add([DestructiveHit("dynamic_sql", hit.severity, _trim_stmt(clean), f"Dynamic SQL string contains {hit.kind}.", "fallback")])
                if _OPAQUE_CALL.match(masked) and not strings:
                    add([DestructiveHit("opaque_call", RISKY, _trim_stmt(clean), "The called code cannot be inspected.", "fallback")])
    return out


def is_destructive(sql: str, dialect: Optional[str] = None, known_types: Optional[dict[str, str]] = None) -> bool:
    return any(h.severity == DESTRUCTIVE for h in detect_destructive(sql, dialect, known_types))


# --- financial protection ---------------------------------------------------

def financial_patterns_from(profile: Any = None, extra: Optional[Sequence[str]] = None) -> tuple[str, ...]:
    """Defaults, plus ``profile.financial_table_patterns`` or ``profile.rules['migration.financial']['patterns']``."""
    found = list(DEFAULT_FINANCIAL_PATTERNS)
    if profile is not None:
        attr = getattr(profile, "financial_table_patterns", None)
        if attr:
            found.extend(attr)
        rules = getattr(profile, "rules", None) or {}
        section = rules.get("migration.financial") or {}
        found.extend(section.get("patterns") or (section.get("params") or {}).get("patterns") or [])
    found.extend(extra or [])
    return tuple(dict.fromkeys(found))


def is_financial_table(name: Optional[str], patterns: Sequence[str] = DEFAULT_FINANCIAL_PATTERNS) -> bool:
    if not name:
        return False
    short = str(name).split(".")[-1]
    for pattern in patterns:
        try:
            if re.search(pattern, short, re.I):
                return True
        except re.error:
            if pattern.lower() in short.lower():
                return True
    return False


# --- approval ---------------------------------------------------------------

def plan_hash(plan: Any) -> str:
    """SHA-256 of the canonical plan content. Any change to the SQL, checks or flags changes the hash."""
    data = plan.to_dict() if hasattr(plan, "to_dict") else plan
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def require_approval(plan: Any, token: Optional[str]) -> str:
    """Return the plan hash, or raise ``ApprovalRequired`` unless ``token`` equals it exactly."""
    expected = plan_hash(plan)
    if not isinstance(token, str) or not token or not hmac.compare_digest(token, expected):
        raise ApprovalRequired("The approval token does not match this exact migration plan. "
                               "Review the plan and supply its plan_hash as the token.")
    return expected


# --- backup -----------------------------------------------------------------

_BACKUP = {
    "postgres": ("Take a verified physical base backup with continuous WAL archiving (pg_basebackup or your backup "
                 "platform), or confirm the latest one is usable. pg_dump is a supplement only, useful for portable "
                 "or partial restore."),
    "mysql": ("Take a verified physical backup with binary logging enabled (for example Percona XtraBackup or MySQL "
              "Enterprise Backup) so point-in-time recovery is possible. mysqldump --single-transaction is a supplement "
              "only, for portable or partial restore."),
    "sqlite": ("Close writers and copy the database with the .backup command or VACUUM INTO to a separate location. "
               "Do not copy the file while another process has it open for writing."),
}


def backup_recommendation(dialect: str) -> str:
    """Backup advice aligned with BDR-003, BDR-004, BDR-005 and BDR-007."""
    base = _BACKUP[normalize_dialect(dialect)]
    return (f"{base} A replica or standby is not a backup. Restore the backup to a separate instance and verify it "
            "before relying on it, and record the time so the recovery point is known.")
