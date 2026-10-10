"""
tests/conftest.py
Shared test fixtures and database override.

Strategy:
  - Tests use a real in-memory fake (dict-based) repository via
    pytest monkeypatching so no MongoDB instance is required for unit tests.
  - Integration tests (marked with @pytest.mark.integration) require a
    running MongoDB; run with: pytest -m integration
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core import database as db_module


# ──────────────────────────────────────────────
# In-memory fake database for unit tests
# ──────────────────────────────────────────────

class FakeCollection:
    """Minimal dict-based collection mirroring PyMongo behaviour."""

    def __init__(self):
        self._store: dict = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"fake_id_{self._counter:04d}"

    def insert_one(self, document: dict):
        oid = self._next_id()
        document["_id"] = oid
        self._store[oid] = dict(document)

        class Result:
            inserted_id = oid

        return Result()

    def find_one(self, query: dict):
        for doc in self._store.values():
            if self._matches(doc, query):
                return dict(doc)
        return None

    def find(self, query: dict = None):
        results = [
            dict(d) for d in self._store.values()
            if self._matches(d, query or {})
        ]
        return _FakeCursor(results)

    def find_one_and_update(self, query: dict, update: dict, return_document=False):
        doc = self.find_one(query)
        if not doc:
            return None
        oid = doc["_id"]
        if "$set" in update:
            self._store[oid].update(update["$set"])
        if "$push" in update:
            for field, value in update["$push"].items():
                self._store[oid].setdefault(field, []).append(value)
        return dict(self._store[oid])

    def create_index(self, *args, **kwargs):
        pass  # No-op for tests

    def aggregate(self, pipeline: list):
        return []  # Analytics tests use integration tests or manual setup

    @staticmethod
    def _matches(doc: dict, query: dict) -> bool:
        for key, value in query.items():
            if isinstance(value, dict):
                doc_val = doc.get(key)
                for op, op_val in value.items():
                    if op == "$gte" and not (doc_val >= op_val):
                        return False
                    if op == "$lte" and not (doc_val <= op_val):
                        return False
            elif doc.get(key) != value:
                return False
        return True


class _FakeCursor:
    def __init__(self, items):
        self._items = items

    def sort(self, *args):
        return self

    def skip(self, n):
        self._items = self._items[n:]
        return self

    def limit(self, n):
        self._items = self._items[:n]
        return self

    def __iter__(self):
        return iter(self._items)


class FakeDB:
    def __init__(self):
        self._collections: dict[str, FakeCollection] = {}

    def __getitem__(self, name: str) -> FakeCollection:
        if name not in self._collections:
            self._collections[name] = FakeCollection()
        return self._collections[name]

    def clear(self):
        self._collections.clear()


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────

@pytest.fixture(scope="function")
def fake_db():
    """Fresh in-memory database for each test."""
    return FakeDB()


@pytest.fixture(scope="function")
def client(fake_db, monkeypatch):
    """
    TestClient with the database patched to use FakeDB.
    Connection/disconnection lifecycle is bypassed.
    """
    monkeypatch.setattr(db_module, "_db", fake_db)
    monkeypatch.setattr(db_module, "connect_db", lambda *a, **kw: None)
    monkeypatch.setattr(db_module, "disconnect_db", lambda: None)

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
