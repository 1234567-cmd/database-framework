"""Read a SQL dump into the model without ever executing it.

Statements are split by a dump-aware scanner, tokenized with sqlglot, and interpreted here. Keeping this at token level
preserves each column's original type text, which sqlglot's AST normalizes. Row data is parsed into Python values
and bound into a private SQLite sandbox.
"""
from __future__ import annotations

import csv
import io
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Optional, Union

from sqlglot.dialects.dialect import Dialect

from ..connectors.base import _NOT_TABLES, _REF_RE, sql_references
from ..model import (CheckConstraint, Column, Database, ForeignKey, Grant, Index, RlsPolicy, Role, Routine, Table, View)
from ._common import Sandbox, read_text

MAX_WARNINGS = 500
_SERIAL = {"serial", "bigserial", "smallserial", "serial2", "serial4", "serial8"}
_DIALECTS = {"postgresql": "postgres", "pg": "postgres", "mariadb": "mysql", "sqlite3": "sqlite", "": "generic", None: "generic"}

_SIGNALS = {
    "mysql": [r"`\w+`", r"\bENGINE\s*=", r"\bAUTO_INCREMENT\b", r"/\*!\d+", r"\bLOCK TABLES\b", r"\bunsigned\b",
              r"\bmysqldump\b", r"\bCHARSET\s*="],
    "postgres": [r"\bCOPY\s+\S+.*FROM\s+stdin", r"\bpg_catalog\b", r"\bALTER TABLE ONLY\b", r"\bSET search_path\b", r"::\w+",
                 r"\bbigserial\b|\bserial\b", r"\bjsonb\b|\btimestamptz\b|\bbytea\b", r"\bPostgreSQL database dump\b",
                 r"\bCREATE EXTENSION\b", r"\$\$", r"\bROW LEVEL SECURITY\b"],
    "sqlite": [r"\bPRAGMA\s+foreign_keys\b", r"\bAUTOINCREMENT\b", r"\bsqlite_sequence\b", r"\bWITHOUT ROWID\b",
               r"\bBEGIN TRANSACTION;"],
}
_SIGNALS_RE = {d: [re.compile(p, re.I) for p in ps] for d, ps in _SIGNALS.items()}


def detect_dialect(text: str) -> str:
    """Return the dialect with the most signals in the dump's first 2 MB, or ``generic``."""
    sample = text[:2_000_000]
    scores = {d: sum(1 for r in rs if r.search(sample)) for d, rs in _SIGNALS_RE.items()}
    best = max(scores, key=lambda d: scores[d])
    return best if scores[best] else "generic"


def _normalize_dialect(dialect: Optional[str]) -> str:
    low = dialect.lower() if dialect else dialect
    return _DIALECTS.get(low, low)  # type: ignore[arg-type]


# --------------------------------------------------------------------------------------------------------------------
# Statement splitting
# --------------------------------------------------------------------------------------------------------------------


@dataclass
class _Statement:
    text: str
    copy_lines: Optional[list[str]] = None


_DELIM_RE = re.compile(r"\s*DELIMITER[ \t]+(\S+)[^\n]*", re.I)
_META_RE = re.compile(r"\s*\\(\w+)[^\n]*")
_COND_OPEN = re.compile(r"/\*M?!\d*")
_DOLLAR = re.compile(r"\$([A-Za-z_][A-Za-z_0-9]*)?\$")
_COMPOUND_HEAD = re.compile(r"(?is)^\s*CREATE\b.{0,200}?\b(TRIGGER|PROCEDURE|FUNCTION|EVENT)\b")
_COPY_STDIN = re.compile(r"(?is)^\s*COPY\b.*\bFROM\s+stdin\b")


def _scan_string(text: str, i: int, quote: str, backslash: bool) -> int:
    """Return the index after the closing quote that opens at ``i``."""
    n = len(text)
    j = i + 1
    while j < n:
        c = text[j]
        if backslash and c == "\\":
            j += 2
        elif c == quote:
            if j + 1 < n and text[j + 1] == quote:
                j += 2
            else:
                return j + 1
        else:
            j += 1
    return n


def _block_depth(code: str) -> int:
    """BEGIN/CASE minus END, used to find the end of compound bodies written without DELIMITER."""
    depth = 0
    for word in re.findall(r"\b(BEGIN|CASE|END)\b", code, re.I):
        depth += -1 if word.upper() == "END" else 1
    return depth


def split_statements(text: str, dialect: str, meta: Optional[dict] = None) -> Iterator[_Statement]:
    """Yield statements with comments removed and MySQL conditional comments unwrapped."""
    mysql = dialect == "mysql"
    postgres = dialect == "postgres"
    delimiter = ";"
    interesting = re.compile("'|\"|`|--|/\\*|\\*/|#|\\$|" + re.escape(delimiter))
    i, n = 0, len(text)
    buf: list[str] = []
    code: list[str] = []
    cond_depth = 0

    def statement_open() -> bool:
        return any(part.strip() for part in buf)

    while i < n:
        if not statement_open():
            m = _DELIM_RE.match(text, i)
            if m:
                delimiter = m.group(1)
                interesting = re.compile("'|\"|`|--|/\\*|\\*/|#|\\$|" + re.escape(delimiter))
                i = m.end()
                continue
            m = _META_RE.match(text, i)
            if m:  # psql meta-command such as \connect or \restrict
                if meta is not None and m.group(1).lower() in {"connect", "c"}:
                    parts = m.group(0).split()
                    if len(parts) > 1:
                        meta["database"] = parts[1].strip('"')
                i = m.end()
                continue
        m = interesting.search(text, i)
        if not m:
            buf.append(text[i:])
            code.append(text[i:])
            break
        p = m.start()
        buf.append(text[i:p])
        code.append(text[i:p])
        token = m.group(0)
        if token == delimiter:
            i = p + len(delimiter)
            joined_code = "".join(code)
            if (delimiter == ";" and not postgres and _COMPOUND_HEAD.match(joined_code)
                    and re.search(r"\bBEGIN\b", joined_code, re.I) and _block_depth(joined_code) > 0):
                buf.append(delimiter)  # a statement inside a compound body
                code.append(delimiter)
                continue
            stmt = "".join(buf).strip()
            buf, code = [], []
            cond_depth = 0
            if not stmt:
                continue
            statement = _Statement(stmt)
            if _COPY_STDIN.match(stmt):
                nl = text.find("\n", i)
                i = n if nl < 0 else nl + 1
                lines: list[str] = []
                while i < n:
                    nl = text.find("\n", i)
                    end = n if nl < 0 else nl
                    line = text[i:end].rstrip("\r")
                    i = n if nl < 0 else nl + 1
                    if line == "\\.":
                        break
                    lines.append(line)
                statement.copy_lines = lines
            yield statement
            continue
        if token in ("'", '"', "`"):
            backslash = token != "`" and (mysql or (postgres and p > 0 and text[p - 1] in "eE" and token == "'"))
            end = _scan_string(text, p, token, backslash)
            buf.append(text[p:end])
            code.append(" ")
            i = end
        elif token == "--":
            if mysql and p + 2 < n and not text[p + 2].isspace():
                buf.append("--")
                code.append("--")
                i = p + 2
            else:
                nl = text.find("\n", p)
                i = n if nl < 0 else nl
        elif token == "#":
            if mysql:
                nl = text.find("\n", p)
                i = n if nl < 0 else nl
            else:
                buf.append("#")
                code.append("#")
                i = p + 1
        elif token == "/*":
            m2 = _COND_OPEN.match(text, p)
            if m2:
                cond_depth += 1
                buf.append(" ")
                code.append(" ")
                i = m2.end()
            else:
                end = _comment_end(text, p, postgres)
                buf.append(" ")
                i = end
        elif token == "*/":
            if cond_depth:
                cond_depth -= 1
                buf.append(" ")
                code.append(" ")
            else:
                buf.append("*/")
                code.append("*/")
            i = p + 2
        elif token == "$":
            m2 = _DOLLAR.match(text, p) if postgres else None
            if m2 and not (p > 0 and (text[p - 1].isalnum() or text[p - 1] == "_")):
                close = text.find(m2.group(0), m2.end())
                end = n if close < 0 else close + len(m2.group(0))
                buf.append(text[p:end])
                code.append(" ")
                i = end
            else:
                buf.append("$")
                code.append("$")
                i = p + 1
    stmt = "".join(buf).strip()
    if stmt:
        yield _Statement(stmt)


def _comment_end(text: str, p: int, nested: bool) -> int:
    if not nested:
        end = text.find("*/", p + 2)
        return len(text) if end < 0 else end + 2
    depth, i = 1, p + 2
    while depth and i < len(text):
        if text.startswith("/*", i):
            depth += 1
            i += 2
        elif text.startswith("*/", i):
            depth -= 1
            i += 2
        else:
            i += 1
    return i


# --------------------------------------------------------------------------------------------------------------------
# Token cursor
# --------------------------------------------------------------------------------------------------------------------


class _ParseError(Exception):
    pass


class _Skip(Exception):
    """A statement that is valid but carries nothing for the model."""


@dataclass(frozen=True)
class _T:
    kind: str  # w word, id quoted identifier, str string, num number, p punctuation
    text: str
    start: int
    end: int

    @property
    def up(self) -> str:
        return self.text.upper() if self.kind == "w" else ""


def _tokenize(sql: str, dialect: str) -> list[_T]:
    glot = None if dialect == "generic" else dialect
    tokens = Dialect.get_or_raise(glot).tokenize(sql)
    out = []
    for t in tokens:
        name = t.token_type.name
        if name == "IDENTIFIER":
            kind = "id"
        elif name.endswith("STRING"):
            kind = "str"
        elif name == "NUMBER":
            kind = "num"
        elif t.text and (t.text[0].isalpha() or t.text[0] == "_"):
            source = sql[t.start:t.end + 1]
            if len(source.split()) > 1:  # sqlglot merges keywords such as PRIMARY KEY into one token
                out.extend(_T("w", m.group(0), t.start + m.start(), t.start + m.end()) for m in re.finditer(r"\S+", source))
                continue
            kind = "w"
        else:
            kind = "p"
        out.append(_T(kind, t.text, t.start, t.end + 1))
    return out


class _Cur:
    def __init__(self, toks: list[_T], sql: str, dialect: str):
        self.toks, self.sql, self.dialect = toks, sql, dialect
        self.i = 0

    def sub(self, lo: int, hi: int) -> "_Cur":
        return _Cur(self.toks[lo:hi], self.sql, self.dialect)

    @property
    def done(self) -> bool:
        return self.i >= len(self.toks)

    def peek(self, offset: int = 0) -> Optional[_T]:
        pos = self.i + offset
        return self.toks[pos] if 0 <= pos < len(self.toks) else None

    def up(self, offset: int = 0) -> str:
        t = self.peek(offset)
        return t.up if t else ""

    def is_p(self, text: str, offset: int = 0) -> bool:
        t = self.peek(offset)
        return t is not None and t.kind == "p" and t.text == text

    def word(self, *words: str) -> bool:
        """Consume this exact sequence of words if it is next."""
        for k, w in enumerate(words):
            if self.up(k) != w:
                return False
        self.i += len(words)
        return True

    def expect(self, *words: str) -> None:
        if not self.word(*words):
            got = self.peek().text if self.peek() else "end of statement"
            raise _ParseError(f"expected {' '.join(words)}, found {got}")

    def ident(self) -> str:
        t = self.peek()
        if t is None or t.kind not in ("w", "id", "str"):
            raise _ParseError(f"expected a name, found {t.text if t else 'end of statement'}")
        self.i += 1
        return t.text

    def dotted(self) -> list[str]:
        parts = [self.ident()]
        while self.is_p(".") and self.peek(1) is not None and self.peek(1).kind in ("w", "id", "str"):
            self.i += 1
            parts.append(self.ident())
        return parts

    def qualified(self) -> tuple[Optional[str], str]:
        parts = self.dotted()
        return (parts[-2] if len(parts) > 1 else None), parts[-1]

    def paren(self) -> tuple[int, int]:
        """With the cursor on ``(``, return the inner token range and move past ``)``."""
        if not self.is_p("("):
            raise _ParseError(f"expected ( but found {self.peek().text if self.peek() else 'end of statement'}")
        depth, start, j = 0, self.i + 1, self.i
        while j < len(self.toks):
            t = self.toks[j]
            if t.kind == "p" and t.text == "(":
                depth += 1
            elif t.kind == "p" and t.text == ")":
                depth -= 1
                if depth == 0:
                    self.i = j + 1
                    return start, j
            j += 1
        raise _ParseError("unbalanced parentheses")

    def slice(self, lo: int, hi: int) -> str:
        """Original text covering tokens lo to hi (exclusive)."""
        if lo >= hi:
            return ""
        return self.sql[self.toks[lo].start: self.toks[hi - 1].end].strip()

    def split_commas(self, lo: int, hi: int) -> list[tuple[int, int]]:
        parts, depth, start = [], 0, lo
        for j in range(lo, hi):
            t = self.toks[j]
            if t.kind == "p" and t.text in "([":
                depth += 1
            elif t.kind == "p" and t.text in ")]":
                depth -= 1
            elif depth == 0 and t.kind == "p" and t.text == ",":
                parts.append((start, j))
                start = j + 1
        if start < hi:
            parts.append((start, hi))
        return parts

    def skip_balanced(self) -> None:
        if self.is_p("("):
            self.paren()
        else:
            self.i += 1

    def skip_to_end(self) -> None:
        self.i = len(self.toks)


def _key_columns(c: _Cur, lo: int, hi: int) -> list[str]:
    names: list[str] = []
    for a, b in c.split_commas(lo, hi):
        item = c.sub(a, b)
        first = item.peek()
        if first is None:
            continue
        simple = first.kind in ("w", "id", "str") and item.peek(1) is None
        if not simple and first.kind in ("w", "id", "str"):
            # name(10) prefix length, or name ASC / opclass, but not a function call
            prefix = item.is_p("(", 1) and item.peek(2) is not None and item.peek(2).kind == "num" and item.is_p(")", 3)
            if prefix or not item.is_p("(", 1):
                simple = True
        names.append(first.text if simple else c.slice(a, b))
    return names


_TABLE_ITEM_START = {"CONSTRAINT", "PRIMARY", "UNIQUE", "FOREIGN", "CHECK", "FULLTEXT", "SPATIAL", "EXCLUDE", "PERIOD", "LIKE"}
_KEY_WORDS = {"KEY", "INDEX"}
_TYPE_STOP = {"NOT", "NULL", "DEFAULT", "PRIMARY", "UNIQUE", "KEY", "AUTO_INCREMENT", "AUTOINCREMENT", "COMMENT", "COLLATE",
              "REFERENCES", "CHECK", "GENERATED", "AS", "ON", "CONSTRAINT", "STORAGE", "COLUMN_FORMAT", "INVISIBLE", "VISIBLE",
              "CHARSET", "ENCODE"}
_DEFAULT_STOP = {"NOT", "NULL", "PRIMARY", "UNIQUE", "KEY", "AUTO_INCREMENT", "AUTOINCREMENT", "COMMENT", "COLLATE", "REFERENCES",
                 "CHECK", "GENERATED", "ON", "CONSTRAINT", "CHARSET", "STORAGE", "COLUMN_FORMAT", "INVISIBLE", "VISIBLE"}


def _is_table_item(item: _Cur) -> bool:
    if item.peek() is None or item.peek().kind != "w":
        return False
    head = item.up()
    if head in _TABLE_ITEM_START:
        return True
    return head in _KEY_WORDS and (item.is_p("(", 1) or item.is_p("(", 2) or item.up(1) in {"USING"})


def _references(c: _Cur, columns: list[str], name: Optional[str]) -> ForeignKey:
    c.expect("REFERENCES")
    schema, table = c.qualified()
    ref_columns: list[str] = []
    if c.is_p("("):
        lo, hi = c.paren()
        ref_columns = _key_columns(c, lo, hi)
    fk = ForeignKey(name=name, columns=columns, ref_table=table, ref_columns=ref_columns, ref_schema=schema)
    while not c.done:
        if c.word("ON", "DELETE"):
            fk.on_delete = _action(c)
        elif c.word("ON", "UPDATE"):
            fk.on_update = _action(c)
        elif c.word("MATCH"):
            c.i += 1
        elif c.word("NOT", "DEFERRABLE") or c.word("DEFERRABLE") or c.word("INITIALLY", "DEFERRED") or c.word("INITIALLY", "IMMEDIATE"):
            pass
        else:
            break
    return fk


def _action(c: _Cur) -> str:
    for words in (("NO", "ACTION"), ("SET", "NULL"), ("SET", "DEFAULT"), ("CASCADE",), ("RESTRICT",)):
        if c.word(*words):
            return " ".join(words)
    raise _ParseError("unknown referential action")


def _expr_columns(expression: str, table: Table, dialect: str) -> list[str]:
    import sqlglot
    from sqlglot import exp
    found: list[str] = []
    try:
        tree = sqlglot.parse_one(f"SELECT {expression}", dialect=None if dialect == "generic" else dialect)
        names = [col.name for col in tree.find_all(exp.Column)]
    except Exception:
        names = re.findall(r"[A-Za-z_][A-Za-z_0-9]*", expression)
    for name in names:
        column = table.column(name)
        if column is not None and column.name not in found:
            found.append(column.name)
    return found


def _table_item(c: _Cur, table: Table) -> None:
    name = None
    if c.word("CONSTRAINT"):
        if c.up() not in {"PRIMARY", "UNIQUE", "FOREIGN", "CHECK", "EXCLUDE"}:
            name = c.ident()
    if c.word("PRIMARY", "KEY"):
        c.word("CLUSTERED") or c.word("NONCLUSTERED")
        if c.word("USING"):
            c.i += 1
        lo, hi = c.paren()
        table.primary_key = _key_columns(c, lo, hi)
        table.primary_key_name = name
        return
    if c.word("UNIQUE"):
        c.word("KEY") or c.word("INDEX")
        index_name = name
        if not c.is_p("("):
            parsed = c.ident()
            index_name = index_name or parsed
        lo, hi = c.paren()
        method = c.peek(1).text if c.up() == "USING" and c.peek(1) else None
        table.indexes.append(Index(name=index_name, columns=_key_columns(c, lo, hi), unique=True, is_constraint=True, method=method))
        return
    if c.word("FOREIGN", "KEY"):
        if not c.is_p("("):
            parsed = c.ident()
            name = name or parsed
        lo, hi = c.paren()
        table.foreign_keys.append(_references(c, _key_columns(c, lo, hi), name))
        return
    if c.word("CHECK"):
        lo, hi = c.paren()
        expression = c.slice(lo, hi)
        table.checks.append(CheckConstraint(name=name, expression=expression,
                                            columns=_expr_columns(expression, table, c.dialect)))
        return
    method = None
    if c.up() in {"FULLTEXT", "SPATIAL"}:
        method = c.up()
        c.i += 1
    if c.word("KEY") or c.word("INDEX"):
        index_name = None if c.is_p("(") else c.ident()
        if c.word("USING"):
            method = c.ident()
        lo, hi = c.paren()
        columns = _key_columns(c, lo, hi)
        if c.word("USING"):
            method = c.ident()
        table.indexes.append(Index(name=index_name, columns=columns, method=method))
        return
    if c.up() in {"EXCLUDE", "PERIOD", "LIKE"}:
        return
    raise _ParseError(f"unsupported table clause near {c.peek().text if c.peek() else 'end of statement'}")


def _parse_column(c: _Cur, table: Table) -> Column:
    name = c.ident()
    lo = c.i
    depth = 0
    while not c.done:
        t = c.peek()
        if t.kind == "p" and t.text in "([":
            depth += 1
        elif t.kind == "p" and t.text in ")]":
            depth -= 1
        elif depth == 0 and t.kind == "w":
            if t.up in _TYPE_STOP or (t.up == "CHARACTER" and c.up(1) == "SET"):
                break
        c.i += 1
    data_type = c.slice(lo, c.i)
    if not data_type and c.dialect != "sqlite":
        raise _ParseError(f"column {name} has no type")
    column = Column(name=name, data_type=data_type, ordinal=len(table.columns) + 1)
    if data_type.lower() in _SERIAL:
        column.is_identity, column.nullable = True, False
    while not c.done:
        if c.word("NOT", "NULL"):
            column.nullable = False
        elif c.word("NULL"):
            pass
        elif c.word("DEFAULT"):
            column.default = _default(c)
        elif c.word("PRIMARY", "KEY"):
            table.primary_key = [name]
            column.nullable = False
            c.word("ASC") or c.word("DESC")
            if c.word("ON", "CONFLICT"):
                c.i += 1
        elif c.word("UNIQUE"):
            c.word("KEY")
            table.indexes.append(Index(name=None, columns=[name], unique=True, is_constraint=True))
            if c.word("ON", "CONFLICT"):
                c.i += 1
        elif c.word("KEY"):  # MySQL inline primary key
            table.primary_key = [name]
            column.nullable = False
        elif c.word("AUTO_INCREMENT") or c.word("AUTOINCREMENT"):
            column.is_identity, column.nullable = True, False
        elif c.word("COMMENT"):
            column.comment = c.ident()
        elif c.word("COLLATE"):
            column.collation = c.ident()
        elif c.word("CHARACTER", "SET") or c.word("CHARSET"):
            c.is_p("=") and c.skip_balanced()
            column.charset = c.ident()
        elif c.up() == "REFERENCES":
            table.foreign_keys.append(_references(c, [name], None))
        elif c.word("CHECK"):
            lo2, hi2 = c.paren()
            table.checks.append(CheckConstraint(name=None, expression=c.slice(lo2, hi2), columns=[name]))
        elif c.word("GENERATED"):
            if c.word("ALWAYS") or c.word("BY", "DEFAULT"):
                pass
            c.expect("AS")
            if c.word("IDENTITY"):
                column.is_identity, column.nullable = True, False
                if c.is_p("("):
                    c.paren()
            else:
                c.paren()
                column.is_generated = True
                c.word("STORED") or c.word("VIRTUAL")
        elif c.word("AS"):
            c.paren()
            column.is_generated = True
            c.word("STORED") or c.word("VIRTUAL") or c.word("PERSISTENT")
        elif c.word("ON", "UPDATE"):
            c.skip_balanced()
            if c.is_p("("):
                c.paren()
        elif c.word("ON", "CONFLICT"):
            c.i += 1
        elif c.word("CONSTRAINT"):
            c.ident()
        else:
            c.skip_balanced()
    return column


def _default(c: _Cur) -> Optional[str]:
    lo = c.i
    if c.done:
        raise _ParseError("DEFAULT without a value")
    c.skip_balanced()
    while not c.done:
        t = c.peek()
        if t.kind == "w" and (t.up in _DEFAULT_STOP or (t.up == "CHARACTER" and c.up(1) == "SET")):
            break
        c.skip_balanced()
    text = c.slice(lo, c.i)
    return None if text.upper() == "NULL" else text


def parse_create_table(sql: str, dialect: str = "generic") -> Table:
    """Parse one CREATE TABLE statement into a Table. Raises on anything it cannot interpret."""
    return _parse_create(sql, dialect)[0]


def _parse_create(sql: str, dialect: str) -> tuple[Table, Optional[int]]:
    """Return the table and its AUTO_INCREMENT=N option, which the model holds in Database.settings."""
    c = _Cur(_tokenize(sql, dialect), sql, dialect)
    c.expect("CREATE")
    while c.up() in {"OR", "REPLACE", "TEMP", "TEMPORARY", "GLOBAL", "LOCAL", "UNLOGGED"}:
        c.i += 1
    if c.up() == "FOREIGN":
        raise _Skip("foreign table")
    c.expect("TABLE")
    c.word("IF", "NOT", "EXISTS")
    schema, name = c.qualified()
    table = Table(name=name, schema=schema)
    if c.word("PARTITION", "OF"):
        raise _Skip("partition of another table")
    if c.up() in {"LIKE", "AS", "SELECT"}:
        raise _ParseError("CREATE TABLE without a column list is not imported")
    lo, hi = c.paren()
    for a, b in c.split_commas(lo, hi):
        item = c.sub(a, b)
        if _is_table_item(item):
            _table_item(item, table)
        else:
            table.columns.append(_parse_column(item, table))
    if not table.columns:
        raise _ParseError("no columns found")
    auto_increment = _table_options(c, table)
    _apply_key_nullability(table)
    return table, auto_increment


def _auto_increment_value(c: _Cur) -> Optional[int]:
    """With the cursor just past AUTO_INCREMENT, read ``[=] N``."""
    if c.is_p("="):
        c.i += 1
    t = c.peek()
    if t is None or t.kind != "num" or not t.text.isdigit():
        return None
    c.i += 1
    return int(t.text)


def _table_options(c: _Cur, table: Table) -> Optional[int]:
    auto_increment = None
    while not c.done:
        if c.word("AUTO_INCREMENT"):
            auto_increment = _auto_increment_value(c)
        elif c.word("ENGINE"):
            c.is_p("=") and c.skip_balanced()
            table.engine = c.ident()
        elif c.word("DEFAULT"):
            continue
        elif c.word("CHARACTER", "SET") or c.word("CHARSET"):
            c.is_p("=") and c.skip_balanced()
            table.charset = c.ident()
        elif c.word("COLLATE"):
            c.is_p("=") and c.skip_balanced()
            table.collation = c.ident()
        elif c.word("COMMENT"):
            c.is_p("=") and c.skip_balanced()
            table.comment = c.ident()
        elif c.word("PARTITION", "BY"):
            while not c.done and not c.is_p("("):
                c.i += 1
            if c.done:
                break
            lo, hi = c.paren()
            names = [t.text for t in c.toks[lo:hi] if t.kind in ("w", "id")]
            table.partition_columns = [col.name for n in names for col in [table.column(n)] if col is not None]
            break  # the partition list after the key carries nothing the model holds
        else:
            c.skip_balanced()
    return auto_increment


def _apply_key_nullability(table: Table) -> None:
    for name in table.primary_key:
        column = table.column(name)
        if column is not None:
            column.nullable = False


# --------------------------------------------------------------------------------------------------------------------
# Row values
# --------------------------------------------------------------------------------------------------------------------

_VALUES_WS = " \t\r\n"
_NUMBER_RE = re.compile(r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?")
_PREFIX_STRING_RE = re.compile(r"(?i)(_\w+\s*|[nb]|e)'")
_HEX_RE = re.compile(r"(?i)0x([0-9a-f]*)")
_XSTRING_RE = re.compile(r"(?i)x'([0-9a-f]*)'")
_WORD_VALUE_RE = re.compile(r"(?i)(NULL|TRUE|FALSE)\b")
_MYSQL_ESCAPES = {"0": "\0", "b": "\b", "n": "\n", "r": "\r", "t": "\t", "Z": "\x1a", "\\": "\\", "'": "'", '"': '"'}


def _read_quoted(text: str, i: int, backslash: bool) -> tuple[str, int]:
    quote = text[i]
    out: list[str] = []
    j, n = i + 1, len(text)
    while j < n:
        c = text[j]
        if backslash and c == "\\" and j + 1 < n:
            nxt = text[j + 1]
            out.append(_MYSQL_ESCAPES.get(nxt, "\\" + nxt))
            j += 2
        elif c == quote:
            if j + 1 < n and text[j + 1] == quote:
                out.append(quote)
                j += 2
            else:
                return "".join(out), j + 1
        else:
            out.append(c)
            j += 1
    raise ValueError("unterminated string in row data")


def _skip_ws(text: str, i: int) -> int:
    n = len(text)
    while i < n and text[i] in _VALUES_WS:
        i += 1
    return i


def _scan_value(text: str, i: int, dialect: str, flags: dict) -> tuple[Any, int]:
    """Parse one row value at ``i``. Expressions are not evaluated: their source text is stored and counted."""
    i = _skip_ws(text, i)
    if i >= len(text):
        raise ValueError("row data ended unexpectedly")
    backslash = dialect == "mysql"
    c = text[i]
    value: Any
    end: int
    m = _XSTRING_RE.match(text, i)
    if m:
        value, end = bytes.fromhex(m.group(1)), m.end()
    elif c == "'" or (c == '"' and dialect == "mysql"):
        value, end = _read_quoted(text, i, backslash)
    elif (m := _PREFIX_STRING_RE.match(text, i)):
        quote_pos = m.end() - 1
        prefix = m.group(1).strip().lower()
        value, end = _read_quoted(text, quote_pos, backslash or prefix == "e")
        if prefix == "b":
            value = int(value, 2) if value else 0
    elif (m := _HEX_RE.match(text, i)) and m.end() > i + 2:
        digits = m.group(1)
        value, end = bytes.fromhex(("0" + digits) if len(digits) % 2 else digits), m.end()
    elif (m := _NUMBER_RE.match(text, i)) and (m.end() >= len(text) or not (text[m.end()].isalnum() or text[m.end()] in "_.(")):
        raw = m.group(0)
        end = m.end()
        if re.fullmatch(r"[+-]?\d+", raw):
            value = int(raw)
        elif len(raw) <= 15:
            value = float(raw)
        else:
            value = raw  # keep high-precision decimals exact
    elif (m := _WORD_VALUE_RE.match(text, i)):
        word = m.group(1).upper()
        value, end = (None if word == "NULL" else int(word == "TRUE")), m.end()
    else:
        value, end = _scan_expression(text, i)
        flags["expressions"] = flags.get("expressions", 0) + 1
    j = _skip_ws(text, end)
    if text.startswith("::", j):  # 'x'::text
        j += 2
        while j < len(text) and text[j] not in ",)":
            if text[j] == "(":
                _, j = _scan_expression(text, j)
            else:
                j += 1
        end = j
    return value, end


def _scan_expression(text: str, i: int) -> tuple[str, int]:
    depth = 0
    j, n = i, len(text)
    while j < n:
        c = text[j]
        if c == "'":
            _, j = _read_quoted(text, j, False)
            continue
        if c == "(":
            depth += 1
        elif c == ")":
            if depth == 0:
                return text[i:j].strip(), j
            depth -= 1
            if depth == 0 and i == j:
                return text[i:j + 1], j + 1
        elif c == "," and depth == 0:
            return text[i:j].strip(), j
        j += 1
    raise ValueError("row data ended unexpectedly")


def _scan_tuples(text: str, i: int, dialect: str, flags: dict) -> list[list[Any]]:
    rows: list[list[Any]] = []
    n = len(text)
    while True:
        i = _skip_ws(text, i)
        if i >= n or text[i] != "(":
            break
        i += 1
        row: list[Any] = []
        while True:
            value, i = _scan_value(text, i, dialect, flags)
            row.append(value)
            i = _skip_ws(text, i)
            if i >= n:
                raise ValueError("row data ended unexpectedly")
            if text[i] == ",":
                i += 1
                continue
            if text[i] == ")":
                i += 1
                break
            raise ValueError(f"unexpected {text[i]!r} in row data")
        rows.append(row)
        i = _skip_ws(text, i)
        if i < n and text[i] == ",":
            i += 1
            continue
        break
    return rows


def _find_values(text: str) -> Optional[int]:
    """Position just after the VALUES keyword, skipping quoted text."""
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c in "'\"`":
            i = _scan_string(text, i, c, False)
            continue
        if text[i:i + 6].upper() == "VALUES" and (i == 0 or not (text[i - 1].isalnum() or text[i - 1] == "_")) and (
                i + 6 >= n or not (text[i + 6].isalnum() or text[i + 6] == "_")):
            return i + 6
        if text[i:i + 6].upper() == "SELECT" and (i == 0 or not (text[i - 1].isalnum() or text[i - 1] == "_")):
            return None
        i += 1
    return None


_COPY_UNESCAPE = {"b": "\b", "f": "\f", "n": "\n", "r": "\r", "t": "\t", "v": "\v", "\\": "\\"}


def _copy_field(raw: str) -> Optional[str]:
    if raw == "\\N":
        return None
    if "\\" not in raw:
        return raw
    out, i, n = [], 0, len(raw)
    while i < n:
        if raw[i] == "\\" and i + 1 < n:
            out.append(_COPY_UNESCAPE.get(raw[i + 1], raw[i + 1]))
            i += 2
        else:
            out.append(raw[i])
            i += 1
    return "".join(out)


def _coerce_bool(value: Any) -> Any:
    if isinstance(value, str):
        low = value.strip().lower()
        if low in {"t", "true"}:
            return 1
        if low in {"f", "false"}:
            return 0
    return value


# --------------------------------------------------------------------------------------------------------------------
# Importer
# --------------------------------------------------------------------------------------------------------------------

_HEAD_RE = re.compile(
    r"(?is)^CREATE\s+(?:(?:OR\s+REPLACE|DEFINER\s*=\s*\S+|ALGORITHM\s*=\s*\w+|SQL\s+SECURITY\s+\w+)\s+)*"
    r"(?:(?:TEMP|TEMPORARY|GLOBAL|LOCAL|UNLOGGED|FOREIGN|MATERIALIZED|UNIQUE|FULLTEXT|SPATIAL|CONSTRAINT|RECURSIVE)\s+)*(\w+)")
_IGNORED = re.compile(
    r"(?is)^(SET|RESET|LOCK\s+TABLES?|UNLOCK\s+TABLES?|BEGIN|COMMIT|END|START\s+TRANSACTION|ROLLBACK|PRAGMA|DROP|ANALYZE|VACUUM|"
    r"DELETE\s+FROM\s+\"?sqlite_\w+|FLUSH|SELECT|SAVEPOINT|RELEASE|REFRESH|CLUSTER|CHECKPOINT|DISCARD|ALTER\s+(SEQUENCE|SCHEMA|DATABASE|TYPE|DOMAIN|FUNCTION|PROCEDURE|"
    r"AGGREGATE|EXTENSION|VIEW|MATERIALIZED|INDEX|TRIGGER|DEFAULT|EVENT|PUBLICATION|SUBSCRIPTION|LANGUAGE|OPERATOR|COLLATION|"
    r"TEXT|FOREIGN|SERVER|LARGE|STATISTICS|POLICY|RULE))\b")
_IGNORED_CREATE = {"SCHEMA", "EXTENSION", "SEQUENCE", "TYPE", "DOMAIN", "DATABASE", "AGGREGATE", "OPERATOR", "COLLATION", "CAST", "EVENT",
                   "RULE", "TABLESPACE", "PUBLICATION", "SUBSCRIPTION", "LANGUAGE", "STATISTICS", "TEXT", "SERVER", "ACCESS", "CONVERSION",
                   "TRANSFORM"}
_SECRET_RE = re.compile(r"(?i)((?:IDENTIFIED\s+(?:WITH\s+\S+\s+)?(?:BY|AS)|PASSWORD)\s+)('(?:[^']|'')*'|\"[^\"]*\"|\S+)")
_DATABASE_RE = re.compile(r"(?is)^(?:CREATE\s+DATABASE|CREATE\s+SCHEMA|USE)\s+(?:/\*.*?\*/\s*)?(?:IF\s+NOT\s+EXISTS\s+)?[`\"]?([\w$-]+)")
_VERSION_RES = [re.compile(r"-- Dumped from database version (\S+)"), re.compile(r"-- Server version\s+(\S+)")]
_ENCODING_RES = [re.compile(r"(?i)SET\s+client_encoding\s*=\s*'([^']+)'"), re.compile(r"(?i)SET\s+NAMES\s+'?(\w+)")]


def _snippet(text: str, limit: int = 120) -> str:
    cleaned = _SECRET_RE.sub(r"\1***", " ".join(text.split()))
    return cleaned if len(cleaned) <= limit else cleaned[:limit] + "..."


class _Importer:
    def __init__(self, text: str, dialect: Optional[str], name: Optional[str], source_path: Optional[str]):
        self.text = text
        self.dialect = _normalize_dialect(dialect) if dialect else detect_dialect(text)
        self.meta: dict[str, str] = {}
        self.db = Database(name=name or "", dialect=self.dialect, source="sql_dump")
        self.requested_name = name
        self.source_path = source_path
        self.statements: list[_Statement] = []
        self.security_seen = False
        self.warning_overflow = 0
        self.auto_increment: dict[str, int] = {}

    def warn(self, message: str) -> None:
        if len(self.db.import_warnings) < MAX_WARNINGS:
            self.db.import_warnings.append(message)
        else:
            self.warning_overflow += 1

    def cursor(self, sql: str) -> _Cur:
        return _Cur(_tokenize(sql, self.dialect), sql, self.dialect)

    def table(self, schema: Optional[str], name: str) -> Optional[Table]:
        return self.db.table(name, schema) or self.db.table(name)

    def need_table(self, schema: Optional[str], name: str) -> Table:
        table = self.table(schema, name)
        if table is None:
            raise _ParseError(f"table {name} was not created in this dump")
        return table

    def run(self) -> Database:
        try:
            self.statements = list(split_statements(self.text, self.dialect, self.meta))
        except Exception as exc:
            self.warn(f"statement splitting stopped early: {exc}")
        creates, others, data = [], [], []
        for s in self.statements:
            head = s.text[:40].upper().lstrip()
            if head.startswith("CREATE") and _HEAD_RE.match(s.text) and _HEAD_RE.match(s.text).group(1).upper() == "TABLE":
                creates.append(s)
            elif head.startswith("INSERT") or head.startswith("REPLACE") or s.copy_lines is not None:
                data.append(s)
            else:
                others.append(s)
        for s in creates:
            self.guarded(s, self.create_table)
        for s in others:
            self.guarded(s, self.dispatch)
        self.remove_view_stand_ins()
        self.load_data(data)
        self.finish()
        return self.db

    def guarded(self, statement: _Statement, handler) -> None:
        try:
            handler(statement)
        except _Skip:
            pass
        except Exception as exc:
            self.warn(f"could not parse statement ({exc}): {_snippet(statement.text)}")

    def create_table(self, statement: _Statement) -> None:
        table, auto_increment = _parse_create(statement.text, self.dialect)
        if auto_increment is not None:
            self.auto_increment[table.name] = auto_increment
        if table.name.lower().startswith("sqlite_"):
            return
        if self.dialect == "postgres":
            table.rls_enabled = False
        if self.dialect == "sqlite" and len(table.primary_key) == 1:
            column = table.column(table.primary_key[0])
            if column is not None and column.data_type.upper() == "INTEGER":
                column.is_identity = True  # rowid alias
        existing = self.db.table(table.name, table.schema) if table.schema else self.db.table(table.name)
        if existing is not None:
            self.db.tables.remove(existing)
        self.db.tables.append(table)

    def dispatch(self, statement: _Statement) -> None:
        text = statement.text
        m = _DATABASE_RE.match(text)
        if m and not self.meta.get("database"):
            self.meta["database"] = m.group(1)
        upper = text[:30].upper()
        if upper.startswith("CREATE"):
            head_match = _HEAD_RE.match(text)
            kind = head_match.group(1).upper() if head_match else ""
            handler = {"VIEW": self.create_view, "TRIGGER": self.create_trigger, "PROCEDURE": self.create_routine,
                       "FUNCTION": self.create_routine, "INDEX": self.create_index, "ROLE": self.create_role, "USER": self.create_role,
                       "GROUP": self.create_role, "POLICY": self.create_policy}.get(kind)
            if kind == "TABLE":
                return
            if handler:
                handler(text)
            elif kind not in _IGNORED_CREATE:
                self.warn(f"unsupported CREATE statement skipped: {_snippet(text)}")
        elif upper.startswith("ALTER TABLE"):
            self.alter_table(text)
        elif re.match(r"(?i)ALTER\s+(ROLE|USER|GROUP)\b", text):
            self.alter_role(text)
        elif upper.startswith("COMMENT"):
            self.comment_on(text)
        elif upper.startswith("GRANT"):
            self.grant(text)
        elif upper.startswith("REVOKE"):
            self.revoke(text)
        elif re.match(r"(?i)USE\b", text):
            pass
        elif not _IGNORED.match(text):
            self.warn(f"unrecognized statement skipped: {_snippet(text)}")

    # DDL other than CREATE TABLE ------------------------------------------------------------------------------------

    def create_view(self, text: str) -> None:
        c = self.cursor(text)
        materialized = False
        while not c.done and c.up() != "VIEW":
            materialized = materialized or c.up() == "MATERIALIZED"
            c.i += 1
        c.expect("VIEW")
        c.word("IF", "NOT", "EXISTS")
        schema, name = c.qualified()
        if c.is_p("("):
            c.paren()
        if not c.word("AS"):
            raise _ParseError("view has no AS clause")
        definition = c.sql[c.peek().start:].strip() if c.peek() else ""
        definition = re.sub(r"(?is)\s+WITH\s+(?:NO\s+)?DATA\s*$", "", definition).rstrip(" ;")
        references = sql_references(definition, self.dialect)
        view = View(name=name, schema=schema, definition=definition, references=references, materialized=materialized)
        self.db.views = [v for v in self.db.views if not (v.name.lower() == name.lower() and v.schema == schema)]
        self.db.views.append(view)

    def remove_view_stand_ins(self) -> None:
        names = {v.name.lower() for v in self.db.views}
        self.db.tables = [t for t in self.db.tables if t.name.lower() not in names]

    def create_trigger(self, text: str) -> None:
        c = self.cursor(text)
        while not c.done and c.up() != "TRIGGER":
            c.i += 1
        c.expect("TRIGGER")
        c.word("IF", "NOT", "EXISTS")
        schema, name = c.qualified()
        while not c.done and not c.up() == "ON":
            c.i += 1
        c.expect("ON")
        _, table = c.qualified()
        self.db.routines.append(Routine(name=name, kind="trigger", table=table, schema=schema, definition=text,
                                        references=self._routine_refs(text)))

    def create_routine(self, text: str) -> None:
        c = self.cursor(text)
        kind = ""
        while not c.done and c.up() not in {"PROCEDURE", "FUNCTION"}:
            c.i += 1
        kind = c.up().lower()
        c.i += 1
        c.word("IF", "NOT", "EXISTS")
        schema, name = c.qualified()
        self.db.routines.append(Routine(name=name, kind=kind, schema=schema, definition=text, references=self._routine_refs(text)))

    def _routine_refs(self, text: str) -> list[str]:
        names = [m.group(1).split(".")[-1].strip('`"[]') for m in _REF_RE.finditer(text)]
        return list(dict.fromkeys(n for n in names if n.lower() not in _NOT_TABLES))

    def create_index(self, text: str) -> None:
        c = self.cursor(text)
        c.expect("CREATE")
        unique = c.word("UNIQUE")
        method = c.up() if c.up() in {"FULLTEXT", "SPATIAL"} else None
        if method:
            c.i += 1
        c.word("CLUSTERED") or c.word("NONCLUSTERED")
        c.expect("INDEX")
        c.word("CONCURRENTLY")
        c.word("IF", "NOT", "EXISTS")
        name = None if c.up() in {"ON", "USING"} else c.qualified()[1]
        if c.word("USING"):
            method = c.ident()
        c.expect("ON")
        c.word("ONLY")
        schema, table_name = c.qualified()
        if c.word("USING"):
            method = c.ident()
        lo, hi = c.paren()
        index = Index(name=name, columns=_key_columns(c, lo, hi), unique=unique, method=method)
        while not c.done:
            if c.word("INCLUDE"):
                lo, hi = c.paren()
                index.include = _key_columns(c, lo, hi)
            elif c.word("USING"):
                index.method = c.ident()
            elif c.word("WITH"):
                if c.is_p("("):
                    c.paren()
            elif c.word("WHERE"):
                index.where = c.slice(c.i, len(c.toks))
                c.skip_to_end()
            else:
                c.skip_balanced()
        self.need_table(schema, table_name).indexes.append(index)

    def alter_table(self, text: str) -> None:
        c = self.cursor(text)
        c.expect("ALTER", "TABLE")
        c.word("IF", "EXISTS")
        c.word("ONLY")
        schema, name = c.qualified()
        table = self.need_table(schema, name)
        for a, b in c.split_commas(c.i, len(c.toks)):
            action = c.sub(a, b)
            if action.word("AUTO_INCREMENT"):
                value = _auto_increment_value(action)
                if value is not None:
                    self.auto_increment[table.name] = value
                continue
            self._alter_action(action, table)
        _apply_key_nullability(table)

    def _alter_action(self, c: _Cur, table: Table) -> None:
        if c.word("ADD"):
            if c.up() in {"CONSTRAINT", "PRIMARY", "UNIQUE", "FOREIGN", "CHECK", "FULLTEXT", "SPATIAL"} or (
                    c.up() in _KEY_WORDS and _is_table_item(c)):
                _table_item(c, table)
                return
            c.word("COLUMN")
            c.word("IF", "NOT", "EXISTS")
            table.columns.append(_parse_column(c, table))
            return
        if c.word("ALTER"):
            c.word("COLUMN")
            column = table.column(c.ident())
            if column is None:
                raise _ParseError("column not found")
            if c.word("SET", "NOT", "NULL"):
                column.nullable = False
            elif c.word("DROP", "NOT", "NULL"):
                column.nullable = True
            elif c.word("SET", "DEFAULT"):
                column.default = _default(c)
                if (column.default or "").lower().startswith("nextval("):
                    column.is_identity, column.nullable = True, False
            elif c.word("DROP", "DEFAULT"):
                column.default = None
            elif c.word("ADD", "GENERATED"):
                column.is_identity, column.nullable = True, False
            elif c.word("SET", "DATA", "TYPE") or c.word("TYPE"):
                lo = c.i
                while not c.done and c.up() not in {"USING", "COLLATE"}:
                    c.i += 1
                column.data_type = c.slice(lo, c.i)
            elif not (c.up() == "SET" or c.up() == "DROP"):
                raise _ParseError("unsupported ALTER COLUMN action")
            return
        if c.word("MODIFY") or c.word("CHANGE"):
            is_change = c.toks[c.i - 1].up == "CHANGE"
            c.word("COLUMN")
            old = c.ident() if is_change else None
            replacement = _parse_column(c, Table(name="scratch", columns=[]))
            current = table.column(old or replacement.name)
            if current is None:
                raise _ParseError("column not found")
            replacement.ordinal = current.ordinal
            table.columns[table.columns.index(current)] = replacement
            return
        if c.word("ENABLE", "ROW", "LEVEL", "SECURITY") or c.word("FORCE", "ROW", "LEVEL", "SECURITY"):
            table.rls_enabled = True
            return
        if c.word("DISABLE", "ROW", "LEVEL", "SECURITY"):
            table.rls_enabled = False
            return
        if c.up() in {"ENABLE", "DISABLE", "OWNER", "CLUSTER", "REPLICA", "ATTACH", "DETACH", "NO", "SET", "RESET", "INHERIT",
                      "VALIDATE", "OF", "AUTO_INCREMENT", "ENGINE", "CONVERT", "DEFAULT", "COMMENT", "ALGORITHM", "LOCK", "ORDER"}:
            return
        raise _ParseError(f"unsupported ALTER TABLE action {c.peek().text if c.peek() else ''}")

    def comment_on(self, text: str) -> None:
        c = self.cursor(text)
        c.expect("COMMENT", "ON")
        kind = c.up()
        if kind not in {"TABLE", "COLUMN"}:
            return
        c.i += 1
        parts = c.dotted()
        c.expect("IS")
        value = None if c.word("NULL") else c.ident()
        if kind == "TABLE":
            self.need_table(parts[-2] if len(parts) > 1 else None, parts[-1]).comment = value
        else:
            table = self.need_table(parts[-3] if len(parts) > 2 else None, parts[-2])
            column = table.column(parts[-1])
            if column is None:
                raise _ParseError("column not found")
            column.comment = value

    # Security -------------------------------------------------------------------------------------------------------

    def _role_name(self, c: _Cur) -> tuple[str, Optional[str]]:
        name = c.ident()
        host = None
        if c.is_p("@") and c.peek(1) is not None:
            c.i += 1
            host = c.ident()
        elif c.peek() is not None and c.peek().text.startswith("@"):
            host = c.peek().text[1:].strip("'\"`") or None
            c.i += 1
        return name, host

    def _role_options(self, c: _Cur, role: Role) -> None:
        while not c.done:
            if c.word("SUPERUSER"):
                role.superuser = True
            elif c.word("NOSUPERUSER"):
                role.superuser = False
            elif c.word("LOGIN"):
                role.can_login = True
            elif c.word("NOLOGIN"):
                role.can_login = False
            elif c.word("BYPASSRLS"):
                role.bypass_rls = True
            elif c.word("NOBYPASSRLS"):
                role.bypass_rls = False
            elif c.word("IDENTIFIED"):
                role.password_set = True
                c.skip_to_end()
            elif c.word("PASSWORD"):
                role.password_set = not c.word("NULL")
                if not c.done and c.peek().kind == "str":
                    c.i += 1
            else:
                c.skip_balanced()

    def create_role(self, text: str) -> None:
        self.security_seen = True
        c = self.cursor(text)
        c.expect("CREATE")
        kind = c.up()
        c.i += 1
        c.word("IF", "NOT", "EXISTS")
        for pos, (a, b) in enumerate(c.split_commas(c.i, len(c.toks))):
            item = c.sub(a, b)
            name, host = self._role_name(item)
            role = Role(name=name, host=host, can_login=kind != "ROLE" and kind != "GROUP")
            self._role_options(item, role)
            self.db.roles = [r for r in self.db.roles if not (r.name == name and r.host == host)]
            self.db.roles.append(role)

    def alter_role(self, text: str) -> None:
        c = self.cursor(text)
        c.expect("ALTER")
        c.i += 1
        c.word("IF", "EXISTS")
        name, host = self._role_name(c)
        if c.up() == "SET" or c.up() == "RESET" or c.up() == "RENAME":
            return
        c.word("WITH")
        role = next((r for r in self.db.roles if r.name == name), None)
        if role is None:
            role = Role(name=name, host=host, can_login=False)
            self.db.roles.append(role)
            self.security_seen = True
        self._role_options(c, role)

    def _parse_grant(self, text: str) -> tuple[list[tuple[str, Optional[str]]], list[tuple[Optional[str], Optional[str]]], list[str], bool, bool]:
        """Return (privilege, column) pairs, (schema, table) targets, grantees, grantable, is_table_level."""
        c = self.cursor(text)
        verb = c.up()
        c.i += 1
        c.word("GRANT", "OPTION", "FOR")
        lo = c.i
        depth = 0
        while not c.done:
            t = c.peek()
            if t.kind == "p" and t.text == "(":
                depth += 1
            elif t.kind == "p" and t.text == ")":
                depth -= 1
            elif depth == 0 and (t.up in {"ON", "TO", "FROM"}):
                break
            c.i += 1
        hi = c.i
        privileges: list[tuple[str, Optional[str]]] = []
        for a, b in c.split_commas(lo, hi):
            item = c.sub(a, b)
            words = []
            columns: list[str] = []
            while not item.done:
                if item.is_p("("):
                    l2, h2 = item.paren()
                    columns.extend(item.toks[k].text for k in range(l2, h2) if item.toks[k].kind in ("w", "id"))
                else:
                    words.append(item.peek().text.upper())
                    item.i += 1
            privilege = " ".join(words).replace(" PRIVILEGES", "")
            privileges.extend((privilege, col) for col in columns or [None])
        table_level = False
        targets: list[tuple[Optional[str], Optional[str]]] = []
        if c.word("ON"):
            if c.word("ALL", "TABLES", "IN", "SCHEMA"):
                targets = [(c.ident(), "*")]
                table_level = True
            elif c.word("SCHEMA"):
                targets = [(c.ident(), None)]
                table_level = True
            elif c.word("DATABASE"):
                targets = [(None, None)]
                table_level = True
                c.ident()
            elif c.up() in {"SEQUENCE", "FUNCTION", "PROCEDURE", "ROUTINE", "TYPE", "DOMAIN", "LANGUAGE", "LARGE", "TABLESPACE", "FOREIGN", "ALL"}:
                while not c.done and c.up() not in {"TO", "FROM"}:
                    c.skip_balanced()
            else:
                c.word("TABLE")
                targets = [self._grant_target(c)]
                table_level = True
                while c.is_p(","):
                    c.i += 1
                    targets.append(self._grant_target(c))
        grantees: list[str] = []
        grantable = False
        if c.word("TO") or c.word("FROM"):
            lo2 = c.i
            hi2 = len(c.toks)
            for j in range(lo2, hi2):
                if c.toks[j].up in {"WITH", "IDENTIFIED", "GRANTED", "REQUIRE", "CASCADE", "RESTRICT"}:
                    hi2 = j
                    break
            for a, b in c.split_commas(lo2, hi2):
                item = c.sub(a, b)
                item.word("ROLE") or item.word("GROUP")
                name, _ = self._role_name(item)
                grantees.append("PUBLIC" if name.upper() == "PUBLIC" else name)
            grantable = any(t.up == "OPTION" for t in c.toks[hi2:]) and verb == "GRANT"
        return privileges, targets, grantees, grantable, table_level

    def _grant_target(self, c: _Cur) -> tuple[Optional[str], Optional[str]]:
        star = lambda: c.is_p("*")
        if star():  # *.* or *
            c.i += 1
            if c.is_p(".") and c.is_p("*", 1):
                c.i += 2
            return None, None
        first = c.ident()
        if c.is_p(".") and c.is_p("*", 1):
            c.i += 2
            return first, "*"
        if c.is_p("."):
            c.i += 1
            return first, c.ident()
        return None, first

    def grant(self, text: str) -> None:
        self.security_seen = True
        privileges, targets, grantees, grantable, table_level = self._parse_grant(text)
        if not table_level:
            return
        for grantee in grantees:
            for schema, table in targets:
                for privilege, column in privileges:
                    self.db.grants.append(Grant(grantee=grantee, privilege=privilege, table=table, schema=schema, column=column,
                                                grantable=grantable))

    def revoke(self, text: str) -> None:
        privileges, targets, grantees, _grantable, table_level = self._parse_grant(text)
        if not table_level:
            return
        names = {p for p, _ in privileges}
        self.db.grants = [g for g in self.db.grants if not (
            g.grantee in grantees and (g.privilege in names or "ALL" in names)
            and any(g.schema == s and g.table == t for s, t in targets))]

    def create_policy(self, text: str) -> None:
        c = self.cursor(text)
        c.expect("CREATE", "POLICY")
        c.word("IF", "NOT", "EXISTS")
        name = c.ident()
        c.expect("ON")
        schema, table_name = c.qualified()
        policy = RlsPolicy(table=table_name, name=name, schema=schema)
        expression_using = expression_check = ""
        while not c.done:
            if c.word("FOR"):
                policy.command = c.ident().upper()
            elif c.word("AS"):
                c.i += 1
            elif c.word("TO"):
                lo = c.i
                while not c.done and c.up() not in {"USING", "WITH"}:
                    c.i += 1
                policy.roles = [c.toks[k].text for k in range(lo, c.i) if c.toks[k].kind in ("w", "id")]
            elif c.word("USING"):
                lo, hi = c.paren()
                expression_using = c.slice(lo, hi)
            elif c.word("WITH", "CHECK"):
                lo, hi = c.paren()
                expression_check = c.slice(lo, hi)
            else:
                c.skip_balanced()
        policy.expression = expression_using or expression_check
        self.need_table(schema, table_name)
        self.db.policies.append(policy)

    # Data -----------------------------------------------------------------------------------------------------------

    def load_data(self, data: list[_Statement]) -> None:
        batches: list[tuple[Table, list[str], list[list[Any]]]] = []
        total = 0
        for statement in data:
            try:
                batch = self.parse_copy(statement) if statement.copy_lines is not None else self.parse_insert(statement)
            except _Skip:
                continue
            except Exception as exc:
                self.warn(f"row data not loaded ({exc}): {_snippet(statement.text)}")
                continue
            if batch:
                batches.append(batch)
                total += len(batch[2])
        if not batches:
            return
        sandbox = Sandbox(self.db.name or "dump")
        names = {id(t): sandbox.add_table(t) for t in self.db.tables}
        counts: dict[int, int] = {id(t): 0 for t in self.db.tables}
        next_identity: dict[int, int] = {}
        for table, columns, rows in batches:
            good = []
            for row in rows:
                if len(row) != len(columns):
                    self.warn(f"{table.name}: row with {len(row)} values does not match {len(columns)} columns; row skipped")
                    continue
                good.append(self._coerce(table, columns, row))
            columns, good = self._fill_identity(table, columns, good, next_identity)
            counts[id(table)] += sandbox.insert(names[id(table)], columns, good)
        sandbox.freeze()
        for table in self.db.tables:
            table.row_count = counts[id(table)]
        self.db.data = sandbox

    def _fill_identity(self, table: Table, columns: list[str], rows: list[list[Any]], counters: dict[int, int]) -> tuple[list[str], list[list[Any]]]:
        """An INSERT that omits an identity column gets numbers from the engine; number the rows here the same way."""
        present = {c.lower() for c in columns}
        column = next((c for c in table.columns if c.is_identity and c.name.lower() not in present), None)
        if column is None or not rows:
            return columns, rows
        start = counters.get(id(table), 1)
        counters[id(table)] = start + len(rows)
        return [*columns, column.name], [[*row, start + i] for i, row in enumerate(rows)]

    def _coerce(self, table: Table, columns: list[str], row: list[Any]) -> list[Any]:
        out = []
        for name, value in zip(columns, row):
            column = table.column(name)
            out.append(_coerce_bool(value) if column is not None and column.type.family == "bool" else value)
        return out

    def parse_insert(self, statement: _Statement) -> Optional[tuple[Table, list[str], list[list[Any]]]]:
        text = statement.text
        position = _find_values(text)
        if position is None:
            raise _ParseError("INSERT without a VALUES list is not loaded")
        head = self.cursor(text[:position - 6])
        while head.up() in {"INSERT", "REPLACE", "LOW_PRIORITY", "DELAYED", "HIGH_PRIORITY", "IGNORE", "OR", "ABORT", "FAIL", "ROLLBACK"}:
            head.i += 1
        head.word("INTO")
        schema, name = head.qualified()
        if name.lower().startswith("sqlite_"):
            raise _Skip()
        table = self.need_table(schema, name)
        columns = [c.name for c in table.columns]
        if head.is_p("("):
            lo, hi = head.paren()
            columns = _key_columns(head, lo, hi)
        self._check_columns(table, columns)
        flags: dict[str, int] = {}
        rows = _scan_tuples(text, position, self.dialect, flags)
        if flags.get("expressions"):
            self.warn(f"{table.name}: {flags['expressions']} value(s) were expressions and are stored as their source text")
        return table, columns, rows

    def _check_columns(self, table: Table, columns: list[str]) -> None:
        missing = [c for c in columns if table.column(c) is None]
        if missing:
            raise _ParseError(f"{table.name} has no column {missing[0]}")

    def parse_copy(self, statement: _Statement) -> Optional[tuple[Table, list[str], list[list[Any]]]]:
        c = self.cursor(statement.text)
        c.expect("COPY")
        schema, name = c.qualified()
        table = self.need_table(schema, name)
        columns = [col.name for col in table.columns]
        if c.is_p("("):
            lo, hi = c.paren()
            columns = _key_columns(c, lo, hi)
        self._check_columns(table, columns)
        tail = statement.text.upper()
        lines = statement.copy_lines or []
        if re.search(r"\bCSV\b", tail):
            rows: list[list[Any]] = [[None if v == "" else v for v in row]
                                     for row in csv.reader(io.StringIO("\n".join(lines))) if row]
        else:
            rows = [[_copy_field(field) for field in line.split("\t")] for line in lines if line]
        return table, columns, rows

    # ----------------------------------------------------------------------------------------------------------------

    def finish(self) -> None:
        db = self.db
        db.security_metadata = self.security_seen
        if not self.requested_name:
            db.name = self.meta.get("database") or (Path(self.source_path).stem if self.source_path else "") or "sql_dump"
        for regex in _VERSION_RES:
            m = regex.search(self.text)
            if m:
                db.settings["server_version"] = m.group(1)
                break
        for regex in _ENCODING_RES:
            m = regex.search(self.text)
            if m:
                db.settings["encoding"] = m.group(1)
                break
        if self.auto_increment:
            db.settings["auto_increment"] = self.auto_increment
        if not db.tables:
            self.warn("no tables were found in this input")
        if self.warning_overflow:
            db.import_warnings.append(f"{self.warning_overflow} further warnings were omitted")


def import_sql(path_or_text: Union[str, "os.PathLike[str]"], dialect: Optional[str] = None, name: Optional[str] = None) -> Database:
    """Parse a SQL dump, given as a file path or as SQL text, into a Database. The SQL is never executed."""
    source_path: Optional[str] = None
    if isinstance(path_or_text, os.PathLike):
        source_path = os.fspath(path_or_text)
        text = read_text(source_path)
    else:
        text = path_or_text
        single_line = "\n" not in text and len(text) < 4096
        if single_line and (os.path.exists(text) or re.fullmatch(r"\S+\.(sql|dump|sql\.gz|txt)", text, re.I)):
            source_path = text
            text = read_text(source_path)
    return _Importer(text, dialect, name, source_path).run()
