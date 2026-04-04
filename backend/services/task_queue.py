import os
from typing import Any, Dict, Optional

from celery import Celery
from celery.result import AsyncResult
from celery.schedules import crontab
from redis import Redis


REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
INFERENCE_QUEUE_NAME = os.getenv("INFERENCE_QUEUE_NAME", "inference")
INFERENCE_JOB_TIMEOUT = int(os.getenv("INFERENCE_JOB_TIMEOUT", "300"))
INFERENCE_RESULT_TTL = int(os.getenv("INFERENCE_RESULT_TTL", "3600"))

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

celery_app = Celery(
    "fashion_app_tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["worker_tasks"],
)
celery_app.conf.update(
    task_default_queue=INFERENCE_QUEUE_NAME,
    task_track_started=True,
    task_time_limit=INFERENCE_JOB_TIMEOUT,
    result_expires=INFERENCE_RESULT_TTL,
    # Celery Beat schedule for periodic tasks
    beat_schedule={
        'compute-metrics-daily': {
            'task': 'worker_tasks.compute_metrics',
            'schedule': crontab(hour=2, minute=0),  # 2 AM UTC daily
            'args': (30,),  # 30 day lookback
        },
        'retrain-models-weekly': {
            'task': 'worker_tasks.retrain_all_models',
            'schedule': crontab(day_of_week=0, hour=3, minute=0),  # Sundays 3 AM UTC
            'args': (30,),  # 30 day lookback
        },
    },
)



def get_redis_connection() -> Redis:
    return Redis.from_url(REDIS_URL)


def _owner_key(job_id: str) -> str:
    return f"job_owner:{job_id}"


def _type_key(job_id: str) -> str:
    return f"job_type:{job_id}"


def enqueue_inference_job(
    task_name: str,
    kwargs: Dict[str, Any],
    user_id: int,
    job_type: str,
) -> str:
    task = celery_app.send_task(task_name, kwargs=kwargs, queue=INFERENCE_QUEUE_NAME)
    redis_conn = get_redis_connection()
    redis_conn.setex(_owner_key(task.id), INFERENCE_RESULT_TTL, str(user_id))
    redis_conn.setex(_type_key(task.id), INFERENCE_RESULT_TTL, job_type)
    return task.id


def fetch_job(job_id: str) -> AsyncResult:
    return AsyncResult(job_id, app=celery_app)


def get_job_owner(job_id: str) -> Optional[int]:
    raw = get_redis_connection().get(_owner_key(job_id))
    if not raw:
        return None
    try:
        return int(raw.decode("utf-8"))
    except (TypeError, ValueError, AttributeError):
        return None


def get_job_type(job_id: str) -> Optional[str]:
    raw = get_redis_connection().get(_type_key(job_id))
    if not raw:
        return None
    try:
        return raw.decode("utf-8")
    except Exception:
        return None
