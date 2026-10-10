"""
app/api/routes/attendance.py
Attendance endpoints: punch-in, punch-out, retrieval.
Route handlers are thin — all logic is in the service layer.
"""
from typing import Optional

from fastapi import APIRouter, Query, status

from app.schemas.attendance import (
    AttendanceResponse,
    PunchInRequest,
    PunchInResponse,
    PunchOutRequest,
    PunchOutResponse,
)
from app.services import attendance_service

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.post(
    "/punch-in",
    response_model=PunchInResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record employee punch-in",
)
def punch_in(payload: PunchInRequest) -> dict:
    """
    Record a punch-in event for an employee.

    - One punch-in per employee per UTC calendar day.
    - Returns HTTP 409 if a record already exists for that day.
    """
    return attendance_service.punch_in(payload)


@router.post(
    "/{attendance_id}/punch-out",
    response_model=PunchOutResponse,
    status_code=status.HTTP_200_OK,
    summary="Record employee punch-out",
)
def punch_out(attendance_id: str, payload: PunchOutRequest) -> dict:
    """
    Record a punch-out for an existing attendance record.

    - Returns HTTP 404 if the record is not found.
    - Returns HTTP 409 if punch-out is already set.
    - Returns HTTP 422 if punch_out ≤ punch_in.
    """
    return attendance_service.punch_out(attendance_id, payload)


@router.get(
    "/{attendance_id}",
    response_model=AttendanceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get attendance record by ID",
)
def get_attendance(attendance_id: str) -> dict:
    """Return a single attendance record including its full correction history."""
    return attendance_service.get_attendance_by_id(attendance_id)


@router.get(
    "/employee/{employee_id}",
    response_model=list[AttendanceResponse],
    status_code=status.HTTP_200_OK,
    summary="List attendance records for an employee",
)
def get_employee_attendance(
    employee_id: str,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Maximum records to return"),
) -> list[dict]:
    """Return attendance history for a given employee, newest first."""
    return attendance_service.get_attendance_by_employee(
        employee_id, skip=skip, limit=limit
    )
