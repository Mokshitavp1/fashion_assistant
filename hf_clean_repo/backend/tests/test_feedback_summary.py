import os
import sys
from pathlib import Path
from uuid import uuid4

os.environ.setdefault("SECRET_KEY", "test-secret-key-with-at-least-32-characters")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from database.database import SessionLocal
from database import models
from main import app, verify_token


client = TestClient(app)


def test_user_feedback_summary_returns_recent_activity() -> None:
    db = SessionLocal()
    try:
        user = models.User(
            name="Feedback User",
            email=f"feedback-{uuid4().hex[:8]}@example.com",
            password_hash="hash",
            email_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        outfit = models.Outfit(
            user_id=user.id,
            name="Test Outfit",
            items_json='{"items": [{"id": 1, "quantity": 1}]}'
        )
        wardrobe_item = models.WardrobeItem(
            user_id=user.id,
            image_path="uploads/test.jpg",
            clothing_type="top",
            color_primary="black",
            color_secondary=None,
            pattern="solid",
            season="all",
            category="top",
        )
        db.add_all([outfit, wardrobe_item])
        db.commit()
        db.refresh(outfit)
        db.refresh(wardrobe_item)

        db.add(models.OutfitRating(user_id=user.id, outfit_id=outfit.id, rating=5, comment="Great"))
        db.add(models.RecommendationFeedback(user_id=user.id, recommendation_type="outfit", recommendation_id=str(outfit.id), helpful=1))
        db.add(models.ItemUsage(user_id=user.id, item_id=wardrobe_item.id, action="worn", wear_count=2))
        db.commit()

        app.dependency_overrides[verify_token] = lambda: user.id

        response = client.get(f"/users/{user.id}/feedback/summary")

        assert response.status_code == 200
        payload = response.json()
        assert payload["user_id"] == user.id
        assert payload["summary"]["outfit_ratings_count"] == 1
        assert payload["summary"]["recommendation_feedback_count"] == 1
        assert payload["summary"]["item_usage_count"] == 1
        assert payload["summary"]["average_outfit_rating"] == 5.0
        assert payload["summary"]["helpful_rate"] == 1.0
        assert len(payload["outfit_ratings"]) == 1
        assert len(payload["recommendation_feedback"]) == 1
        assert len(payload["item_usage"]) == 1
    finally:
        app.dependency_overrides.pop(verify_token, None)
        db.close()