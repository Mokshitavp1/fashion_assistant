# Import ultralytics YOLO for pose estimation
# Import cv2 and numpy for image processing
from ultralytics import YOLO
import cv2
import numpy as np
from fastapi import HTTPException
from typing import Optional, Dict, Tuple

# Load model once at module level for efficiency
model = YOLO('yolov8n-pose.pt')


def _select_best_person(results, image_bgr) -> Tuple[np.ndarray, Dict]:
    """Select the best detected person based on visibility, keypoint quality, and size.
    
    Args:
        results: YOLO results
        image_bgr: Original image for size reference
        
    Returns:
        tuple: (keypoints_data, quality_info)
        
    Raises:
        HTTPException if no valid person detected
    """
    if len(results) == 0 or results[0].keypoints is None or len(results[0].keypoints.data) == 0:
        raise HTTPException(status_code=400, detail="No person detected in the image.")
    
    keypoints_list = results[0].keypoints.data
    image_height, image_width = image_bgr.shape[:2]
    
    best_score = -1.0
    best_idx = 0
    best_quality = {}
    
    for idx, keypoints_data in enumerate(keypoints_list):
        quality = _assess_pose_quality(keypoints_data, image_width, image_height)
        
        # Composite score: mean confidence, visibility ratio, and size
        composite_score = (
            quality["mean_confidence"] * 0.5 +
            quality["visible_ratio"] * 0.35 +
            min(quality["bbox_area_ratio"], 1.0) * 0.15
        )
        
        if composite_score > best_score:
            best_score = composite_score
            best_idx = idx
            best_quality = quality
    
    if best_score < 0.3:
        raise HTTPException(
            status_code=400,
            detail="Detected person has poor pose quality (score < 0.3). Try a clearer photo.",
        )
    
    return keypoints_list[best_idx], best_quality


def _assess_pose_quality(keypoints_data: np.ndarray, img_width: int, img_height: int) -> Dict:
    """Assess the quality of detected pose for reliability.
    
    Args:
        keypoints_data: YOLO keypoint data [17, 3] (x, y, confidence)
        img_width: Image width in pixels
        img_height: Image height in pixels
        
    Returns:
        dict with visibility and confidence metrics
    """
    # YOLO Pose keypoint indices
    REQUIRED_KEYPOINTS = [5, 6, 11, 12]  # shoulders, hips
    VISIBILITY_KEYPOINTS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
    
    # Check individual keypoint confidences
    keypoint_confs = [float(keypoints_data[i][2]) for i in REQUIRED_KEYPOINTS]
    mean_confidence = np.mean(keypoint_confs) if keypoint_confs else 0.0
    
    # Check how many keypoints are visible (confidence > 0.3)
    visible_count = sum(1 for i in VISIBILITY_KEYPOINTS if float(keypoints_data[i][2]) > 0.3)
    visible_ratio = visible_count / len(VISIBILITY_KEYPOINTS)
    
    # Check if person bounding box is reasonable (not too close to edges)
    xs = [float(keypoints_data[i][0]) for i in VISIBILITY_KEYPOINTS if float(keypoints_data[i][2]) > 0.3]
    ys = [float(keypoints_data[i][1]) for i in VISIBILITY_KEYPOINTS if float(keypoints_data[i][2]) > 0.3]
    
    bbox_area_ratio = 0.0
    if xs and ys:
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        bbox_width = x_max - x_min
        bbox_height = y_max - y_min
        bbox_area = bbox_width * bbox_height
        image_area = img_width * img_height
        bbox_area_ratio = bbox_area / image_area if image_area > 0 else 0.0
        
        # Penalize poses close to image edges (less than 5% margin)
        margin_penalty = 0.0
        if x_min < img_width * 0.05 or x_max > img_width * 0.95:
            margin_penalty += 0.1
        if y_min < img_height * 0.05 or y_max > img_height * 0.95:
            margin_penalty += 0.1
        bbox_area_ratio = max(0, bbox_area_ratio - margin_penalty)
    
    return {
        "mean_confidence": float(mean_confidence),
        "visible_ratio": float(visible_ratio),
        "bbox_area_ratio": float(bbox_area_ratio),
    }


def detect_body_keypoints(image_bgr):
    """
    Detects body keypoints using YOLO pose estimation with quality filtering.
    
    Args:
        image_bgr: OpenCV BGR image
        
    Returns:
        dict: Dictionary containing keypoint coordinates, confidence scores, and quality info
        
    Raises:
        HTTPException: If no valid person is detected
    """
    results = model(image_bgr, verbose=False)
    
    # Select best person based on quality metrics
    keypoints_data, quality_info = _select_best_person(results, image_bgr)
    
    # YOLO Pose keypoint indices:
    # 5: left_shoulder, 6: right_shoulder
    # 1: neck (for waist estimation)
    # 11: left_hip, 12: right_hip
    
    keypoint_dict = {
        "left_shoulder": {
            "x": float(keypoints_data[5][0]),
            "y": float(keypoints_data[5][1]),
            "confidence": float(keypoints_data[5][2])
        },
        "right_shoulder": {
            "x": float(keypoints_data[6][0]),
            "y": float(keypoints_data[6][1]),
            "confidence": float(keypoints_data[6][2])
        },
        "neck": {
            "x": float(keypoints_data[1][0]),
            "y": float(keypoints_data[1][1]),
            "confidence": float(keypoints_data[1][2])
        },
        "left_hip": {
            "x": float(keypoints_data[11][0]),
            "y": float(keypoints_data[11][1]),
            "confidence": float(keypoints_data[11][2])
        },
        "right_hip": {
            "x": float(keypoints_data[12][0]),
            "y": float(keypoints_data[12][1]),
            "confidence": float(keypoints_data[12][2])
        }
    }
    
    # Include pose quality for end-to-end assessment
    keypoint_dict["_quality"] = quality_info
    return keypoint_dict

def calculate_body_measurements(keypoints):
    """
    Calculates body measurements from keypoints with anatomical validity checks.
    
    Args:
        keypoints: Dictionary with shoulder, hip, and neck coordinates
        
    Returns:
        dict: shoulder_width, hip_width, waist_width in pixels, and validity flags
    """
    left_shoulder = np.array([keypoints["left_shoulder"]["x"], keypoints["left_shoulder"]["y"]])
    right_shoulder = np.array([keypoints["right_shoulder"]["x"], keypoints["right_shoulder"]["y"]])
    neck = np.array([keypoints["neck"]["x"], keypoints["neck"]["y"]])
    left_hip = np.array([keypoints["left_hip"]["x"], keypoints["left_hip"]["y"]])
    right_hip = np.array([keypoints["right_hip"]["x"], keypoints["right_hip"]["y"]])
    
    # Calculate widths using Euclidean distance
    shoulder_width = np.linalg.norm(left_shoulder - right_shoulder)
    hip_width = np.linalg.norm(left_hip - right_hip)
    
    # Estimate waist from neck-to-hip midpoint
    hip_midpoint = (left_hip + right_hip) / 2.0
    waist_width = np.linalg.norm(hip_midpoint - neck) * 0.4
    
    # Anatomical validity checks
    avg_width = (shoulder_width + hip_width) / 2
    shoulder_hip_ratio = shoulder_width / max(hip_width, 1.0)
    is_anatomically_valid = (
        0.3 < shoulder_hip_ratio < 3.5 and  # Reasonable ratio
        shoulder_width > 20 and hip_width > 20 and  # Minimum size
        waist_width > 0
    )
    
    return {
        "shoulder_width": float(shoulder_width),
        "hip_width": float(hip_width),
        "waist_width": float(waist_width),
        "is_anatomically_valid": is_anatomically_valid,
    }

def classify_body_shape_from_measurements(measurements):
    """
    Classifies body shape based on measurements with fallback for invalid anatomies.
    
    Args:
        measurements: Dictionary with shoulder_width, hip_width, waist_width
        
    Returns:
        dict: Body shape classification, confidence, and validity info
    """
    if not measurements.get("is_anatomically_valid", False):
        return {
            "shape": "unknown",
            "confidence": 0.3,
            "reason": "anatomically_invalid_or_low_quality",
        }
    
    shoulder_width = measurements["shoulder_width"]
    hip_width = measurements["hip_width"]
    waist_width = measurements["waist_width"]
    
    # Avoid division by zero
    if hip_width == 0:
        return {
            "shape": "unknown",
            "confidence": 0.2,
            "reason": "zero_hip_width",
        }
    
    shoulder_to_hip_ratio = shoulder_width / hip_width
    
    # Calculate if waist is significantly narrower
    avg_width = (shoulder_width + hip_width) / 2
    waist_is_narrow = waist_width < avg_width * 0.75
    
    # Classify with confidence based on measurement consistency
    waist_ratio = waist_width / max(avg_width, 1.0)
    measurement_consistency = 1.0 - abs(waist_ratio - 0.65)  # ~0.65 is typical
    
    shape = "rectangle"
    if shoulder_to_hip_ratio > 1.05:
        shape = "inverted_triangle"
    elif shoulder_to_hip_ratio < 0.95:
        shape = "pear"
    else:
        # Ratio is balanced (0.95 to 1.05)
        if waist_is_narrow:
            shape = "hourglass"
    
    confidence = min(0.95, 0.7 + measurement_consistency * 0.25)
    
    return {
        "shape": shape,
        "confidence": float(confidence),
        "reason": "valid_measurement",
    }

def classify_body_shape_with_bmi(image_bgr, height_cm, weight_kg):
    """
    Classifies body shape considering pose quality, BMI adjustments, and fallbacks.
    
    Args:
        image_bgr: OpenCV BGR image
        height_cm: Height in centimeters
        weight_kg: Weight in kilograms
        
    Returns:
        dict: body_shape, confidence, measurements, bmi, pose_quality, and debug info
    """
    keypoints = detect_body_keypoints(image_bgr)
    pose_quality = keypoints.pop("_quality", {})
    
    measurements = calculate_body_measurements(keypoints)
    shape_result = classify_body_shape_from_measurements(measurements)
    base_shape = shape_result["shape"]
    shape_confidence = shape_result["confidence"]
    
    # Calculate BMI
    bmi = weight_kg / ((height_cm / 100) ** 2)
    
    # BMI-based adjustments (only for confident measurements)
    body_shape = base_shape
    if shape_confidence > 0.6 and bmi > 27:
        if base_shape == "rectangle":
            body_shape = "apple"
        elif base_shape == "pear":
            body_shape = "full_pear"
    
    # Combined confidence: keypoint quality + measurement validity + shape confidence
    kp_conf = np.mean([
        keypoints["left_shoulder"]["confidence"],
        keypoints["right_shoulder"]["confidence"],
        keypoints["left_hip"]["confidence"],
        keypoints["right_hip"]["confidence"],
    ])
    combined_confidence = min(
        0.95,
        kp_conf * 0.5 +
        pose_quality.get("mean_confidence", 0.0) * 0.25 +
        shape_confidence * 0.25
    )
    
    return {
        "body_shape": body_shape,
        "confidence": round(float(combined_confidence), 2),
        "measurements": measurements,
        "bmi": round(bmi, 2),
        "pose_quality": pose_quality,
        "shape_validity": shape_result["reason"],
    }

def calculate_confidence(keypoints, measurements):
    """
    Legacy function for backward compatibility.
    
    Deprecated: Use classify_body_shape_with_bmi result["confidence"] instead.
    """
    return 0.85

# Legacy function for backward compatibility with main.py
def classify_body_shape_simple(image_bgr, height_cm, weight_kg):
    """
    Simplified function that returns just the body shape string.
    Used by main.py for backward compatibility.
    """
    result = classify_body_shape_with_bmi(image_bgr, height_cm, weight_kg)
    return result["body_shape"]

# Legacy function for backward compatibility with main.py
def body_shape_confidence(keypoints=None, measurements=None):
    """
    Returns confidence score. If called without params (legacy), returns default.
    """
    if keypoints is not None and measurements is not None:
        return calculate_confidence(keypoints, measurements)
    return 0.85 