"""
app/services/attendance_service.py
Business logic for punch-in / punch-out / retrieval.
All database access is delegated to the repository.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status

from app.repositories import attendance_repository as repo
from app.schemas.attendance import PunchInRequest, PunchOutRequest

logger = logging.getLogger(__name__)


def _compute_status(punch_in: Optional[datetime], punch_out: Optional[datetime]) -> str:
    if punch_in and punch_out:
        return "present"
    if punch_in and not punch_out:
        return "incomplete"
    return "absent"


def _compute_duration(
    punch_in: Optional[datetime], punch_out: Optional[datetime]
) -> Optional[int]:
    if punch_in and punch_out:
        delta = punch_out - punch_in
        return max(0, int(delta.total_seconds() // 60))
    return None


def punch_in(payload: PunchInRequest) -> dict:
    """
    Record a punch-in for an employee.
    Business rules:
      - One punch-in per employee per calendar day (UTC date of punch_in).
      - Duplicate same-day punch-in is rejected with HTTP 409.
    """
    date_str = payload.punch_in.strftime("%Y-%m-%d")

    existing = repo.find_by_employee_and_date(payload.employee_id, date_str)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Employee '{payload.employee_id}' already has an attendance record for {date_str}.",
        )

    now = datetime.now(tz=timezone.utc)
    document = {
        "employee_id": payload.employee_id,
        "date": date_str,
        "punch_in": payload.punch_in,
        "punch_out": None,
        "status": "incomplete",
        "work_duration_minutes": None,
        "corrections": [],
        "created_at": now,
        "updated_at": now,
    }
    created = repo.create_attendance(document)
    logger.info("Punch-in recorded: employee=%s date=%s", payload.employee_id, date_str)
    return created


def punch_out(attendance_id: str, payload: PunchOutRequest) -> dict:
    """
    Record a punch-out for an existing attendance record.
    Business rules:
      - Record must exist.
      - Punch-out must not already be set (no double punch-out).
      - Punch-out timestamp must be after punch-in timestamp.
    """
    record = repo.find_by_id(attendance_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attendance record '{attendance_id}' not found.",
        )

    if record.get("punch_out") is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Punch-out already recorded for this attendance record.",
        )

    punch_in_dt: datetime = record["punch_in"]
    if isinstance(punch_in_dt, str):
        punch_in_dt = datetime.fromisoformat(punch_in_dt)

    if payload.punch_out <= punch_in_dt:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="punch_out must be after punch_in.",
        )

    duration = _compute_duration(punch_in_dt, payload.punch_out)
    updated = repo.update_attendance(
        attendance_id,
        {
            "punch_out": payload.punch_out,
            "status": "present",
            "work_duration_minutes": duration,
        },
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update attendance record.",
        )
    logger.info("Punch-out recorded: id=%s duration=%s min", attendance_id, duration)
    return updated


def get_attendance_by_id(attendance_id: str) -> dict:
    record = repo.find_by_id(attendance_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attendance record '{attendance_id}' not found.",
        )
    return record


def get_attendance_by_employee(
    employee_id: str, skip: int = 0, limit: int = 50
) -> list[dict]:
    return repo.find_by_employee(employee_id, skip=skip, limit=limit)
