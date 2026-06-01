import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from database.models import WardrobeItem
from services import discard_analyzer as da
from services import outfit_generator as og
from services import shopping_assistant as sa


def _item(item_id: int, type_: str, category: str, color: str, pattern: str = "solid") -> WardrobeItem:
    return WardrobeItem(
        id=item_id,
        clothing_type=type_,
        category=category,
        color_primary=color,
        color_secondary=None,
        pattern=pattern,
        season="all",
        image_path=f"uploads/{item_id}.jpg",
        user_id=1,
    )


def test_generate_outfit_recommendations_formats_scores() -> None:
    wardrobe = [
        _item(1, "fitted", "top", "red"),
        _item(2, "bootcut", "bottom", "cyan"),
        _item(3, "sneakers", "shoes", "white"),
    ]

    outfits = og.get_outfit_recommendations(wardrobe, "rectangle", "warm")

    assert outfits
    assert outfits[0]["outfit_number"] == 1
    assert outfits[0]["overall_score"] >= 0
    assert outfits[0]["items"]


def test_discard_recommendations_identify_weak_item() -> None:
    wardrobe = [
        _item(1, "boxy", "top", "blue"),
        _item(2, "bootcut", "bottom", "blue"),
        _item(3, "sneakers", "shoes", "white"),
    ]

    result = da.get_discard_recommendations(wardrobe, "rectangle", "warm")

    assert result["total_items"] == 3
    assert result["discard_count"] >= 1
    assert result["items_to_discard"]
    assert result["items_to_discard"][0]["overall_score"] <= result["items_to_keep"][0]["overall_score"]


def test_shopping_helpers_detect_match_duplicate_and_recommendation() -> None:
    wardrobe = [
        _item(1, "fitted", "top", "red"),
        _item(2, "bootcut", "bottom", "cyan"),
        _item(3, "sneakers", "shoes", "white"),
    ]

    matches = sa.find_matching_wardrobe_items("red", "top", wardrobe)
    assert matches

    compatibility = sa.calculate_wardrobe_compatibility_score(matches, total_relevant_items=1)
    assert 0 <= compatibility["compatibility_score"] <= 1
    assert compatibility["match_count"] >= 1

    duplicate = sa.check_duplicate_in_wardrobe("red", "fitted", wardrobe)
    assert duplicate["is_duplicate"] is True
    assert duplicate["similar_items"]

    recommendation = sa.generate_purchase_recommendation(
        compatibility_score=0.75,
        is_duplicate=False,
        body_shape_score=0.9,
        matching_items_count=2,
    )
    assert recommendation["recommendation"] == "buy"
    assert recommendation["reasons"]


def test_shopping_helpers_skip_duplicate_or_low_score() -> None:
    recommendation = sa.generate_purchase_recommendation(
        compatibility_score=0.2,
        is_duplicate=True,
        body_shape_score=0.2,
        matching_items_count=0,
    )

    assert recommendation["recommendation"] == "skip"
