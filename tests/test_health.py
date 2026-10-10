"""tests/test_health.py — Health endpoint tests."""
from fastapi.testclient import TestClient
from app.main import app


def test_health_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_ok_status(client):
    response = client.get("/health")
    data = response.json()
    assert data["status"] == "ok"


def test_health_returns_version(client):
    response = client.get("/health")
    assert "version" in response.json()
