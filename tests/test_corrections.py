"""
tests/test_corrections.py
Unit tests for manual attendance correction and audit trail endpoints.
"""
import pytest

BASE = "/api/v1/attendance"

PUNCH_IN_PAYLOAD = {
    "employee_id": "EMP001",
    "punch_in": "2024-06-01T09:00:00",
}

CORRECTION_PAYLOAD = {
    "punch_in": "2024-06-01T08:45:00",
    "reason": "Employee swiped in earlier than system recorded",
    "corrected_by": "admin@hrone.com",
}


def _create_punched_in(client) -> str:
    resp = client.post(f"{BASE}/punch-in", json=PUNCH_IN_PAYLOAD)
    assert resp.status_code == 201
    return resp.json()["_id"]


def _create_complete(client) -> str:
    aid = _create_punched_in(client)
    client.post(f"{BASE}/{aid}/punch-out", json={"punch_out": "2024-06-01T17:00:00"})
    return aid


# ──────────────────────────────────────────────
# Apply correction
# ──────────────────────────────────────────────

def test_correction_success(client):
    aid = _create_complete(client)
    resp = client.post(f"{BASE}/{aid}/correct", json=CORRECTION_PAYLOAD)
    assert resp.status_code == 200
    data = resp.json()
    assert data["_id"] == aid


def test_correction_updates_punch_in(client):
    aid = _create_complete(client)
    resp = client.post(f"{BASE}/{aid}/correct", json=CORRECTION_PAYLOAD)
    assert "08:45" in resp.json()["punch_in"]


def test_correction_appends_to_audit_trail(client):
    aid = _create_complete(client)
    client.post(f"{BASE}/{aid}/correct", json=CORRECTION_PAYLOAD)
    resp = client.get(f"{BASE}/{aid}")
    corrections = resp.json()["corrections"]
    assert len(corrections) == 1
    assert corrections[0]["reason"] == CORRECTION_PAYLOAD["reason"]
    assert corrections[0]["corrected_by"] == CORRECTION_PAYLOAD["corrected_by"]


def test_correction_records_old_and_new_values(client):
    aid = _create_complete(client)
    client.post(f"{BASE}/{aid}/correct", json=CORRECTION_PAYLOAD)
    corrections = client.get(f"{BASE}/{aid}").json()["corrections"]
    entry = corrections[0]
    assert "old_values" in entry
    assert "new_values" in entry
    assert "punch_in" in entry["old_values"]
    assert "punch_in" in entry["new_values"]


def test_multiple_corrections_accumulate(client):
    aid = _create_complete(client)
    client.post(f"{BASE}/{aid}/correct", json=CORRECTION_PAYLOAD)
    client.post(
        f"{BASE}/{aid}/correct",
        json={
            "punch_out": "2024-06-01T18:00:00",
            "reason": "Extended work approved",
            "corrected_by": "manager@hrone.com",
        },
    )
    corrections = client.get(f"{BASE}/{aid}").json()["corrections"]
    assert len(corrections) == 2


def test_correction_not_found_returns_404(client):
    resp = client.post(f"{BASE}/nonexistent/correct", json=CORRECTION_PAYLOAD)
    assert resp.status_code == 404


def test_correction_missing_reason_returns_422(client):
    aid = _create_complete(client)
    resp = client.post(
        f"{BASE}/{aid}/correct",
        json={"punch_in": "2024-06-01T08:45:00", "corrected_by": "admin"},
    )
    assert resp.status_code == 422


def test_correction_missing_corrected_by_returns_422(client):
    aid = _create_complete(client)
    resp = client.post(
        f"{BASE}/{aid}/correct",
        json={"punch_in": "2024-06-01T08:45:00", "reason": "Fix"},
    )
    assert resp.status_code == 422


def test_correction_no_fields_returns_422(client):
    aid = _create_complete(client)
    resp = client.post(
        f"{BASE}/{aid}/correct",
        json={"reason": "No change provided", "corrected_by": "admin"},
    )
    assert resp.status_code == 422


def test_correction_punch_out_before_punch_in_returns_422(client):
    aid = _create_complete(client)
    resp = client.post(
        f"{BASE}/{aid}/correct",
        json={
            "punch_out": "2024-06-01T07:00:00",
            "reason": "Invalid time",
            "corrected_by": "admin",
        },
    )
    assert resp.status_code == 422


# ──────────────────────────────────────────────
# Audit trail retrieval
# ──────────────────────────────────────────────

def test_get_corrections_empty_on_fresh_record(client):
    aid = _create_complete(client)
    resp = client.get(f"{BASE}/{aid}/corrections")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_corrections_after_one_correction(client):
    aid = _create_complete(client)
    client.post(f"{BASE}/{aid}/correct", json=CORRECTION_PAYLOAD)
    resp = client.get(f"{BASE}/{aid}/corrections")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_get_corrections_not_found_returns_404(client):
    resp = client.get(f"{BASE}/nonexistent/corrections")
    assert resp.status_code == 404
