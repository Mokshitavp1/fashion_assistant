# 🐳 Fashion App Docker Deployment

Complete containerized setup for the Fashion App with automated learning system.

## Files Created

- **`docker-compose.yml`** - Orchestration file for all services (Redis, Backend, Frontend, Celery)
- **`backend/Dockerfile`** - Backend API container image  
- **`frontend/Dockerfile`** - Frontend React container image
- **`backend/.dockerignore`** - Files to exclude from backend image
- **`frontend/.dockerignore`** - Files to exclude from frontend image
- **`START_DOCKER.md`** - Quick start guide for Windows
- **`DOCKER_SETUP.md`** - Comprehensive Docker setup and troubleshooting guide

---

## 🚀 Quick Start

### 1. Prerequisites
- **Docker Desktop** installed on Windows
- **Docker daemon running** (check system tray for Docker icon)
- Port availability: 5173, 8000, 6379 (or modify in docker-compose.yml)

### 2. Start All Services
```powershell
cd C:\Users\vpmok\OneDrive\Desktop\projects\fashion_app
docker-compose up -d
```

### 3. Verify Services Running
```powershell
docker-compose ps
```

### 4. Access Services
| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:5173 |
| **Backend API** | http://localhost:8000 |
| **API Docs** | http://localhost:8000/docs |

---

## 🛑 Got Docker Issues?

### Docker Daemon Not Running
**Error**: `failed to connect to the docker API`

**Solution**: Start Docker Desktop
1. Press Windows key, type "Docker Desktop"
2. Click to open application
3. Wait for Docker icon to appear in system tray
4. Try `docker-compose up -d` again

👉 **See START_DOCKER.md for detailed setup instructions**

---

## 🏗️ Services Architecture

```
┌─────────┐     ┌─────────┐     ┌─────────────┐
│Frontend │────→│Backend  │────→│Database     │
│:5173    │     │:8000    │     │(SQLite)     │
└─────────┘     └─────────┘     └─────────────┘
                     ↓
                ┌─────────┐
                │Redis    │
                │:6379    │
                └────┬────┘
         ┌──────────┬──────────┐
         ↓          ↓          ↓
    ┌────────┐  ┌────────┐  ┌────────┐
    │Celery  │  │Celery  │  │Task    │
    │Worker  │  │Beat    │  │Queue   │
    └────────┘  └────────┘  └────────┘
```

### Services

1. **Redis** - Message broker & result backend
2. **Backend** - FastAPI with Uvicorn (auto-reload)
3. **Frontend** - React Vite dev server (HMR enabled)
4. **Celery Worker** - Background task processor
5. **Celery Beat** - Periodic task scheduler

**All services communicate via custom Docker network `fashion_network`**

---

## 📋 Common Operations

### View Status
```powershell
docker-compose ps
```

### View Logs
```powershell
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f celery_worker
docker-compose logs -f redis
```

### Stop Services
```powershell
# Stop all
docker-compose down

# Stop specific service
docker-compose stop backend
```

### Restart Services
```powershell
# Restart all
docker-compose restart

# Restart specific
docker-compose restart backend
```

### Rebuild (after dependency changes)
```powershell
docker-compose build
docker-compose up -d
```

### View Detailed Service Info
```powershell
docker-compose exec backend get-content clothing_database.db
```

---

## 🔧 Development Workflow

### Make Code Changes
1. **Backend code** - Auto-reloads via `--reload` flag
2. **Frontend code** - Auto-reloads via Vite HMR
3. **NO manual restart needed!** 🔄

### Monitor Changes
```powershell
# Watch frontend logs
docker-compose logs -f frontend

# Watch backend logs
docker-compose logs -f backend

# Watch Celery tasks
docker-compose logs -f celery_worker
```

### Test API Changes
1. Edit code in `backend/main.py`
2. Changes auto-reload
3. Open http://localhost:8000/docs
4. Test endpoint in Swagger UI
5. No restart needed!

---

## 📊 Learning System (Automatic)

Once Docker is running, the learning system works automatically:

### Daily Tasks (2 AM UTC)
```
Celery Beat → Redis Queue → Celery Worker
  ↓
- Compute outfit accuracy metrics
- Evaluate recommendation helpfulness
- Detect model drift
```

### Weekly Tasks (Sunday 3 AM UTC)
```
Celery Beat → Redis Queue → Celery Worker
  ↓
- Analyze user feedback
- Retrain color harmony rules
- Retrain clothing classifier
- Retrain body shape detection
- Deploy improved models if 2%+ better
```

### Monitor Tasks
```powershell
docker-compose logs -f celery_beat     # Scheduler
docker-compose logs -f celery_worker   # Task processor
```

---

## 🧪 Testing the App

### Create Test User
1. Open http://localhost:5173
2. Sign up with email/password
3. Complete onboarding

### Generate Feedback (Tests Learning System)
```powershell
# Rate outfits (goes to backend)
POST http://localhost:8000/users/{user_id}/outfits/{outfit_id}/rate
Body: {"rating": 5, "comment": "Love it!"}

# Mark recommendations helpful
POST http://localhost:8000/users/{user_id}/recommendations/outfit/{rec_id}/feedback
Body: {"helpful": true}

# Track item usage
POST http://localhost:8000/users/{user_id}/wardrobe/{item_id}/usage
Body: {"action": "worn", "wear_count": 1}
```

### Check Metrics
```
GET http://localhost:8000/admin/metrics/feedback-volume
GET http://localhost:8000/admin/metrics/models
```

---

## 🚨 Troubleshooting

### Port Already in Use
```powershell
# Find what's using port 8000
netstat -ano | findstr :8000

# Kill it or change port in docker-compose.yml
```

### Service Won't Start
```powershell
# Check specific service logs
docker-compose logs backend

# Rebuild and restart
docker-compose build backend
docker-compose up -d backend
```

### Redis Connection Errors
```powershell
# Check Redis status
docker-compose ps redis

# View Redis logs
docker-compose logs redis

# Restart Redis
docker-compose restart redis
```

### Frontend Can't Connect to Backend
```powershell
# Verify backend is running
curl http://localhost:8000/docs

# Check CORS in backend logs
docker-compose logs backend | findstr CORS
```

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| **START_DOCKER.md** | Windows-specific Docker setup guide |
| **DOCKER_SETUP.md** | Comprehensive configuration & troubleshooting |
| **QUICKSTART.md** | App features & usage guide |
| **LEARNING_SYSTEM_SETUP.md** | Adaptive learning system details |

---

## 📝 File Structure

```
fashion_app/
├── docker-compose.yml          ← Main Docker orchestration
├── START_DOCKER.md            ← Quick start (Windows)
├── DOCKER_SETUP.md            ← Comprehensive guide
├── backend/
│   ├── Dockerfile             ← Backend image definition
│   ├── .dockerignore          ← Files to exclude
│   ├── main.py                ← FastAPI app
│   ├── requirements.txt        ← Python dependencies
│   ├── worker_tasks.py         ← Celery tasks
│   └── services/              ← ML services
├── frontend/
│   ├── Dockerfile             ← Frontend image definition
│   ├── .dockerignore          ← Files to exclude
│   ├── package.json           ← Node dependencies
│   ├── vite.config.js         ← Vite config
│   └── src/                   ← React components
└── uploaded_images/           ← Persistent volume (if needed)
```

---

## ⚙️ Environment Variables

Created in `docker-compose.yml`:

```yaml
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
DATABASE_URL=sqlite:///./clothing_database.db
ENV=development
```

For production, set:
```
ENV=production
DATABASE_URL=mysql+pymysql://user:pass@rds-host:3306/fashion
REDIS_URL=redis://redis-managed-service:6379/0
SECRET_KEY=<generate-strong-key>
```

---

## ✅ Verification Checklist

- [ ] Docker Desktop installed
- [ ] Docker daemon running
- [ ] All 5 services running (`docker-compose ps`)
- [ ] Frontend accessible (http://localhost:5173)
- [ ] Backend accessible (http://localhost:8000)
- [ ] Redis responding (`docker-compose exec redis redis-cli ping`)
- [ ] Celery worker connected (check `docker-compose logs celery_worker`)

---

## 🎯 Next Steps

1. **Start services**: `docker-compose up -d`
2. **Open frontend**: http://localhost:5173
3. **Explore API**: http://localhost:8000/docs
4. **Rate outfits**: Test feedback system
5. **Monitor tasks**: `docker-compose logs -f`
6. **Read guides**: Check documentation links above

---

**Your entire adaptive learning fashion app is now containerized and ready for deployment!** 🚀

Need help? See [START_DOCKER.md](START_DOCKER.md) or [DOCKER_SETUP.md](DOCKER_SETUP.md).
