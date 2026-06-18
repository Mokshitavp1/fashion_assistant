"""Persistent model registry, lineage, and experiment tracking.

This module keeps lightweight JSON-based records so retraining events are
versioned, rollbackable, and auditable even without a dedicated ML platform.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

ARTIFACT_DIR = Path(__file__).resolve().parents[1] / "model_artifacts"
REGISTRY_PATH = ARTIFACT_DIR / "model_registry.json"
LINEAGE_PATH = ARTIFACT_DIR / "model_lineage.jsonl"
EXPERIMENTS_PATH = ARTIFACT_DIR / "model_experiments.jsonl"
ROLLBACK_DIR = ARTIFACT_DIR / "rollback_snapshots"


@dataclass
class ModelRecord:
    model_name: str
    version: str
    status: str
    created_at: str
    deployed_at: Optional[str]
    parent_version: Optional[str]
    artifact_path: Optional[str]
    metrics: Dict[str, Any]
    training_summary: Dict[str, Any]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_paths() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    ROLLBACK_DIR.mkdir(parents=True, exist_ok=True)
    if not REGISTRY_PATH.exists():
        REGISTRY_PATH.write_text("{}", encoding="utf-8")


def _load_registry() -> Dict[str, Any]:
    _ensure_paths()
    try:
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.warning("model registry is corrupt; resetting to empty registry")
        return {}


def _save_registry(registry: Dict[str, Any]) -> None:
    _ensure_paths()
    REGISTRY_PATH.write_text(
        json.dumps(registry, indent=2, sort_keys=True), encoding="utf-8"
    )


def _append_jsonl(path: Path, payload: Dict[str, Any]) -> None:
    _ensure_paths()
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, default=str, sort_keys=True))
        handle.write("\n")


def register_model_version(
    model_name: str,
    version: str,
    *,
    parent_version: Optional[str],
    artifact_path: Optional[str],
    training_summary: Dict[str, Any],
    metrics: Dict[str, Any],
    status: str = "candidate",
) -> ModelRecord:
    """Persist a new model version and lineage record."""
    registry = _load_registry()
    record = ModelRecord(
        model_name=model_name,
        version=version,
        status=status,
        created_at=_utc_now(),
        deployed_at=None,
        parent_version=parent_version,
        artifact_path=artifact_path,
        metrics=metrics,
        training_summary=training_summary,
    )

    registry.setdefault(model_name, {})[version] = asdict(record)
    registry.setdefault(model_name, {}).setdefault("current_version", None)
    registry.setdefault(model_name, {}).setdefault("active_version", None)
    _save_registry(registry)

    _append_jsonl(
        LINEAGE_PATH,
        {
            "event": "version_created",
            "created_at": record.created_at,
            "model_name": model_name,
            "version": version,
            "parent_version": parent_version,
            "artifact_path": artifact_path,
            "training_summary": training_summary,
            "metrics": metrics,
        },
    )
    return record


def record_experiment(
    model_name: str,
    control_version: str,
    candidate_version: str,
    metrics: Dict[str, Any],
    decision: str,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Persist an A/B test or shadow test result."""
    payload = {
        "experiment_id": f"{model_name}-{candidate_version}",
        "created_at": _utc_now(),
        "model_name": model_name,
        "control_version": control_version,
        "candidate_version": candidate_version,
        "metrics": metrics,
        "decision": decision,
        "notes": notes,
    }
    _append_jsonl(EXPERIMENTS_PATH, payload)
    return payload


def promote_model_version(model_name: str, version: str) -> Dict[str, Any]:
    """Mark a version as active and store the previous active version for rollback."""
    registry = _load_registry()
    model_bucket = registry.setdefault(model_name, {})
    previous_version = model_bucket.get("active_version")

    if previous_version and previous_version in model_bucket:
        model_bucket[previous_version]["status"] = "previous"
        model_bucket[previous_version]["demoted_at"] = _utc_now()

    if version not in model_bucket:
        raise KeyError(f"Model version not found: {model_name}:{version}")

    model_bucket[version]["status"] = "active"
    model_bucket[version]["deployed_at"] = _utc_now()
    model_bucket["previous_version"] = previous_version
    model_bucket["active_version"] = version
    model_bucket["current_version"] = version
    _save_registry(registry)

    _append_jsonl(
        LINEAGE_PATH,
        {
            "event": "version_promoted",
            "created_at": _utc_now(),
            "model_name": model_name,
            "version": version,
            "previous_version": previous_version,
        },
    )
    return {
        "model_name": model_name,
        "active_version": version,
        "previous_version": previous_version,
    }


def rollback_model_version(model_name: str) -> Dict[str, Any]:
    """Rollback to the most recently active version."""
    registry = _load_registry()
    model_bucket = registry.get(model_name, {})
    active_version = model_bucket.get("active_version")
    previous_version = model_bucket.get("previous_version")

    if not previous_version:
        raise KeyError(f"No rollback target available for {model_name}")

    if active_version and active_version in model_bucket:
        model_bucket[active_version]["status"] = "rolled_back"
        model_bucket[active_version]["rolled_back_at"] = _utc_now()

    model_bucket[previous_version]["status"] = "active"
    model_bucket[previous_version]["deployed_at"] = _utc_now()
    model_bucket["active_version"] = previous_version
    model_bucket["current_version"] = previous_version
    model_bucket["previous_version"] = active_version
    _save_registry(registry)

    rollback_snapshot = {
        "created_at": _utc_now(),
        "model_name": model_name,
        "from_version": active_version,
        "to_version": previous_version,
    }
    _append_jsonl(LINEAGE_PATH, {"event": "rollback", **rollback_snapshot})
    _append_jsonl(
        ROLLBACK_DIR / f"{model_name}.jsonl",
        rollback_snapshot,
    )
    return rollback_snapshot


def get_active_model_version(model_name: str) -> Optional[str]:
    registry = _load_registry()
    return registry.get(model_name, {}).get("active_version")


def get_model_history(model_name: str) -> List[Dict[str, Any]]:
    registry = _load_registry()
    model_bucket = registry.get(model_name, {})
    return [value for key, value in model_bucket.items() if isinstance(value, dict)]
