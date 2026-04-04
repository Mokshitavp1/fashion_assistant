import asyncio
import json
import os
import statistics
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Tuple

import httpx

import main
from database.database import SessionLocal
from database import models


BASE_URL = os.getenv("LOAD_BASE_URL", "http://127.0.0.1:8000")
USERS = int(os.getenv("LOAD_USERS", "8"))
ANALYZE_ROUNDS = int(os.getenv("LOAD_ANALYZE_ROUNDS", "1"))
WARDROBE_ROUNDS = int(os.getenv("LOAD_WARDROBE_ROUNDS", "2"))
MAX_INFLIGHT = int(os.getenv("LOAD_MAX_INFLIGHT", "8"))
REQUEST_TIMEOUT_SECONDS = int(os.getenv("LOAD_TIMEOUT_SECONDS", "180"))

ANALYZE_IMAGE_PATH = Path(os.getenv("LOAD_ANALYZE_IMAGE", "profile.jpg"))
WARDROBE_IMAGE_PATH = Path(os.getenv("LOAD_WARDROBE_IMAGE", "test_clothing.jpg"))


@dataclass
class RequestResult:
    endpoint: str
    status_code: int
    elapsed_ms: float
    ok: bool
    detail: str = ""


def _percentile(values: List[float], percentile: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    k = (len(values) - 1) * percentile
    f = int(k)
    c = min(f + 1, len(values) - 1)
    if f == c:
        return values[f]
    return values[f] + (values[c] - values[f]) * (k - f)


def _create_or_get_users(user_count: int) -> List[Tuple[int, str]]:
    users: List[Tuple[int, str]] = []
    run_tag = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    db = SessionLocal()
    try:
        for i in range(user_count):
            email = f"loadtest_{run_tag}_{i}@example.com"
            user = models.User(
                name=f"Load Test {i}",
                email=email,
                password_hash=main.hash_password("LoadTest123A"),
            )
            db.add(user)
            db.flush()
            token = main.create_access_token(user.id)
            users.append((user.id, token))
        db.commit()
    finally:
        db.close()
    return users


async def _post_analyze(
    client: httpx.AsyncClient,
    user_id: int,
    token: str,
    image_bytes: bytes,
) -> RequestResult:
    headers = {"Authorization": f"Bearer {token}"}
    files = {"image": ("profile.jpg", image_bytes, "image/jpeg")}
    data = {"height": "170", "weight": "65"}

    start = time.perf_counter()
    try:
        response = await client.post(
            f"/users/{user_id}/analyze",
            data=data,
            files=files,
            headers=headers,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        ok = 200 <= response.status_code < 300
        detail = ""
        if not ok:
            try:
                detail = response.json().get("detail", "")
            except Exception:
                detail = response.text[:120]
        return RequestResult("analyze", response.status_code, elapsed_ms, ok, detail)
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return RequestResult("analyze", 0, elapsed_ms, False, str(exc))


async def _post_wardrobe(
    client: httpx.AsyncClient,
    user_id: int,
    token: str,
    image_bytes: bytes,
) -> RequestResult:
    headers = {"Authorization": f"Bearer {token}"}
    files = {"image": ("item.jpg", image_bytes, "image/jpeg")}
    data = {"category": "casual", "season": "all"}

    start = time.perf_counter()
    try:
        response = await client.post(
            f"/users/{user_id}/wardrobe/add",
            data=data,
            files=files,
            headers=headers,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        ok = 200 <= response.status_code < 300
        detail = ""
        if not ok:
            try:
                detail = response.json().get("detail", "")
            except Exception:
                detail = response.text[:120]
        return RequestResult("wardrobe_add", response.status_code, elapsed_ms, ok, detail)
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return RequestResult("wardrobe_add", 0, elapsed_ms, False, str(exc))


async def _run_phase(
    name: str,
    users: List[Tuple[int, str]],
    rounds: int,
    operation: Callable[[httpx.AsyncClient, int, str], asyncio.Future],
) -> List[RequestResult]:
    semaphore = asyncio.Semaphore(MAX_INFLIGHT)
    results: List[RequestResult] = []

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=REQUEST_TIMEOUT_SECONDS) as client:
        async def one_call(user_id: int, token: str):
            async with semaphore:
                return await operation(client, user_id, token)

        tasks = []
        for _ in range(rounds):
            for user_id, token in users:
                tasks.append(asyncio.create_task(one_call(user_id, token)))

        for task in asyncio.as_completed(tasks):
            results.append(await task)

    return results


def _summarize(results: List[RequestResult]) -> Dict[str, object]:
    total = len(results)
    success = [r for r in results if r.ok]
    failures = [r for r in results if not r.ok]
    elapsed_all = [r.elapsed_ms for r in results]
    elapsed_success = [r.elapsed_ms for r in success]

    status_counts: Dict[str, int] = {}
    for r in results:
        key = str(r.status_code)
        status_counts[key] = status_counts.get(key, 0) + 1

    details: Dict[str, int] = {}
    for r in failures:
        if r.detail:
            details[r.detail] = details.get(r.detail, 0) + 1

    return {
        "total_requests": total,
        "successful_requests": len(success),
        "failed_requests": len(failures),
        "success_rate": (len(success) / total) if total else 0.0,
        "status_counts": status_counts,
        "latency_ms": {
            "mean_all": statistics.mean(elapsed_all) if elapsed_all else 0.0,
            "p50_all": _percentile(sorted(elapsed_all), 0.50) if elapsed_all else 0.0,
            "p95_all": _percentile(sorted(elapsed_all), 0.95) if elapsed_all else 0.0,
            "mean_success": statistics.mean(elapsed_success) if elapsed_success else 0.0,
            "p50_success": _percentile(sorted(elapsed_success), 0.50) if elapsed_success else 0.0,
            "p95_success": _percentile(sorted(elapsed_success), 0.95) if elapsed_success else 0.0,
        },
        "failure_details": details,
    }


async def main_async() -> int:
    if not ANALYZE_IMAGE_PATH.exists() or not WARDROBE_IMAGE_PATH.exists():
        print("Missing input images. Set LOAD_ANALYZE_IMAGE and LOAD_WARDROBE_IMAGE.")
        return 2

    analyze_image_bytes = ANALYZE_IMAGE_PATH.read_bytes()
    wardrobe_image_bytes = WARDROBE_IMAGE_PATH.read_bytes()

    users = _create_or_get_users(USERS)

    print(
        json.dumps(
            {
                "base_url": BASE_URL,
                "users": USERS,
                "analyze_rounds": ANALYZE_ROUNDS,
                "wardrobe_rounds": WARDROBE_ROUNDS,
                "max_inflight": MAX_INFLIGHT,
                "timestamp_utc": datetime.utcnow().isoformat(),
            },
            indent=2,
        )
    )

    async def analyze_op(client: httpx.AsyncClient, user_id: int, token: str):
        return await _post_analyze(client, user_id, token, analyze_image_bytes)

    async def wardrobe_op(client: httpx.AsyncClient, user_id: int, token: str):
        return await _post_wardrobe(client, user_id, token, wardrobe_image_bytes)

    analyze_results = await _run_phase("analyze", users, ANALYZE_ROUNDS, analyze_op)
    wardrobe_results = await _run_phase("wardrobe", users, WARDROBE_ROUNDS, wardrobe_op)

    report = {
        "config": {
            "max_concurrent_image_jobs": os.getenv("MAX_CONCURRENT_IMAGE_JOBS"),
            "db_pool_size": os.getenv("DB_POOL_SIZE"),
            "db_max_overflow": os.getenv("DB_MAX_OVERFLOW"),
            "db_pool_timeout": os.getenv("DB_POOL_TIMEOUT"),
            "db_pool_recycle": os.getenv("DB_POOL_RECYCLE"),
            "database_url": os.getenv("DATABASE_URL"),
            "env": os.getenv("ENV"),
        },
        "analyze": _summarize(analyze_results),
        "wardrobe_add": _summarize(wardrobe_results),
    }

    print(json.dumps(report, indent=2))

    output_path = Path("load_test_results.json")
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote report to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main_async()))
