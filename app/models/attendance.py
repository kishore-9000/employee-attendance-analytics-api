"""
app/models/attendance.py
Internal MongoDB document representation (not exposed directly in API).
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class CorrectionEntry:
    """A single audit record stored inside the attendance document."""
    corrected_at: datetime
    corrected_by: str
    reason: str
    old_values: dict
    new_values: dict


@dataclass
class AttendanceDocument:
    """
    Maps 1-to-1 with a document in the `attendance` MongoDB collection.
    _id is handled by PyMongo (ObjectId).
    """
    employee_id: str
    date: str                          # ISO date string: YYYY-MM-DD
    punch_in: Optional[datetime]
    punch_out: Optional[datetime]
    status: str                        # "present" | "absent" | "incomplete"
    work_duration_minutes: Optional[int]
    corrections: list[CorrectionEntry] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
