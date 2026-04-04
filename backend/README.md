# Backend Setup Guide

This backend is a FastAPI app with JWT auth, image processing, and SQLAlchemy.

## Fresh Machine Quick Start

1. Create env file:
   - Copy `.env.example` to `.env` inside `backend/`.
2. Keep SQLite for local development (recommended):
   - `DATABASE_URL=sqlite:///./backend/clothing_database.db`
3. Set a secret key in `.env`:
  - `SECRET_KEY=<at least 32 chars>`
4. Install Python dependencies from workspace root:
   - `pip install -r backend/requirements.txt`
5. Start the API from workspace root:
   - `npm run backend:dev`
6. Verify server is up:
   - Open `http://127.0.0.1:8000/`
   - Expected payload includes `"status": "ok"`.

## Env Variables

- `ENV`
  - Values: `dev`, `development`, `local`, `production`, etc.
  - Default behavior is local-friendly.

- `DATABASE_URL`
  - Local default (recommended): `sqlite:///./backend/clothing_database.db`
  - Optional MySQL: `mysql+pymysql://user:password@host:3306/clothing_database`
  - Optional PostgreSQL: `postgresql+psycopg://user:password@host:5432/clothing_database`
  - In production (`ENV=production`), SQLite is blocked at startup.

- `MAX_CONCURRENT_IMAGE_JOBS`
  - Limits concurrent CPU-heavy image jobs per API instance.
  - Default: `4`

- `INFERENCE_QUEUE_ENABLED`
  - When `true`, `/users/{user_id}/analyze` and `/users/{user_id}/wardrobe/add` enqueue background jobs.
  - Default: `false` in dev/local, `true` in production.

- `REDIS_URL`
  - Redis connection URL for job queue.
  - Default: `redis://127.0.0.1:6379/0`

- `INFERENCE_QUEUE_NAME`
  - Queue name for ML inference jobs.
  - Default: `inference`

- `INFERENCE_JOB_TIMEOUT`
  - Max seconds for one inference job.
  - Default: `300`

- `INFERENCE_RESULT_TTL`
  - Seconds to keep completed/failed job results.
  - Default: `3600`

- `DB_POOL_SIZE`
  - SQLAlchemy connection pool size for MySQL/PostgreSQL.
  - Default: `10`

- `DB_MAX_OVERFLOW`
  - Extra DB connections above pool size.
  - Default: `20`

- `DB_POOL_TIMEOUT`
  - Seconds to wait for a pooled connection.
  - Default: `30`

- `DB_POOL_RECYCLE`
  - Connection recycle interval in seconds.
  - Default: `1800`

- `SECRET_KEY`
  - Used to sign JWT tokens.
  - Required in all environments.
  - Must be at least 32 characters.
  - Example generation command:
    - `python -c "import secrets; print(secrets.token_urlsafe(48))"`

- `ACCESS_TOKEN_EXPIRATION_MINUTES`
  - Access token TTL in minutes.
  - Default: `15`

- `REFRESH_TOKEN_EXPIRATION_DAYS`
  - Refresh token TTL in days.
  - Default: `7`

- `PASSWORD_RESET_TOKEN_EXPIRATION_MINUTES`
  - Password reset token TTL in minutes.
  - Default: `30`

- `ALLOWED_ORIGINS`
  - Comma-separated CORS origins.
  - Example: `http://localhost:3000,http://localhost:5173`

## Common Startup Issues

### 1) Import error around FastAPI security types

- Ensure dependencies are installed from `backend/requirements.txt`.
- Restart terminal after install if needed.

### 2) Database connection error

- For first run, use SQLite in `.env`:
  - `DATABASE_URL=sqlite:///./backend/clothing_database.db`
- If using MySQL, verify host, port, username, password, and DB permissions.

### 3) 401 responses from protected routes

- Most `/users/...` endpoints require `Authorization: Bearer <token>`.
- Create/login via:
  - `POST /auth/register`
  - `POST /auth/login`
  - Register body now requires `name`, `email`, and `password`.
  - Login form data now requires `email` and `password`.
  - Rotate tokens using `POST /auth/refresh` with JSON `{ "refresh_token": "..." }`.
  - Refresh tokens are persisted server-side and rotated on each refresh.
  - Reusing a previously rotated refresh token is rejected.
  - Logout current session using `POST /auth/logout` with JSON `{ "refresh_token": "..." }`.
  - Logout all devices using `POST /auth/logout-all` with access token auth.
  - List sessions using `GET /auth/sessions` with access token auth.
  - Revoke one session using `DELETE /auth/sessions/{jti}` with access token auth.
  - Request password reset with `POST /auth/password-reset/request` and JSON `{ "email": "..." }`.
  - Confirm password reset with `POST /auth/password-reset/confirm` and JSON `{ "reset_token": "...", "new_password": "..." }`.
  - Password reset revokes all active refresh tokens for the user.

### 4) 429 Too Many Requests during repeated script runs

- Rate limiting is enabled and keying prefers authenticated user ID when available.
- Auth route limits are tuned for production defaults:
  - Register: 3/minute
  - Login: 5/minute
  - Refresh: 30/minute
  - Password reset request: 3/minute
  - Password reset confirm: 5/minute
- Wait briefly before retrying or use fewer repeated auth calls.

### 5) Auth audit logs

- Security-relevant auth events are logged with structured payloads under `AUTH_AUDIT`.
- Events include register, login, refresh, logout, logout-all, session listing/revocation, and password reset flows.

## Useful Commands

From workspace root:

- Run backend: `npm run backend:dev`
- Run backend pytest: `python -m pytest -q backend`

## Worker Queue (Horizontal ML Scalability)

Run API and workers separately so API instances stay stateless:

1. Start Redis:
  - Example Docker: `docker run -p 6379:6379 redis:7`
2. Start API:
  - `python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000`
3. Start one or more workers:
  - `cd backend && celery -A services.task_queue.celery_app worker -Q inference --loglevel=info`

Behavior when queue is enabled:

- `POST /users/{user_id}/analyze` returns `202 Accepted` with `job_id`.
- `POST /users/{user_id}/wardrobe/add` returns `202 Accepted` with `job_id`.
- Poll `GET /jobs/{job_id}` (authenticated, owner-only) for `queued|started|finished|failed` and final result payload.

Scale by adding worker replicas (CPU/GPU nodes) independently from API replicas.

## Production Scalability Notes

- Heavy image tasks (skin tone, body-shape inference, clothing classification) run in a bounded worker pool instead of blocking the event loop.
- SQLite remains available for local development only; production must use managed MySQL/PostgreSQL.
- For SQLite local runs, WAL mode and busy-timeout are enabled automatically to improve concurrent read/write behavior.
- For production, run multiple API replicas and place them behind a load balancer.

Suggested production env baseline:

- `ENV=production`
- `DATABASE_URL=mysql+pymysql://...` or `postgresql+psycopg://...`
- `DB_POOL_SIZE=20`
- `DB_MAX_OVERFLOW=40`
- `DB_POOL_TIMEOUT=30`
- `DB_POOL_RECYCLE=1800`
- `MAX_CONCURRENT_IMAGE_JOBS=8`

## Train A Clothing Classifier

You can train a lightweight transfer-learning model (MobileNetV3 or EfficientNet-B0) using:

- `python backend/train_fashion_model.py --data-dir <path-to-dataset> --model mobilenet_v3_small --epochs 10`

Expected dataset structure (ImageFolder):

- `<data-dir>/train/<class_name>/*.jpg`
- `<data-dir>/val/<class_name>/*.jpg`

Example:

- `python backend/train_fashion_model.py --data-dir backend/data/deepfashion_subset --model efficientnet_b0 --epochs 15 --batch-size 32`

Artifacts are saved to `backend/model_artifacts/` by default:

- Best checkpoint: `<model>_best.pth`
- Label mapping: `classes.json`

## Local Pretrained Vision Classifier

The backend clothing classifier now uses a local Hugging Face pretrained model (no API key):

- Default model: `google/vit-base-patch16-224`
- Override model via env: `HF_CLOTHING_MODEL=<huggingface-model-id>`
- Clothing-region detector model: `facebook/detr-resnet-50`
- Override detector via env: `HF_CLOTHING_DETECTOR_MODEL=<huggingface-model-id>`
- Confidence threshold for model output: `HF_CLASSIFICATION_MIN_CONF` (default `0.35`)

Example override:

- `HF_CLOTHING_MODEL=google/vit-base-patch16-224`

If confidence is below the threshold, the backend applies heuristic fallback logic and returns
debug fields in wardrobe responses: `model_confidence`, `confidence_threshold`, `used_fallback`,
`fallback_reason`, `top_model_label`, and `region_detection`.

Note: some general-purpose vision checkpoints are not fashion-specialized. If labels are generic,
consider a fashion-specific checkpoint later for better category/pattern accuracy.
