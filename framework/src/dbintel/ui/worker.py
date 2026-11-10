"""The analysis child process.

Running the pipeline in a separate process makes cancel immediate and leaves nothing partial behind: the parent kills the
process and removes its working directory. The whole assessment and any sandbox test run on this process's main thread,
so the thread-bound SQLite sandbox connections are created and used on one thread. A password arrives over the private
pipe, goes only into this process's environment, and is removed as soon as the source has been read.
"""
from __future__ import annotations

import importlib
import json
import os
import time
from pathlib import Path
from typing import Any, Callable, Optional

from ..config import Profile, load_profile
from ..connectors.base import scrub as scrub_secrets
from ..migrate.safety import ApprovalRequired
from ..migrate.sandbox import SandboxRefused, test_plan_in_sandbox
from ..pipeline import assess
from ..reporting import write_reports
from ..reporting.content import scrub as scrub_values
from .rebuild import RebuildError, rebuild
from .store import build_summary

PASSWORD_ENV = "DBINTEL_UI_SOURCE_PASSWORD"
DEFAULT_IDLE_SECONDS = 3600
_PROFILE_FIELDS = ("workload", "tenancy", "tenant_column", "company_column", "multi_company")


def build_profile(settings: dict[str, Any], profile_path: Optional[str]) -> Profile:
    profile = load_profile(profile_path)
    for key in _PROFILE_FIELDS:
        value = settings.get(key)
        if value not in (None, ""):
            setattr(profile, key, value)
    return profile


def _resolve_hook(spec: Optional[str]) -> Callable[..., Any]:
    if not spec:
        return assess
    module, _, name = spec.partition(":")
    return getattr(importlib.import_module(module), name)


def _message_for(exc: BaseException, secrets: list[str]) -> str:
    text = scrub_secrets(str(exc) or "", secrets)
    if isinstance(exc, MemoryError):
        return "The computer ran out of memory during the analysis."
    if isinstance(exc, (FileNotFoundError, PermissionError, ValueError, OSError)) or type(exc).__name__ == "ConnectorError":
        message = text or type(exc).__name__
    else:
        message = f"The analysis stopped because of an error: {type(exc).__name__}: {text}".rstrip(": ")
    return message[:1500]


def _send(conn: Any, *message: Any) -> None:
    try:
        conn.send(message)
    except (BrokenPipeError, OSError, EOFError):
        raise SystemExit(0) from None


def _analyze(conn: Any, job: dict[str, Any]) -> Optional[Any]:
    password = job.pop("password", None)
    secrets = [password] if password else []
    if password:
        os.environ[PASSWORD_ENV] = password
    partial = Path(job["partial_dir"])

    def progress(stage: str, state: str, seconds: float) -> None:
        _send(conn, "progress", stage, state, seconds)
        if stage == "import_and_extract" and state == "done":
            os.environ.pop(PASSWORD_ENV, None)

    try:
        profile = build_profile(job.get("settings") or {}, job.get("profile_path"))
        assess_fn = _resolve_hook(job.get("assess_hook"))
        assessment = assess_fn(job["source"], profile=profile, dialect=job.get("dialect"), name=job.get("name"),
                               password_env=PASSWORD_ENV if password else None, query_log=job.get("query_log") or None,
                               pipelines=job.get("pipelines") or None, app_source_dir=job.get("app_source_dir") or None,
                               target_dialect=job.get("target_dialect"), progress=progress)
        os.environ.pop(PASSWORD_ENV, None)
        if job.get("source_label"):
            assessment.source_label = job["source_label"]
        started = time.perf_counter()
        _send(conn, "progress", "write_reports", "start", 0.0)
        write_reports(assessment, partial)
        report = json.loads((partial / "report.json").read_text(encoding="utf-8"))
        (partial / "summary.json").write_text(json.dumps(build_summary(job["run_id"], report), indent=1), encoding="utf-8")
        _send(conn, "progress", "write_reports", "done", round(time.perf_counter() - started, 4))
        _send(conn, "done", {"has_rows": assessment.db.data is not None})
        return assessment
    except SystemExit:
        raise
    except BaseException as exc:  # includes the connector's scrubbed errors; the message is sanitized and has no traceback
        _send(conn, "failed", _message_for(exc, secrets))
        return None
    finally:
        os.environ.pop(PASSWORD_ENV, None)


def _sandbox_result(db: Any, plan: Any, token: str) -> tuple[str, Any]:
    try:
        report = test_plan_in_sandbox(db, plan, token)
    except ApprovalRequired as exc:
        return "refused", str(exc)
    except SandboxRefused as exc:
        return "refused", str(exc)
    except Exception as exc:
        return "failed", _message_for(exc, [])
    return "result", scrub_values(report.to_dict())


def _serve(conn: Any, assessment: Any, idle_seconds: float) -> None:
    while True:
        if not conn.poll(idle_seconds):
            return
        try:
            message = conn.recv()
        except (EOFError, OSError):
            return
        if message[0] == "exit":
            return
        if message[0] == "sandbox":
            kind, payload = _sandbox_result(assessment.db, assessment.plan, message[1])
            _send(conn, f"sandbox_{kind}", payload)


def _run_saved_sandbox(conn: Any, job: dict[str, Any]) -> None:
    try:
        plan, db = rebuild(Path(job["run_dir"]))
    except RebuildError as exc:
        _send(conn, "sandbox_failed", str(exc))
        return
    kind, payload = _sandbox_result(db, plan, job["token"])
    _send(conn, f"sandbox_{kind}", payload)


def worker_main(conn: Any) -> None:
    try:
        job = conn.recv()
    except (EOFError, OSError):
        return
    if job.get("type") == "analyze":
        idle_seconds = float(job.get("idle_seconds") or DEFAULT_IDLE_SECONDS)
        assessment = _analyze(conn, job)
        if assessment is not None:
            _serve(conn, assessment, idle_seconds)
    elif job.get("type") == "sandbox_saved":
        _run_saved_sandbox(conn, job)
