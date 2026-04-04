# Import necessary libraries
import cv2
import numpy as np
from sklearn.cluster import KMeans
from collections import Counter
import os
from functools import lru_cache
from typing import Optional, Tuple

from PIL import Image

try:
    from transformers import pipeline
except Exception:  # pragma: no cover - runtime dependency fallback
    pipeline = None

def extract_clothing_colors(image: cv2.Mat, n_colors=3):
    """
    Extract dominant colors from clothing image using k-means clustering.
    
    Args:
        image: OpenCV BGR image
        n_colors: Number of dominant colors to extract
        
    Returns:
        list: List of RGB color tuples sorted by dominance
    """
    # Resize image for faster processing
    image_resized = cv2.resize(image, (150, 150))

    # Convert to HSV so we can remove likely background pixels (very bright/low-saturation).
    hsv = cv2.cvtColor(image_resized, cv2.COLOR_BGR2HSV)
    sat = hsv[:, :, 1]
    val = hsv[:, :, 2]

    # Also suppress near-white pixels explicitly (common studio/ecommerce backgrounds).
    bgr = image_resized
    b = bgr[:, :, 0]
    g = bgr[:, :, 1]
    r = bgr[:, :, 2]
    near_white = (
        (r > 210) & (g > 210) & (b > 210) &
        (sat < 40) &
        (np.abs(r.astype(np.int16) - g.astype(np.int16)) < 25) &
        (np.abs(g.astype(np.int16) - b.astype(np.int16)) < 25)
    )

    # Keep pixels that are not washed-out background and also keep darker neutrals.
    # This avoids repeatedly classifying white walls/background as clothing color.
    foreground_mask = ((sat >= 35) | (val <= 200)) & (~near_white)

    pixels_bgr = image_resized[foreground_mask]

    # If masking becomes too strict, fallback to a center crop (often where clothing is).
    if pixels_bgr.shape[0] < 400:
        h, w = image_resized.shape[:2]
        y1, y2 = int(h * 0.2), int(h * 0.85)
        x1, x2 = int(w * 0.2), int(w * 0.85)
        center_crop = image_resized[y1:y2, x1:x2]

        # Re-apply the white suppression on the center crop.
        center_hsv = cv2.cvtColor(center_crop, cv2.COLOR_BGR2HSV)
        center_sat = center_hsv[:, :, 1]
        center_val = center_hsv[:, :, 2]
        cb = center_crop[:, :, 0]
        cg = center_crop[:, :, 1]
        cr = center_crop[:, :, 2]
        center_near_white = (
            (cr > 210) & (cg > 210) & (cb > 210) &
            (center_sat < 40) &
            (np.abs(cr.astype(np.int16) - cg.astype(np.int16)) < 25) &
            (np.abs(cg.astype(np.int16) - cb.astype(np.int16)) < 25)
        )
        center_mask = ((center_sat >= 30) | (center_val <= 190)) & (~center_near_white)
        filtered_center = center_crop[center_mask]
        pixels_bgr = filtered_center if filtered_center.shape[0] >= 120 else center_crop.reshape((-1, 3))

    if pixels_bgr.shape[0] == 0:
        pixels_bgr = image_resized.reshape((-1, 3))

    pixels = np.float32(pixels_bgr)

    # KMeans cannot have more clusters than samples.
    clusters = max(1, min(n_colors, len(pixels)))

    # Apply k-means clustering
    kmeans = KMeans(n_clusters=clusters, n_init=10, random_state=42)
    kmeans.fit(pixels)
    
    # Get the colors and their counts
    colors = kmeans.cluster_centers_
    labels = kmeans.labels_
    counts = Counter(labels)
    
    # Sort colors by frequency
    sorted_colors = [colors[i] for i, count in counts.most_common(clusters)]
    
    # Convert BGR to RGB
    rgb_colors = []
    for color in sorted_colors:
        # Convert from BGR to RGB and round to integers
        rgb = (int(color[2]), int(color[1]), int(color[0]))
        rgb_colors.append(rgb)
    
    return rgb_colors

def rgb_to_color_name(rgb: tuple) -> str:
    """
    Map RGB values to basic color names.
    
    Args:
        rgb: RGB color tuple (r, g, b)
        
    Returns:
        str: Color name
    """
    r, g, b = [int(max(0, min(255, c))) for c in rgb]

    # Use HSV to classify hues more robustly across lighting/background variance.
    hsv = cv2.cvtColor(np.uint8([[[r, g, b]]]), cv2.COLOR_RGB2HSV)[0, 0]
    h, s, v = int(hsv[0]), int(hsv[1]), int(hsv[2])

    # Rescue low-saturation denim/faded blues before neutral bucketing.
    if (b - r) >= 22 and (b - g) >= 12 and v >= 70:
        return "blue"

    # Neutral shades first.
    if v <= 55:
        return "black"
    if s <= 28:
        if v >= 220:
            return "white"
        return "gray"

    # Hue buckets (OpenCV hue range: 0-179).
    if h <= 8 or h >= 170:
        return "red"
    if 9 <= h <= 20:
        # Distinguish brown from orange based on brightness.
        return "brown" if v < 150 else "orange"
    if 21 <= h <= 33:
        return "yellow"
    if 34 <= h <= 84:
        return "green"
    if 85 <= h <= 100:
        return "teal"
    if 101 <= h <= 130:
        return "blue"
    if 131 <= h <= 155:
        return "purple"
    if 156 <= h <= 169:
        return "pink"

    return "multicolor"

@lru_cache(maxsize=1)
def _get_image_classifier():
    """Load and cache a local Hugging Face image classification pipeline."""
    if pipeline is None:
        return None

    # Defaults to a small ViT model that runs locally.
    model_id = os.getenv("HF_CLOTHING_MODEL", "google/vit-base-patch16-224")
    try:
        return pipeline("image-classification", model=model_id)
    except Exception:
        return None


@lru_cache(maxsize=1)
def _get_object_detector():
    """Load and cache a local Hugging Face object detection pipeline."""
    if pipeline is None:
        return None

    # COCO-pretrained detector; typically provides person boxes used for clothing crop.
    detector_id = os.getenv("HF_CLOTHING_DETECTOR_MODEL", "facebook/detr-resnet-50")
    try:
        return pipeline("object-detection", model=detector_id)
    except Exception:
        return None


def _cv2_to_pil(image: cv2.Mat) -> Image.Image:
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)


def _clip_box(
    box: Tuple[int, int, int, int], width: int, height: int
) -> Optional[Tuple[int, int, int, int]]:
    x1, y1, x2, y2 = box
    x1 = max(0, min(x1, width - 1))
    y1 = max(0, min(y1, height - 1))
    x2 = max(0, min(x2, width))
    y2 = max(0, min(y2, height))
    if x2 - x1 < 10 or y2 - y1 < 10:
        return None
    return x1, y1, x2, y2


def _torso_from_person_box(
    person_box: Tuple[int, int, int, int], width: int, height: int
) -> Optional[Tuple[int, int, int, int]]:
    """Derive a torso-focused crop from a detected person box."""
    x1, y1, x2, y2 = person_box
    w = max(x2 - x1, 1)
    h = max(y2 - y1, 1)

    # Focus on central torso where tops/outerwear are most visible.
    tx1 = int(x1 + 0.10 * w)
    tx2 = int(x2 - 0.10 * w)
    ty1 = int(y1 + 0.20 * h)
    ty2 = int(y1 + 0.72 * h)
    return _clip_box((tx1, ty1, tx2, ty2), width, height)


def _extract_clothing_region(image: cv2.Mat) -> tuple[cv2.Mat, dict]:
    """Crop to a likely clothing region using local object detection.

    Falls back to the original image when detection is unavailable or uncertain.
    """
    debug = {
        "used_crop": False,
        "detector_model": os.getenv("HF_CLOTHING_DETECTOR_MODEL", "facebook/detr-resnet-50"),
        "detector_score": None,
        "crop_box": None,
    }

    detector = _get_object_detector()
    if detector is None:
        return image, debug

    height, width = image.shape[:2]
    try:
        detections = detector(_cv2_to_pil(image), threshold=0.25)
    except Exception:
        return image, debug

    best_person_box = None
    best_person_score = -1.0

    # Prefer the highest-confidence person detection.
    for det in detections:
        label = str(det.get("label", "")).lower()
        if "person" not in label:
            continue
        score = float(det.get("score", 0.0))
        raw_box = det.get("box", {})
        x1 = int(raw_box.get("xmin", 0))
        y1 = int(raw_box.get("ymin", 0))
        x2 = int(raw_box.get("xmax", 0))
        y2 = int(raw_box.get("ymax", 0))
        clipped = _clip_box((x1, y1, x2, y2), width, height)
        if clipped is None:
            continue
        if score > best_person_score:
            best_person_score = score
            best_person_box = clipped

    if best_person_box is None:
        return image, debug

    torso_box = _torso_from_person_box(best_person_box, width, height)
    if torso_box is None:
        return image, debug

    x1, y1, x2, y2 = torso_box
    debug["used_crop"] = True
    debug["detector_score"] = round(best_person_score, 4)
    debug["crop_box"] = {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
    return image[y1:y2, x1:x2], debug


def _map_label_to_type(label: str) -> str:
    text = label.lower()
    type_keywords = {
        "dress": ["dress", "gown", "sundress"],
        "top": ["shirt", "t-shirt", "jersey", "blouse", "sweater", "cardigan", "tank"],
        "jeans": ["jean", "denim"],
        "bottom": ["trouser", "pants", "shorts", "skirt", "leggings"],
        "outerwear": ["jacket", "coat", "poncho", "hoodie", "parka", "cloak"],
    }
    for mapped, keywords in type_keywords.items():
        if any(keyword in text for keyword in keywords):
            return mapped
    return "other"


def _map_label_to_pattern(label: str) -> str:
    text = label.lower()
    if any(k in text for k in ["stripe", "striped"]):
        return "striped"
    if any(k in text for k in ["dot", "dotted", "polka"]):
        return "dotted"
    if any(k in text for k in ["floral", "flower"]):
        return "floral"
    if any(k in text for k in ["plaid", "check", "checked"]):
        return "plaid"
    if any(k in text for k in ["texture", "woven", "knit", "ribbed"]):
        return "textured"
    return "solid"


def _detect_pattern_heuristic(image: cv2.Mat) -> str:
    """Fallback pattern detector when model confidence is low."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)

    edge_pixels = np.sum(edges > 0)
    total_pixels = edges.shape[0] * edges.shape[1]
    edge_ratio = edge_pixels / max(total_pixels, 1)

    lines = cv2.HoughLinesP(
        edges,
        1,
        np.pi / 180,
        threshold=50,
        minLineLength=30,
        maxLineGap=10,
    )

    if edge_ratio < 0.05:
        return "solid"
    if lines is not None and len(lines) > 10:
        return "striped"
    if edge_ratio > 0.15:
        return "floral"
    if 0.05 <= edge_ratio <= 0.15:
        return "textured"
    return "other"


def _detect_clothing_type_simple(image: cv2.Mat) -> str:
    """Fallback type detector based on aspect ratio."""
    height, width = image.shape[:2]
    if width <= 0:
        return "other"
    aspect_ratio = height / width

    if aspect_ratio > 1.3:
        return "dress"
    if 0.8 < aspect_ratio <= 1.3:
        return "top"
    if aspect_ratio <= 0.8:
        return "bottom"
    return "other"


def _predict_with_model(image: cv2.Mat) -> dict:
    """Return confidence-aware classification with fallback metadata."""
    min_conf = float(os.getenv("HF_CLASSIFICATION_MIN_CONF", "0.35"))
    result = {
        "type": "other",
        "pattern": "solid",
        "model_confidence": 0.0,
        "threshold": min_conf,
        "used_fallback": False,
        "fallback_reason": None,
        "top_model_label": None,
    }

    classifier = _get_image_classifier()
    if classifier is None:
        result["used_fallback"] = True
        result["fallback_reason"] = "classifier_unavailable"
        result["type"] = _detect_clothing_type_simple(image)
        result["pattern"] = _detect_pattern_heuristic(image)
        return result

    try:
        predictions = classifier(_cv2_to_pil(image), top_k=5)
    except Exception:
        result["used_fallback"] = True
        result["fallback_reason"] = "classifier_error"
        result["type"] = _detect_clothing_type_simple(image)
        result["pattern"] = _detect_pattern_heuristic(image)
        return result

    if not predictions:
        result["used_fallback"] = True
        result["fallback_reason"] = "no_predictions"
        result["type"] = _detect_clothing_type_simple(image)
        result["pattern"] = _detect_pattern_heuristic(image)
        return result

    top_pred = predictions[0]
    top_conf = float(top_pred.get("score", 0.0))
    result["model_confidence"] = top_conf
    result["top_model_label"] = str(top_pred.get("label", ""))

    predicted_type = "other"
    predicted_pattern = "solid"
    for pred in predictions:
        label = pred.get("label", "")
        mapped_type = _map_label_to_type(label)
        if mapped_type != "other" and predicted_type == "other":
            predicted_type = mapped_type

        mapped_pattern = _map_label_to_pattern(label)
        if mapped_pattern != "solid":
            predicted_pattern = mapped_pattern

    if top_conf < min_conf:
        result["used_fallback"] = True
        result["fallback_reason"] = "low_confidence"
        result["type"] = _detect_clothing_type_simple(image)
        result["pattern"] = _detect_pattern_heuristic(image)
        return result

    if predicted_type == "other":
        result["used_fallback"] = True
        result["fallback_reason"] = "unknown_label_mapping"
        result["type"] = _detect_clothing_type_simple(image)
        result["pattern"] = (
            predicted_pattern
            if predicted_pattern != "solid"
            else _detect_pattern_heuristic(image)
        )
        return result

    result["type"] = predicted_type
    result["pattern"] = predicted_pattern
    return result

def _is_probably_denim(rgb: tuple) -> bool:
    """Heuristic: blue-dominant and moderate brightness implies denim-like color."""
    if not rgb or len(rgb) != 3:
        return False
    r, g, b = rgb
    # require blue noticeably higher than red/green and reasonably bright
    return (b > r + 30 and b > g + 30 and b > 80)

def classify_clothing(image: cv2.Mat) -> dict:
    """
    Classify clothing item including type, colors, and pattern.
    """
    # Crop to clothing-focused region first to reduce background noise.
    clothing_region, region_debug = _extract_clothing_region(image)

    # Predict clothing type and pattern from a local pretrained vision model.
    model_result = _predict_with_model(clothing_region)
    model_type = model_result["type"]
    model_pattern = model_result["pattern"]
    
    # Extract dominant colors
    colors = extract_clothing_colors(clothing_region, n_colors=3)
    
    # Get color names
    color_primary = rgb_to_color_name(colors[0]) if colors else "multicolor"
    color_secondary = rgb_to_color_name(colors[1]) if len(colors) > 1 else None
    
    # Keep denim color heuristic to refine generic bottom predictions.
    mapped_type = model_type
    if mapped_type == "bottom" and colors and _is_probably_denim(colors[0]):
        mapped_type = "jeans"
    
    return {
        "type": mapped_type,
        "color_primary": color_primary,
        "color_secondary": color_secondary if color_secondary != color_primary else None,
        "pattern": model_pattern,
        "rgb_colors": colors,
        "model_confidence": model_result["model_confidence"],
        "confidence_threshold": model_result["threshold"],
        "used_fallback": model_result["used_fallback"],
        "fallback_reason": model_result["fallback_reason"],
        "top_model_label": model_result["top_model_label"],
        "region_detection": region_debug,
    }