"""
API Latency Benchmark Script
Measures FastAPI event loop and CPU-heavy ML inference latency under stepped concurrency.
Runs in-process via httpx.AsyncClient to evaluate FastAPI async handlers, SQLAlchemy pool, 
and local image semaphores directly against the real app and models.
"""

import asyncio
import os
import sys
import time
import random
import statistics
from pathlib import Path
from typing import Dict, List, Any, Tuple

import httpx
from sqlalchemy.orm import Session

# Add the backend directory to path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Set env var for testing to prevent rate limits from skewing latency metrics
os.environ["EMAIL_VERIFICATION_REQUIRED"] = "false"

import main
from database.database import SessionLocal
from database import models, crud

# Config parameters
TEST_CONCURRENCY_LEVELS = [1, 2, 4, 8]  # Step-up concurrency levels
REQUESTS_PER_CLIENT = 5  # Number of requests each simulated client will make in a tier
TIMEOUT_SECONDS = 30.0

# Image paths
PROFILE_IMAGE_PATH = backend_dir / "profile.jpg"
WARDROBE_IMAGE_PATH = backend_dir / "test_clothing.jpg"


def ensure_real_images() -> Tuple[bytes, bytes]:
    """Verify real images are available; print warning if fallbacks are used."""
    has_real_profile = PROFILE_IMAGE_PATH.exists()
    has_real_wardrobe = WARDROBE_IMAGE_PATH.exists()

    if has_real_profile:
        profile_bytes = PROFILE_IMAGE_PATH.read_bytes()
    else:
        # Fallback to synthetic 1x1 pixel image if file missing
        print("[WARNING] Real profile.jpg not found! Using 1x1 synthetic pixel data instead.")
        profile_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00\xbf\x00\xff\xd9"

    if has_real_wardrobe:
        wardrobe_bytes = WARDROBE_IMAGE_PATH.read_bytes()
    else:
        print("[WARNING] Real test_clothing.jpg not found! Using 1x1 synthetic pixel data instead.")
        wardrobe_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00\xbf\x00\xff\xd9"

    return profile_bytes, wardrobe_bytes

def setup_benchmark_users(db: Session, count: int) -> List[Dict[str, Any]]:
    """Create benchmark users directly in DB, bypass verification, and issue real tokens."""
    users_data = []
    run_tag = int(time.time())
    
    for i in range(count):
        email = f"benchuser_{run_tag}_{i}@gmail.com"  # Needs to match gmail validator
        name = f"Benchmark User {i}"
        password_hash = main.hash_password("BenchPass123!")
        
        # Create user record
        user = models.User(
            name=name,
            email=email,
            password_hash=password_hash,
            email_verified=True,
            email_verified_at=main.utcnow()
        )
        db.add(user)
        db.flush()
        
        # Issue real JWT tokens using app authentication utility
        token_payload = main.build_auth_response(db, user.id)
        
        users_data.append({
            "user_id": user.id,
            "email": email,
            "token": token_payload["access_token"],
            "headers": {"Authorization": f"Bearer {token_payload['access_token']}"}
        })
        
    db.commit()
    return users_data

def cleanup_benchmark_users(db: Session, users: List[Dict[str, Any]]) -> None:
    """Safely delete all generated benchmark users and cascading relations from the DB."""
    try:
        user_ids = [u["user_id"] for u in users]
        for user_id in user_ids:
            user_obj = db.query(models.User).filter(models.User.id == user_id).first()
            if user_obj:
                db.delete(user_obj)
        db.commit()
        print(f"Cleanup: Successfully deleted {len(user_ids)} benchmark users.")
    except Exception as e:
        db.rollback()
        print(f"Error during cleanup of benchmark users: {e}")

async def run_client_workload(
    client: httpx.AsyncClient,
    user_info: Dict[str, Any],
    profile_img: bytes,
    wardrobe_img: bytes,
    num_requests: int
) -> List[Dict[str, Any]]:
    """Simulate a single user performing sequential requests containing a mixed workload."""
    user_id = user_info["user_id"]
    headers = user_info["headers"]
    results = []

    # Workload mix: 60% Reads (Profile/Wardrobe), 20% Analyze (Pose), 20% Wardrobe Add (HuggingFace)
    endpoints_pool = []
    for _ in range(num_requests):
        r = random.random()
        if r < 0.30:
            endpoints_pool.append("GET_PROFILE")
        elif r < 0.60:
            endpoints_pool.append("GET_WARDROBE")
        elif r < 0.80:
            endpoints_pool.append("POST_ANALYZE")
        else:
            endpoints_pool.append("POST_WARDROBE_ADD")

    for action in endpoints_pool:
        start_time = time.perf_counter()
        status_code = 0
        error_type = ""
        
        try:
            if action == "GET_PROFILE":
                resp = await client.get(f"/users/{user_id}", headers=headers, timeout=TIMEOUT_SECONDS)
                status_code = resp.status_code
            elif action == "GET_WARDROBE":
                resp = await client.get(f"/users/{user_id}/wardrobe", headers=headers, timeout=TIMEOUT_SECONDS)
                status_code = resp.status_code
            elif action == "POST_ANALYZE":
                files = {"image": ("profile.jpg", profile_img, "image/jpeg")}
                data = {"height": "175.5", "weight": "70.2"}
                resp = await client.post(
                    f"/users/{user_id}/analyze", 
                    headers=headers, 
                    data=data, 
                    files=files, 
                    timeout=TIMEOUT_SECONDS
                )
                status_code = resp.status_code
            elif action == "POST_WARDROBE_ADD":
                files = {"image": ("clothing.jpg", wardrobe_img, "image/jpeg")}
                data = {"category": "top", "season": "spring"}
                resp = await client.post(
                    f"/users/{user_id}/wardrobe/add", 
                    headers=headers, 
                    data=data, 
                    files=files, 
                    timeout=TIMEOUT_SECONDS
                )
                status_code = resp.status_code
                
        except httpx.TimeoutException:
            status_code = 0
            error_type = "Timeout"
        except Exception as exc:
            status_code = 0
            error_type = type(exc).__name__
            
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        results.append({
            "action": action,
            "status_code": status_code,
            "elapsed_ms": elapsed_ms,
            "error_type": error_type
        })
        
    return results

def calculate_percentile(sorted_list: List[float], percentile: float) -> float:
    if not sorted_list:
        return 0.0
    k = (len(sorted_list) - 1) * percentile
    f = int(k)
    c = min(f + 1, len(sorted_list) - 1)
    if f == c:
        return sorted_list[f]
    return sorted_list[f] + (sorted_list[c] - sorted_list[f]) * (k - f)

def print_metrics_summary(concurrency: int, total_duration_s: float, results: List[Dict[str, Any]]) -> None:
    """Evaluate and output statistical summary of latency values."""
    all_latencies = sorted([r["elapsed_ms"] for r in results])
    success_requests = [r for r in results if 200 <= r["status_code"] < 300]
    total_reqs = len(results)
    success_rate = (len(success_requests) / total_reqs * 100) if total_reqs else 0
    rps = total_reqs / total_duration_s if total_duration_s > 0 else 0
    
    # Calculate percentiles
    p50 = calculate_percentile(all_latencies, 0.50)
    p95 = calculate_percentile(all_latencies, 0.95)
    p99 = calculate_percentile(all_latencies, 0.99)
    mean_latency = statistics.mean(all_latencies) if all_latencies else 0.0
    
    # Error classification
    errors = {}
    for r in results:
        code = r["status_code"]
        err = r["error_type"]
        if code < 200 or code >= 300:
            key = f"HTTP {code}" if code != 0 else err
            errors[key] = errors.get(key, 0) + 1

    print(f"\n================ CONCURRENCY LEVEL: {concurrency} ================")
    print(f"Total Requests:      {total_reqs}")
    print(f"Throughput (RPS):    {rps:.2f} req/s")
    print(f"Success Rate:        {success_rate:.1f}%")
    print(f"Average Latency:     {mean_latency:.1f} ms")
    print(f"Median (p50):        {p50:.1f} ms")
    print(f"p95 Tail Latency:    {p95:.1f} ms")
    print(f"p99 Tail Latency:    {p99:.1f} ms")
    
    if errors:
        print("Failure / Status Breakdown:")
        for k, v in errors.items():
            print(f"  - {k}: {v} occurrence(s)")
    else:
        print("Failures:            None")
    print("=========================================================")

async def run_benchmark():
    db = SessionLocal()
    
    # Identify environment database configuration
    db_url = str(db.bind.url) if db.bind else "Unknown"
    print(f"Initial Setup: Target DB is {db_url}")
    
    # 1. Image checks
    profile_bytes, wardrobe_bytes = ensure_real_images()
    
    # Determine model configuration source of truth
    min_conf = os.getenv("HF_CLASSIFICATION_MIN_CONF", "0.35")
    image_concurrency_max = os.getenv("MAX_CONCURRENT_IMAGE_JOBS", "4")
    print(f"Model settings: HF_CLASSIFICATION_MIN_CONF={min_conf}, MAX_CONCURRENT_IMAGE_JOBS={image_concurrency_max}")
    
    # 2. Setup benchmark users
    max_concurrency = max(TEST_CONCURRENCY_LEVELS)
    print(f"Generating {max_concurrency} temporary test users in DB...")
    users = setup_benchmark_users(db, max_concurrency)
    
    # Disable queue processing temporarily to measure local app execution latency 
    # (otherwise tasks would return immediately with 202 Accepted status)
    main.INFERENCE_QUEUE_ENABLED = False
    
    # Setup HTTP client pointing to our in-process FastAPI application
    # httpx >= 0.20 dropped the app= shorthand; use ASGITransport explicitly
    transport = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://benchmark-server") as client:
        print("\nStarting step-up load benchmark...")
        
        for concurrency in TEST_CONCURRENCY_LEVELS:
            active_users = users[:concurrency]
            
            # Start parallel client tasks
            start_time = time.perf_counter()
            tasks = [
                run_client_workload(
                    client,
                    user,
                    profile_bytes,
                    wardrobe_bytes,
                    REQUESTS_PER_CLIENT
                )
                for user in active_users
            ]
            
            # Run all tasks concurrently and gather results
            batch_results = await asyncio.gather(*tasks)
            duration_s = time.perf_counter() - start_time
            
            # Flatten list of metrics
            flat_results = [r for sublist in batch_results for r in sublist]
            
            # Generate summary reports
            print_metrics_summary(concurrency, duration_s, flat_results)
            
            # Small cooldown sleep between steps
            await asyncio.sleep(1.0)
            
    # 3. Clean up DB records
    cleanup_benchmark_users(db, users)
    db.close()

if __name__ == "__main__":
    print("---------------------------------------------------------")
    print("               Fashion App API Latency Benchmark         ")
    print("---------------------------------------------------------")
    
    # Display synthetic warning if needed
    has_real_profile = PROFILE_IMAGE_PATH.exists()
    has_real_wardrobe = WARDROBE_IMAGE_PATH.exists()
    if not (has_real_profile and has_real_wardrobe):
        print("\n[WARNING] DATA INTEGRITY NOTICE:")
        print("Some real image assets were missing from the local folder. The benchmark script is using")
        print("synthetic dummy image bytes in their place. This will result in different file upload payloads,")
        print("causing image-processing libraries (OpenCV/detr) to skip regions, which will return")
        print("lower CPU/GPU execution latencies than actual real wardrobe photo uploads.")
        print("To verify real-world latencies, please place real JPG images at:")
        print(f"  - profile: {PROFILE_IMAGE_PATH}")
        print(f"  - wardrobe: {WARDROBE_IMAGE_PATH}\n")
    else:
        print("\n[INFO] Real image files detected. Benchmark will run using real visual data.")
        
    print("NOTE: Running in-process via httpx.AsyncClient. The recorded metrics represent application logic")
    print("execution time only and do NOT include network transit latency (TCP handshake, transit overhead, etc.).")
    print("---------------------------------------------------------\n")
    
    asyncio.run(run_benchmark())
