# Fashion App

Fashion App is a React + FastAPI wardrobe assistant that recommends outfits, tracks feedback, and learns from user ratings.

## What to use

- `frontend/` is the active web app.
- `backend/` is the active API.
- `legacy-mobile/` is archived reference code.

## Fastest Start

If you want the easiest path for GitHub users, use Docker:

1. Install Docker Desktop.
2. Start the stack:
   - `docker-compose up -d`
3. Open the app:
   - Frontend: http://localhost:5173
   - API docs: http://localhost:8000/docs

That starts the frontend, backend, Redis, Celery worker, and Celery Beat.

## GitHub Codespaces

If you want a browser-based setup with no local installs, open the repo on GitHub and choose `Code` > `Codespaces` > `Create codespace on main`.

The codespace is preconfigured to:
- Install Python and Node dependencies on first launch
- Forward the frontend on port `5173`
- Forward the backend API on port `8000`

Once it opens, start the app with:
- Backend: `npm run backend:dev`
- Frontend: `npm run dev`

## Local Development

If you prefer running it without Docker:

1. Copy config files:
   - `backend/.env.example` to `backend/.env`
   - `frontend/.env.example` to `frontend/.env.local` if you need a custom API URL
2. Install dependencies:
   - Backend: `pip install -r backend/requirements.txt`
   - Frontend: `npm --prefix frontend install`
3. Start the app:
   - Backend: `npm run backend:dev`
   - Frontend: `npm run dev`

## How to test it

1. Go to http://localhost:5173
2. Create a Gmail account through onboarding.
3. In development, the API returns a confirmation token so you can complete the email-confirmation flow without a real inbox.
4. After confirming, sign in and test outfit ratings, recommendation feedback, and item usage tracking.

## Scripts

- `npm run dev`: start the frontend
- `npm run build`: build the frontend
- `npm run lint`: lint the frontend
- `npm run preview`: preview the frontend build
- `npm run backend:dev`: start the backend API

## Useful Docs

- [backend/README.md](backend/README.md)
- [frontend/README.md](frontend/README.md)
- [DOCKER.md](DOCKER.md)
- [QUICKSTART.md](QUICKSTART.md)

## Production Notes

- Use managed MySQL or PostgreSQL instead of SQLite.
- Keep Redis available for Celery background jobs.
- Remove dev-only token echoing before sending email confirmation tokens in production.
