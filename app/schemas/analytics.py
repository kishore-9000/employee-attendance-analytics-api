"""
app/schemas/analytics.py
Pydantic v2 schemas for analytics response payloads.
"""
from pydantic import BaseModel, Field
from typing import Optional


class DailySummary(BaseModel):
    date: str
    total_employees: int
    present: int
    absent: int
    incomplete: int


class EmployeeSummary(BaseModel):
    employee_id: str
    total_days: int
    present_days: int
    absent_days: int
    incomplete_days: int
    total_work_minutes: int
    average_work_minutes: Optional[float] = None


class AttendanceSummaryResponse(BaseModel):
    start_date: str
    end_date: str
    daily: list[DailySummary] = Field(default_factory=list)


class EmployeeSummaryResponse(BaseModel):
    start_date: str
    end_date: str
    employees: list[EmployeeSummary] = Field(default_factory=list)


class OverallSummaryResponse(BaseModel):
    total_records: int
    total_present: int
    total_absent: int
    total_incomplete: int
    total_work_minutes: int
