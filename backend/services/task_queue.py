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
from services import analysis_service
from services.workflow_runtime import mark_active, set_last_error

logger = logging.getLogger("task_queue")

_task_q: "queue.Queue[Dict[str,Any]]" = queue.Queue()


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
    }


def _worker_loop():
    logger.info("Background worker started")
    while True:
        try:
            task = _task_q.get()
            logger.info("Processing task: %s", task.get("type"))
            ttype = task.get("type")
            if ttype == "analyze_resume":
                upload_id = task.get("upload_id")
                workflow_id = task.get("workflow_id")
                mark_active(upload_id, True)
                set_last_error(upload_id, None)
                # run async analysis in event loop
                try:
                    asyncio.run(
                        analysis_service.analyze_and_persist(
                            upload_id,
                            None,
                            task.get("target_roles") or [],
                            start_stage=task.get("retry_stage") or "processing",
                        )
                    )
                except analysis_service.WorkflowCancelledError:
                    logger.info("Workflow cancelled: %s", upload_id)
                except Exception as exc:
                    if workflow_id:
                        from services.workflow_orchestration_service import record_failure

                        record_failure(workflow_id, str(exc), stage=task.get("retry_stage") or "ats_analysis")
                    set_last_error(upload_id, str(exc))
                    logger.exception("Background analysis task failed")
                finally:
                    mark_active(upload_id, False)
            else:
                # Placeholder: sleep to simulate work
                time.sleep(0.1)
                logger.info("Task complete: %s", task.get("type"))
        except Exception:
            logger.exception("Worker failed processing task")


def start_worker_in_background():
    t = threading.Thread(target=_worker_loop, daemon=True)
    t.start()
