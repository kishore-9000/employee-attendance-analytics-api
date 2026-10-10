"""
scripts/seed_data.py
Load demonstration attendance records into the configured MongoDB database.

Usage:
    python scripts/seed_data.py

Set MONGODB_URI and MONGODB_DATABASE in your .env or environment before running.
Safe to run multiple times — existing records are not duplicated.
"""
import os
import sys
from datetime import datetime, timezone, timedelta

# Allow running from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv

load_dotenv()

from app.core.database import connect_db, disconnect_db, get_db

DEMO_EMPLOYEES = ["EMP001", "EMP002", "EMP003", "EMP004", "EMP005"]

BASE_DATE = datetime(2024, 6, 1, tzinfo=timezone.utc)


def build_record(employee_id: str, day_offset: int) -> dict:
    """Build a realistic attendance record for a given employee and day."""
    date = BASE_DATE + timedelta(days=day_offset)
    date_str = date.strftime("%Y-%m-%d")

    # Skip weekends
    if date.weekday() >= 5:
        return None

    punch_in = date.replace(hour=9, minute=0, second=0)
    punch_out = date.replace(hour=17, minute=30, second=0)
    duration = int((punch_out - punch_in).total_seconds() // 60)

    return {
        "employee_id": employee_id,
        "date": date_str,
        "punch_in": punch_in,
        "punch_out": punch_out,
        "status": "present",
        "work_duration_minutes": duration,
        "corrections": [],
        "created_at": datetime.now(tz=timezone.utc),
        "updated_at": datetime.now(tz=timezone.utc),
    }


def seed():
    connect_db()
    db = get_db()
    col = db["attendance"]

    inserted = 0
    skipped = 0

    for emp in DEMO_EMPLOYEES:
        for day in range(30):  # June 2024
            record = build_record(emp, day)
            if record is None:
                continue

            # Idempotency: skip if already present
            existing = col.find_one({
                "employee_id": record["employee_id"],
                "date": record["date"],
            })
            if existing:
                skipped += 1
                continue

            col.insert_one(record)
            inserted += 1

    print(f"Seed complete: {inserted} records inserted, {skipped} skipped.")
    disconnect_db()


if __name__ == "__main__":
    seed()
