"""Lightweight background task scaffolding for future automation.

Provides an in-memory queue and placeholder worker functions. Intended as
an architectural placeholder — not a production queue.
"""
from typing import Any, Dict
import threading
import queue
import time
import logging

logger = logging.getLogger("task_queue")

_task_q: "queue.Queue[Dict[str,Any]]" = queue.Queue()


def enqueue_task(task: Dict[str, Any]) -> None:
    _task_q.put(task)
    logger.info("Task enqueued: %s", task.get("type"))


def _worker_loop():
    logger.info("Background worker started")
    while True:
        try:
            task = _task_q.get()
            logger.info("Processing task: %s", task.get("type"))
            # Placeholder: sleep to simulate work
            time.sleep(0.1)
            logger.info("Task complete: %s", task.get("type"))
        except Exception:
            logger.exception("Worker failed processing task")


def start_worker_in_background():
    t = threading.Thread(target=_worker_loop, daemon=True)
    t.start()
