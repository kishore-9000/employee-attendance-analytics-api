"""
app/repositories/attendance_repository.py
All MongoDB read/write operations for the attendance collection.
Business logic must NOT live here — only database access.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from bson.errors import InvalidId
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError

from app.core.database import get_db

logger = logging.getLogger(__name__)

COLLECTION = "attendance"


def _col() -> Collection:
    return get_db()[COLLECTION]


def _serialize(doc: dict) -> dict:
    """Convert ObjectId to string for JSON serialisation."""
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


# ──────────────────────────────────────────────
# Create
# ──────────────────────────────────────────────

def create_attendance(document: dict) -> dict:
    """Insert a new attendance record and return it with string _id."""
    result = _col().insert_one(document)
    doc = _col().find_one({"_id": result.inserted_id})
    return _serialize(doc)


# ──────────────────────────────────────────────
# Read
# ──────────────────────────────────────────────

def find_by_id(attendance_id: str) -> Optional[dict]:
    try:
        oid = ObjectId(attendance_id)
    except (InvalidId, TypeError):
        return None
    doc = _col().find_one({"_id": oid})
    return _serialize(doc) if doc else None


def find_by_employee_and_date(employee_id: str, date: str) -> Optional[dict]:
    doc = _col().find_one({"employee_id": employee_id, "date": date})
    return _serialize(doc) if doc else None


def find_by_employee(employee_id: str, skip: int = 0, limit: int = 50) -> list[dict]:
    cursor = (
        _col()
        .find({"employee_id": employee_id})
        .sort("punch_in", -1)
        .skip(skip)
        .limit(limit)
    )
    return [_serialize(doc) for doc in cursor]


def find_by_date_range(start_date: str, end_date: str) -> list[dict]:
    cursor = _col().find(
        {"date": {"$gte": start_date, "$lte": end_date}}
    ).sort("date", 1)
    return [_serialize(doc) for doc in cursor]


# ──────────────────────────────────────────────
# Update
# ──────────────────────────────────────────────

def update_attendance(attendance_id: str, update_fields: dict) -> Optional[dict]:
    """
    Apply $set update and return the updated document.
    Always sets updated_at to now.
    """
    try:
        oid = ObjectId(attendance_id)
    except (InvalidId, TypeError):
        return None

    update_fields["updated_at"] = datetime.now(tz=timezone.utc)
    result = _col().find_one_and_update(
        {"_id": oid},
        {"$set": update_fields},
        return_document=True,  # pymongo ReturnDocument.AFTER equivalent
    )
    return _serialize(result) if result else None


def push_correction(attendance_id: str, correction: dict, set_fields: dict) -> Optional[dict]:
    """
    Atomically push a correction entry into the corrections array
    and update the main fields in a single operation.
    """
    try:
        oid = ObjectId(attendance_id)
    except (InvalidId, TypeError):
        return None

    set_fields["updated_at"] = datetime.now(tz=timezone.utc)
    result = _col().find_one_and_update(
        {"_id": oid},
        {
            "$set": set_fields,
            "$push": {"corrections": correction},
        },
        return_document=True,
    )
    return _serialize(result) if result else None


# ──────────────────────────────────────────────
# Aggregation (analytics)
# ──────────────────────────────────────────────

def aggregate(pipeline: list[dict]) -> list[dict]:
    """Execute an arbitrary aggregation pipeline and return results."""
    return list(_col().aggregate(pipeline))
