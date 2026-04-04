# Fashion App - Quick Start Guide

## Current Status ✅

**All services are running. Open the app at: http://localhost:5173**

### Running Services
- ✅ Frontend (Vite React): http://localhost:5173
- ✅ Backend API (FastAPI): http://0.0.0.0:8000
- ✅ API Documentation: http://localhost:8000/docs
- ✅ SQLite Database: `backend/clothing_database.db`

---

## Using the App

### 1. Sign Up / Log In
- Landing page with authentication
- Email/password signup, or demo account

### 2. Onboarding
- Set your body shape
- Choose 3-5 style preferences
- Upload initial wardrobe photos

### 3. Core Features

#### 👗 Wardrobe
- View all clothing items
- Filter by category, color, style
- Edit or delete items

#### ✨ Outfits
- Get personalized outfit recommendations
- **⭐ NEW: Rate outfits 1-5 stars** (feedback system)
- Optional comment for additional feedback
- System learns from your ratings!

#### 🛍️ Shopping Assistant
- Get smart shopping suggestions
- Mark recommendations helpful/not helpful
- Filter by price range and style

#### 📝 Discard Analyzer
- Track items you don't wear
- Feedback helps improve future recommendations

#### 📊 Sessions
- View recommendation history
- Track system performance

---

## Feedback System (NEW) 📈

The app now learns and improves from your feedback!

### How It Works
1. **You provide feedback** through the UI:
   - Rate outfits (1-5 stars)
   - Mark recommendations helpful/unhelpful
   - Track item usage (worn, kept, discarded)

2. **System computes metrics** (daily at 2 AM UTC):
   - Accuracy of outfit recommendations
   - Helpfulness rate by recommendation type
   - Model drift detection

3. **Models retrain weekly** (Sundays 3 AM UTC):
   - Color harmony rules improve from outfit patterns
   - Clothing classifier learns wear/discard signals
   - Body shape detection improves from feedback
   - Conservative deployment (only if 2%+ improvement)

---

## Setting Up Learning System (Redis/Celery)

### Option 1: Docker (Easiest)
```powershell
# Start Redis
docker run -d -p 6379:6379 --name fashion-redis redis:latest

# New terminal - Start Celery worker
cd backend
celery -A worker_tasks worker --loglevel=info

# Another terminal - Start Celery beat scheduler
cd backend
celery -A worker_tasks beat --loglevel=info
```

### Option 2: Local Redis (Windows)
1. Download: https://github.com/microsoftarchive/redis/releases
2. Extract and run: `redis-server.exe`
3. Then start Celery worker/beat as in Option 1

### Option 3: WSL (Linux Subsystem)
```bash
# In WSL terminal
sudo apt-get install redis-server
redis-server

# In another WSL terminal
cd /path/to/fashion_app/backend
celery -A worker_tasks worker --loglevel=info

# Another terminal
celery -A worker_tasks beat --loglevel=info
```

**Once Redis + Celery are running, metrics will compute automatically!**

---

## API Endpoints (All Available Now)

### Feedback Collection
```
POST /users/{user_id}/outfits/{outfit_id}/rate
  - Rate an outfit 1-5 with optional comment

POST /users/{user_id}/recommendations/{rec_type}/{rec_id}/feedback
  - Mark recommendation helpful/unhelpful
  - rec_type: "outfit" | "shopping" | "discard"

POST /users/{user_id}/wardrobe/{item_id}/usage
  - Track item usage (worn, kept, discarded)
```

### Admin Metrics
```
GET /admin/metrics/models
  - View model performance metrics over time

GET /admin/metrics/feedback-volume
  - See feedback collection statistics
```

### Existing Endpoints
- All wardrobe, outfit, shopping, discard endpoints working
- Full authentication with JWT tokens
- Rate limiting enabled

---

## Stopping Services

### PowerShell
```powershell
# Kill current processes
Get-Process | Where-Object {$_.Name -match "uvicorn|node|celery"} | Stop-Process -Force

# Kill Redis container
docker stop fashion-redis
docker rm fashion-redis
```

### Or press Ctrl+C in each terminal

---

## Troubleshooting

### Frontend shows "Cannot connect to API"
- Verify backend is running: http://localhost:8000/docs
- Check CORS is enabled (it is by default)
- Try hard refresh: Ctrl+Shift+Delete

### Ratings not saving
- Check network tab in browser devtools
- Verify user_id and outfit_id are valid
- Check backend logs for errors

### Celery tasks not running
- Verify Redis is running: `redis-cli ping` (should return PONG)
- Check Celery worker terminal for connection errors
- Verify environment variable: `REDIS_URL=redis://127.0.0.1:6379/0`

### Database errors
- Database auto-initializes on first API startup
- If issues: Delete `backend/clothing_database.db` and restart backend
- Tables created: users, wardrobe_items, outfits, outfit_ratings, recommendation_feedback, item_usage, model_metrics

---

## Next Steps

1. **Test feedback system**: Rate a few outfits and check them in database
2. **Set up Redis** (optional but recommended for learning system)
3. **Start Celery/beat** to enable automatic metrics + retraining
4. **Try all features**: Generate recommendations, provide feedback, watch system improve!

---

## File Structure

```
fashion_app/
├── frontend/              # React Vite app
│   ├── src/components/   # UI components (with new rating UI)
│   └── src/services/     # API client functions
├── backend/              # FastAPI server
│   ├── main.py          # API endpoints (6 feedback endpoints added)
│   ├── database/        # SQLAlchemy models + CRUD
│   ├── services/        # ML services + learning system
│   └── worker_tasks.py  # Celery tasks
├── LEARNING_SYSTEM_SETUP.md  # Detailed setup guide
└── QUICKSTART.md         # This file
```

---

**Questions?** Check LEARNING_SYSTEM_SETUP.md for detailed implementation info!
