"""Lightweight in-memory worker registry and lease helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any


_workers: dict[str, dict[str, Any]] = {}
_leases: dict[str, dict[str, Any]] = {}
_lock = Lock()
_LEASE_TTL = timedelta(seconds=30)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def register_worker(worker_id: str, capabilities: list[str] | None = None) -> None:
    with _lock:
        current = _workers.get(worker_id, {})
        _workers[worker_id] = {
            "worker_id": worker_id,
            "capabilities": capabilities or current.get("capabilities") or ["local-in-memory-queue"],
            "status": current.get("status") or "idle",
            "current_task": current.get("current_task"),
            "started_at": current.get("started_at") or _now().isoformat(),
            "last_seen": _now().isoformat(),
        }


def heartbeat(worker_id: str, status: str = "idle", current_task: dict[str, Any] | None = None) -> None:
    register_worker(worker_id)
    with _lock:
        _workers[worker_id]["status"] = status
        _workers[worker_id]["current_task"] = current_task
        _workers[worker_id]["last_seen"] = _now().isoformat()


def acquire_lease(workflow_id: str | None, worker_id: str) -> bool:
    if not workflow_id:
        return True
    now = _now()
    with _lock:
        lease = _leases.get(workflow_id)
        if lease:
            expires_at = datetime.fromisoformat(lease["expires_at"])
            if expires_at > now and lease.get("worker_id") != worker_id:
                return False
        _leases[workflow_id] = {
            "workflow_id": workflow_id,
            "worker_id": worker_id,
            "expires_at": (now + _LEASE_TTL).isoformat(),
        }
        return True


def release_lease(workflow_id: str | None, worker_id: str) -> None:
    if not workflow_id:
        return
    with _lock:
        lease = _leases.get(workflow_id)
        if lease and lease.get("worker_id") == worker_id:
            _leases.pop(workflow_id, None)


def snapshot_registry() -> dict[str, Any]:
    now = _now()
    with _lock:
        active_leases = [
            lease
            for lease in _leases.values()
            if datetime.fromisoformat(lease["expires_at"]) > now
        ]
        workers = list(_workers.values())
    return {
        "workers": workers,
        "leases": active_leases,
        "total_workers": len(workers),
        "active_workers": sum(1 for worker in workers if worker.get("status") == "busy"),
    }