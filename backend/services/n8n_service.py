"""Placeholder integration layer for future n8n workflows."""

import httpx

from core.config import settings


async def trigger_job_workflow(payload: dict) -> dict[str, str | bool]:
    if not settings.n8n_webhook_url:
        return {"triggered": False, "message": "n8n webhook is not configured."}

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(settings.n8n_webhook_url, json=payload)
        response.raise_for_status()
    return {"triggered": True, "message": "n8n workflow triggered."}