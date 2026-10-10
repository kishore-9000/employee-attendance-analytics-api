"""
app/schemas/attendance.py
Pydantic v2 schemas for attendance request/response validation.
"""
from datetime import datetime
from typing import Annotated, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ──────────────────────────────────────────────
# Shared / helpers
# ──────────────────────────────────────────────

class PyObjectId(str):
    """Serialise MongoDB ObjectId as plain string in JSON responses."""
    pass


# ──────────────────────────────────────────────
# Punch-in
# ──────────────────────────────────────────────

class PunchInRequest(BaseModel):
    employee_id: str = Field(..., min_length=1, description="Unique employee identifier")
    punch_in: datetime = Field(..., description="UTC punch-in timestamp")

    @field_validator("employee_id")
    @classmethod
    def employee_id_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("employee_id must not be blank")
        return v.strip()


class PunchInResponse(BaseModel):
    id: str = Field(..., alias="_id")
    employee_id: str
    date: str
    punch_in: datetime
    punch_out: Optional[datetime] = None
    status: str
    work_duration_minutes: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"populate_by_name": True}


# ──────────────────────────────────────────────
# Punch-out
# ──────────────────────────────────────────────

class PunchOutRequest(BaseModel):
    punch_out: datetime = Field(..., description="UTC punch-out timestamp")

    @model_validator(mode="after")
    def punch_out_must_be_set(self) -> "PunchOutRequest":
        if self.punch_out is None:
            raise ValueError("punch_out is required")
        return self


class PunchOutResponse(PunchInResponse):
    pass


# ──────────────────────────────────────────────
# Attendance record (retrieval)
# ──────────────────────────────────────────────

class AttendanceResponse(PunchInResponse):
    corrections: list[dict] = Field(default_factory=list)
