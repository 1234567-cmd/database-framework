"""Turn the import form into a validated job description. Nothing is opened here; errors are for people to read."""
from __future__ import annotations

import os
import re
import shutil
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Optional
from urllib.parse import quote

MB = 1024 * 1024
_UPLOAD_PREFIX = "dbintel_ui_"
WORKLOADS = ("OLTP", "OLAP", "data_warehouse", "lakehouse")
TENANCIES = ("none", "pool", "bridge", "silo")
DIALECTS = ("postgres", "mysql", "sqlite")
ENGINES = ("mysql", "postgres", "sqlite")
SLOTS = ("source", "query_log", "pipelines", "profile")
SOURCE_SUFFIXES = {".sql", ".dump", ".ddl", ".gz", ".csv", ".tsv", ".xlsx", ".xlsm", ".json", ".db", ".sqlite", ".sqlite3", ".db3"}
_HOST = re.compile(r"^[A-Za-z0-9.\-]{1,253}$|^\[[0-9A-Fa-f:]+\]$")
_NAME_CHARS = re.compile(r"[^\w.\- ]", re.UNICODE)
_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]{0,63}$")


class IntakeError(ValueError):
    """The request is invalid. ``field`` names the form field."""

    def __init__(self, message: str, field: Optional[str] = None, status: int = 400):
        super().__init__(message)
        self.field = field
        self.status = status


def sanitize_filename(name: str) -> str:
    """Keep a plain base name so that an upload cannot escape its private directory and its extension still identifies the type."""
    base = re.split(r"[\\/]", name or "")[-1].strip()
    if base in ("", ".", ".."):
        raise IntakeError("That file name is not usable.")
    cleaned = _NAME_CHARS.sub("_", base).lstrip(".")
    if not cleaned or cleaned.upper().split(".")[0] in {"CON", "PRN", "AUX", "NUL", "COM1", "LPT1"}:
        cleaned = f"file_{cleaned}"
    return cleaned[:150]


def _sweep_stale_uploads(max_age_seconds: float = 12 * 3600) -> None:
    """Remove upload directories left by a launch that was closed without shutting down, such as a closed console window."""
    for child in Path(tempfile.gettempdir()).glob(f"{_UPLOAD_PREFIX}*"):
        try:
            if child.is_dir() and time.time() - child.stat().st_mtime > max_age_seconds:
                shutil.rmtree(child, ignore_errors=True)
        except OSError:
            continue


class Uploads:
    """Uploaded inputs, streamed to a private temporary directory and removed when the run ends."""

    def __init__(self, max_bytes: int):
        self.max_bytes = max_bytes
        _sweep_stale_uploads()
        self.root = Path(tempfile.mkdtemp(prefix=_UPLOAD_PREFIX))
        self._lock = threading.Lock()

    def _slot(self, slot: str) -> Path:
        if slot not in SLOTS:
            raise IntakeError("Unknown upload slot.")
        path = self.root / slot
        path.mkdir(mode=0o700, exist_ok=True)
        return path

    def store(self, slot: str, filename: str, stream: Any, length: int) -> dict[str, Any]:
        if length > self.max_bytes:
            raise IntakeError(f"That file is larger than the limit of {self.max_bytes // MB} MB. "
                              "Use the path option for large files, or restart with a larger --max-upload-mb.", status=413)
        target_dir = self._slot(slot)
        name = sanitize_filename(filename)
        target = target_dir / name
        count = 0
        with self._lock:
            if slot in ("query_log", "pipelines", "profile"):  # one file per optional slot
                for child in target_dir.iterdir():
                    child.unlink(missing_ok=True)
            try:
                with open(target, "wb") as handle:
                    remaining = length
                    while remaining > 0:
                        chunk = stream.read(min(1024 * 1024, remaining))
                        if not chunk:
                            break
                        count += len(chunk)
                        remaining -= len(chunk)
                        if count > self.max_bytes:
                            raise IntakeError(f"That file is larger than the limit of {self.max_bytes // MB} MB.", status=413)
                        handle.write(chunk)
                if count != length:
                    raise IntakeError("The upload was interrupted. Please try again.")
            except BaseException:
                target.unlink(missing_ok=True)
                raise
        return {"slot": slot, "name": name, "bytes": count}

    def list_files(self) -> dict[str, list[dict[str, Any]]]:
        out: dict[str, list[dict[str, Any]]] = {s: [] for s in SLOTS}
        for slot in SLOTS:
            path = self.root / slot
            if path.is_dir():
                out[slot] = [{"name": c.name, "bytes": c.stat().st_size} for c in sorted(path.iterdir()) if c.is_file()]
        return out

    def clear_slot(self, slot: str) -> None:
        if slot not in SLOTS:
            raise IntakeError("Unknown upload slot.")
        with self._lock:
            shutil.rmtree(self.root / slot, ignore_errors=True)

    def clear_all(self) -> None:
        with self._lock:
            for slot in SLOTS:
                shutil.rmtree(self.root / slot, ignore_errors=True)

    def slot_files(self, slot: str) -> list[Path]:
        path = self.root / slot
        return sorted(c for c in path.iterdir() if c.is_file()) if path.is_dir() else []

    def remove_root(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)


def _clean_text(body: dict[str, Any], key: str, limit: int = 300) -> Optional[str]:
    value = body.get(key)
    if value in (None, ""):
        return None
    if not isinstance(value, str) or len(value) > limit:
        raise IntakeError(f"{key.replace('_', ' ').title()} is not valid.", key)
    return value.strip() or None


def _path_field(raw: Any, label: str, field: str, directory: bool = False) -> Optional[str]:
    if raw in (None, ""):
        return None
    if not isinstance(raw, str) or len(raw) > 2000 or "\x00" in raw:
        raise IntakeError(f"{label}: the path is not valid.", field)
    text = raw.strip().strip('"')
    if not text:
        return None
    if "://" in text:
        raise IntakeError(f"{label}: enter a file path, not a URL. Use the connection form for a server.", field)
    path = Path(text)
    if not path.is_absolute():
        raise IntakeError(f"{label}: enter a full path, for example C:\\exports\\database.sql.", field)
    if directory:
        if not path.is_dir():
            raise IntakeError(f"{label}: no folder at {text}.", field)
    elif not (path.is_file() or path.is_dir()):
        raise IntakeError(f"{label}: nothing found at {text}.", field)
    return str(path)


def _connection(body: dict[str, Any]) -> tuple[str, Optional[str], str]:
    conn = body.get("connection") or {}
    if not isinstance(conn, dict):
        raise IntakeError("The connection details are not valid.", "connection")
    engine = conn.get("engine")
    if engine not in ENGINES:
        raise IntakeError("Choose a database engine.", "engine")
    if engine == "sqlite":
        path = _path_field(conn.get("sqlite_path"), "SQLite file", "sqlite_path")
        if not path or not Path(path).is_file():
            raise IntakeError("SQLite file: enter the full path of an existing database file.", "sqlite_path")
        return f"sqlite:///{Path(path).resolve().as_posix()}", None, f"sqlite:{Path(path).name}"
    host = str(conn.get("host") or "localhost").strip()
    if not _HOST.match(host):
        raise IntakeError("Host name is not valid.", "host")
    user = str(conn.get("user") or "").strip()
    database = str(conn.get("database") or "").strip()
    if not user:
        raise IntakeError("Enter a user name.", "user")
    if not database:
        raise IntakeError("Enter a database name.", "database")
    try:
        port = int(conn.get("port") or (3306 if engine == "mysql" else 5432))
    except (TypeError, ValueError):
        raise IntakeError("Port must be a number.", "port") from None
    if not 1 <= port <= 65535:
        raise IntakeError("Port must be between 1 and 65535.", "port")
    password = conn.get("password") or None
    if password is not None and (not isinstance(password, str) or len(password) > 2048):
        raise IntakeError("The password is not valid.", "password")
    scheme = "postgresql" if engine == "postgres" else "mysql"
    url = f"{scheme}://{quote(user, safe='')}@{host}:{port}/{quote(database, safe='')}"
    return url, password, f"{scheme}://{quote(user, safe='')}@{host}:{port}/{quote(database, safe='')}"


def _uploaded_source(uploads: Uploads) -> tuple[str, str]:
    files = uploads.slot_files("source")
    if not files:
        raise IntakeError("Add a file to analyze, or choose another source.", "source")
    if len(files) == 1:
        return str(files[0]), files[0].name
    if all(f.suffix.lower() in (".csv", ".tsv") for f in files):
        return str(uploads.root / "source"), f"{len(files)} CSV files"
    raise IntakeError("Several files can only be analyzed together when they are all CSV. Keep one file, or use a folder path.", "source")


def build_job(body: dict[str, Any], uploads: Uploads) -> dict[str, Any]:
    """Validate the form. The returned job holds the password only until it is sent to the analysis process."""
    if not isinstance(body, dict):
        raise IntakeError("The request is not valid.")
    source = body.get("source") or {}
    kind = source.get("kind") if isinstance(source, dict) else None
    job: dict[str, Any] = {"type": "analyze", "password": None}
    label = ""
    if kind == "upload":
        job["source"], label = _uploaded_source(uploads)
    elif kind == "path":
        path = _path_field(source.get("path"), "File path", "path")
        if not path:
            raise IntakeError("Enter the full path of a file or folder on this computer.", "path")
        job["source"] = path
        label = path
    elif kind == "connection":
        job["source"], job["password"], label = _connection(body | {"connection": source.get("connection")})
    else:
        raise IntakeError("Choose how to provide the database: a file, a path, or a connection.", "source")
    job["source_label"] = label
    job["name"] = _clean_text(body, "name", 120)
    settings = body.get("settings") or {}
    if not isinstance(settings, dict):
        raise IntakeError("The settings are not valid.", "settings")
    workload = settings.get("workload") or None
    tenancy = settings.get("tenancy") or None
    target = settings.get("target_dialect") or None
    dialect = settings.get("dialect") or None
    if workload is not None and workload not in WORKLOADS:
        raise IntakeError("Workload is not one of the supported values.", "workload")
    if tenancy is not None and tenancy not in TENANCIES:
        raise IntakeError("Tenancy is not one of the supported values.", "tenancy")
    if target is not None and target not in DIALECTS:
        raise IntakeError("Target dialect is not one of the supported values.", "target_dialect")
    if dialect is not None and dialect not in DIALECTS:
        raise IntakeError("Dump dialect is not one of the supported values.", "dialect")
    multi_company = settings.get("multi_company")
    if multi_company is not None and not isinstance(multi_company, bool):
        raise IntakeError("Multi-company must be true or false.", "multi_company")
    clean: dict[str, Any] = {"workload": workload, "tenancy": tenancy, "multi_company": multi_company}
    for key in ("tenant_column", "company_column"):
        value = settings.get(key) or None
        if value is not None and (not isinstance(value, str) or not _IDENTIFIER.match(value)):
            raise IntakeError(f"{key.replace('_', ' ').title()} must be a plain column name.", key)
        clean[key] = value
    job["settings"] = clean
    job["dialect"] = dialect
    job["target_dialect"] = target
    inputs = body.get("inputs") or {}
    if not isinstance(inputs, dict):
        raise IntakeError("The optional inputs are not valid.", "inputs")
    job["query_log"] = _optional_file(inputs, "query_log", "Query log", uploads)
    job["pipelines"] = _optional_file(inputs, "pipelines", "Pipeline manifest", uploads)
    job["app_source_dir"] = _path_field(inputs.get("app_source_dir"), "Application source folder", "app_source_dir", directory=True)
    profile_files = uploads.slot_files("profile")
    job["profile_path"] = str(profile_files[0]) if profile_files else None
    return job


def _optional_file(inputs: dict[str, Any], key: str, label: str, uploads: Uploads) -> list[str]:
    path = _path_field(inputs.get(f"{key}_path"), label, key)
    if path:
        if not Path(path).is_file():
            raise IntakeError(f"{label}: {path} is not a file.", key)
        return [path]
    return [str(p) for p in uploads.slot_files(key)]


def form_options() -> dict[str, Any]:
    return {"workloads": list(WORKLOADS), "tenancies": list(TENANCIES), "dialects": list(DIALECTS), "engines": list(ENGINES),
            "source_suffixes": sorted(SOURCE_SUFFIXES)}
