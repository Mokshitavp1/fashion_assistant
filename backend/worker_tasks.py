import os
import base64
from typing import Any, Dict
from pathlib import Path

import cv2
import numpy as np
from dotenv import load_dotenv

from database.database import SessionLocal
from database import crud
from services.color_analysis import (
    detect_face_region,
    extract_dominant_skin_color,
    classify_undertone,
)
from services.body_shape import classify_body_shape_with_bmi
from services.clothing_classifier import classify_clothing
from services.secure_image_storage import store_encrypted_image
from services.task_queue import celery_app


load_dotenv(Path(__file__).resolve().with_name(".env"))
SECRET_KEY = os.getenv("SECRET_KEY", "")


def _to_json_compatible(value: Any):
    if isinstance(value, dict):
        return {k: _to_json_compatible(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_json_compatible(v) for v in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def _decode_image_payload(image_b64: str) -> bytes:
    try:
        return base64.b64decode(image_b64.encode("utf-8"), validate=True)
    except Exception as exc:
        raise ValueError("Invalid image payload") from exc


@celery_app.task(name="worker_tasks.process_analyze_job")
def process_analyze_job(
    user_id: int,
    height: float,
    weight: float,
    image_b64: str,
) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        image_bytes = _decode_image_payload(image_b64)
        user = crud.get_user_by_id(db, user_id)
        if not user:
            raise ValueError("User not found")

        np_array = np.frombuffer(image_bytes, np.uint8)
        image_array = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
        if image_array is None:
            raise ValueError("Invalid image file")

        image_id, image_reference = store_encrypted_image(
            image_bytes=image_bytes,
            user_id=user_id,
            secret_key=SECRET_KEY,
            image_type="profile",
            metadata={"width": int(image_array.shape[1]), "height": int(image_array.shape[0])},
        )

        face_region = detect_face_region(image_array)
        dominant_color = extract_dominant_skin_color(face_region)
        undertone = classify_undertone(dominant_color)

        body_analysis = classify_body_shape_with_bmi(image_array, height, weight)

        updated_user = crud.update_user_analysis(
            db=db,
            user_id=user_id,
            height=height,
            weight=weight,
            body_shape=body_analysis["body_shape"],
            undertone=undertone,
            bmi=body_analysis["bmi"],
        )
        updated_user.profile_image_path = image_reference
        db.commit()

        return {
            "message": "Analysis complete and saved",
            "user_id": user_id,
            "dominant_skin_color_rgb": _to_json_compatible(dominant_color),
            "undertone": undertone,
            "body_shape": body_analysis["body_shape"],
            "body_shape_confidence": _to_json_compatible(body_analysis["confidence"]),
            "measurements": _to_json_compatible(body_analysis["measurements"]),
            "bmi": _to_json_compatible(body_analysis["bmi"]),
            "height": height,
            "weight": weight,
            "profile_image_id": image_id,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@celery_app.task(name="worker_tasks.process_wardrobe_add_job")
def process_wardrobe_add_job(
    user_id: int,
    category: str,
    season: str,
    image_b64: str,
) -> Dict[str, Any]:
    def normalize_type_with_category(predicted_type: str, selected_category: str) -> str:
        predicted = (predicted_type or "other").strip().lower()
        category_norm = (selected_category or "").strip().lower()

        if category_norm == "bottom" and predicted in {"top", "outerwear", "dress"}:
            return "bottom"
        if category_norm == "top" and predicted in {"bottom", "jeans", "dress"}:
            return "top"
        if category_norm == "dress":
            return "dress"
        if category_norm == "shoes":
            return "shoes"
        if category_norm == "accessories":
            return "accessories"
        return predicted

    db = SessionLocal()
    try:
        image_bytes = _decode_image_payload(image_b64)
        user = crud.get_user_by_id(db, user_id)
        if not user:
            raise ValueError("User not found")

        np_array = np.frombuffer(image_bytes, np.uint8)
        image_array = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
        if image_array is None:
            raise ValueError("Invalid image file")

        image_id, image_reference = store_encrypted_image(
            image_bytes=image_bytes,
            user_id=user_id,
            secret_key=SECRET_KEY,
            image_type="wardrobe",
            metadata={"width": int(image_array.shape[1]), "height": int(image_array.shape[0])},
        )

        classification = classify_clothing(image_array)
        normalized_type = normalize_type_with_category(classification.get("type"), category)

        wardrobe_item = crud.create_wardrobe_item(
            db=db,
            user_id=user_id,
            image_path=image_reference,
            clothing_type=normalized_type,
            color_primary=classification["color_primary"],
            color_secondary=classification["color_secondary"],
            pattern=classification["pattern"],
            season=season or "all",
            category=category,
        )

        db.commit()
        db.refresh(wardrobe_item)

        return {
            "message": "Clothing item added to wardrobe",
            "item": {
                "id": getattr(wardrobe_item, "id", None),
                "type": getattr(wardrobe_item, "clothing_type", None),
                "category": getattr(wardrobe_item, "category", None),
                "color_primary": getattr(wardrobe_item, "color_primary", None),
                "color_secondary": getattr(wardrobe_item, "color_secondary", None),
                "pattern": getattr(wardrobe_item, "pattern", None),
                "season": getattr(wardrobe_item, "season", None),
                "image_id": image_id,
                "rgb_colors": classification.get("rgb_colors"),
                "model_confidence": classification.get("model_confidence"),
                "confidence_threshold": classification.get("confidence_threshold"),
                "used_fallback": classification.get("used_fallback"),
                "fallback_reason": classification.get("fallback_reason"),
                "top_model_label": classification.get("top_model_label"),
                "region_detection": classification.get("region_detection"),
            },
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ============ LEARNING SYSTEM TASKS ============

@celery_app.task(name="worker_tasks.compute_metrics")
def compute_metrics(lookback_days: int = 30) -> Dict[str, Any]:
    """
    Compute all model performance metrics. Called daily by Celery beat.
    
    Args:
        lookback_days: Lookback period for feedback analysis
    
    Returns:
        Summary of metrics computed
    """
    from services import model_metrics
    
    db = SessionLocal()
    try:
        print(f"[Celery] Starting metrics computation (lookback={lookback_days} days)...")
        result = model_metrics.compute_all_metrics(db)
        print(f"[Celery] Metrics computation complete: {result}")
        return result
    except Exception as e:
        print(f"[Celery] Error computing metrics: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


@celery_app.task(name="worker_tasks.retrain_all_models")
def retrain_all_models_task(lookback_days: int = 30) -> Dict[str, Any]:
    """
    Full model retraining pipeline. Called weekly by Celery beat.
    
    Args:
        lookback_days: Feedback lookback period
    
    Returns:
        Retraining result summary
    """
    from services import model_retrainer
    
    db = SessionLocal()
    try:
        print(f"[Celery] Starting model retraining (lookback={lookback_days} days)...")
        result = model_retrainer.retrain_all_models(db, lookback_days=lookback_days)
        print(f"[Celery] Retraining complete: {result}")
        return result
    except Exception as e:
        print(f"[Celery] Error during retraining: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        db.close()
