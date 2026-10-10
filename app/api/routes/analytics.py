"""
app/api/routes/analytics.py
Analytics endpoints backed by MongoDB aggregation pipelines.
"""
from typing import Optional

from fastapi import APIRouter, Query, status

from app.schemas.analytics import (
    AttendanceSummaryResponse,
    EmployeeSummaryResponse,
    OverallSummaryResponse,
)
from app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "/daily",
    response_model=AttendanceSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Daily attendance summary",
)
def daily_summary(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
) -> dict:
    """
    Return per-day attendance counts (present / absent / incomplete) for the
    specified date range. Uses a MongoDB $group aggregation pipeline.
    """
    _validate_date_range(start_date, end_date)
    daily = analytics_service.get_daily_summary(start_date, end_date)
    return {
        "start_date": start_date,
        "end_date": end_date,
        "daily": daily,
    }


@router.get(
    "/employees",
    response_model=EmployeeSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Per-employee attendance summary",
)
def employee_summary(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
) -> dict:
    """
    Return per-employee attendance metrics over a date range, including total
    work minutes and average work minutes on days marked present.
    """
    _validate_date_range(start_date, end_date)
    employees = analytics_service.get_employee_summary(start_date, end_date)
    return {
        "start_date": start_date,
        "end_date": end_date,
        "employees": employees,
    }


@router.get(
    "/summary",
    response_model=OverallSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Overall attendance summary",
)
def overall_summary(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
) -> dict:
    """
    Return overall attendance counts and total work minutes.
    If no date range is provided, aggregates all records.
    """
    if start_date or end_date:
        _validate_date_range(start_date or "", end_date or "")
    return analytics_service.get_overall_summary(start_date, end_date)


# ──────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────

def _validate_date_range(start_date: str, end_date: str) -> None:
    from fastapi import HTTPException
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_date must not be after end_date.",
        )
