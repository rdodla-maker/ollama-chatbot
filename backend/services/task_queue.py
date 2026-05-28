"""Lightweight background task scaffolding for future automation.

Provides an in-memory queue and placeholder worker functions. Intended as
an architectural placeholder — not a production queue.
"""
from typing import Any, Dict
import threading
import queue
import time
import logging
import asyncio
from services import analysis_service, workflow_execution_service
from services.workflow_runtime import mark_active, set_last_error
from services.worker_registry_service import acquire_lease, heartbeat, register_worker, release_lease, snapshot_registry

logger = logging.getLogger("task_queue")

_task_q: "queue.Queue[Dict[str,Any]]" = queue.Queue()
_worker_thread: threading.Thread | None = None
_worker_lock = threading.Lock()
_stop_event = threading.Event()


def enqueue_task(task: Dict[str, Any]) -> None:
    _task_q.put(task)
    logger.info("Task enqueued: %s", task.get("type"))
    if task.get("workflow_id"):
        try:
            from services.workflow_event_bus import publish_event

            publish_event(
                "workflow.queued",
                workflow_id=task.get("workflow_id"),
                source="workflow-queue",
                event={
                    "workflow_id": task.get("workflow_id"),
                    "upload_id": task.get("upload_id"),
                    "retry_stage": task.get("retry_stage"),
                    "retry_count": task.get("retry_count") or 0,
                },
            )
        except Exception:
            logger.debug("Failed to publish queue event")


def cancel_queued_workflow(workflow_id: str | None, upload_id: str | None) -> bool:
    removed = False
    with _task_q.mutex:
        retained = []
        for item in list(_task_q.queue):
            if (
                item.get("type") == "analyze_resume"
                and (item.get("workflow_id") == workflow_id or item.get("upload_id") == upload_id)
                and not removed
            ):
                removed = True
                continue
            retained.append(item)
        _task_q.queue.clear()
        _task_q.queue.extend(retained)
    return removed


def get_queue_snapshot() -> Dict[str, Any]:
    pending = list(_task_q.queue)
    return {
        "size": len(pending),
        "pending": [
            {
                "type": item.get("type"),
                "workflow_id": item.get("workflow_id"),
                "upload_id": item.get("upload_id"),
                "target_roles": item.get("target_roles") or [],
                "retry_count": item.get("retry_count") or 0,
            }
            for item in pending[:10]
        ],
        "workers": snapshot_registry(),
    }


def _worker_loop():
    worker_id = threading.current_thread().name
    register_worker(worker_id)
    logger.info("Background worker started")
    while not _stop_event.is_set():
        try:
            heartbeat(worker_id, status="idle")
            task = _task_q.get(timeout=0.5)
            logger.info("Processing task: %s", task.get("type"))
            ttype = task.get("type")
            if ttype == "analyze_resume":
                upload_id = task.get("upload_id")
                workflow_id = task.get("workflow_id")
                if not acquire_lease(workflow_id, worker_id):
                    _task_q.put(task)
                    time.sleep(0.05)
                    continue
                heartbeat(worker_id, status="busy", current_task={"workflow_id": workflow_id, "type": ttype})
                mark_active(upload_id, True)
                set_last_error(upload_id, None)
                task["worker_id"] = worker_id
                # run async analysis in event loop
                try:
                    asyncio.run(workflow_execution_service.execute_workflow_task(task))
                except analysis_service.WorkflowCancelledError:
                    logger.info("Workflow cancelled: %s", upload_id)
                except analysis_service.WorkflowPausedError:
                    logger.info("Workflow paused: %s", upload_id)
                except Exception as exc:
                    if workflow_id:
                        workflow_execution_service.record_failure(
                            workflow_id,
                            str(exc),
                            stage=task.get("retry_stage") or "ats_analysis",
                            retry_count=task.get("retry_count") or 0,
                        )
                    set_last_error(upload_id, str(exc))
                    logger.exception("Background analysis task failed")
                finally:
                    mark_active(upload_id, False)
                    release_lease(workflow_id, worker_id)
                    heartbeat(worker_id, status="idle")
            else:
                # Placeholder: sleep to simulate work
                time.sleep(0.1)
                logger.info("Task complete: %s", task.get("type"))
        except queue.Empty:
            continue
        except Exception:
            logger.exception("Worker failed processing task")
    logger.info("Background worker stopped")


def start_worker_in_background():
    global _worker_thread
    with _worker_lock:
        if _worker_thread and _worker_thread.is_alive():
            return
        _stop_event.clear()
        _worker_thread = threading.Thread(target=_worker_loop, daemon=True, name="workflow-task-worker")
        _worker_thread.start()


def stop_worker(timeout: float = 2.0) -> None:
    global _worker_thread
    with _worker_lock:
        if not _worker_thread:
            return
        _stop_event.set()
        _worker_thread.join(timeout=timeout)
        _worker_thread = None
