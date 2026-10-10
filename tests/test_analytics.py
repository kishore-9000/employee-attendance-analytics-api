"""
tests/test_analytics.py
Analytics endpoint tests.
Unit tests verify HTTP routing and empty-result behaviour.
Integration tests (marked) verify actual aggregation against MongoDB.
"""
import pytest

BASE = "/api/v1/analytics"


# ──────────────────────────────────────────────
# Daily summary
# ──────────────────────────────────────────────

def test_daily_summary_returns_200(client):
    resp = client.get(f"{BASE}/daily?start_date=2024-06-01&end_date=2024-06-30")
    assert resp.status_code == 200


def test_daily_summary_response_shape(client):
    resp = client.get(f"{BASE}/daily?start_date=2024-06-01&end_date=2024-06-30")
    data = resp.json()
    assert "start_date" in data
    assert "end_date" in data
    assert "daily" in data
    assert isinstance(data["daily"], list)


def test_daily_summary_empty_range_returns_empty_list(client):
    resp = client.get(f"{BASE}/daily?start_date=2024-06-01&end_date=2024-06-30")
    # FakeDB aggregate returns [] — so daily list is empty
    assert resp.json()["daily"] == []


def test_daily_summary_inverted_range_returns_422(client):
    resp = client.get(f"{BASE}/daily?start_date=2024-06-30&end_date=2024-06-01")
    assert resp.status_code == 422


def test_daily_summary_missing_params_returns_422(client):
    resp = client.get(f"{BASE}/daily?start_date=2024-06-01")
    assert resp.status_code == 422


# ──────────────────────────────────────────────
# Employee summary
# ──────────────────────────────────────────────

def test_employee_summary_returns_200(client):
    resp = client.get(f"{BASE}/employees?start_date=2024-06-01&end_date=2024-06-30")
    assert resp.status_code == 200


def test_employee_summary_response_shape(client):
    data = client.get(f"{BASE}/employees?start_date=2024-06-01&end_date=2024-06-30").json()
    assert "employees" in data
    assert isinstance(data["employees"], list)


def test_employee_summary_inverted_range_returns_422(client):
    resp = client.get(f"{BASE}/employees?start_date=2024-12-01&end_date=2024-01-01")
    assert resp.status_code == 422


# ──────────────────────────────────────────────
# Overall summary
# ──────────────────────────────────────────────

def test_overall_summary_returns_200(client):
    resp = client.get(f"{BASE}/summary")
    assert resp.status_code == 200


def test_overall_summary_has_required_fields(client):
    data = client.get(f"{BASE}/summary").json()
    required_fields = [
        "total_records",
        "total_present",
        "total_absent",
        "total_incomplete",
        "total_work_minutes",
    ]
    for field in required_fields:
        assert field in data, f"Missing field: {field}"


def test_overall_summary_empty_db_returns_zeros(client):
    data = client.get(f"{BASE}/summary").json()
    assert data["total_records"] == 0
    assert data["total_present"] == 0


def test_overall_summary_with_date_range_returns_200(client):
    resp = client.get(f"{BASE}/summary?start_date=2024-06-01&end_date=2024-06-30")
    assert resp.status_code == 200


def test_overall_summary_inverted_range_returns_422(client):
    resp = client.get(f"{BASE}/summary?start_date=2024-12-01&end_date=2024-01-01")
    assert resp.status_code == 422
