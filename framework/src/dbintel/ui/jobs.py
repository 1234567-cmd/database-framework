"""One analysis or sandbox test at a time, each in a child process. Results become visible only when fully written."""
from __future__ import annotations

import datetime as dt
import hmac
import multiprocessing
import os
import shutil
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from ..pipeline import ASSESSMENT_STAGES
from .intake import Uploads
from .rebuild import RebuildError, rebuild
from .store import RunStore, StoreError
from .worker import worker_main

STAGE_LABELS = {"import_and_extract": "Reading the source", "analyze_inputs": "Reading query logs and manifests", "run_rules": "Running the rule checks",
                "classify_and_score": "Scoring health", "explain_root_causes": "Grouping root causes", "generate_proposed_sql": "Writing proposed SQL",
                "recommend_before_and_after": "Building recommendations", "lineage_and_limitations": "Tracing lineage", "write_reports": "Saving the reports"}
ALL_STAGES = tuple(ASSESSMENT_STAGES) + ("write_reports",)
SANDBOX_STAGE = ("sandbox", "Testing the plan in a temporary copy")
ACTIVE_STATES = ("starting", "running", "cancelling")


class JobBusy(Exception):
    """Another analysis or test is still running."""


class JobNotRunning(Exception):
    """There is nothing to cancel."""


class SandboxUnavailable(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


class ApprovalMismatch(Exception):
    """The typed plan hash does not match this exact plan."""


@dataclass
class Job:
    id: str
    kind: str  # analysis | sandbox
    state: str = "starting"  # starting | running | cancelling | done | failed | cancelled
    run_id: Optional[str] = None
    label: str = ""
    error: Optional[str] = None
    started: float = field(default_factory=time.monotonic)
    started_at: str = field(default_factory=lambda: dt.datetime.now().isoformat(timespec="seconds"))
    finished: Optional[float] = None
    stages: dict[str, dict[str, Any]] = field(default_factory=dict)
    process: Any = None
    cancel_requested: bool = False

    @property
    def active(self) -> bool:
        return self.state in ACTIVE_STATES

    def snapshot(self) -> dict[str, Any]:
        end = self.finished if self.finished is not None else time.monotonic()
        return {"id": self.id, "kind": self.kind, "state": self.state, "run_id": self.run_id, "label": self.label, "error": self.error,
                "started_at": self.started_at, "elapsed": round(end - self.started, 1), "stages": [dict(key=k, **v) for k, v in self.stages.items()]}


@dataclass
class _Worker:
    process: Any
    conn: Any
    run_id: str
    has_rows: bool
    lock: threading.Lock = field(default_factory=threading.Lock)


def _kill(process: Any) -> None:
    try:
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)
            if process.is_alive():
                process.kill()
                process.join(timeout=5)
    except (ValueError, OSError):
        pass


def _remove_dir(path: Path) -> None:
    for _ in range(40):
        shutil.rmtree(path, ignore_errors=True)
        if not path.exists():
            return
        time.sleep(0.25)


class JobManager:
    def __init__(self, store: RunStore, uploads: Uploads, assess_hook: Optional[str] = None, idle_seconds: Optional[float] = None):
        self.store = store
        self.uploads = uploads
        self.assess_hook = assess_hook
        self.idle_seconds = idle_seconds
        self._lock = threading.Lock()
        self._ctx = multiprocessing.get_context("spawn")
        self._job: Optional[Job] = None
        self._worker: Optional[_Worker] = None
        self._sandbox_results: dict[str, dict[str, Any]] = {}
        self._rebuild_cache: dict[str, tuple[bool, str]] = {}

    def current(self) -> dict[str, Any]:
        with self._lock:
            return self._job.snapshot() if self._job else {"state": "idle"}

    def busy(self) -> bool:
        with self._lock:
            return bool(self._job and self._job.active)

    def _next_job_id(self) -> str:
        return hex(time.monotonic_ns())[2:]

    # --- analysis -------------------------------------------------------

    def start_analysis(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            if self._job and self._job.active:
                raise JobBusy()
            old_worker, self._worker = self._worker, None
            run_id = self.store.new_run_id()
            job = Job(id=self._next_job_id(), kind="analysis", run_id=run_id, label=payload.get("source_label", ""),
                      stages={k: {"label": STAGE_LABELS[k], "state": "pending", "seconds": None} for k in ALL_STAGES})
            self._job = job
        if old_worker is not None:
            _kill(old_worker.process)
        payload = dict(payload, run_id=run_id, partial_dir=str(self.store.partial_dir(run_id)), assess_hook=self.assess_hook,
                       idle_seconds=self.idle_seconds)
        threading.Thread(target=self._monitor_analysis, args=(job, payload), daemon=True).start()
        return job.snapshot()

    def _spawn(self, payload: dict[str, Any]) -> tuple[Any, Any]:
        parent, child = self._ctx.Pipe()
        process = self._ctx.Process(target=worker_main, args=(child,), daemon=True)
        process.start()
        child.close()
        parent.send(payload)
        return process, parent

    def _monitor_analysis(self, job: Job, payload: dict[str, Any]) -> None:
        process = conn = None
        partial = self.store.partial_dir(job.run_id)
        final_state, error = "failed", "The analysis process stopped unexpectedly."
        has_rows = False
        try:
            try:
                process, conn = self._spawn(payload)
            except Exception:
                error = "The analysis process could not be started."
                return
            finally:
                payload.pop("password", None)
            with self._lock:
                job.process = process
                if job.state == "starting":
                    job.state = "running"
                if job.cancel_requested:
                    _kill(process)
            while True:
                try:
                    if not conn.poll(0.25):
                        if not process.is_alive() and not conn.poll(0):
                            break
                        continue
                    message = conn.recv()
                except (EOFError, OSError):
                    break
                kind = message[0]
                if kind == "progress":
                    _, stage, state, seconds = message
                    with self._lock:
                        entry = job.stages.get(stage)
                        if entry is not None:
                            entry["state"] = "running" if state == "start" else "done"
                            entry["seconds"] = seconds if state == "done" else None
                elif kind == "done":
                    has_rows = bool(message[1].get("has_rows"))
                    final_state, error = "done", None
                    break
                elif kind == "failed":
                    final_state, error = "failed", str(message[1])
                    break
        finally:
            self._finish_analysis(job, process, conn, partial, final_state, error, has_rows)

    def _finish_analysis(self, job: Job, process: Any, conn: Any, partial: Path, final_state: str, error: Optional[str], has_rows: bool) -> None:
        keep_worker = False
        with self._lock:
            cancelled = job.cancel_requested
        if cancelled:
            final_state, error = "cancelled", None
        if final_state == "done":
            target = self.store.root / job.run_id
            try:
                os.replace(partial, target)
                keep_worker = True
            except OSError:
                final_state, error = "failed", "The finished reports could not be saved."
        if not keep_worker:
            if process is not None:
                _kill(process)
            if conn is not None:
                try:
                    conn.close()
                except OSError:
                    pass
            _remove_dir(partial)
        self.uploads.clear_all()
        with self._lock:
            job.state = final_state
            job.error = error
            job.finished = time.monotonic()
            job.process = None
            if keep_worker:
                self._worker = _Worker(process=process, conn=conn, run_id=job.run_id, has_rows=has_rows)

    # --- cancel ---------------------------------------------------------

    def cancel(self) -> dict[str, Any]:
        with self._lock:
            job = self._job
            if job is None or not job.active:
                raise JobNotRunning()
            job.cancel_requested = True
            job.state = "cancelling"
            process = job.process
            worker_conn = None
            if job.kind == "sandbox" and self._worker is not None and self._worker.process is process:
                worker_conn, self._worker = self._worker, None
        if process is not None:
            threading.Thread(target=_kill, args=(process,), daemon=True).start()
        if worker_conn is not None:
            try:
                worker_conn.conn.close()
            except OSError:
                pass
        return self.current()

    # --- sandbox --------------------------------------------------------

    def _rebuild_check(self, run_id: str, run_dir: Path) -> tuple[bool, str]:
        cached = self._rebuild_cache.get(run_id)
        if cached is not None:
            return cached
        try:
            rebuild(run_dir)
            result = (True, "")
        except RebuildError as exc:
            result = (False, str(exc))
        except Exception as exc:
            result = (False, f"The saved plan could not be rebuilt ({type(exc).__name__}).")
        self._rebuild_cache[run_id] = result
        return result

    def sandbox_status(self, run_id: str, plan_hash: Optional[str], run_dir: Path) -> dict[str, Any]:
        with self._lock:
            worker = self._worker if self._worker and self._worker.run_id == run_id and self._worker.process.is_alive() else None
            job = self._job
            busy = bool(job and job.active)
            last = self._sandbox_results.get(run_id)
            running_here = bool(job and job.active and job.kind == "sandbox" and job.run_id == run_id)
        status: dict[str, Any] = {"plan_hash": plan_hash, "busy": busy, "running_here": running_here, "last_result": last, "engine": "sqlite-temp-copy"}
        if worker is not None:
            status.update(available=True, mode="live",
                          has_sample_rows=worker.has_rows,
                          note=("Uses sample rows held in memory from this run." if worker.has_rows else
                                "A live source was closed after reading, so the copy has its schema but no sample rows."))
            return status
        ok, reason = self._rebuild_check(run_id, run_dir)
        if ok:
            status.update(available=True, mode="saved", has_sample_rows=False,
                          note="This saved run is tested from its stored schema only. No row data is stored, so paths that depend on data are not tested.")
        else:
            status.update(available=False, mode=None, has_sample_rows=False, reason=reason)
        return status

    def start_sandbox(self, run_id: str, token: str, plan_hash: Optional[str], run_dir: Path) -> dict[str, Any]:
        if not plan_hash or not isinstance(token, str) or not hmac.compare_digest(token, plan_hash):
            raise ApprovalMismatch()
        with self._lock:
            if self._job and self._job.active:
                raise JobBusy()
            worker = self._worker if self._worker and self._worker.run_id == run_id and self._worker.process.is_alive() else None
            job = Job(id=self._next_job_id(), kind="sandbox", run_id=run_id, label="Sandbox test",
                      stages={SANDBOX_STAGE[0]: {"label": SANDBOX_STAGE[1], "state": "running", "seconds": None}})
            self._job = job
        if worker is None:
            ok, reason = self._rebuild_check(run_id, run_dir)
            if not ok:
                with self._lock:
                    self._job = None
                raise SandboxUnavailable(reason)
        threading.Thread(target=self._monitor_sandbox, args=(job, worker, token, run_dir), daemon=True).start()
        return job.snapshot()

    def _monitor_sandbox(self, job: Job, worker: Optional[_Worker], token: str, run_dir: Path) -> None:
        final_state, error = "failed", "The sandbox test stopped unexpectedly."
        result: Optional[dict[str, Any]] = None
        process = None
        conn = None
        spawned = False
        mode = "live" if worker is not None else "saved"
        try:
            if worker is not None:
                process, conn = worker.process, worker.conn
                with worker.lock:
                    try:
                        conn.send(("sandbox", token))
                    except (OSError, BrokenPipeError):
                        return
            else:
                try:
                    process, conn = self._spawn({"type": "sandbox_saved", "run_dir": str(run_dir), "token": token})
                    spawned = True
                except Exception:
                    error = "The sandbox process could not be started."
                    return
            with self._lock:
                job.process = process
                job.state = "running"
                if job.cancel_requested:
                    _kill(process)
            while True:
                try:
                    if not conn.poll(0.25):
                        if not process.is_alive() and not conn.poll(0):
                            break
                        continue
                    message = conn.recv()
                except (EOFError, OSError):
                    break
                kind = message[0]
                if kind == "sandbox_result":
                    final_state, error, result = "done", None, message[1]
                    break
                if kind == "sandbox_refused":
                    final_state, error = "failed", f"The sandbox refused to run: {message[1]}"
                    break
                if kind == "sandbox_failed":
                    final_state, error = "failed", str(message[1])
                    break
        finally:
            with self._lock:
                cancelled = job.cancel_requested
                if cancelled:
                    final_state, error, result = "cancelled", None, None
                job.state = final_state
                job.error = error
                job.finished = time.monotonic()
                job.process = None
                entry = job.stages.get(SANDBOX_STAGE[0])
                if entry is not None:
                    entry["state"] = "done" if final_state == "done" else final_state
                    entry["seconds"] = round(job.finished - job.started, 1)
                if result is not None:
                    self._sandbox_results[job.run_id] = {**result, "mode": mode, "finished_at": dt.datetime.now().isoformat(timespec="seconds")}
            if spawned and process is not None:
                _kill(process)

    # --- run bookkeeping ------------------------------------------------

    def forget_run(self, run_id: str) -> None:
        with self._lock:
            self._sandbox_results.pop(run_id, None)
            self._rebuild_cache.pop(run_id, None)
            if self._worker is not None and self._worker.run_id == run_id:
                worker, self._worker = self._worker, None
                _kill(worker.process)

    def ensure_deletable(self, run_id: str) -> None:
        with self._lock:
            if self._job and self._job.active and self._job.run_id == run_id:
                raise JobBusy()

    def shutdown(self) -> None:
        with self._lock:
            job, self._job = self._job, None
            worker, self._worker = self._worker, None
        if job is not None and job.process is not None:
            _kill(job.process)
        if worker is not None:
            _kill(worker.process)
        self.uploads.remove_root()
        for child in self.store.root.iterdir():
            if child.name.startswith(".partial-"):
                _remove_dir(child)


__all__ = ["ApprovalMismatch", "JobBusy", "JobManager", "JobNotRunning", "SandboxUnavailable", "StoreError"]
