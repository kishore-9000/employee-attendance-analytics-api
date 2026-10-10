"""
app/core/database.py
MongoDB connection management using PyMongo.
One MongoClient is created at startup and reused throughout.
"""
import logging
from typing import Optional

# pyrefly: ignore [missing-import]
from pymongo import MongoClient, ASCENDING, DESCENDING
# pyrefly: ignore [missing-import]
from pymongo.database import Database
# pyrefly: ignore [missing-import]
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: Optional[MongoClient] = None
_db: Optional[Database] = None


def connect_db(uri: Optional[str] = None, db_name: Optional[str] = None) -> None:
    """
    Open the MongoDB connection.
    Called once at application startup (or in tests with override values).
    """
    global _client, _db

    resolved_uri = uri or settings.mongodb_uri
    resolved_db = db_name or settings.mongodb_database

    logger.info("Connecting to MongoDB database '%s'", resolved_db)
    try:
        _client = MongoClient(resolved_uri, serverSelectionTimeoutMS=5000)
        # Trigger actual connection to catch failures early
        _client.admin.command("ping")
        _db = _client[resolved_db]
        _ensure_indexes()
        logger.info("MongoDB connection established.")
    except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
        logger.error("Cannot connect to MongoDB: %s", exc)
        raise


def disconnect_db() -> None:
    """Close the MongoDB connection. Called at application shutdown."""
    global _client, _db
    if _client is not None:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB connection closed.")


def get_db() -> Database:
    """Return the active database. Raises if not connected."""
    if _db is None:
        raise RuntimeError(
            "Database is not connected. Call connect_db() before using get_db()."
        )
    return _db


def _ensure_indexes() -> None:
    """Create all required indexes. Safe to call on every startup (idempotent)."""
    db = get_db()

    # attendance collection indexes
    attendance = db["attendance"]
    attendance.create_index(
        [("employee_id", ASCENDING), ("punch_in", DESCENDING)],
        name="employee_punch_in",
    )
    attendance.create_index(
        [("date", ASCENDING)],
        name="attendance_date",
    )
    attendance.create_index(
        [("status", ASCENDING)],
        name="attendance_status",
    )

    logger.info("MongoDB indexes ensured.")
