"""
tests/test_attendance.py
Unit tests for punch-in, punch-out and retrieval endpoints.
Uses FakeDB (no MongoDB required).
"""
import pytest


BASE = "/api/v1/attendance"

PUNCH_IN_PAYLOAD = {
    "employee_id": "EMP001",
    "punch_in": "2024-06-01T09:00:00",
}


# ──────────────────────────────────────────────
# Punch-in
# ──────────────────────────────────────────────

def test_punch_in_success(client):
    resp = client.post(f"{BASE}/punch-in", json=PUNCH_IN_PAYLOAD)
    assert resp.status_code == 201
    data = resp.json()
    assert data["employee_id"] == "EMP001"
    assert data["status"] == "incomplete"
    assert data["punch_out"] is None
    assert "_id" in data


def test_punch_in_returns_date(client):
    resp = client.post(f"{BASE}/punch-in", json=PUNCH_IN_PAYLOAD)
    assert resp.json()["date"] == "2024-06-01"


def test_punch_in_duplicate_same_day_returns_409(client):
    client.post(f"{BASE}/punch-in", json=PUNCH_IN_PAYLOAD)
    resp = client.post(f"{BASE}/punch-in", json=PUNCH_IN_PAYLOAD)
    assert resp.status_code == 409


def test_punch_in_missing_employee_id_returns_422(client):
    resp = client.post(f"{BASE}/punch-in", json={"punch_in": "2024-06-01T09:00:00"})
    assert resp.status_code == 422


def test_punch_in_missing_punch_in_returns_422(client):
    resp = client.post(f"{BASE}/punch-in", json={"employee_id": "EMP001"})
    assert resp.status_code == 422


def test_punch_in_blank_employee_id_returns_422(client):
    resp = client.post(f"{BASE}/punch-in", json={"employee_id": "  ", "punch_in": "2024-06-01T09:00:00"})
    assert resp.status_code == 422


def test_punch_in_different_day_succeeds(client):
    client.post(f"{BASE}/punch-in", json=PUNCH_IN_PAYLOAD)
    resp = client.post(
        f"{BASE}/punch-in",
        json={"employee_id": "EMP001", "punch_in": "2024-06-02T09:00:00"},
    )
    assert resp.status_code == 201


def test_punch_in_different_employee_same_day_succeeds(client):
    client.post(f"{BASE}/punch-in", json=PUNCH_IN_PAYLOAD)
    resp = client.post(
        f"{BASE}/punch-in",
        json={"employee_id": "EMP002", "punch_in": "2024-06-01T09:00:00"},
    )
    assert resp.status_code == 201


# ──────────────────────────────────────────────
# Punch-out
# ──────────────────────────────────────────────

def _create_attendance(client) -> str:
    resp = client.post(f"{BASE}/punch-in", json=PUNCH_IN_PAYLOAD)
    return resp.json()["_id"]


def test_punch_out_success(client):
    aid = _create_attendance(client)
    resp = client.post(
        f"{BASE}/{aid}/punch-out",
        json={"punch_out": "2024-06-01T17:00:00"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "present"
    assert data["work_duration_minutes"] == 480


def test_punch_out_not_found_returns_404(client):
    resp = client.post(
        f"{BASE}/nonexistent_id/punch-out",
        json={"punch_out": "2024-06-01T17:00:00"},
    )
    assert resp.status_code == 404


def test_punch_out_before_punch_in_returns_422(client):
    aid = _create_attendance(client)
    resp = client.post(
        f"{BASE}/{aid}/punch-out",
        json={"punch_out": "2024-06-01T08:00:00"},
    )
    assert resp.status_code == 422


def test_punch_out_duplicate_returns_409(client):
    aid = _create_attendance(client)
    client.post(f"{BASE}/{aid}/punch-out", json={"punch_out": "2024-06-01T17:00:00"})
    resp = client.post(f"{BASE}/{aid}/punch-out", json={"punch_out": "2024-06-01T18:00:00"})
    assert resp.status_code == 409


def test_punch_out_missing_payload_returns_422(client):
    aid = _create_attendance(client)
    resp = client.post(f"{BASE}/{aid}/punch-out", json={})
    assert resp.status_code == 422


# ──────────────────────────────────────────────
# Retrieval
# ──────────────────────────────────────────────

def test_get_attendance_by_id(client):
    aid = _create_attendance(client)
    resp = client.get(f"{BASE}/{aid}")
    assert resp.status_code == 200
    assert resp.json()["_id"] == aid


def test_get_attendance_not_found_returns_404(client):
    resp = client.get(f"{BASE}/nonexistent")
    assert resp.status_code == 404


def test_get_employee_attendance_list(client):
    client.post(f"{BASE}/punch-in", json=PUNCH_IN_PAYLOAD)
    resp = client.get(f"{BASE}/employee/EMP001")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) >= 1


def test_get_employee_attendance_empty_list(client):
    resp = client.get(f"{BASE}/employee/UNKNOWN_EMP")
    assert resp.status_code == 200
    assert resp.json() == []
