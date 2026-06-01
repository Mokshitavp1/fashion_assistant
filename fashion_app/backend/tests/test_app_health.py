import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-with-at-least-32-characters")

from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_root_health() -> None:
    response = client.get("/")
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("status") == "ok"
