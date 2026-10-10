"""
app/services/correction_service.py
Business logic for manual attendance corrections with full audit trail.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status

from app.repositories import attendance_repository as repo
from app.schemas.correction import CorrectionRequest

logger = logging.getLogger(__name__)


def _compute_duration(
    punch_in: Optional[datetime], punch_out: Optional[datetime]
) -> Optional[int]:
    if punch_in and punch_out:
        delta = punch_out - punch_in
        return max(0, int(delta.total_seconds() // 60))
    return None


def _compute_status(punch_in: Optional[datetime], punch_out: Optional[datetime]) -> str:
    if punch_in and punch_out:
        return "present"
    if punch_in and not punch_out:
        return "incomplete"
    return "absent"


def apply_correction(attendance_id: str, payload: CorrectionRequest) -> dict:
    """
    Apply a manual correction to an attendance record.

    Rules:
      - Record must exist.
      - At least one of punch_in or punch_out must be provided.
      - If both are provided, punch_out must be after punch_in.
      - Old and new values are captured in the audit entry.
      - The corrections array is appended (never replaced).
    """
    record = repo.find_by_id(attendance_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attendance record '{attendance_id}' not found.",
        )

    if payload.punch_in is None and payload.punch_out is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one of 'punch_in' or 'punch_out' must be provided.",
        )

    # Determine new values (fall back to existing if not provided)
    new_punch_in: Optional[datetime] = payload.punch_in or record.get("punch_in")
    new_punch_out: Optional[datetime] = payload.punch_out or record.get("punch_out")

    # Normalise existing datetimes (stored as datetime objects by PyMongo)
    if isinstance(new_punch_in, str):
        new_punch_in = datetime.fromisoformat(new_punch_in)
    if isinstance(new_punch_out, str):
        new_punch_out = datetime.fromisoformat(new_punch_out)

    # Validate chronological order when both timestamps are present
    if new_punch_in and new_punch_out and new_punch_out <= new_punch_in:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="punch_out must be after punch_in.",
        )

    # Build the old-values snapshot (only fields being changed)
    old_values: dict = {}
    new_values: dict = {}

    if payload.punch_in is not None:
        old_values["punch_in"] = record.get("punch_in")
        new_values["punch_in"] = payload.punch_in
    if payload.punch_out is not None:
        old_values["punch_out"] = record.get("punch_out")
        new_values["punch_out"] = payload.punch_out

    if not new_values:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No correctable fields were changed.",
        )

    # Recompute derived fields
    new_status = _compute_status(new_punch_in, new_punch_out)
    new_duration = _compute_duration(new_punch_in, new_punch_out)

    correction_entry = {
        "corrected_at": datetime.now(tz=timezone.utc),
        "corrected_by": payload.corrected_by,
        "reason": payload.reason,
        "old_values": old_values,
        "new_values": new_values,
    }

    set_fields: dict = {
        "punch_in": new_punch_in,
        "punch_out": new_punch_out,
        "status": new_status,
        "work_duration_minutes": new_duration,
    }

    updated = repo.push_correction(attendance_id, correction_entry, set_fields)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to apply correction.",
        )

    logger.info(
        "Correction applied: id=%s by=%s reason='%s'",
        attendance_id,
        payload.corrected_by,
        payload.reason,
    )
    return updated


def get_corrections(attendance_id: str) -> list[dict]:
    """Return the audit trail (corrections list) for a given attendance record."""
    record = repo.find_by_id(attendance_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attendance record '{attendance_id}' not found.",
        )
    return record.get("corrections", [])
