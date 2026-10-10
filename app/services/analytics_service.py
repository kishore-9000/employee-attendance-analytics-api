"""
app/services/analytics_service.py
Analytics using MongoDB aggregation pipelines.
All heavy computation is done in MongoDB, not in Python.
"""
import logging
from typing import Optional

from app.repositories import attendance_repository as repo

logger = logging.getLogger(__name__)


def get_daily_summary(start_date: str, end_date: str) -> list[dict]:
    """
    Aggregate attendance counts per day between start_date and end_date (inclusive).
    Returns list of: {date, total_employees, present, absent, incomplete}
    """
    pipeline = [
        {"$match": {"date": {"$gte": start_date, "$lte": end_date}}},
        {
            "$group": {
                "_id": "$date",
                "total_employees": {"$sum": 1},
                "present": {
                    "$sum": {"$cond": [{"$eq": ["$status", "present"]}, 1, 0]}
                },
                "absent": {
                    "$sum": {"$cond": [{"$eq": ["$status", "absent"]}, 1, 0]}
                },
                "incomplete": {
                    "$sum": {"$cond": [{"$eq": ["$status", "incomplete"]}, 1, 0]}
                },
            }
        },
        {"$sort": {"_id": 1}},
        {
            "$project": {
                "_id": 0,
                "date": "$_id",
                "total_employees": 1,
                "present": 1,
                "absent": 1,
                "incomplete": 1,
            }
        },
    ]
    return repo.aggregate(pipeline)


def get_employee_summary(start_date: str, end_date: str) -> list[dict]:
    """
    Per-employee attendance summary over a date range.
    Returns: {employee_id, total_days, present_days, absent_days,
              incomplete_days, total_work_minutes, average_work_minutes}
    """
    pipeline = [
        {"$match": {"date": {"$gte": start_date, "$lte": end_date}}},
        {
            "$group": {
                "_id": "$employee_id",
                "total_days": {"$sum": 1},
                "present_days": {
                    "$sum": {"$cond": [{"$eq": ["$status", "present"]}, 1, 0]}
                },
                "absent_days": {
                    "$sum": {"$cond": [{"$eq": ["$status", "absent"]}, 1, 0]}
                },
                "incomplete_days": {
                    "$sum": {"$cond": [{"$eq": ["$status", "incomplete"]}, 1, 0]}
                },
                "total_work_minutes": {
                    "$sum": {"$ifNull": ["$work_duration_minutes", 0]}
                },
            }
        },
        {"$sort": {"_id": 1}},
        {
            "$project": {
                "_id": 0,
                "employee_id": "$_id",
                "total_days": 1,
                "present_days": 1,
                "absent_days": 1,
                "incomplete_days": 1,
                "total_work_minutes": 1,
                "average_work_minutes": {
                    "$cond": [
                        {"$gt": ["$present_days", 0]},
                        {"$divide": ["$total_work_minutes", "$present_days"]},
                        None,
                    ]
                },
            }
        },
    ]
    return repo.aggregate(pipeline)


def get_overall_summary(start_date: Optional[str], end_date: Optional[str]) -> dict:
    """
    Overall attendance counts and total work minutes.
    If no date range is supplied, aggregates all records.
    """
    match_stage: dict = {}
    if start_date and end_date:
        match_stage = {"date": {"$gte": start_date, "$lte": end_date}}

    pipeline = [
        *(([{"$match": match_stage}]) if match_stage else []),
        {
            "$group": {
                "_id": None,
                "total_records": {"$sum": 1},
                "total_present": {
                    "$sum": {"$cond": [{"$eq": ["$status", "present"]}, 1, 0]}
                },
                "total_absent": {
                    "$sum": {"$cond": [{"$eq": ["$status", "absent"]}, 1, 0]}
                },
                "total_incomplete": {
                    "$sum": {"$cond": [{"$eq": ["$status", "incomplete"]}, 1, 0]}
                },
                "total_work_minutes": {
                    "$sum": {"$ifNull": ["$work_duration_minutes", 0]}
                },
            }
        },
        {
            "$project": {
                "_id": 0,
                "total_records": 1,
                "total_present": 1,
                "total_absent": 1,
                "total_incomplete": 1,
                "total_work_minutes": 1,
            }
        },
    ]

    results = repo.aggregate(pipeline)
    if not results:
        return {
            "total_records": 0,
            "total_present": 0,
            "total_absent": 0,
            "total_incomplete": 0,
            "total_work_minutes": 0,
        }
    return results[0]
