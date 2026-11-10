"""Assessment stand-ins that run inside the UI worker process, selected through ``UIApp(assess_hook=...)``."""
import json
import os
import time
from pathlib import Path

from dbintel.connectors.base import ConnectorError
from dbintel.model import Column, Database, Table
from dbintel.pipeline import assess


def _tiny() -> Database:
    return Database(name="tiny", dialect="sqlite", source="sql_dump", tables=[Table(name="a", columns=[Column("id", "integer", nullable=False)], primary_key=["id"])])


def slow_assess(source, **kw):
    progress = kw.get("progress")
    if progress:
        progress("import_and_extract", "start", 0.0)
    time.sleep(120)
    raise AssertionError("cancel should have ended this process")


def recording_assess(source, **kw):
    """Record how the password reached this process, then finish with a tiny database."""
    env_name = kw.get("password_env")
    Path(os.environ["DBINTEL_TEST_MARKER"]).write_text(json.dumps({"source": os.fspath(source), "password_env": env_name, "env_value": os.environ.get(env_name or "", "")}), encoding="utf-8")
    return assess(_tiny(), profile=kw.get("profile"), progress=kw.get("progress"))


def failing_assess(source, **kw):
    password = os.environ.get(kw.get("password_env") or "", "")
    raise ConnectorError(f"could not connect with password {password} to {source}")
