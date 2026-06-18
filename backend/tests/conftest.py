import os
from io import BytesIO
from pathlib import Path
import uuid

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
TEST_DB_PATH = ROOT / "backend" / "tests" / "test_auth.db"
TEST_DB_URL = f"sqlite:///{TEST_DB_PATH.as_posix()}"


os.environ.setdefault("SECRET_KEY", "test-secret-key-with-at-least-32-characters")
os.environ.setdefault("DATABASE_URL", TEST_DB_URL)
os.environ.setdefault("ENV", "development")
os.environ.setdefault("EMAIL_VERIFICATION_REQUIRED", "true")
os.environ.setdefault("INFERENCE_QUEUE_ENABLED", "false")

if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()


from backend import main as app_module
from backend.database.database import SessionLocal
from backend.database import models


@pytest.fixture(autouse=True)
def clean_database() -> None:
    session = SessionLocal()
    try:
        session.query(models.RefreshToken).delete(synchronize_session=False)
        session.query(models.ItemUsage).delete(synchronize_session=False)
        session.query(models.RecommendationFeedback).delete(synchronize_session=False)
        session.query(models.OutfitRating).delete(synchronize_session=False)
        session.query(models.WardrobeItem).delete(synchronize_session=False)
        session.query(models.Outfit).delete(synchronize_session=False)
        session.query(models.User).delete(synchronize_session=False)
        session.commit()
        yield
    finally:
        session.query(models.RefreshToken).delete(synchronize_session=False)
        session.query(models.ItemUsage).delete(synchronize_session=False)
        session.query(models.RecommendationFeedback).delete(synchronize_session=False)
        session.query(models.OutfitRating).delete(synchronize_session=False)
        session.query(models.WardrobeItem).delete(synchronize_session=False)
        session.query(models.Outfit).delete(synchronize_session=False)
        session.query(models.User).delete(synchronize_session=False)
        session.commit()
        session.close()


@pytest.fixture(autouse=True)
def isolate_rate_limits(monkeypatch: pytest.MonkeyPatch) -> None:
    test_client_id = f"pytest-{uuid.uuid4()}"

    def _get_remote_address(request):
        return request.headers.get("X-Test-Client-Id", test_client_id)

    monkeypatch.setattr(app_module, "get_remote_address", _get_remote_address)


@pytest.fixture()
def client() -> TestClient:
    return TestClient(
        app_module.app, headers={"X-Test-Client-Id": f"pytest-{uuid.uuid4()}"}
    )


def make_png_bytes(color: tuple[int, int, int] = (255, 0, 0)) -> bytes:
    from PIL import Image

    buffer = BytesIO()
    Image.new("RGB", (1, 1), color).save(buffer, format="PNG")
    return buffer.getvalue()
