"""
test_healthz.py — Unit test for production GET /healthz endpoint.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthz_endpoint():
    """Verify GET /healthz returns HTTP 200 and {"status": "ok"}."""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
