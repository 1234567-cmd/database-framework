"""Read-only guard, connector interface, URL handling and the connector registry.

The guard is deliberately fail-closed: anything it cannot classify with certainty is rejected. It is the
second of two layers; every connector also puts its session into a database-enforced read-only mode.
"""
from __future__ import annotations

import abc
import os
import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional, Sequence
from urllib.parse import quote as _urlquote, unquote

from ..model import Database


class ConnectorError(Exception):
    """A connection or query failed. The message never contains a password."""


class ReadOnlyViolation(ConnectorError):
    """A statement was refused because it is not provably read-only."""


# --------------------------------------------------------------------------------------------------------------------
# Read-only guard
# --------------------------------------------------------------------------------------------------------------------

_MODES = ("postgres", "mysql", "sqlite")
_ALIASES = {"postgresql": "postgres", "mariadb": "mysql", "sqlite3": "sqlite"}

# Words that may not appear (unquoted) anywhere in a SELECT or WITH statement.
_WRITE_VERBS = {
    "INSERT", "UPDATE", "DELETE", "MERGE", "UPSERT", "DROP", "ALTER", "CREATE", "TRUNCATE", "GRANT", "REVOKE",
    "RENAME", "INTO", "ATTACH", "DETACH", "VACUUM", "REINDEX", "CALL", "EXEC", "EXECUTE", "COPY",
}
_DML_VERBS = {"INSERT", "UPDATE", "DELETE", "MERGE", "REPLACE"}

# Built-in functions that write, touch the file system, signal other sessions, take locks or stall the server.
_FORBIDDEN_FUNCTIONS = {
    "pg_read_file", "pg_read_binary_file", "pg_ls_dir", "pg_stat_file", "pg_reload_conf", "pg_rotate_logfile",
    "pg_terminate_backend", "pg_cancel_backend", "pg_switch_wal", "pg_create_restore_point", "pg_start_backup",
    "pg_stop_backup", "pg_backup_start", "pg_backup_stop", "pg_promote", "pg_sleep", "pg_sleep_for",
    "pg_sleep_until", "pg_advisory_lock", "pg_advisory_lock_shared", "pg_advisory_xact_lock",
    "pg_advisory_xact_lock_shared", "pg_try_advisory_lock", "pg_try_advisory_lock_shared",
    "pg_try_advisory_xact_lock", "pg_try_advisory_xact_lock_shared", "pg_logical_emit_message",
    "pg_create_physical_replication_slot", "pg_create_logical_replication_slot", "pg_drop_replication_slot",
    "pg_stat_reset", "pg_stat_statements_reset", "nextval", "setval", "set_config", "lo_import", "lo_export",
    "lo_create", "lo_creat", "lo_unlink", "lo_put", "lo_from_bytea", "lo_open", "lo_write", "lowrite",
    "dblink", "dblink_exec", "dblink_connect", "dblink_send_query", "query_to_xml", "table_to_xml",
    "cursor_to_xml", "schema_to_xml", "database_to_xml", "query_to_xml_and_xmlschema",
    "sleep", "benchmark", "load_file", "get_lock", "release_lock", "release_all_locks", "master_pos_wait",
    "source_pos_wait", "load_extension", "writefile", "readfile", "edit", "fts3_tokenizer",
}

# PRAGMAs callable with an argument (introspection), and PRAGMAs only callable bare, because passing them a value writes.
_PRAGMA_WITH_ARG = {
    "table_info", "table_xinfo", "index_list", "index_info", "index_xinfo", "foreign_key_list", "foreign_key_check",
    "integrity_check", "quick_check", "table_list",
}
_PRAGMA_BARE = {
    "database_list", "collation_list", "compile_options", "encoding", "page_count", "page_size", "freelist_count",
    "schema_version", "user_version", "journal_mode", "foreign_keys", "function_list", "module_list", "pragma_list",
    "auto_vacuum", "query_only", "synchronous", "application_id", "table_list", "integrity_check", "quick_check",
    "foreign_key_check", "data_version", "secure_delete",
}

_DOLLAR_RE = re.compile(r"\$([A-Za-z_\u0080-\uffff][A-Za-z_0-9\u0080-\uffff]*)?\$")
_WORD_RE = re.compile(r"[\w$]+", re.UNICODE)


@dataclass(frozen=True)
class _Tok:
    kind: str  # word | string | punct
    text: str
    start: int
    end: int
    quote: str = ""

    @property
    def upper(self) -> str:
        return self.text.upper() if self.kind == "word" else ""


def _deny(reason: str) -> ReadOnlyViolation:
    return ReadOnlyViolation(f"statement refused by the read-only guard: {reason}")


def _lex(sql: str, mode: str) -> list[_Tok]:
    """Tokenize as the given engine would, raising ReadOnlyViolation on anything the engines might read differently."""
    toks: list[_Tok] = []
    i, n = 0, len(sql)
    eol = "\n\r" if mode == "postgres" else "\n"
    while i < n:
        c = sql[i]
        if c.isspace():
            i += 1
        elif sql.startswith("--", i):
            if mode == "mysql" and i + 2 < n and not sql[i + 2].isspace():
                toks.append(_Tok("punct", "-", i, i + 1))  # MySQL reads "1--1" as arithmetic, not a comment
                i += 1
            else:
                while i < n and sql[i] not in eol:
                    i += 1
        elif c == "#" and mode == "mysql":
            while i < n and sql[i] != "\n":
                i += 1
        elif sql.startswith("/*", i):
            if sql.startswith(("/*!", "/*M!"), i):
                raise _deny("executable conditional comment")
            end = sql.find("*/", i + 2)
            if end < 0:
                raise _deny("unterminated comment")
            if "/*" in sql[i + 2:end]:
                raise _deny("nested comment, which engines parse differently")
            i = end + 2
        elif c in "'\"" or (c == "`" and mode != "postgres"):
            j = i + 1
            while True:
                j = sql.find(c, j)
                if j < 0:
                    raise _deny("unterminated quoted text")
                if sql.startswith(c * 2, j):
                    j += 2
                    continue
                break
            body = sql[i + 1:j]
            if c != "`" and (f"\\{c}" in body or body.endswith("\\")):
                raise _deny("backslash next to a quote, which engines parse differently")
            toks.append(_Tok("string", body, i, j + 1, c))
            i = j + 1
        elif c == "[" and mode == "sqlite":
            j = sql.find("]", i + 1)
            if j < 0:
                raise _deny("unterminated bracket identifier")
            toks.append(_Tok("string", sql[i + 1:j], i, j + 1, "["))
            i = j + 1
        elif c == "$" and mode == "postgres" and (m := _DOLLAR_RE.match(sql, i)):
            j = sql.find(m.group(0), m.end())
            if j < 0:
                raise _deny("unterminated dollar quote")
            toks.append(_Tok("string", sql[m.end():j], i, j + len(m.group(0)), "$"))
            i = j + len(m.group(0))
        elif m := _WORD_RE.match(sql, i):
            toks.append(_Tok("word", m.group(0), i, m.end()))
            i = m.end()
        else:
            toks.append(_Tok("punct", c, i, i + 1))
            i += 1
    return toks


def _check_select_body(toks: list[_Tok]) -> None:
    for pos, t in enumerate(toks):
        nxt = toks[pos + 1] if pos + 1 < len(toks) else None
        prev = toks[pos - 1] if pos else None
        followed_by_paren = nxt is not None and nxt.text == "(" and nxt.kind == "punct"
        if followed_by_paren and t.text.lower() in _FORBIDDEN_FUNCTIONS and (t.kind == "word" or t.quote != "'"):
            raise _deny(f"call to forbidden function {t.text.lower()}")
        word = t.upper
        if not word or (prev is not None and prev.text == "." and prev.kind == "punct"):
            continue
        if word in _WRITE_VERBS:
            raise _deny(f"contains {word}")
        if word == "REPLACE" and not followed_by_paren:
            raise _deny("contains REPLACE")
        if word == "FOR" and nxt is not None and nxt.upper in {"SHARE", "NO", "KEY"}:
            raise _deny("contains a locking clause")
        if word == "LOCK" and nxt is not None and nxt.upper == "IN":
            raise _deny("contains a locking clause")


def _check_explain(toks: list[_Tok]) -> None:
    i, analyze = 1, False
    if i < len(toks) and toks[i].text == "(" and toks[i].kind == "punct":
        depth = 0
        while i < len(toks):
            if toks[i].kind == "punct" and toks[i].text == "(":
                depth += 1
            elif toks[i].kind == "punct" and toks[i].text == ")":
                depth -= 1
                if depth == 0:
                    i += 1
                    break
            elif toks[i].upper in {"ANALYZE", "ANALYSE"}:
                analyze = True
            i += 1
    else:
        while i < len(toks):
            word = toks[i].upper
            if word in {"ANALYZE", "ANALYSE"}:
                analyze = True
                i += 1
            elif word in {"VERBOSE", "EXTENDED", "PARTITIONS", "QUERY", "PLAN"}:
                i += 1
            elif word == "FORMAT" and i + 2 < len(toks) and toks[i + 1].text == "=":
                i += 3
            else:
                break
    if i >= len(toks):
        raise _deny("EXPLAIN without a statement")
    head = toks[i].upper
    if head in {"SELECT", "WITH"}:
        _check_select_body(toks[i:])
    elif head in _DML_VERBS and not analyze:
        return  # planning only: nothing is executed
    else:
        raise _deny("EXPLAIN ANALYZE is only allowed for SELECT" if analyze else "unsupported EXPLAIN target")


def _check_pragma(toks: list[_Tok]) -> None:
    rest = toks[1:]
    if len(rest) >= 3 and rest[1].text == "." and rest[1].kind == "punct":  # schema.pragma
        rest = rest[2:]
    if not rest or rest[0].kind != "word":
        raise _deny("malformed PRAGMA")
    name = rest[0].text.lower()
    if any(t.kind == "punct" and t.text == "=" for t in rest):
        raise _deny("PRAGMA assignment")
    if len(rest) == 1:
        if name not in _PRAGMA_BARE:
            raise _deny(f"PRAGMA {name} is not on the allow-list")
        return
    if name not in _PRAGMA_WITH_ARG:
        raise _deny(f"PRAGMA {name} may not take an argument")


def _check_mode(sql: str, mode: str) -> None:
    toks = _lex(sql, mode)
    while toks and toks[-1].kind == "punct" and toks[-1].text == ";":
        toks.pop()
    if not toks:
        raise _deny("empty statement")
    if any(t.kind == "punct" and t.text == ";" for t in toks):
        raise _deny("multiple statements")
    head = toks[0].upper
    if head in {"SELECT", "WITH"}:
        _check_select_body(toks)
    elif head == "EXPLAIN":
        _check_explain(toks)
    elif head == "SHOW":
        if len(toks) < 2:
            raise _deny("malformed SHOW")
    elif head in {"DESCRIBE", "DESC"}:
        for t in toks[1:]:
            if t.kind == "punct" and t.text != ".":
                raise _deny("malformed DESCRIBE")
            if t.upper in _WRITE_VERBS | _DML_VERBS | {"SELECT", "WITH", "ANALYZE", "ANALYSE", "FORMAT", "EXPLAIN"}:
                raise _deny("DESCRIBE may only name a table")
        if len(toks) < 2:
            raise _deny("malformed DESCRIBE")
    elif head == "PRAGMA":
        _check_pragma(toks)
    else:
        raise _deny("only SELECT, WITH, EXPLAIN, SHOW, DESCRIBE and allow-listed PRAGMA are permitted")


def assert_read_only(sql: str, dialect: Optional[str] = None) -> None:
    """Raise ReadOnlyViolation unless ``sql`` is one provably read-only statement.

    With a dialect, the text is read as that engine reads it. Without one, it must pass under every supported
    engine's lexical rules, because comment and quote syntax differ between them and those differences can hide writes.
    """
    if not isinstance(sql, str):
        raise _deny("statement is not text")
    if "\x00" in sql:
        raise _deny("NUL byte in statement")
    mode = _ALIASES.get((dialect or "").lower(), (dialect or "").lower())
    for m in ([mode] if mode in _MODES else _MODES):
        _check_mode(sql, m)


def _adapt_placeholders(sql: str, dialect: str, paramstyle: str) -> str:
    """Accept both ``?`` and ``%s`` placeholders and emit the driver's own style. Only called when params are bound."""
    mode = _ALIASES.get(dialect, dialect)
    toks = _lex(sql, mode if mode in _MODES else "postgres")
    out: list[str] = []
    pos = 0

    def gap(text: str) -> str:
        return text.replace("%", "%%") if paramstyle == "format" else text

    skip_next = False
    for i, t in enumerate(toks):
        out.append(gap(sql[pos:t.start]))
        pos = t.end
        if skip_next:
            skip_next = False
            continue
        nxt = toks[i + 1] if i + 1 < len(toks) else None
        is_percent_s = t.kind == "punct" and t.text == "%" and nxt is not None and nxt.start == t.end and nxt.text == "s"
        if is_percent_s:
            out.append("%s" if paramstyle == "format" else "?")
            skip_next = True
        elif t.kind == "punct" and t.text == "?":
            out.append("%s" if paramstyle == "format" else "?")
        else:
            out.append(gap(sql[t.start:t.end]))
    out.append(gap(sql[pos:]))
    return "".join(out)


# --------------------------------------------------------------------------------------------------------------------
# URLs and redaction
# --------------------------------------------------------------------------------------------------------------------

_SCHEME_RE = re.compile(r"^([A-Za-z][A-Za-z0-9+.\-]*)://(.*)$", re.S)
_QUERY_SECRET_RE = re.compile(r"(?i)((?:password|passwd|pwd|sslpassword)=)[^&#\s]*")
_ANY_URL_CREDS_RE = re.compile(r"([A-Za-z][A-Za-z0-9+.\-]*://[^\s/:@]*:)[^\s@]*(@)")


def _split_authority(rest: str) -> tuple[str, str]:
    """Split the text after ``scheme://`` into authority and the remainder, tolerating unescaped passwords."""
    if rest.startswith("/"):
        return "", rest
    m = re.search(r"[/?#]", rest)
    if not m:
        return rest, ""
    authority = rest[: m.start()]
    host_part = authority.rsplit("@", 1)[-1]
    if "@" in rest[m.start():] and ":" in host_part:
        port = host_part.rsplit(":", 1)[1]
        if not port.isdigit():  # a password containing / ? or #, written without percent-encoding
            at = rest.rfind("@")
            tail = re.search(r"[/?#]", rest[at:])
            cut = at + tail.start() if tail else len(rest)
            return rest[:cut], rest[cut:]
    return authority, rest[m.start():]


def redact_url(url: str) -> str:
    """Return ``url`` with any password replaced by ``***``."""
    m = _SCHEME_RE.match(url or "")
    if not m:
        return _QUERY_SECRET_RE.sub(r"\1***", url or "")
    scheme, rest = m.group(1), m.group(2)
    authority, tail = _split_authority(rest)
    if "@" in authority:
        userinfo, host = authority.rsplit("@", 1)
        if ":" in userinfo:
            userinfo = userinfo.split(":", 1)[0] + ":***"
        authority = f"{userinfo}@{host}"
    tail = _QUERY_SECRET_RE.sub(r"\1***", tail)
    return f"{scheme}://{authority}{tail}"


@dataclass
class ConnectionInfo:
    """A parsed connection URL. The password is excluded from ``repr``."""
    scheme: str
    host: Optional[str] = None
    port: Optional[int] = None
    user: Optional[str] = None
    password: Optional[str] = field(default=None, repr=False)
    database: str = ""
    options: dict[str, str] = field(default_factory=dict, repr=False)

    @property
    def secrets(self) -> list[str]:
        values = [self.password] if self.password else []
        values += [v for k, v in self.options.items() if k.lower() in {"password", "passwd", "pwd", "sslpassword"} and v]
        return values


def parse_url(url: str) -> ConnectionInfo:
    m = _SCHEME_RE.match(url or "")
    if not m:
        raise ConnectorError(f"not a connection URL: {redact_url(url or '')}")
    scheme, rest = m.group(1).lower(), m.group(2)
    if scheme in {"sqlite", "sqlite3"}:
        return ConnectionInfo(scheme="sqlite", database=_sqlite_path(rest))
    authority, tail = _split_authority(rest)
    info = ConnectionInfo(scheme=scheme)
    if "@" in authority:
        userinfo, authority = authority.rsplit("@", 1)
        user, sep, password = userinfo.partition(":")
        info.user = unquote(user) or None
        if sep and password:
            info.password = unquote(password)
    if authority.startswith("["):  # IPv6
        host, _, port_part = authority[1:].partition("]")
        port_text = port_part.lstrip(":")
    else:
        host, _, port_text = authority.partition(":")
    info.host = host or None
    if port_text:
        if not port_text.isdigit():
            raise ConnectorError(f"invalid port in URL: {redact_url(url)}")
        info.port = int(port_text)
    path, _, query = tail.partition("?")
    info.database = unquote(path.lstrip("/"))
    for pair in filter(None, query.split("#", 1)[0].split("&")):
        k, _, v = pair.partition("=")
        info.options[unquote(k)] = unquote(v)
    return info


def _sqlite_path(rest: str) -> str:
    """``sqlite:///C:/x.db`` and ``sqlite:////abs/x.db`` are absolute. ``sqlite:///x.db`` is relative unless only the absolute path exists."""
    path = unquote(rest.split("?", 1)[0])
    if re.match(r"^/[A-Za-z]:", path):
        return path[1:]
    if path.startswith("//"):
        return path[1:]
    if path.startswith("/"):
        relative = path[1:]
        return path if os.path.exists(path) and not os.path.exists(relative) else relative
    return path


def scrub(text: str, secrets: Iterable[str] = ()) -> str:
    """Remove known secrets and URL credentials from ``text``."""
    for secret in secrets:
        if secret:
            text = text.replace(secret, "***").replace(_urlquote(secret, safe=""), "***")
    text = _ANY_URL_CREDS_RE.sub(r"\1***\2", text)
    return _QUERY_SECRET_RE.sub(r"\1***", text)


# --------------------------------------------------------------------------------------------------------------------
# Connector
# --------------------------------------------------------------------------------------------------------------------


class Connector(abc.ABC):
    """Read-only access to one database. Satisfies ``model.DataAccess``.

    To add an engine: subclass, implement ``_execute``, ``extract`` and ``close``, accept a ``ConnectionInfo`` in the
    constructor, put the session in the engine's read-only mode there, and call ``register_connector``.
    """
    dialect: str = "generic"
    paramstyle: str = "format"  # format (%s) or qmark (?)

    def __init__(self, info: Optional[ConnectionInfo] = None):
        self.info = info
        self._secrets: list[str] = info.secrets if info else []

    @abc.abstractmethod
    def _execute(self, sql: str, params: Sequence[Any]) -> list[tuple]:
        """Run an already-guarded statement."""

    @abc.abstractmethod
    def extract(self) -> Database:
        """Read metadata and return a Database whose ``data`` is this connector."""

    @abc.abstractmethod
    def close(self) -> None:
        """Release the connection."""

    def query(self, sql: str, params: Sequence[Any] = ()) -> list[tuple]:
        """Run one read-only statement. ``?`` and ``%s`` placeholders are both accepted when params are given."""
        assert_read_only(sql, dialect=self.dialect)
        statement = _adapt_placeholders(sql, self.dialect, self.paramstyle) if params else sql
        try:
            return self._execute(statement, params)
        except ConnectorError:
            raise
        except Exception as exc:
            raise ConnectorError(self._clean(exc)) from None

    def quote(self, identifier: str) -> str:
        return '"' + identifier.replace('"', '""') + '"'

    def _clean(self, exc: Any) -> str:
        return scrub(f"{type(exc).__name__}: {exc}".strip(), self._secrets)

    def _section(self, db: Database, label: str, sql: str, params: Sequence[Any] = ()) -> Optional[list[tuple]]:
        """Run a metadata query; a failure (usually a missing privilege) becomes an import warning."""
        try:
            return self.query(sql, params)
        except ReadOnlyViolation:
            raise
        except ConnectorError as exc:
            db.import_warnings.append(f"{label} not read: {exc}")
            return None

    def __enter__(self) -> "Connector":
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"<{type(self).__name__} dialect={self.dialect}>"


def import_driver(module: str, extra: str):
    """Import an optional database driver, or explain how to get it."""
    import importlib
    try:
        return importlib.import_module(module)
    except ImportError:
        raise ConnectorError(f"the {module} driver is not installed; run: pip install dbintel[{extra}]") from None


_REGISTRY: dict[str, type] = {}
_SCHEME_ALIASES = {"postgres": "postgresql", "mariadb": "mysql", "sqlite3": "sqlite"}


def register_connector(scheme: str, cls: type) -> None:
    """Make URLs with this scheme open ``cls``. ``cls`` is constructed with one ``ConnectionInfo`` argument."""
    _REGISTRY[scheme.lower()] = cls


def open_connector(url: str, password_env: Optional[str] = None) -> Connector:
    """Open a read-only connector. A password comes from the named environment variable, or else from the URL."""
    info = parse_url(url)
    if password_env:
        value = os.environ.get(password_env)
        if value is None:
            raise ConnectorError(f"environment variable {password_env} is not set")
        info.password = value
    scheme = _SCHEME_ALIASES.get(info.scheme, info.scheme)
    cls = _REGISTRY.get(scheme) or _REGISTRY.get(info.scheme)
    if cls is None:
        raise ConnectorError(f"no connector registered for scheme {info.scheme!r}; known: {', '.join(sorted(_REGISTRY))}")
    try:
        return cls(info)
    except ConnectorError:
        raise
    except Exception as exc:
        raise ConnectorError(scrub(f"{type(exc).__name__}: {exc}", info.secrets)) from None


# --------------------------------------------------------------------------------------------------------------------
# Helpers shared by connectors and importers
# --------------------------------------------------------------------------------------------------------------------

_REF_RE = re.compile(r"""(?is)\b(?:from|join|into|update)\s+((?:[`"\[]?[\w$]+[`"\]]?\.)*[`"\[]?[\w$]+[`"\]]?)""")
_NOT_TABLES = {"select", "set", "only", "lateral", "unnest", "dual", "values", "new", "old", "where", "on"}


def sql_references(sql: str, dialect: Optional[str] = None) -> list[str]:
    """Bare names of the tables a statement reads or writes, excluding CTEs. Falls back to a regex if unparseable."""
    if not (sql or "").strip():
        return []
    try:
        import sqlglot
        from sqlglot import exp
        tree = sqlglot.parse_one(sql, dialect=None if dialect in (None, "generic") else dialect)
        ctes = {c.alias.lower() for c in tree.find_all(exp.CTE)}
        names = [t.name for t in tree.find_all(exp.Table) if t.name and t.name.lower() not in ctes]
    except Exception:
        names = [m.group(1).split(".")[-1].strip('`"[]') for m in _REF_RE.finditer(sql)]
        names = [n for n in names if n.lower() not in _NOT_TABLES]
    seen: dict[str, None] = {}
    for n in names:
        seen.setdefault(n)
    return list(seen)


__all__ = [
    "ConnectionInfo", "Connector", "ConnectorError", "ReadOnlyViolation", "assert_read_only", "import_driver",
    "open_connector", "parse_url", "redact_url", "register_connector", "scrub", "sql_references",
]
