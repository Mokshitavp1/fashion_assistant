# Free No-Card Deployment Guide

This project can be deployed as a public demo without asking visitors to clone the repo and without using a free tier that requires card details.

## Recommended Stack

- Frontend: Cloudflare Pages or GitHub Pages
- Backend API: Hugging Face Spaces Docker Space
- Database: Neon free Postgres

This keeps the demo simple for users: one public frontend URL that talks to one public API URL.

## Why This Stack

- The frontend already supports a configurable backend URL through `VITE_API_BASE_URL`.
- The backend already supports production CORS and rejects SQLite in production.
- The public demo can avoid SMTP by disabling verification with `EMAIL_VERIFICATION_REQUIRED=false`.
- Redis/Celery can stay optional for the demo if the free host cannot run them reliably.

## Deployment Values

### Backend

Set these environment variables on the API host:

- `ENV=production`
- `SECRET_KEY=<strong random string at least 32 chars>`
- `DATABASE_URL=<Neon Postgres connection string>`
- `ALLOWED_ORIGINS=<frontend URL>`
- `EMAIL_VERIFICATION_REQUIRED=false`

Optional, only if you want queue-backed features in the demo:

- `REDIS_URL=<Redis URL>`
- `INFERENCE_QUEUE_ENABLED=true`

### Frontend

Set this environment variable during the frontend build:

- `VITE_API_BASE_URL=<backend URL>`
- `VITE_EMAIL_VERIFICATION_REQUIRED=false`

## Build Flow

1. Deploy the backend first.
2. Copy the backend URL into `VITE_API_BASE_URL`.
3. Build and deploy the frontend.
4. Add the frontend origin to `ALLOWED_ORIGINS` on the backend.

## Public Demo Behavior

For a friction-free trial, keep the public demo focused on the main product loop:

- Sign up or use a demo account.
- Upload a wardrobe image.
- Generate recommendations.

If the free host cannot support workers, leave Redis/Celery out of the demo and keep the core API synchronous.

## Notes

- Do not use SQLite in production.
- Do not rely on local uploaded files for demo persistence unless the host provides durable storage.
- If you want the demo to be extra smooth, seed one demo user and a few wardrobe items.