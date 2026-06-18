import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services import body_shape_rules as bsr
from services import color_harmony as ch


def test_rgb_to_hsv_converts_primary_red() -> None:
    hue, saturation, value = ch.rgb_to_hsv((255, 0, 0))

    assert round(hue) == 0
    assert saturation == 1.0
    assert value == 1.0


def test_color_temperature_classifies_warm_and_cool_colors() -> None:
    assert ch.get_color_temperature((255, 128, 0)) == "warm"
    assert ch.get_color_temperature((0, 120, 255)) == "cool"


def test_color_harmony_detects_complementary_colors() -> None:
    result = ch.check_color_harmony((255, 0, 0), (0, 255, 255))

    assert result["compatible"] is True
    assert result["harmony_type"] == "complementary"
    assert result["score"] == 1.0


def test_outfit_color_score_averages_pairwise_harmony() -> None:
    score = ch.calculate_outfit_color_score(
        [(255, 0, 0), (0, 255, 255), (255, 255, 255)]
    )

    assert score == 1.0


def test_body_shape_rules_score_flattering_and_avoid_items() -> None:
    assert bsr.is_flattering_for_body_shape("rectangle", "fitted", "top") is True
    assert bsr.get_body_shape_score("rectangle", "boxy", "top") == 0.3


def test_outfit_body_shape_score_averages_item_scores() -> None:
    items = [
        {"type": "fitted", "category": "top"},
        {"type": "bootcut", "category": "bottom"},
    ]

    assert bsr.calculate_outfit_body_shape_score("rectangle", items) == 1.0


def test_unknown_body_shape_defaults_to_neutral_behavior() -> None:
    assert bsr.is_flattering_for_body_shape("mystery", "anything", "top") is True
    assert bsr.get_body_shape_score("mystery", "anything", "top") == 0.7
