"""
app/schemas/correction.py
Pydantic v2 schemas for manual attendance correction endpoints.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class CorrectionRequest(BaseModel):
    punch_in: Optional[datetime] = Field(None, description="Corrected punch-in (UTC)")
    punch_out: Optional[datetime] = Field(None, description="Corrected punch-out (UTC)")
    reason: str = Field(..., min_length=1, description="Mandatory reason for correction")
    corrected_by: str = Field(..., min_length=1, description="Who performed the correction")

    @field_validator("reason", "corrected_by")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field must not be blank")
        return v.strip()

    @field_validator("punch_in", "punch_out", mode="before")
    @classmethod
    def allow_none(cls, v):
        return v  # None is valid — only provided fields are updated


class CorrectionEntry(BaseModel):
    corrected_at: datetime
    corrected_by: str
    reason: str
    old_values: dict
    new_values: dict


class CorrectionResponse(BaseModel):
    id: str = Field(..., alias="_id")
    employee_id: str
    date: str
    punch_in: Optional[datetime] = None
    punch_out: Optional[datetime] = None
    status: str
    work_duration_minutes: Optional[int] = None
    corrections: list[CorrectionEntry] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"populate_by_name": True}
