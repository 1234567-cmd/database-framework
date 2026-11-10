"""The local web interface: API, security, jobs, history, compare and the no-apply guarantee."""
import hashlib
import http.client
import inspect
import json
import os
import re
import sqlite3
import subprocess
import sys
import threading
import time
import zipfile
from io import BytesIO
from pathlib import Path

import pytest

import dbintel.ui.server as server_module
from dbintel import cli
from dbintel.pipeline import ASSESSMENT_STAGES, assess
from dbintel.ui.intake import IntakeError, Uploads, sanitize_filename
from dbintel.ui.rebuild import RebuildError, rebuild, rebuild_database, rebuild_plan
from dbintel.ui.server import BIND_HOST, CSP, ROUTES, STATIC_DIR, TOKEN_HEADER, UIApp, make_server

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "samples"
ERP = str(SAMPLES / "erp_mysql.sql")
PACKAGE = ROOT / "src" / "dbintel" / "ui"


class Client:
    def __init__(self, app: UIApp, server):
        self.app = app
        self.server = server
        self.port = app.port

    def req(self, method, path, body=None, headers=None, token=True, host=None, raw_body=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        hdrs = dict(headers or {})
        if token:
            hdrs.setdefault(TOKEN_HEADER, self.app.token)
        if host is not None:
            hdrs["Host"] = host
        payload = raw_body
        if body is not None:
            payload = json.dumps(body).encode("utf-8")
            hdrs.setdefault("Content-Type", "application/json")
        if payload is not None:
            hdrs.setdefault("Content-Length", str(len(payload)))
        conn.putrequest(method, path, skip_host="Host" in hdrs, skip_accept_encoding=True)
        for key, value in hdrs.items():
            conn.putheader(key, value)
        conn.endheaders()
        if payload:
            conn.send(payload)
        response = conn.getresponse()
        data = response.read()
        result = (response.status, dict((k.lower(), v) for k, v in response.getheaders()), data)
        conn.close()
        return result

    def json(self, method, path, body=None, headers=None, token=True, host=None):
        status, _, data = self.req(method, path, body=body, headers=headers, token=token, host=host)
        return status, json.loads(data.decode("utf-8")) if data else None

    def wait_job(self, seconds=120, kinds=("done", "failed", "cancelled")):
        deadline = time.time() + seconds
        while time.time() < deadline:
            _, job = self.json("GET", "/api/analysis/current")
            if job.get("state") in kinds:
                return job
            time.sleep(0.1)
        raise AssertionError("job did not finish")


def _client_for(app: UIApp):
    server = make_server(app, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    client = Client(app, server)
    return client, server, thread


@pytest.fixture()
def client(tmp_path):
    app = UIApp(runs_dir=tmp_path / "runs")
    c, server, _ = _client_for(app)
    yield c
    server.shutdown()
    server.server_close()
    app.shutdown()


@pytest.fixture(scope="module")
def erp_run(tmp_path_factory):
    """A real analysis of the ERP sample through the HTTP API, followed by read-only checks."""
    runs = tmp_path_factory.mktemp("runs")
    app = UIApp(runs_dir=runs)
    client, server, _ = _client_for(app)
    status, job = client.json("POST", "/api/analysis", {"source": {"kind": "path", "path": ERP}, "settings": {"workload": "OLTP"}})
    assert status == 202
    assert job["kind"] == "analysis" and [s["key"] for s in job["stages"]][:8] == list(ASSESSMENT_STAGES)
    job = client.wait_job()
    assert job["state"] == "done", job
    yield {"client": client, "run_id": job["run_id"], "app": app, "runs": runs}
    server.shutdown()
    server.server_close()
    app.shutdown()


def write_synthetic(runs_dir: Path, run_id: str, findings_by_id=None, n: int = 0, overall: float = 72.0, tables: int = 5):
    d = runs_dir / run_id
    d.mkdir(parents=True)
    findings = []
    source = findings_by_id or [{"id": f"RUL-{i:05d}"} for i in range(n)]
    for i, f in enumerate(source):
        findings.append({"id": f["id"], "rule_id": f.get("rule_id", "RUL"), "title": f.get("title", f"Finding {i}"), "severity": f.get("severity", ["critical", "high", "medium", "low", "informational"][i % 5]),
                         "kind": f.get("kind", ["optional_improvement", "confirmed_defect", "context_dependent"][i % 3]), "category": f.get("category", "schema_quality"),
                         "database": "synth", "table": f.get("table", f"t{i % tables}"), "column": None, "evidence": "e", "root_cause": "r", "business_impact": "b", "technical_impact": "t",
                         "standards": [], "standard_statements": {}, "recommended_solution": "s", "complexity": "low", "migration_requirements": "m", "risks": "x", "validation_strategy": "v",
                         "confidence": 0.9, "provisional_standard": False, "fix": None, "data": {}})
    report = {"format": "dbintel-report", "version": 1, "generated_at": "2026-01-01T00:00:00+00:00", "source": {"name": "synth", "dialect": "mysql", "kind": "sql_dump", "label": "synth.sql"},
              "profile": {"workload": "OLTP", "tenancy": "none", "multi_company": False},
              "summary": {"text": ["Synthetic."], "top_risks": [], "critical": 0, "high": 0, "confirmed_defects": 0, "tables": tables},
              "health": {"overall": overall, "grade": "B", "confidence": 0.9, "capped": False, "categories": [{"category": "schema_quality", "score": overall, "grade": "B", "confidence": 0.9, "rules_executed": 1, "rules_skipped": 0, "deductions": [], "skipped_reasons": []}], "method": "m", "weights": {}},
              "distribution": {"severity": {}, "kind": {}, "category": {}},
              "findings": {"confirmed_defect": [f for f in findings if f["kind"] == "confirmed_defect"], "context_dependent": [f for f in findings if f["kind"] == "context_dependent"], "optional_improvement": [f for f in findings if f["kind"] == "optional_improvement"]},
              "findings_total": len(findings), "root_cause_groups": [], "recommendations": [], "migration": {"plan_hash": "h" * 64, "steps": []}, "lineage": {"edges": [], "nodes": [], "gaps": [], "notes": []},
              "architecture": {"tables": [{"name": f"t{i}", "columns": 1, "primary_key": ["id"], "foreign_keys": 0, "indexes": 0, "referenced_by": 0, "row_count": None, "column_list": [{"name": "id", "type": "int", "nullable": False, "default": None, "comment": None}]} for i in range(tables)],
                               "relations": [], "domains": [], "views": [], "routines": []},
              "roadmap": {"phases": [], "prerequisites": [], "basis": ""}, "coverage": {"rules_executed": [], "rules_executed_count": 0, "skipped": [], "skipped_count": 0, "errors": [], "errors_count": 0, "capabilities": []},
              "import_warnings": [], "limitations": [], "er": {"current": [], "proposed": []}, "timing": {}}
    (d / "report.json").write_text(json.dumps(report), encoding="utf-8")
    summary = {"id": run_id, "name": "synth", "generated_at": report["generated_at"], "overall": overall, "findings_total": len(findings)}
    (d / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    return d


# --- security ---------------------------------------------------------------

def test_server_binds_only_to_loopback(client):
    assert client.server.server_address[0] == "127.0.0.1" and BIND_HOST == "127.0.0.1"
    assert "host" not in inspect.signature(make_server).parameters


@pytest.mark.parametrize("host", ["evil.example", "evil.example:80", "attacker.test:8765"])
def test_bad_host_header_is_refused(client, host):
    status, _, _ = client.req("GET", "/", token=False, host=host)
    assert status == 403


def test_host_validation_allows_loopback_names(client):
    assert client.req("GET", "/", token=False, host=f"127.0.0.1:{client.port}")[0] == 200
    assert client.req("GET", "/", token=False, host=f"localhost:{client.port}")[0] == 200


def test_missing_host_header_is_refused(client):
    conn = http.client.HTTPConnection("127.0.0.1", client.port, timeout=10)
    conn.putrequest("GET", "/", skip_host=True)
    conn.endheaders()
    assert conn.getresponse().status == 403


@pytest.mark.parametrize("path", ["/api/meta", "/api/runs", "/api/analysis/current"])
def test_api_requires_token(client, path):
    assert client.req("GET", path, token=False)[0] == 401
    assert client.req("GET", path, headers={TOKEN_HEADER: "wrong"}, token=False)[0] == 401
    assert client.req("GET", path)[0] == 200


def test_state_changing_requests_require_token(client):
    assert client.req("POST", "/api/analysis", body={}, token=False)[0] == 401
    assert client.req("POST", "/api/analysis/cancel", body={}, token=False)[0] == 401
    assert client.req("DELETE", "/api/runs/20250101-000000-abcdef", token=False)[0] == 401
    assert client.req("POST", "/api/uploads?slot=source", raw_body=b"x", headers={"X-Filename": "a.sql"}, token=False)[0] == 401


@pytest.mark.parametrize("headers", [{"Origin": "http://evil.example"}, {"Origin": "http://127.0.0.1:1"}, {"Sec-Fetch-Site": "cross-site"}])
def test_cross_origin_requests_are_refused(client, headers):
    assert client.req("GET", "/api/runs", headers=headers)[0] == 403
    assert client.req("POST", "/api/analysis/cancel", body={}, headers=headers)[0] == 403


def test_same_origin_header_is_accepted(client):
    assert client.req("GET", "/api/runs", headers={"Origin": f"http://127.0.0.1:{client.port}"})[0] == 200
    assert client.req("GET", "/api/runs", headers={"Origin": f"http://localhost:{client.port}", "Sec-Fetch-Site": "same-origin"})[0] == 200


@pytest.mark.parametrize("method,path", [("GET", "/"), ("GET", "/api/runs"), ("GET", "/static/css/app.css"), ("GET", "/api/nope")])
def test_security_headers_on_every_response(client, method, path):
    status, headers, _ = client.req(method, path)
    assert headers.get("content-security-policy") == CSP
    assert headers.get("x-content-type-options") == "nosniff"
    assert headers.get("x-frame-options") == "DENY"
    assert headers.get("cache-control") == "no-store"
    assert "unsafe-inline" not in CSP and "unsafe-eval" not in CSP and "default-src 'none'" in CSP and "script-src 'self'" in CSP


def test_token_is_random_per_launch(tmp_path):
    a = UIApp(runs_dir=tmp_path / "a")
    b = UIApp(runs_dir=tmp_path / "b")
    try:
        assert a.token != b.token and len(a.token) > 30
    finally:
        a.shutdown()
        b.shutdown()


def test_http_methods_without_routes_are_refused(client):
    for method in ("PUT", "PATCH", "OPTIONS", "HEAD"):
        assert client.req(method, "/api/runs")[0] == 405


def test_index_is_served_without_token_and_contains_no_inline_script(client):
    status, headers, data = client.req("GET", "/", token=False)
    html = data.decode("utf-8")
    assert status == 200 and headers["content-type"].startswith("text/html")
    assert not re.search(r"<script(?![^>]*\bsrc=)", html, re.I)
    assert not re.search(r"\son\w+\s*=", html, re.I)
    assert "<style" not in html.lower()


def static_files():
    return [p for p in STATIC_DIR.rglob("*") if p.is_file()]


def test_static_assets_have_no_external_urls():
    allowed = {"http://www.w3.org/2000/svg"}
    bad = []
    for path in static_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for url in re.findall(r"""https?://[^\s"'`)<>]+""", text):
            if url not in allowed:
                bad.append((path.name, url))
        if re.search(r"""(?:src|href)\s*=\s*["']//""", text):
            bad.append((path.name, "protocol-relative"))
    assert not bad


def test_static_assets_avoid_html_string_insertion():
    forbidden = re.compile(r"innerHTML|outerHTML|insertAdjacentHTML|document\.write|\beval\s*\(|new\s+Function\b|setHTML\b|createContextualFragment")
    offenders = [p.name for p in static_files() if p.suffix == ".js" and forbidden.search(p.read_text(encoding="utf-8"))]
    assert not offenders


def test_static_css_and_html_have_no_inline_event_handlers_or_style_attributes():
    for path in static_files():
        if path.suffix == ".html":
            text = path.read_text(encoding="utf-8")
            assert ' style="' not in text and not re.search(r"\son\w+\s*=", text, re.I)
    js = "".join(p.read_text(encoding="utf-8") for p in static_files() if p.suffix == ".js")
    assert 'setAttribute("style"' not in js and "cssText" not in js


def test_static_path_traversal_is_refused(client):
    for path in ("/static/../server.py", "/static/%2e%2e/server.py", "/static/..%5cserver.py", "/static/js/../../server.py", "/static/", "/static/nothing.js"):
        assert client.req("GET", path, token=False)[0] == 404, path


@pytest.mark.parametrize("bad", ["..", "..%2F..%2Fsecret", "a", "20250101-000000-ABCDEF", "20250101-000000-abcde%2F..", "20250101-000000-abcdeg"])
def test_run_id_traversal_is_refused(client, bad):
    assert client.req("GET", f"/api/runs/{bad}")[0] in (403, 404)
    assert client.req("DELETE", f"/api/runs/{bad}")[0] in (403, 404, 405)


def test_export_traversal_and_unknown_format_are_refused(erp_run):
    c = erp_run["client"]
    run_id = erp_run["run_id"]
    for fmt in ("..%2Freport.json", "pdf", "..\\report.json", "report.json"):
        assert c.req("GET", f"/api/runs/{run_id}/export/{fmt}")[0] in (403, 404)


def test_bad_json_and_oversize_body_are_handled(client):
    assert client.req("POST", "/api/analysis", raw_body=b"{not json")[0] == 400
    status, _, data = client.req("POST", "/api/analysis", raw_body=b"[1]")
    assert status == 400 and b"Traceback" not in data


def test_errors_never_contain_stack_traces(client):
    for method, path, body in [("GET", "/api/runs/20250101-000000-abcdef", None), ("POST", "/api/analysis", {"source": {"kind": "path", "path": "C:\\no\\such\\file.sql"}}), ("GET", "/api/compare", None)]:
        status, _, data = client.req(method, path, body=body)
        assert status >= 400
        text = data.decode("utf-8")
        assert "Traceback" not in text and "File \"" not in text and "error" in json.loads(text)


# --- uploads --------------------------------------------------------------

def test_upload_limit_rejects_oversize_and_leaves_nothing(tmp_path):
    app = UIApp(runs_dir=tmp_path / "runs", max_upload_mb=1)
    c, server, _ = _client_for(app)
    try:
        status, _, data = c.req("POST", "/api/uploads?slot=source", raw_body=b"x" * (2 * 1024 * 1024), headers={"X-Filename": "big.sql"})
        assert status == 413 and b"limit" in data
        assert not any((app.uploads.root / "source").glob("*")) if (app.uploads.root / "source").exists() else True
        status, _, _ = c.req("POST", "/api/uploads?slot=source", raw_body=b"select 1;", headers={"X-Filename": "ok.sql"})
        assert status == 200
    finally:
        server.shutdown(); server.server_close(); app.shutdown()


def test_upload_streams_to_private_temp_and_rejects_bad_names(client):
    status, _, data = client.req("POST", "/api/uploads?slot=source", raw_body=b"select 1;", headers={"X-Filename": "..%5C..%5Cevil.sql"})
    assert status == 200
    stored = json.loads(data)["file"]["name"]
    assert "/" not in stored and "\\" not in stored and ".." not in stored
    root = client.app.uploads.root
    assert root.is_dir() and (root / "source" / stored).read_bytes() == b"select 1;"
    assert client.req("POST", "/api/uploads?slot=../../x", raw_body=b"a", headers={"X-Filename": "a.sql"})[0] == 400


def test_sanitize_filename():
    assert sanitize_filename("C:\\dump\\my db.sql") == "my db.sql"
    assert sanitize_filename("../../etc/passwd.sql") == "passwd.sql"
    with pytest.raises(IntakeError):
        sanitize_filename("..")


def test_stale_upload_directories_are_swept_at_launch(tmp_path, monkeypatch):
    import tempfile

    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    stale = tmp_path / "dbintel_ui_old"
    stale.mkdir()
    (stale / "dump.sql").write_text("x", encoding="utf-8")
    old = time.time() - 48 * 3600
    os.utime(stale, (old, old))
    fresh = tmp_path / "dbintel_ui_recent"
    fresh.mkdir()
    unrelated = tmp_path / "other_folder"
    unrelated.mkdir()
    os.utime(unrelated, (old, old))
    uploads = Uploads(10)
    try:
        assert not stale.exists() and fresh.is_dir() and unrelated.is_dir()
    finally:
        uploads.remove_root()


def test_upload_limit_counted_while_streaming(tmp_path):
    uploads = Uploads(10)
    try:
        with pytest.raises(IntakeError):
            uploads.store("source", "a.sql", BytesIO(b"x" * 11), 11)
        assert not list((uploads.root / "source").glob("*"))
    finally:
        uploads.remove_root()


# --- analysis, progress, cancel, history -----------------------------------

def test_progress_callback_reports_each_stage_in_order():
    seen = []
    assess(str(SAMPLES / "clean_postgres.sql"), progress=lambda stage, state, seconds: seen.append((stage, state, seconds)))
    starts = [s for s, st, _ in seen if st == "start"]
    dones = [s for s, st, _ in seen if st == "done"]
    assert starts == list(ASSESSMENT_STAGES) and dones == list(ASSESSMENT_STAGES)
    assert all(sec >= 0 for _, _, sec in seen)


def test_assess_without_progress_still_works():
    assert assess(str(SAMPLES / "clean_postgres.sql")).findings is not None


def test_real_analysis_exposes_overview_and_stores_only_reports(erp_run):
    c, run_id, runs = erp_run["client"], erp_run["run_id"], erp_run["runs"]
    status, overview = c.json("GET", f"/api/runs/{run_id}")
    assert status == 200 and overview["id"] == run_id
    assert overview["health"]["categories"] and overview["findings_total"] > 0 and overview["migration"]["plan_hash"]
    assert all(k in overview for k in ("summary", "distribution", "import_warnings", "limitations"))
    names = {p.name for p in (runs / run_id).iterdir()}
    assert names == {"report.html", "report.json", "report.md", "er", "migrations", "summary.json"}
    assert not [p for p in runs.iterdir() if p.name.startswith(".partial")]


def test_run_data_stays_under_configured_directory(tmp_path):
    app = UIApp(runs_dir=tmp_path / "reports" / "ui_runs")
    try:
        assert app.store.root.is_dir() and app.store.root.parent.name == "reports"
    finally:
        app.shutdown()


def test_default_runs_dir_is_reports_ui_runs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    app = UIApp()
    try:
        assert app.runs_dir == tmp_path / "reports" / "ui_runs" and app.runs_dir.is_dir()
    finally:
        app.shutdown()


def test_finding_detail_links_recommendation_and_step(erp_run):
    c, run_id = erp_run["client"], erp_run["run_id"]
    status, page = c.json("GET", f"/api/runs/{run_id}/findings?size=200")
    assert status == 200 and page["items"][0]["kind"] == "confirmed_defect" and page["default_view"] is True
    linked = None
    for row in page["items"]:
        _, detail = c.json("GET", f"/api/runs/{run_id}/findings/{row['id']}")
        if detail["recommendations"] and detail["steps"]:
            linked = detail
            break
    assert linked is not None
    finding = linked["finding"]
    for key in ("id", "database", "table", "column", "evidence", "root_cause", "business_impact", "technical_impact", "standards", "standard_statements", "recommended_solution",
                "complexity", "migration_requirements", "risks", "validation_strategy", "confidence", "kind", "provisional_standard"):
        assert key in finding, key
    assert c.req("GET", f"/api/runs/{run_id}/findings/does-not-exist")[0] == 404


def test_findings_filter_search_sort_and_facets(erp_run):
    c, run_id = erp_run["client"], erp_run["run_id"]
    _, all_page = c.json("GET", f"/api/runs/{run_id}/findings?size=200")
    total = all_page["total"]
    assert all_page["facets"]["severity"] and all_page["facets"]["kind"]
    _, high = c.json("GET", f"/api/runs/{run_id}/findings?severity=critical,high&size=200")
    assert high["total"] < total and all(f["severity"] in ("critical", "high") for f in high["items"])
    _, confirmed = c.json("GET", f"/api/runs/{run_id}/findings?kind=confirmed_defect&size=200")
    assert all(f["kind"] == "confirmed_defect" for f in confirmed["items"])
    rule = all_page["items"][0]["rule_id"]
    _, by_rule = c.json("GET", f"/api/runs/{run_id}/findings?rule={rule}")
    assert all(f["rule_id"] == rule for f in by_rule["items"]) and by_rule["facets"]["severity"]
    table = next(f["table"] for f in all_page["items"] if f["table"])
    _, by_table = c.json("GET", f"/api/runs/{run_id}/findings?table={table}")
    assert by_table["total"] >= 1 and all((f["table"] or "").lower() == table.lower() for f in by_table["items"])
    _, searched = c.json("GET", f"/api/runs/{run_id}/findings?q={rule}")
    assert searched["total"] >= by_rule["total"] > 0
    _, conf = c.json("GET", f"/api/runs/{run_id}/findings?confidence=high&size=5")
    assert all(f["confidence"] >= 0.8 for f in conf["items"])
    _, sorted_page = c.json("GET", f"/api/runs/{run_id}/findings?sort=title&size=20")
    titles = [f["title"].lower() for f in sorted_page["items"]]
    assert titles == sorted(titles)
    _, desc = c.json("GET", f"/api/runs/{run_id}/findings?sort=confidence&order=desc&size=20")
    values = [f["confidence"] for f in desc["items"]]
    assert values == sorted(values, reverse=True)


def test_large_result_pagination_is_server_side(client):
    write_synthetic(client.app.runs_dir, "20250101-000000-aaaaaa", n=20000)
    run_id = "20250101-000000-aaaaaa"
    started = time.time()
    status, page1 = client.json("GET", f"/api/runs/{run_id}/findings?size=50&page=1")
    assert status == 200 and page1["total"] == 20000 and page1["pages"] == 400 and len(page1["items"]) == 50
    _, last = client.json("GET", f"/api/runs/{run_id}/findings?size=50&page=400")
    assert len(last["items"]) == 50 and last["items"][0]["id"] != page1["items"][0]["id"]
    _, clamped = client.json("GET", f"/api/runs/{run_id}/findings?size=50&page=99999")
    assert clamped["page"] == 400
    _, big = client.json("GET", f"/api/runs/{run_id}/findings?size=100000")
    assert len(big["items"]) == 200
    assert time.time() - started < 15
    ids = {row["id"] for row in page1["items"]}
    assert len(ids) == 50


def test_tables_list_and_detail(erp_run):
    c, run_id = erp_run["client"], erp_run["run_id"]
    _, page = c.json("GET", f"/api/runs/{run_id}/tables?size=200")
    assert page["total"] == page["total_tables"] >= 1
    assert all("findings" in t and "severity_counts" in t for t in page["items"])
    name = page["items"][0]["name"]
    _, detail = c.json("GET", f"/api/runs/{run_id}/tables/{name}")
    assert detail["columns"] and "indexes" in detail and "relations_out" in detail and "relations_in" in detail and "dependencies" in detail and "findings" in detail
    assert c.req("GET", f"/api/runs/{run_id}/tables/no_such_table")[0] == 404
    _, searched = c.json("GET", f"/api/runs/{run_id}/tables?q={name[:3]}")
    assert searched["total"] >= 1


def test_er_views_do_not_draw_everything_for_large_schemas(client):
    write_synthetic(client.app.runs_dir, "20250101-000000-bbbbbb", n=0, tables=213)
    run_id = "20250101-000000-bbbbbb"
    _, view = client.json("GET", f"/api/runs/{run_id}/er")
    assert view["total_tables"] == 213 and len(view["nodes"]) <= view["node_limit"]


def test_er_focus_proposed_and_mermaid(erp_run):
    c, run_id = erp_run["client"], erp_run["run_id"]
    _, view = c.json("GET", f"/api/runs/{run_id}/er")
    assert view["nodes"] and view["diagrams"] and view["proposed_available"] is True
    table = view["nodes"][0]["name"]
    _, focused = c.json("GET", f"/api/runs/{run_id}/er?focus={table}&hops=1")
    assert focused["focus"] == table and any(n["focus"] for n in focused["nodes"]) and len(focused["nodes"]) <= focused["node_limit"]
    _, proposed = c.json("GET", f"/api/runs/{run_id}/er?mode=proposed&focus={table}")
    assert proposed["mode"] == "proposed"
    status, headers, data = c.req("GET", f"/api/runs/{run_id}/er/mermaid?diagram=0")
    assert status == 200 and b"erDiagram" in data and "attachment" in headers["content-disposition"]
    status, _, data = c.req("GET", f"/api/runs/{run_id}/er/mermaid?focus={table}")
    assert status == 200 and b"erDiagram" in data
    assert c.req("GET", f"/api/runs/{run_id}/er?focus=not_a_table")[0] == 404


def test_recommendations_show_when_application_impact_was_not_evaluated(erp_run):
    c, run_id = erp_run["client"], erp_run["run_id"]
    _, page = c.json("GET", f"/api/runs/{run_id}/recommendations")
    rec_id = page["items"][0]["id"]
    assert page["items"][0]["application_impact_evaluated"] is False
    _, detail = c.json("GET", f"/api/runs/{run_id}/recommendations/{rec_id}")
    r = detail["recommendation"]
    for key in ("priority_rationale", "existing_structure", "recommended_structure", "before_after", "proposed_sql", "application_dependencies", "data_dependencies", "data_migration", "rollback", "validation_tests"):
        assert key in r, key
    assert r["application_impact_evaluated"] is False and r["application_dependencies"][0]["status"] == "not_evaluated"
    assert c.req("GET", f"/api/runs/{run_id}/recommendations/REC-none")[0] == 404


def test_migration_steps_filters_detail_and_zip(erp_run):
    c, run_id = erp_run["client"], erp_run["run_id"]
    _, page = c.json("GET", f"/api/runs/{run_id}/migration/steps?size=200")
    assert page["total"] == page["total_steps"] and page["flag_counts"]["manual"] >= 0
    _, destructive = c.json("GET", f"/api/runs/{run_id}/migration/steps?flags=destructive")
    assert all(s["destructive"] for s in destructive["items"])
    _, manual = c.json("GET", f"/api/runs/{run_id}/migration/steps?flags=manual&size=3")
    step_id = next(s["id"] for s in page["items"] if not s["manual"])
    _, detail = c.json("GET", f"/api/runs/{run_id}/migration/steps/{step_id}")
    step = detail["step"]
    for key in ("up_script", "down_script", "prechecks", "postchecks", "reversible", "destructive", "requires_data_repair"):
        assert key in step, key
    assert any("sql" in check for check in step["prechecks"] + step["postchecks"])
    status, headers, data = c.req("GET", f"/api/runs/{run_id}/migration/zip")
    assert status == 200 and headers["content-type"] == "application/zip" and data.startswith(b"PK")
    with zipfile.ZipFile(BytesIO(data)) as archive:
        names = archive.namelist()
    assert "migrations/plan.json" in names and "migrations/README.md" in names
    assert all(n.startswith("migrations/") for n in names)


def test_sections_and_exports(erp_run):
    c, run_id = erp_run["client"], erp_run["run_id"]
    for section in ("roadmap", "lineage", "architecture", "coverage", "limitations"):
        status, payload = c.json("GET", f"/api/runs/{run_id}/section/{section}")
        assert status == 200 and payload["data"] is not None, section
    assert c.req("GET", f"/api/runs/{run_id}/section/secrets")[0] == 404
    for fmt, needle in (("html", b"<html"), ("md", b"#"), ("json", b"dbintel-report")):
        status, headers, data = c.req("GET", f"/api/runs/{run_id}/export/{fmt}")
        assert status == 200 and needle in data and "attachment" in headers["content-disposition"], fmt


def test_cancel_stops_the_analysis_and_leaves_no_partial_run(tmp_path):
    app = UIApp(runs_dir=tmp_path / "runs", assess_hook="ui_test_hooks:slow_assess")
    c, server, _ = _client_for(app)
    try:
        status, _, _ = c.req("POST", "/api/uploads?slot=source", raw_body=b"create table t (id int);", headers={"X-Filename": "t.sql"})
        assert status == 200
        status, job = c.json("POST", "/api/analysis", {"source": {"kind": "upload"}})
        assert status == 202
        deadline = time.time() + 60
        while time.time() < deadline:
            _, current = c.json("GET", "/api/analysis/current")
            if current["stages"][0]["state"] == "running":
                break
            time.sleep(0.05)
        assert current["stages"][0]["state"] == "running"
        status, body = c.json("POST", "/api/analysis", {"source": {"kind": "upload"}})
        assert status == 409 and body["code"] == "busy"
        status, cancelled = c.json("POST", "/api/analysis/cancel", {})
        assert status == 200 and cancelled["state"] == "cancelling"
        final = c.wait_job()
        assert final["state"] == "cancelled"
        assert list(app.runs_dir.iterdir()) == []
        assert app.uploads.list_files()["source"] == [], "uploads must be removed after the run"
        assert c.json("GET", "/api/runs")[1]["runs"] == []
        assert c.req("POST", "/api/analysis/cancel", body={})[0] == 409
    finally:
        server.shutdown(); server.server_close(); app.shutdown()


def test_failed_analysis_reports_a_plain_message_and_no_partial(tmp_path):
    app = UIApp(runs_dir=tmp_path / "runs")
    c, server, _ = _client_for(app)
    bad = tmp_path / "input.txt"
    bad.write_text("not a recognizable database", encoding="utf-8")
    try:
        status, _ = c.json("POST", "/api/analysis", {"source": {"kind": "path", "path": str(bad)}})
        assert status == 202
        job = c.wait_job()
        assert job["state"] == "failed" and "Traceback" not in job["error"] and job["error"]
        assert list(app.runs_dir.iterdir()) == []
    finally:
        server.shutdown(); server.server_close(); app.shutdown()


def test_input_validation_messages(client):
    cases = [({"source": {"kind": "nope"}}, "source"), ({"source": {"kind": "upload"}}, "source"), ({"source": {"kind": "path", "path": "relative/file.sql"}}, "path"),
             ({"source": {"kind": "path", "path": "http://x/y"}}, "path"),
             ({"source": {"kind": "connection", "connection": {"engine": "mysql", "user": "a", "database": "b", "host": "bad host!"}}}, "host"),
             ({"source": {"kind": "connection", "connection": {"engine": "oracle"}}}, "engine"),
             ({"source": {"kind": "connection", "connection": {"engine": "sqlite", "sqlite_path": "C:\\none\\x.db"}}}, "sqlite_path"),
             ({"source": {"kind": "upload"}, "settings": {"workload": "bad"}}, "workload"),
             ({"source": {"kind": "upload"}, "settings": {"tenant_column": "drop table"}}, "tenant_column")]
    for body, field in cases:
        status, payload = client.json("POST", "/api/analysis", body)
        assert status in (400, 409) and payload.get("field") in (field, "source"), (body, payload)


def test_history_reopen_delete_and_compare(client):
    runs = client.app.runs_dir
    before = "20250101-000000-111111"
    after = "20250102-000000-222222"
    write_synthetic(runs, before, findings_by_id=[{"id": "A-1", "severity": "high", "kind": "confirmed_defect"}, {"id": "A-2", "severity": "low", "kind": "confirmed_defect"}, {"id": "A-3", "severity": "low", "kind": "confirmed_defect"}], overall=60.0)
    write_synthetic(runs, after, findings_by_id=[{"id": "A-2", "severity": "high", "kind": "confirmed_defect"}, {"id": "A-3", "severity": "low", "kind": "confirmed_defect"}, {"id": "A-4", "severity": "critical", "kind": "confirmed_defect"}], overall=70.0)
    status, listing = client.json("GET", "/api/runs")
    assert status == 200 and [r["id"] for r in listing["runs"]] == [after, before]
    assert client.json("GET", f"/api/runs/{before}")[0] == 200  # reopening reads saved files; nothing runs
    status, compared = client.json("GET", f"/api/compare?a={before}&b={after}")
    assert status == 200 and compared["overall_delta"] == 10.0
    assert [f["id"] for f in compared["new"]] == ["A-4"] and [f["id"] for f in compared["resolved"]] == ["A-1"]
    assert compared["new_count"] == 1 and compared["resolved_count"] == 1 and compared["unchanged_count"] == 1
    assert [c["id"] for c in compared["changed"]] == ["A-2"] and compared["category_changes"][0]["delta"] == 10.0
    assert client.req("GET", f"/api/compare?a={before}&b={before}")[0] == 400
    assert client.req("GET", f"/api/compare?a={before}&b=20260101-000000-999999")[0] == 404
    status, deleted = client.json("DELETE", f"/api/runs/{before}")
    assert status == 200 and deleted["deleted"] == before and not (runs / before).exists()
    assert client.req("GET", f"/api/runs/{before}")[0] == 404


def test_partial_directories_are_removed_on_startup(tmp_path):
    runs = tmp_path / "runs"
    (runs / ".partial-20250101-000000-abcdef").mkdir(parents=True)
    app = UIApp(runs_dir=runs)
    try:
        assert not list(runs.glob(".partial-*"))
    finally:
        app.shutdown()


# --- passwords -------------------------------------------------------------

PASSWORD = "S3cret-Passw0rd!"


def _assert_password_absent(root: Path):
    for path in root.rglob("*"):
        if path.is_file():
            assert PASSWORD.encode() not in path.read_bytes(), path


def test_password_reaches_only_the_worker_environment(tmp_path, monkeypatch):
    marker = tmp_path / "marker.json"
    monkeypatch.setenv("DBINTEL_TEST_MARKER", str(marker))
    app = UIApp(runs_dir=tmp_path / "runs", assess_hook="ui_test_hooks:recording_assess")
    c, server, _ = _client_for(app)
    try:
        status, job = c.json("POST", "/api/analysis", {"source": {"kind": "connection", "connection": {"engine": "postgres", "host": "localhost", "database": "app", "user": "admin", "password": PASSWORD}}})
        assert status == 202 and PASSWORD not in json.dumps(job)
        final = c.wait_job()
        assert final["state"] == "done", final
        assert PASSWORD not in json.dumps(final)
        seen = json.loads(marker.read_text(encoding="utf-8"))
        assert PASSWORD not in seen["source"] and seen["password_env"] and seen["env_value"] == PASSWORD
        _assert_password_absent(app.runs_dir)
        assert PASSWORD not in json.dumps(c.json("GET", "/api/runs")[1])
        assert PASSWORD not in json.dumps(c.json("GET", f"/api/runs/{final['run_id']}")[1])
    finally:
        server.shutdown(); server.server_close(); app.shutdown()


def test_password_is_scrubbed_from_error_messages(tmp_path):
    app = UIApp(runs_dir=tmp_path / "runs", assess_hook="ui_test_hooks:failing_assess")
    c, server, _ = _client_for(app)
    try:
        status, _ = c.json("POST", "/api/analysis", {"source": {"kind": "connection", "connection": {"engine": "mysql", "host": "localhost", "database": "app", "user": "admin", "password": PASSWORD}}})
        assert status == 202
        final = c.wait_job()
        assert final["state"] == "failed" and PASSWORD not in final["error"] and "***" in final["error"]
    finally:
        server.shutdown(); server.server_close(); app.shutdown()


def test_form_only_overrides_profile_values_it_was_given(tmp_path):
    from dbintel.ui.worker import build_profile

    profile = tmp_path / "p.yaml"
    profile.write_text("workload: OLAP\ntenancy: pool\nmulti_company: true\ntenant_column: org_id\n", encoding="utf-8")
    kept = build_profile({"workload": None, "tenancy": None, "multi_company": None, "tenant_column": None, "company_column": None}, str(profile))
    assert (kept.workload, kept.tenancy, kept.multi_company, kept.tenant_column) == ("OLAP", "pool", True, "org_id")
    changed = build_profile({"workload": "OLTP", "multi_company": False}, str(profile))
    assert changed.workload == "OLTP" and changed.multi_company is False and changed.tenancy == "pool"


def test_password_never_appears_in_the_job_url_or_label():
    from dbintel.ui.intake import build_job

    class NoUploads:
        @staticmethod
        def slot_files(slot):
            return []

    job = build_job({"source": {"kind": "connection", "connection": {"engine": "postgres", "host": "h", "database": "d", "user": "u@x", "password": PASSWORD}}}, NoUploads())
    assert PASSWORD not in job["source"] and PASSWORD not in job["source_label"] and job["password"] == PASSWORD
    assert job["source"].startswith("postgresql://u%40x@h:5432/d")


# --- no apply and sandbox -----------------------------------------------------

def _source_files():
    return [p for p in PACKAGE.rglob("*.py")] + [p for p in STATIC_DIR.rglob("*.js")]


def test_no_endpoint_applies_anything():
    words = re.compile(r"apply|deploy|execute|commit", re.I)
    for method, pattern, handler in ROUTES:
        assert not words.search(pattern.pattern) and not words.search(handler), pattern.pattern
    assert not re.search(r"""["']/?api[^"']*apply""", "".join(p.read_text(encoding="utf-8") for p in STATIC_DIR.rglob("*.js")), re.I)


def test_ui_package_cannot_reach_a_writable_target():
    text = "".join(p.read_text(encoding="utf-8") for p in PACKAGE.rglob("*.py"))
    assert "scratch_url" not in text and "allow_hosts" not in text
    assert not re.search(r"^\s*(?:import|from)\s+(?:psycopg|pymysql|sqlite3)\b", text, re.M)
    for forbidden in ("open_connector", ".executescript", ".execute(", ".executemany("):
        assert forbidden not in text, forbidden
    assert text.count("test_plan_in_sandbox(") == 1  # the one sandbox call, in the worker, with no scratch target


def test_static_ui_has_no_apply_control():
    for path in STATIC_DIR.rglob("*.js"):
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"Apply (?:migration|plan|to source)|Run on source|Execute plan", text, re.I), path.name
    all_text = "".join(p.read_text(encoding="utf-8") for p in STATIC_DIR.rglob("*.js"))
    assert "no apply function" in all_text


def test_sandbox_requires_exact_plan_hash(erp_run):
    c, run_id = erp_run["client"], erp_run["run_id"]
    status, payload = c.json("POST", f"/api/runs/{run_id}/sandbox", {"plan_hash": "0" * 64})
    assert status == 403 and payload["code"] == "plan_hash_mismatch"
    status, payload = c.json("POST", f"/api/runs/{run_id}/sandbox", {})
    assert status == 403


def test_sandbox_run_reports_honest_statuses_and_leaves_source_unchanged(erp_run):
    c, run_id = erp_run["client"], erp_run["run_id"]
    before = hashlib.sha256(Path(ERP).read_bytes()).hexdigest()
    status, info = c.json("GET", f"/api/runs/{run_id}/sandbox")
    assert status == 200 and info["available"] and info["mode"] == "live" and info["has_sample_rows"] is True
    status, job = c.json("POST", f"/api/runs/{run_id}/sandbox", {"plan_hash": info["plan_hash"]})
    assert status == 202 and job["kind"] == "sandbox"
    assert c.req("POST", f"/api/runs/{run_id}/sandbox", body={"plan_hash": info["plan_hash"]})[0] == 409
    final = c.wait_job(seconds=240)
    assert final["state"] == "done", final
    _, info = c.json("GET", f"/api/runs/{run_id}/sandbox")
    result = info["last_result"]
    assert {r["status"] for r in result["results"]} <= {"passed", "failed", "not_testable"}
    assert result["overall"] in ("passed", "failed", "partial", "not_testable")
    assert result["engine"] == "sqlite-temp-copy" and result["isolated"] is True
    assert hashlib.sha256(Path(ERP).read_bytes()).hexdigest() == before


def test_sandbox_on_saved_run_after_restart_is_schema_only(erp_run, tmp_path):
    runs = erp_run["runs"]
    run_id = erp_run["run_id"]
    app = UIApp(runs_dir=runs)  # a new launch: the in-memory worker is gone
    c, server, _ = _client_for(app)
    try:
        status, info = c.json("GET", f"/api/runs/{run_id}/sandbox")
        assert status == 200 and info["available"] and info["mode"] == "saved" and info["has_sample_rows"] is False
        status, _ = c.json("POST", f"/api/runs/{run_id}/sandbox", {"plan_hash": info["plan_hash"]})
        assert status == 202
        final = c.wait_job(seconds=240)
        assert final["state"] == "done", final
        _, info = c.json("GET", f"/api/runs/{run_id}/sandbox")
        result = info["last_result"]
        assert result["mode"] == "saved" and any("no sample rows" in w for w in result["warnings"])
    finally:
        server.shutdown(); server.server_close(); app.shutdown()


def test_old_run_without_rebuildable_plan_disables_sandbox(client):
    run_id = "20250101-000000-cccccc"
    write_synthetic(client.app.runs_dir, run_id, n=3)
    status, info = client.json("GET", f"/api/runs/{run_id}/sandbox")
    assert status == 200 and info["available"] is False and "plan" in info["reason"].lower()
    status, payload = client.json("POST", f"/api/runs/{run_id}/sandbox", {"plan_hash": info["plan_hash"]})
    assert status == 409 and payload["code"] == "sandbox_unavailable"


def test_rebuild_restores_the_exact_plan_hash(erp_run):
    run_dir = erp_run["runs"] / erp_run["run_id"]
    report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    plan, db = rebuild(run_dir)
    assert plan.dialect == report["migration"]["dialect"] and len(plan.steps) == report["migration"]["total_steps"]
    assert len(db.tables) == len(report["architecture"]["tables"]) and db.data is None


def test_rebuild_refuses_tampered_or_old_reports(erp_run, tmp_path):
    run_dir = erp_run["runs"] / erp_run["run_id"]
    report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    with pytest.raises(RebuildError):
        rebuild_plan(run_dir, "bad-hash")
    old = {**report, "architecture": {**report["architecture"], "tables": [{k: v for k, v in t.items() if k != "index_list"} for t in report["architecture"]["tables"]]}}
    with pytest.raises(RebuildError):
        rebuild_database(old)
    with pytest.raises(RebuildError):
        rebuild_plan(tmp_path)


def test_sqlite_source_file_is_unchanged_by_analysis_and_sandbox(tmp_path):
    db_path = tmp_path / "source.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, total REAL, customer_id INTEGER)")
    conn.execute("INSERT INTO orders VALUES (1, 9.5, 2)")
    conn.commit()
    conn.close()
    before = hashlib.sha256(db_path.read_bytes()).hexdigest()
    app = UIApp(runs_dir=tmp_path / "runs")
    c, server, _ = _client_for(app)
    try:
        status, _ = c.json("POST", "/api/analysis", {"source": {"kind": "connection", "connection": {"engine": "sqlite", "sqlite_path": str(db_path)}}})
        assert status == 202
        job = c.wait_job()
        assert job["state"] == "done", job
        run_id = job["run_id"]
        _, info = c.json("GET", f"/api/runs/{run_id}/sandbox")
        assert info["available"] and info["has_sample_rows"] is False
        status, _ = c.json("POST", f"/api/runs/{run_id}/sandbox", {"plan_hash": info["plan_hash"]})
        assert status == 202
        assert c.wait_job(seconds=120)["state"] == "done"
        assert hashlib.sha256(db_path.read_bytes()).hexdigest() == before
    finally:
        server.shutdown(); server.server_close(); app.shutdown()


# --- hostile content ---------------------------------------------------------

def test_script_tags_in_table_names_and_values_are_returned_as_data(tmp_path):
    dump = tmp_path / "xss.sql"
    dump.write_text("CREATE TABLE `<script>alert(1)</script>` (`id` int NOT NULL PRIMARY KEY, `note` varchar(50) COMMENT '<img src=x onerror=alert(2)>');\n"
                    "INSERT INTO `<script>alert(1)</script>` VALUES (1,'<script>alert(3)</script>');\n", encoding="utf-8")
    app = UIApp(runs_dir=tmp_path / "runs")
    c, server, _ = _client_for(app)
    try:
        status, _ = c.json("POST", "/api/analysis", {"source": {"kind": "path", "path": str(dump)}})
        assert status == 202
        job = c.wait_job()
        assert job["state"] == "done", job
        run_id = job["run_id"]
        status, headers, data = c.req("GET", f"/api/runs/{run_id}/tables?size=50")
        assert status == 200 and headers["content-type"] == "application/json; charset=utf-8" and headers["x-content-type-options"] == "nosniff"
        names = [t["name"] for t in json.loads(data)["items"]]
        assert "<script>alert(1)</script>" in names
        status, _, data = c.req("GET", f"/api/runs/{run_id}/tables/%3Cscript%3Ealert(1)%3C%2Fscript%3E")
        assert status == 200 and json.loads(data)["name"] == "<script>alert(1)</script>"
        status, _, html = c.req("GET", f"/api/runs/{run_id}/export/html")
        assert b"<script>alert(1)" not in html
        for path in ("/", "/static/js/app.js"):
            assert b"alert(1)" not in c.req("GET", path, token=False)[2]
    finally:
        server.shutdown(); server.server_close(); app.shutdown()


# --- launch ------------------------------------------------------------------

def test_cli_parser_exposes_ui_command():
    parsed = cli.build_parser().parse_args(["ui"])
    assert parsed.port == 8765 and parsed.no_open is False and parsed.max_upload_mb == 2048
    parsed = cli.build_parser().parse_args(["ui", "--port", "9000", "--no-open", "--max-upload-mb", "10"])
    assert parsed.port == 9000 and parsed.no_open is True and parsed.max_upload_mb == 10


def test_cmd_ui_calls_run_ui(monkeypatch):
    calls = {}
    import dbintel.ui.server

    monkeypatch.setattr(dbintel.ui.server, "run_ui", lambda **kw: calls.update(kw) or 0)
    assert cli.main(["ui", "--port", "9001", "--no-open"]) == 0
    assert calls == {"port": 9001, "open_browser": False, "max_upload_mb": 2048}


def test_run_ui_opens_browser_with_token_fragment(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    opened = []
    monkeypatch.setattr(server_module.webbrowser, "open", lambda url: opened.append(url))
    monkeypatch.setattr(server_module._Server, "serve_forever", lambda self: None)
    monkeypatch.setattr(server_module.threading, "Timer", lambda delay, fn, args=(): type("T", (), {"start": lambda self: fn(*args)})())
    assert server_module.run_ui(port=0, open_browser=True, max_upload_mb=1) == 0
    assert len(opened) == 1 and re.match(r"http://127\.0\.0\.1:\d+/#token=", opened[0])
    assert (tmp_path / "reports" / "ui_runs").is_dir()


def test_run_ui_reports_port_in_use_clearly(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    app = UIApp(runs_dir=tmp_path / "runs")
    server = make_server(app, 0)
    port = app.port
    try:
        assert server_module.run_ui(port=port, open_browser=False, max_upload_mb=1) == 1
        assert "in use" in capsys.readouterr().err
    finally:
        server.server_close()
        app.shutdown()


@pytest.mark.skipif(sys.platform != "win32", reason="ui.bat is Windows only")
def test_ui_bat_launches_and_serves(tmp_path):
    bat = ROOT / "ui.bat"
    assert bat.is_file()
    text = bat.read_text(encoding="utf-8")
    assert "-m dbintel ui" in text and "%*" in text
    import socket
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    proc = subprocess.Popen(["cmd", "/c", str(bat), "--no-open", "--port", str(port), "--max-upload-mb", "1"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=ROOT)
    try:
        deadline = time.time() + 60
        url = None
        while time.time() < deadline and url is None:
            line = proc.stdout.readline().decode("utf-8", "replace")
            if not line:
                break
            match = re.search(r"http://127\.0\.0\.1:\d+/#token=\S+", line)
            if match:
                url = match.group(0)
        assert url, "ui.bat did not print the launch URL"
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=20)
        conn.request("GET", "/")
        assert conn.getresponse().status == 200
        conn.close()
    finally:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
        proc.stdout.close()
        proc.wait(timeout=30)


def test_package_data_includes_static_assets():
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert '"ui/static/*"' in text and '"ui/static/js/*"' in text and '"ui/static/js/views/*"' in text and '"ui/static/css/*"' in text
    expected = {"index.html", "app.css", "print.css", "app.js", "er.js", "findings.js", "layout.js"}
    assert expected <= {p.name for p in static_files()}
