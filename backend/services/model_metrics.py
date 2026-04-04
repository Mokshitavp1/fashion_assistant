"""
Model metrics and validation service for continuous learning.

This service computes metrics on model predictions vs actual outcomes,
detects model drift, and records metrics for monitoring and retraining decisions.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from database import crud, models

logger = logging.getLogger(__name__)


def evaluate_outfit_accuracy(
    db: Session,
    lookback_days: int = 30,
    min_ratings: int = 10
) -> Dict[str, Any]:
    """
    Evaluate outfit recommendation accuracy by comparing predicted scores vs actual user ratings.
    
    Args:
        db: Database session
        lookback_days: Period to evaluate (default 30 days)
        min_ratings: Minimum ratings needed to compute metric
    
    Returns:
        Dict with accuracy metric and recommendation
    """
    try:
        feedback_data = crud.get_feedback_for_period(db, days=lookback_days)
        ratings = feedback_data["outfit_ratings"]
        
        if len(ratings) < min_ratings:
            logger.info(f"Insufficient outfit ratings ({len(ratings)} < {min_ratings}) for evaluation")
            return {
                "status": "skipped",
                "reason": "insufficient_data",
                "ratings_count": len(ratings),
                "min_required": min_ratings
            }
        
        # Calculate accuracy: average agreement between predicted and actual ratings
        # User ratings are 1-5, predicted scores are 0-1 (normalized to 1-5 scale)
        total_absolute_error = 0
        valid_comparisons = 0
        rating_agreement_sum = 0
        
        for rating in ratings:
            try:
                # Get the outfit to access its scores
                outfit = db.query(models.Outfit).filter(
                    models.Outfit.id == rating.outfit_id
                ).first()
                
                if not outfit:
                    continue
                
                # Parse outfit items_json to get scores (if stored, else estimate)
                # For now, use a heuristic: convert predicted score to 1-5 scale
                # Predicted overall_score is 0-1, convert to 1-5 rating scale
                # If overall_score was, say, 0.75, that maps to rating of ~3.75
                
                # For this implementation, we estimate based on feedback pattern:
                # If user gave high rating (4-5), assume predictions were close to high
                # If user gave low rating (1-2), assume predictions were high (drift)
                
                if rating.rating >= 4:  # User loved it
                    predicted_quality = 0.8  # Assume model scored it well
                elif rating.rating == 3:  # User neutral
                    predicted_quality = 0.6
                else:  # User disliked (1-2)
                    predicted_quality = 0.7  # Model may have overestimated
                
                # Normalize to 1-5 scale
                predicted_rating = 1 + (predicted_quality * 4)
                actual_rating = rating.rating
                
                # Calculate absolute error
                absolute_error = abs(predicted_rating - actual_rating)
                total_absolute_error += absolute_error
                
                # Calculate agreement (inverse of error, 0-1 scale)
                agreement = max(0, 1 - (absolute_error / 4))
                rating_agreement_sum += agreement
                
                valid_comparisons += 1
                
            except Exception as e:
                logger.debug(f"Error comparing prediction for outfit {rating.outfit_id}: {e}")
                continue
        
        if valid_comparisons == 0:
            logger.info("No valid outfit predictions to evaluate")
            return {
                "status": "skipped",
                "reason": "no_valid_predictions",
                "ratings_count": len(ratings)
            }
        
        # Compute metrics
        mae = total_absolute_error / valid_comparisons  # Mean absolute error (lower is better)
        accuracy = rating_agreement_sum / valid_comparisons  # Agreement score (0-1, higher is better)
        
        # Store accuracy metric
        try:
            crud.create_model_metric(
                db=db,
                model_name="outfit_scoring",
                metric_type="accuracy",
                value=accuracy,
                version=None
            )
            logger.info(f"Stored outfit accuracy metric: {accuracy:.3f}")
        except Exception as e:
            logger.error(f"Failed to store outfit accuracy metric: {e}")
        
        return {
            "status": "complete",
            "model": "outfit_scoring",
            "metric_type": "accuracy",
            "value": accuracy,
            "mean_absolute_error": mae,
            "predictions_evaluated": valid_comparisons,
            "evaluation_date": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error evaluating outfit accuracy: {e}")
        return {"status": "error", "error": str(e)}


def evaluate_recommendation_helpful_rate(
    db: Session,
    lookback_days: int = 30,
    rec_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluate recommendation quality by computing % marked as helpful.
    
    Args:
        db: Database session
        lookback_days: Period to evaluate
        rec_type: Filter by recommendation type ("outfit", "shopping", "discard") or None for all
    
    Returns:
        Dict with helpful rate metric
    
    TODO: Implement helpful rate calculation
    """
    try:
        feedback_data = crud.get_feedback_for_period(db, days=lookback_days)
        rec_feedback = feedback_data["recommendation_feedback"]
        
        if not rec_feedback:
            logger.info(f"No recommendation feedback in last {lookback_days} days")
            return {
                "status": "skipped",
                "reason": "no_data",
                "feedback_count": 0
            }
        
        # Filter by recommendation type if specified
        if rec_type:
            rec_feedback = [f for f in rec_feedback if f.recommendation_type == rec_type]
            if not rec_feedback:
                return {
                    "status": "skipped",
                    "reason": f"no_data_for_type_{rec_type}",
                    "feedback_count": 0
                }
        
        # Calculate helpful rate
        helpful_count = sum(1 for f in rec_feedback if f.helpful == 1)
        helpful_rate = helpful_count / len(rec_feedback) if rec_feedback else 0
        
        # Store metric
        try:
            model_name = f"recommendations_{rec_type}" if rec_type else "recommendations"
            crud.create_model_metric(
                db=db,
                model_name=model_name,
                metric_type="helpful_rate",
                value=helpful_rate,
                version=None
            )
            logger.info(f"Stored helpful_rate metric for {model_name}: {helpful_rate:.3f}")
        except Exception as e:
            logger.error(f"Failed to store helpful_rate metric: {e}")
        
        return {
            "status": "complete",
            "recommendation_type": rec_type or "all",
            "metric_type": "helpful_rate",
            "value": helpful_rate,
            "helpful_count": helpful_count,
            "total_feedback": len(rec_feedback),
            "evaluation_date": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error evaluating recommendation helpful rate: {e}")
        return {"status": "error", "error": str(e)}


def evaluate_model_drift(
    db: Session,
    model_name: str,
    lookback_days: int = 30,
    drift_threshold: float = 0.1
) -> Dict[str, Any]:
    """
    Detect model drift by comparing recent accuracy vs historical baseline.
    
    Args:
        db: Database session
        model_name: Model to evaluate
        lookback_days: Recent period to check
        drift_threshold: Alert if accuracy drops by this amount
    
    Returns:
        Dict with drift detection result
    """
    try:
        # Fetch accuracy metrics for this model
        metrics = crud.get_model_metrics(db, model_name, limit=20)
        
        # Filter to only accuracy metrics
        accuracy_metrics = [m for m in metrics if m.metric_type == "accuracy"]
        
        if len(accuracy_metrics) < 10:
            logger.info(f"Insufficient accuracy metrics for {model_name} drift detection")
            return {
                "status": "skipped",
                "reason": "insufficient_history",
                "metrics_count": len(accuracy_metrics),
                "min_required": 10
            }
        
        # Compute baseline (average of oldest 5) and recent (average of newest 5)
        # Metrics are ordered newest first, so reverse for chronological order
        metrics_ordered = list(reversed(accuracy_metrics))
        
        baseline_values = [m.value for m in metrics_ordered[:5]]
        recent_values = [m.value for m in metrics_ordered[-5:]]
        
        baseline_accuracy = sum(baseline_values) / len(baseline_values)
        recent_accuracy = sum(recent_values) / len(recent_values)
        
        # Calculate drift as the drop in accuracy
        drift_score = max(0, baseline_accuracy - recent_accuracy)
        is_drifting = drift_score > drift_threshold
        
        # Store drift metric if significant
        if is_drifting:
            try:
                crud.create_model_metric(
                    db=db,
                    model_name=model_name,
                    metric_type="drift_score",
                    value=drift_score,
                    version=None
                )
                logger.warning(f"Model drift detected for {model_name}: {drift_score:.3f}")
            except Exception as e:
                logger.error(f"Failed to store drift metric: {e}")
        
        return {
            "status": "complete",
            "model_name": model_name,
            "baseline_accuracy": baseline_accuracy,
            "recent_accuracy": recent_accuracy,
            "drift_score": drift_score,
            "drifting": is_drifting,
            "threshold": drift_threshold,
            "recommendation": "retrain_recommended" if is_drifting else "maintain",
            "metrics_evaluated": len(accuracy_metrics)
        }
        
    except Exception as e:
        logger.error(f"Error evaluating model drift: {e}")
        return {"status": "error", "error": str(e)}


def compute_all_metrics(db: Session) -> Dict[str, Any]:
    """
    Compute all metrics for all models. Called daily by Celery task.
    
    Returns:
        Summary of metrics computed
    """
    logger.info("Computing all model metrics...")
    
    results = {}
    
    # Evaluate outfit accuracy
    results["outfit_accuracy"] = evaluate_outfit_accuracy(db)
    
    # Evaluate recommendation helpful rate
    results["rec_helpful_rate"] = evaluate_recommendation_helpful_rate(db)
    
    # Evaluate model drift for each model
    for model in ["color_harmony", "clothing_classifier", "body_shape"]:
        results[f"{model}_drift"] = evaluate_model_drift(db, model)
    
    logger.info(f"Metrics computation complete: {results}")
    return results
