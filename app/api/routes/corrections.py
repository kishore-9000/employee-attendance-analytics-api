"""
app/api/routes/corrections.py
Manual attendance correction endpoints.
"""
from fastapi import APIRouter, status

from app.schemas.correction import CorrectionRequest, CorrectionResponse, CorrectionEntry
from app.services import correction_service

router = APIRouter(prefix="/attendance", tags=["Corrections"])


@router.post(
    "/{attendance_id}/correct",
    response_model=CorrectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Apply manual correction to attendance record",
)
def correct_attendance(attendance_id: str, payload: CorrectionRequest) -> dict:
    """
    Apply a manual correction to punch_in and/or punch_out.

    - Old and new values are captured in the audit trail.
    - The corrections array is append-only — history is never lost.
    - Returns HTTP 404 if the record is not found.
    - Returns HTTP 422 if no correctable fields are provided.
    """
    return correction_service.apply_correction(attendance_id, payload)


@router.get(
    "/{attendance_id}/corrections",
    response_model=list[CorrectionEntry],
    status_code=status.HTTP_200_OK,
    summary="Get correction audit trail for an attendance record",
)
def get_corrections(attendance_id: str) -> list[dict]:
    """Return the full audit trail (all corrections) for an attendance record."""
    return correction_service.get_corrections(attendance_id)
