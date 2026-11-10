"""The local web interface: a stdlib HTTP server bound to 127.0.0.1 and the JSON API for the single-page app.

Security: bind to loopback only, Host validated, per-launch token and Origin check on every API request, strict CSP, no
inline scripts, nothing derived from a database used in a path. No route applies anything to a source database; the only
write target is the temporary SQLite copy inside ``migrate.sandbox``.
"""
from __future__ import annotations

import hmac
import json
import re
import secrets
import shutil
import sys
import tempfile
import threading
import webbrowser
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Optional
from urllib.parse import parse_qsl, unquote, urlsplit

from .. import __version__
from . import store as queries
from .intake import MB, IntakeError, Uploads, build_job, form_options
from .jobs import ApprovalMismatch, JobBusy, JobManager, JobNotRunning, SandboxUnavailable
from .store import RunStore, StoreError

BIND_HOST = "127.0.0.1"
STATIC_DIR = Path(__file__).resolve().parent / "static"
CONTENT_TYPES = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8",
                 ".svg": "image/svg+xml", ".png": "image/png", ".ico": "image/x-icon", ".txt": "text/plain; charset=utf-8"}
CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; "
       "base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
MAX_JSON_BODY = 4 * MB
TOKEN_HEADER = "X-DBIntel-Token"


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, **extra: Any):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.extra = extra


class UIApp:
    """State shared by all requests. One instance per launch; ``token`` is generated fresh each launch."""

    def __init__(self, runs_dir: Optional[Path] = None, max_upload_mb: int = 2048, assess_hook: Optional[str] = None,
                 idle_seconds: Optional[float] = None, token: Optional[str] = None):
        self.runs_dir = Path(runs_dir) if runs_dir else Path.cwd() / "reports" / "ui_runs"
        self.max_upload_mb = max_upload_mb
        self.token = token or secrets.token_urlsafe(32)
        self.uploads = Uploads(max_upload_mb * MB)
        self.store = RunStore(self.runs_dir)
        self.jobs = JobManager(self.store, self.uploads, assess_hook=assess_hook, idle_seconds=idle_seconds)
        self.port = 0

    def allowed_hosts(self) -> set[str]:
        hosts = {f"127.0.0.1:{self.port}", f"localhost:{self.port}"}
        if self.port == 80:
            hosts |= {"127.0.0.1", "localhost"}
        return {h.lower() for h in hosts}

    def allowed_origins(self) -> set[str]:
        origins = {f"http://127.0.0.1:{self.port}", f"http://localhost:{self.port}"}
        if self.port == 80:
            origins |= {"http://127.0.0.1", "http://localhost"}
        return origins

    def shutdown(self) -> None:
        self.jobs.shutdown()


class Handler(BaseHTTPRequestHandler):
    server_version = "dbintel-ui"
    sys_version = ""
    protocol_version = "HTTP/1.1"
    app: UIApp  # set on the bound subclass

    # --- plumbing --------------------------------------------------------

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        return  # requests are never logged, so nothing sensitive can reach a log

    def handle_expect_100(self) -> bool:
        self.send_response_only(100)
        self.end_headers()
        return True

    def _common_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", CSP)
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Cache-Control", "no-store")

    def _send_bytes(self, status: int, data: bytes, content_type: str, extra: Optional[dict[str, str]] = None, send_body: bool = True) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self._common_headers()
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        if status >= 400:
            self.send_header("Connection", "close")
            self.close_connection = True
        self.end_headers()
        if send_body and data:
            self.wfile.write(data)

    def _send_json(self, status: int, payload: Any) -> None:
        self._send_bytes(status, json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8"), "application/json; charset=utf-8")

    def _send_error_json(self, status: int, code: str, message: str, **extra: Any) -> None:
        self._send_json(status, {"error": message, "code": code, **extra})

    def send_error(self, code: int, message: Optional[str] = None, explain: Optional[str] = None) -> None:  # type: ignore[override]
        try:
            self._send_error_json(code, "http_error", "The request could not be processed.")
        except OSError:
            pass

    def _send_attachment(self, path: Path, content_type: str, filename: str) -> None:
        self._send_bytes(200, path.read_bytes(), content_type, {"Content-Disposition": f'attachment; filename="{_attachment_name(filename)}"'})

    # --- request entry ---------------------------------------------------

    def do_GET(self) -> None:  # noqa: N802
        self._handle("GET")

    def do_POST(self) -> None:  # noqa: N802
        self._handle("POST")

    def do_DELETE(self) -> None:  # noqa: N802
        self._handle("DELETE")

    def do_PUT(self) -> None:  # noqa: N802
        self._send_error_json(405, "method_not_allowed", "This method is not supported.")

    do_PATCH = do_PUT  # noqa: N815
    do_OPTIONS = do_PUT  # noqa: N815
    do_HEAD = do_PUT  # noqa: N815

    def _handle(self, method: str) -> None:
        app = self.app
        try:
            host = (self.headers.get("Host") or "").strip().lower()
            if host not in app.allowed_hosts():
                self._send_error_json(403, "bad_host", "This address is not allowed. Open the app at http://127.0.0.1.")
                return
            split = urlsplit(self.path)
            path = split.path
            query = dict(parse_qsl(split.query, keep_blank_values=True))
            if not path.startswith("/api/"):
                if method != "GET":
                    self._send_error_json(405, "method_not_allowed", "This method is not supported.")
                    return
                self._serve_static(path)
                return
            self._check_token_and_origin()
            self._route(method, path, query)
        except ApiError as exc:
            self._send_error_json(exc.status, exc.code, exc.message, **exc.extra)
        except StoreError as exc:
            self._send_error_json(exc.status, exc.code, str(exc))
        except IntakeError as exc:
            self._send_error_json(exc.status, "invalid_input", str(exc), field=exc.field)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            self.close_connection = True
        except Exception as exc:  # the response must never contain a stack trace
            self._send_error_json(500, "server_error", f"Something went wrong handling that request ({type(exc).__name__}).")

    def _check_token_and_origin(self) -> None:
        token = self.headers.get(TOKEN_HEADER) or ""
        if not hmac.compare_digest(token, self.app.token):
            raise ApiError(401, "unauthorized", "This session is not valid. Open the link printed when dbintel started.")
        origin = self.headers.get("Origin")
        if origin is not None and origin.lower() not in {o.lower() for o in self.app.allowed_origins()}:
            raise ApiError(403, "bad_origin", "Requests from other sites are not allowed.")
        if (self.headers.get("Sec-Fetch-Site") or "").lower() == "cross-site":
            raise ApiError(403, "bad_origin", "Requests from other sites are not allowed.")

    # --- static files ----------------------------------------------------

    def _serve_static(self, path: str) -> None:
        relative = unquote(path).lstrip("/")
        if relative in ("", "index.html"):
            relative = "index.html"
        elif not relative.startswith("static/"):
            self._send_error_json(404, "not_found", "Not found.")
            return
        else:
            relative = relative[len("static/"):]
        if "\\" in relative or "\x00" in relative or any(part in ("..", "") for part in relative.split("/")):
            self._send_error_json(404, "not_found", "Not found.")
            return
        base = STATIC_DIR.resolve()
        target = (base / relative).resolve()
        if base not in target.parents or not target.is_file() or target.suffix.lower() not in CONTENT_TYPES:
            self._send_error_json(404, "not_found", "Not found.")
            return
        self._send_bytes(200, target.read_bytes(), CONTENT_TYPES[target.suffix.lower()])

    # --- routing ---------------------------------------------------------

    def _route(self, method: str, path: str, query: dict[str, str]) -> None:
        for route_method, pattern, handler_name in ROUTES:
            if route_method != method:
                continue
            match = pattern.match(path)
            if match:
                getattr(self, handler_name)(query, *[unquote(group) for group in match.groups()])
                return
        for _, pattern, _ in ROUTES:
            if pattern.match(path):
                raise ApiError(405, "method_not_allowed", "This method is not supported.")
        raise ApiError(404, "not_found", "Not found.")

    def _json_body(self) -> dict[str, Any]:
        length = self._content_length()
        if length > MAX_JSON_BODY:
            self.close_connection = True
            raise ApiError(413, "too_large", "That request is too large.")
        raw = self.rfile.read(length) if length else b""
        try:
            payload = json.loads(raw.decode("utf-8")) if raw else {}
        except (UnicodeDecodeError, ValueError):
            raise ApiError(400, "invalid_input", "The request body is not valid JSON.") from None
        if not isinstance(payload, dict):
            raise ApiError(400, "invalid_input", "The request body must be a JSON object.")
        return payload

    def _drain_body(self, length: int, limit: int = 8 * MB) -> None:
        """Read a small rejected body so that the error response is delivered. Larger bodies just close the connection."""
        remaining = min(length, limit)
        while remaining > 0:
            chunk = self.rfile.read(min(1024 * 1024, remaining))
            if not chunk:
                break
            remaining -= len(chunk)
        self.close_connection = True

    def _content_length(self) -> int:
        text = self.headers.get("Content-Length")
        if text is None:
            raise ApiError(411, "length_required", "This request needs a Content-Length header.")
        try:
            length = int(text)
        except ValueError:
            raise ApiError(400, "invalid_input", "The Content-Length header is not valid.") from None
        if length < 0:
            raise ApiError(400, "invalid_input", "The Content-Length header is not valid.")
        return length

    # --- API: general ----------------------------------------------------

    def api_meta(self, query: dict[str, str]) -> None:
        self._send_json(200, {"version": __version__, "port": self.app.port, "max_upload_mb": self.app.max_upload_mb, "options": form_options(),
                              "job": self.app.jobs.current(), "uploads": self.app.uploads.list_files(), "runs_dir": str(self.app.runs_dir)})

    def api_upload(self, query: dict[str, str]) -> None:
        length = self._content_length()
        if length > self.app.uploads.max_bytes:
            self._drain_body(length)  # so the browser can read the 413 instead of seeing a reset connection
        slot = query.get("slot", "")
        filename = unquote(self.headers.get("X-Filename") or "")
        try:
            info = self.app.uploads.store(slot, filename, self.rfile, length)
        except IntakeError:
            self.close_connection = True
            raise
        self._send_json(200, {"file": info, "uploads": self.app.uploads.list_files()})

    def api_upload_clear(self, query: dict[str, str], slot: str) -> None:
        if self.app.jobs.busy():
            raise ApiError(409, "busy", "An analysis is running. Wait for it to finish or cancel it.")
        self.app.uploads.clear_slot(slot)
        self._send_json(200, {"uploads": self.app.uploads.list_files()})

    def api_uploads(self, query: dict[str, str]) -> None:
        self._send_json(200, {"uploads": self.app.uploads.list_files()})

    def api_job_current(self, query: dict[str, str]) -> None:
        self._send_json(200, self.app.jobs.current())

    def api_start_analysis(self, query: dict[str, str]) -> None:
        body = self._json_body()
        if self.app.jobs.busy():
            raise ApiError(409, "busy", "An analysis is already running. Wait for it to finish or cancel it.")
        job_spec = build_job(body, self.app.uploads)
        try:
            snapshot = self.app.jobs.start_analysis(job_spec)
        except JobBusy:
            raise ApiError(409, "busy", "An analysis is already running. Wait for it to finish or cancel it.") from None
        self._send_json(202, snapshot)

    def api_cancel(self, query: dict[str, str]) -> None:
        try:
            snapshot = self.app.jobs.cancel()
        except JobNotRunning:
            raise ApiError(409, "not_running", "Nothing is running.") from None
        self._send_json(200, snapshot)

    # --- API: runs -------------------------------------------------------

    def _run(self, run_id: str) -> Any:
        return self.app.store.load(run_id)

    def api_runs(self, query: dict[str, str]) -> None:
        self._send_json(200, {"runs": self.app.store.list_runs(), "job": self.app.jobs.current()})

    def api_run(self, query: dict[str, str], run_id: str) -> None:
        self._send_json(200, queries.run_overview(self._run(run_id)))

    def api_run_delete(self, query: dict[str, str], run_id: str) -> None:
        self.app.store.run_dir(run_id)
        try:
            self.app.jobs.ensure_deletable(run_id)
        except JobBusy:
            raise ApiError(409, "busy", "This run is being tested. Wait for the test to finish or cancel it.") from None
        self.app.jobs.forget_run(run_id)
        self.app.store.delete(run_id)
        self._send_json(200, {"deleted": run_id})

    def api_findings(self, query: dict[str, str], run_id: str) -> None:
        self._send_json(200, queries.query_findings(self._run(run_id), query))

    def api_finding(self, query: dict[str, str], run_id: str, finding_id: str) -> None:
        self._send_json(200, queries.finding_detail(self._run(run_id), finding_id))

    def api_tables(self, query: dict[str, str], run_id: str) -> None:
        self._send_json(200, queries.query_tables(self._run(run_id), query))

    def api_table_names(self, query: dict[str, str], run_id: str) -> None:
        self._send_json(200, {"names": queries.table_names(self._run(run_id))})

    def api_table(self, query: dict[str, str], run_id: str, name: str) -> None:
        self._send_json(200, queries.table_detail(self._run(run_id), name))

    def api_er(self, query: dict[str, str], run_id: str) -> None:
        self._send_json(200, queries.er_view(self._run(run_id), query))

    def api_er_mermaid(self, query: dict[str, str], run_id: str) -> None:
        text, filename = queries.er_mermaid(self._run(run_id), query)
        self._send_bytes(200, text.encode("utf-8"), "text/plain; charset=utf-8", {"Content-Disposition": f'attachment; filename="{_attachment_name(filename)}"'})

    def api_recommendations(self, query: dict[str, str], run_id: str) -> None:
        self._send_json(200, queries.query_recommendations(self._run(run_id), query))

    def api_recommendation(self, query: dict[str, str], run_id: str, rec_id: str) -> None:
        self._send_json(200, queries.recommendation_detail(self._run(run_id), rec_id))

    def api_steps(self, query: dict[str, str], run_id: str) -> None:
        self._send_json(200, queries.query_steps(self._run(run_id), query))

    def api_step(self, query: dict[str, str], run_id: str, step_id: str) -> None:
        self._send_json(200, queries.step_detail(self._run(run_id), step_id))

    def api_section(self, query: dict[str, str], run_id: str, name: str) -> None:
        self._send_json(200, {"section": name, "data": queries.run_section(self._run(run_id), name)})

    def api_export(self, query: dict[str, str], run_id: str, fmt: str) -> None:
        path, content_type, filename = self.app.store.export_path(run_id, fmt)
        self._send_attachment(path, content_type, filename)

    def api_migration_zip(self, query: dict[str, str], run_id: str) -> None:
        directory = self.app.store.run_dir(run_id)
        migrations = directory / "migrations"
        if not migrations.is_dir():
            raise StoreError("This run has no migration files.")
        with tempfile.SpooledTemporaryFile(max_size=32 * MB) as spool:
            with zipfile.ZipFile(spool, "w", zipfile.ZIP_DEFLATED) as archive:
                for file in sorted(migrations.iterdir()):
                    if file.is_file():
                        archive.write(file, f"migrations/{file.name}")
            spool.seek(0)
            data = spool.read()
        self._send_bytes(200, data, "application/zip", {"Content-Disposition": f'attachment; filename="migrations_{run_id}.zip"'})

    def api_compare(self, query: dict[str, str]) -> None:
        a, b = query.get("a", ""), query.get("b", "")
        if not a or not b or a == b:
            raise ApiError(400, "invalid_input", "Choose two different runs to compare.")
        self._send_json(200, queries.compare_runs(self._run(a), self._run(b)))

    # --- API: sandbox ----------------------------------------------------

    def _plan_hash(self, run_id: str) -> Optional[str]:
        return (self._run(run_id).report.get("migration") or {}).get("plan_hash")

    def api_sandbox_status(self, query: dict[str, str], run_id: str) -> None:
        directory = self.app.store.run_dir(run_id)
        self._send_json(200, self.app.jobs.sandbox_status(run_id, self._plan_hash(run_id), directory))

    def api_sandbox_start(self, query: dict[str, str], run_id: str) -> None:
        directory = self.app.store.run_dir(run_id)
        body = self._json_body()
        token = body.get("plan_hash")
        if self.app.jobs.busy():
            raise ApiError(409, "busy", "An analysis or test is already running. Wait for it to finish or cancel it.")
        try:
            snapshot = self.app.jobs.start_sandbox(run_id, str(token or ""), self._plan_hash(run_id), directory)
        except ApprovalMismatch:
            raise ApiError(403, "plan_hash_mismatch", "That is not the hash of this migration plan. Copy the exact plan hash shown above.") from None
        except JobBusy:
            raise ApiError(409, "busy", "An analysis or test is already running. Wait for it to finish or cancel it.") from None
        except SandboxUnavailable as exc:
            raise ApiError(409, "sandbox_unavailable", exc.reason) from None
        self._send_json(202, snapshot)


def _attachment_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", name)[:200]


RUN = r"(\d{8}-\d{6}-[0-9a-f]{6})"
RAW_RUN = r"([^/]+)"
SEG = r"([^/]+)"
ROUTES: list[tuple[str, re.Pattern, str]] = [(m, re.compile("^" + p + "$"), h) for m, p, h in [
    ("GET", "/api/meta", "api_meta"),
    ("GET", "/api/analysis/current", "api_job_current"),
    ("POST", "/api/analysis", "api_start_analysis"),
    ("POST", "/api/analysis/cancel", "api_cancel"),
    ("POST", "/api/uploads", "api_upload"),
    ("GET", "/api/uploads", "api_uploads"),
    ("DELETE", f"/api/uploads/{SEG}", "api_upload_clear"),
    ("GET", "/api/runs", "api_runs"),
    ("GET", f"/api/runs/{RAW_RUN}", "api_run"),
    ("DELETE", f"/api/runs/{RAW_RUN}", "api_run_delete"),
    ("GET", f"/api/runs/{RAW_RUN}/findings", "api_findings"),
    ("GET", f"/api/runs/{RAW_RUN}/findings/{SEG}", "api_finding"),
    ("GET", f"/api/runs/{RAW_RUN}/tables", "api_tables"),
    ("GET", f"/api/runs/{RAW_RUN}/table-names", "api_table_names"),
    ("GET", f"/api/runs/{RAW_RUN}/tables/{SEG}", "api_table"),
    ("GET", f"/api/runs/{RAW_RUN}/er", "api_er"),
    ("GET", f"/api/runs/{RAW_RUN}/er/mermaid", "api_er_mermaid"),
    ("GET", f"/api/runs/{RAW_RUN}/recommendations", "api_recommendations"),
    ("GET", f"/api/runs/{RAW_RUN}/recommendations/{SEG}", "api_recommendation"),
    ("GET", f"/api/runs/{RAW_RUN}/migration/steps", "api_steps"),
    ("GET", f"/api/runs/{RAW_RUN}/migration/steps/{SEG}", "api_step"),
    ("GET", f"/api/runs/{RAW_RUN}/migration/zip", "api_migration_zip"),
    ("GET", f"/api/runs/{RAW_RUN}/section/{SEG}", "api_section"),
    ("GET", f"/api/runs/{RAW_RUN}/export/{SEG}", "api_export"),
    ("GET", f"/api/runs/{RAW_RUN}/sandbox", "api_sandbox_status"),
    ("POST", f"/api/runs/{RAW_RUN}/sandbox", "api_sandbox_start"),
    ("GET", "/api/compare", "api_compare"),
]]


class _Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False  # a second instance on the port must fail to bind, not silently share it

    def handle_error(self, request: Any, client_address: Any) -> None:
        return  # no traceback on the console for dropped connections


def make_server(app: UIApp, port: int = 0) -> _Server:
    """Create the server bound to 127.0.0.1. Always loopback; this function takes no host argument."""
    handler = type("BoundHandler", (Handler,), {"app": app})
    server = _Server((BIND_HOST, port), handler)
    app.port = server.server_address[1]
    return server


def run_ui(port: int = 8765, open_browser: bool = True, max_upload_mb: int = 2048) -> int:
    """Serve the interface until interrupted. Returns a process exit code."""
    app = UIApp(max_upload_mb=max_upload_mb)
    try:
        server = make_server(app, port)
    except OSError:
        app.shutdown()
        print(f"Port {port} on 127.0.0.1 is in use. Start with a different port: --port <number>.", file=sys.stderr)
        return 1
    url = f"http://127.0.0.1:{app.port}/#token={app.token}"
    print(f"dbintel UI: {url}", flush=True)
    print("It listens only on this computer. Press Ctrl+C to stop.", flush=True)
    if open_browser:
        threading.Timer(0.4, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping.", flush=True)
    finally:
        server.server_close()
        app.shutdown()
    return 0


__all__ = ["ApiError", "BIND_HOST", "CSP", "Handler", "ROUTES", "TOKEN_HEADER", "UIApp", "make_server", "run_ui"]
