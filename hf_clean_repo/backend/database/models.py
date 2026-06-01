"""Database models for the Fashion Assistant app — no inference logic here."""
APP_NAME = "Fashion Assistant"

def models_use_ai() -> bool:
    """Quick programmatic hint: models module does not perform inference."""
    return False

# Create User model class that:
# - inherits from Base
# - has table name "users"
# - has columns: id (primary key), name (string), email (string, unique), created_at (datetime)
# - has columns for analysis: height (float), weight (float), body_shape (string), undertone (string), bmi (float)
# - has relationship to wardrobe items (one-to-many)

# Create WardrobeItem model class that:
# - inherits from Base
# - has table name "wardrobe_items"
# - has columns: id (primary key), user_id (foreign key to users), created_at (datetime)
# - has columns: image_path (string), clothing_type (string), color_primary (string), color_secondary (string, nullable)
# - has columns: pattern (string, nullable), season (string, nullable), category (string)
# - has relationship to user (many-to-one)

# Create Outfit model class that:
# - inherits from Base
# - has table name "outfits"
# - has columns: id (primary key), user_id (foreign key to users), created_at (datetime)
# - has columns: name (string), occasion (string, nullable), items_json (text to store item IDs as JSON)
# - has relationship to user (many-to-one)
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base
import re


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    email_verification_token_hash = Column(String(255), nullable=True)
    email_verification_expires_at = Column(DateTime, nullable=True)
    email_verified_at = Column(DateTime, nullable=True)
    profile_image_path = Column(String(255), nullable=True)
    
    # Analysis fields
    height = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)
    body_shape = Column(String(50), nullable=True)
    undertone = Column(String(50), nullable=True)
    bmi = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    wardrobe_items = relationship("WardrobeItem", back_populates="user", cascade="all, delete-orphan")
    outfits = relationship("Outfit", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    outfit_ratings = relationship("OutfitRating", cascade="all, delete-orphan")
    recommendation_feedback = relationship("RecommendationFeedback", cascade="all, delete-orphan")
    item_usage = relationship("ItemUsage", cascade="all, delete-orphan")


class WardrobeItem(Base):
    __tablename__ = "wardrobe_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    image_path = Column(String, nullable=False)
    clothing_type = Column(String, nullable=False)
    color_primary = Column(String, nullable=False)
    color_secondary = Column(String, nullable=True)
    pattern = Column(String, nullable=True)
    season = Column(String, nullable=True)
    category = Column(String, nullable=False)

    user = relationship("User", back_populates="wardrobe_items")


class Outfit(Base):
    __tablename__ = "outfits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    name = Column(String, nullable=False)
    occasion = Column(String, nullable=True)
    items_json = Column(Text, nullable=False)  # Store item IDs as JSON string

    user = relationship("User", back_populates="outfits")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    jti = Column(String(64), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    user_agent = Column(String(255), nullable=True)
    ip_address = Column(String(64), nullable=True)
    revoked_reason = Column(String(100), nullable=True)
    replaced_by_jti = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="refresh_tokens")


class OutfitRating(Base):
    """User ratings of generated outfits for feedback-driven improvement."""
    __tablename__ = "outfit_ratings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    outfit_id = Column(Integer, ForeignKey("outfits.id"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)  # 1-5 scale
    comment = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User")
    outfit = relationship("Outfit")


class RecommendationFeedback(Base):
    """Feedback on recommendations (outfit, shopping, discard) to track accuracy."""
    __tablename__ = "recommendation_feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    recommendation_type = Column(String(50), nullable=False)  # "outfit" | "shopping" | "discard"
    recommendation_id = Column(String(255), nullable=False)  # ID of the specific recommendation
    helpful = Column(Integer, nullable=False)  # 1 for yes, 0 for no
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User")


class ItemUsage(Base):
    """Track wardrobe item usage (worn, kept, discarded) for improving recommendations."""
    __tablename__ = "item_usage"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("wardrobe_items.id"), nullable=False, index=True)
    action = Column(String(50), nullable=False)  # "kept" | "discarded" | "worn"
    wear_count = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User")
    wardrobe_item = relationship("WardrobeItem")


class ModelMetrics(Base):
    """Track model performance metrics over time for monitoring and retraining decisions."""
    __tablename__ = "model_metrics"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(100), nullable=False)  # "color_harmony" | "clothing_classifier" | "body_shape"
    metric_type = Column(String(50), nullable=False)  # "accuracy" | "avg_rating" | "helpful_rate" | "drift_score"
    value = Column(Float, nullable=False)
    evaluation_date = Column(DateTime, default=datetime.utcnow, index=True)
    version = Column(String(50), nullable=True)  # Model version/epoch for tracking
    
    created_at = Column(DateTime, default=datetime.utcnow)


def _item_to_dict_minimal(item):
    """Return a minimal dict for an item input that may be:
    - a WardrobeItem instance (has .id and attrs)
    - a dict-like object
    - an int or numeric string representing the id
    If only an id is available, other fields are left as None.
    """
    # WardrobeItem-like object
    try:
        _item_id = getattr(item, "id", None)
        if _item_id is not None:
            return {
                "id": _item_id,
                "type": getattr(item, "clothing_type", None),
                "category": getattr(item, "category", None),
                "color": getattr(item, "color_primary", None),
                "pattern": getattr(item, "pattern", None),
                "image_path": getattr(item, "image_path", None),
            }
    except Exception:
        pass

    # dict-like
    try:
        if isinstance(item, dict):
            return {
                "id": item.get("id"),
                "type": item.get("clothing_type") or item.get("type"),
                "category": item.get("category"),
                "color": item.get("color_primary") or item.get("color"),
                "pattern": item.get("pattern"),
                "image_path": item.get("image_path"),
            }
    except Exception:
        pass

    # str or int (id only) — improved parsing for numeric strings
    try:
        if isinstance(item, int):
            return {"id": item, "type": None, "category": None, "color": None, "pattern": None, "image_path": None}
        if isinstance(item, str):
            s = item.strip()
            if s.isdigit():
                _item_id = int(s)
                return {"id": _item_id, "type": None, "category": None, "color": None, "pattern": None, "image_path": None}
            # try to extract first digit sequence from the string
            m = re.search(r"(\d+)", s)
            if m:
                _item_id = int(m.group(1))
                return {"id": _item_id, "type": None, "category": None, "color": None, "pattern": None, "image_path": None}
    except Exception:
        pass

    # Fallback
    return {"id": None, "type": None, "category": None, "color": None, "pattern": None, "image_path": None}

def normalize_items_for_response(items):
    """Normalize a list of items (mixed types) into a list of minimal dicts.
    Use this in endpoints while you fix callers to provide real WardrobeItem objects.
     """
    return [_item_to_dict_minimal(i) for i in (items or [])]

