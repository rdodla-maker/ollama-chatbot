"""Routes for pending file edit approvals."""

from fastapi import APIRouter, HTTPException

from core.logging_config import get_logger
from models.schemas import PendingChangeDetail, PendingChangeSummary
from services import pending_changes

logger = get_logger("api")

router = APIRouter(prefix="/pending-changes", tags=["pending-changes"])


@router.get("", response_model=list[PendingChangeSummary])
async def list_pending_changes():
    return pending_changes.list_pending()


@router.get("/{change_id}", response_model=PendingChangeDetail)
async def get_pending_change(change_id: str):
    change = pending_changes.get_change(change_id)
    if not change:
        raise HTTPException(status_code=404, detail="Change not found.")
    return PendingChangeDetail(
        id=change.id,
        file_path=change.file_path,
        status=change.status.value,
        created_at=change.created_at,
        new_content=change.new_content,
        original_preview=change.original_preview,
    )


@router.post("/{change_id}/approve")
async def approve_change(change_id: str):
    try:
        result = pending_changes.approve_change(change_id)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Approve failed")
        raise HTTPException(status_code=500, detail="Failed to apply change.") from exc


@router.post("/{change_id}/reject")
async def reject_change(change_id: str):
    try:
        return pending_changes.reject_change(change_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
