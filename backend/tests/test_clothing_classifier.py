import numpy as np

from backend.services import clothing_classifier as cc


def _dummy_image(height: int = 240, width: int = 120) -> np.ndarray:
    # Build a simple gradient image so color clustering has enough variation.
    x = np.linspace(80, 220, width, dtype=np.uint8)
    y = np.linspace(60, 200, height, dtype=np.uint8)
    xv, yv = np.meshgrid(x, y)
    channel_r = xv
    channel_g = yv
    channel_b = ((xv.astype(np.uint16) + yv.astype(np.uint16)) // 2).astype(np.uint8)
    return np.stack([channel_b, channel_g, channel_r], axis=2)


def test_predict_with_model_uses_confident_label(monkeypatch) -> None:
    image = _dummy_image()

    cc._get_image_classifier.cache_clear()
    monkeypatch.setenv("HF_CLASSIFICATION_MIN_CONF", "0.35")
    monkeypatch.setattr(
        cc,
        "_get_image_classifier",
        lambda: (lambda _img, top_k=5: [{"label": "jersey, T-shirt, tee shirt", "score": 0.92}]),
    )

    result = cc._predict_with_model(image)
    assert result["used_fallback"] is False
    assert result["fallback_reason"] is None
    assert result["type"] == "top"
    assert result["model_confidence"] >= result["threshold"]


def test_predict_with_model_falls_back_on_low_confidence(monkeypatch) -> None:
    image = _dummy_image(height=220, width=220)

    cc._get_image_classifier.cache_clear()
    monkeypatch.setenv("HF_CLASSIFICATION_MIN_CONF", "0.99")
    monkeypatch.setattr(
        cc,
        "_get_image_classifier",
        lambda: (lambda _img, top_k=5: [{"label": "jersey, T-shirt, tee shirt", "score": 0.50}]),
    )

    result = cc._predict_with_model(image)
    assert result["used_fallback"] is True
    assert result["fallback_reason"] == "low_confidence"
    # square aspect ratio should map to fallback "top"
    assert result["type"] == "top"


def test_extract_clothing_region_returns_crop_and_debug(monkeypatch) -> None:
    image = _dummy_image(height=300, width=200)

    cc._get_object_detector.cache_clear()

    def fake_detector(_img, threshold=0.25):
        return [
            {
                "label": "person",
                "score": 0.87,
                "box": {"xmin": 20, "ymin": 20, "xmax": 180, "ymax": 280},
            }
        ]

    monkeypatch.setattr(cc, "_get_object_detector", lambda: fake_detector)

    crop, debug = cc._extract_clothing_region(image)
    assert debug["used_crop"] is True
    assert debug["detector_score"] == 0.87
    assert debug["crop_box"] is not None
    assert crop.shape[0] < image.shape[0]
    assert crop.shape[1] < image.shape[1]


def test_classify_clothing_includes_model_metadata(monkeypatch) -> None:
    image = _dummy_image(height=200, width=140)

    monkeypatch.setattr(
        cc,
        "_extract_clothing_region",
        lambda img: (
            img,
            {
                "used_crop": True,
                "detector_model": "facebook/detr-resnet-50",
                "detector_score": 0.9,
                "crop_box": {"x1": 1, "y1": 2, "x2": 100, "y2": 150},
            },
        ),
    )
    monkeypatch.setattr(
        cc,
        "_predict_with_model",
        lambda _img: {
            "type": "top",
            "pattern": "solid",
            "model_confidence": 0.88,
            "threshold": 0.35,
            "used_fallback": False,
            "fallback_reason": None,
            "top_model_label": "jersey, T-shirt, tee shirt",
        },
    )

    result = cc.classify_clothing(image)

    assert result["type"] == "top"
    assert result["pattern"] == "solid"
    assert "model_confidence" in result
    assert "confidence_threshold" in result
    assert "used_fallback" in result
    assert "fallback_reason" in result
    assert "top_model_label" in result
    assert "region_detection" in result