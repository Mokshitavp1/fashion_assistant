# Docker Setup Guide for Fashion App

## Quick Start with Docker

Run the entire application stack with a single command:

```bash
docker-compose up -d
```

This will start all services:
- ✅ Redis (message broker)
- ✅ Backend API (FastAPI)
- ✅ Frontend (React Vite)
- ✅ Celery Worker (background tasks)
- ✅ Celery Beat (task scheduler)

---

## Services Overview

### 1. Redis (`redis:latest`)
- **Purpose**: Message broker for Celery, task result backend
- **Port**: `6379:6379`
- **Container**: `fashion-redis`
- **Health Check**: Pings Redis every 10s

### 2. Backend API (`backend:latest`)
- **Purpose**: FastAPI application with all endpoints
- **Port**: `8000:8000`
- **Container**: `fashion-backend`
- **Features**:
  - Live reload with `--reload` flag
  - Volume mount for local development
  - Depends on Redis health check
- **Command**: `uvicorn main:app --host 0.0.0.0 --port 8000 --reload`

### 3. Frontend (`frontend:latest`)
- **Purpose**: React Vite dev server
- **Port**: `5173:5173`
- **Container**: `fashion-frontend`
- **Features**:
  - Live reload on file changes
  - Volume mount for local development
  - node_modules excluded to prevent conflicts
- **Command**: `npm run dev -- --host 0.0.0.0`

### 4. Celery Worker (`backend:latest`)
- **Purpose**: Process background inference tasks
- **Container**: `fashion-celery-worker`
- **Features**:
  - Processes tasks from Redis queue
  - Logs all task execution
  - Auto-restarts on failure
- **Command**: `celery -A worker_tasks worker --loglevel=info`

### 5. Celery Beat (`backend:latest`)
- **Purpose**: Schedule periodic tasks (daily metrics, weekly retraining)
- **Container**: `fashion-celery-beat`
- **Features**:
  - Runs daily metrics computation (2 AM UTC)
  - Runs weekly model retraining (Sunday 3 AM UTC)
  - Scheduler persistence
- **Command**: `celery -A worker_tasks beat --loglevel=info`

---

## Common Commands

### Start All Services
```bash
docker-compose up -d
```

### Start Specific Service Only
```bash
docker-compose up -d frontend
docker-compose up -d backend
docker-compose up -d celery_worker
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f celery_worker
docker-compose logs -f celery_beat
docker-compose logs -f frontend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Stop All Services
```bash
docker-compose down
```

### Stop Specific Service
```bash
docker-compose down backend
```

### Rebuild Images (after dependency changes)
```bash
docker-compose build
docker-compose up -d
```

### Rebuild Specific Service
```bash
docker-compose build backend
docker-compose up -d backend
```

### Remove All Containers and Volumes
```bash
docker-compose down -v
```

---

## Accessing Services

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Docs (ReDoc) | http://localhost:8000/redoc |
| Redis | localhost:6379 |

---

## Development Workflow

### 1. Make Code Changes
- Backend code: Changes auto-reload via `--reload`
- Frontend code: Changes auto-reload via Vite HMR
- No restart needed!

### 2. View Live Logs
```bash
docker-compose logs -f backend
```

### 3. Test New Endpoints
- Open http://localhost:8000/docs
- Try the request directly in Swagger UI

### 4. Check Background Tasks
```bash
docker-compose logs -f celery_worker
docker-compose logs -f celery_beat
```

---

## Environment Configuration

### Development (.env)
```
ENV=development
DATABASE_URL=sqlite:///./clothing_database.db
REDIS_URL=redis://redis:6379/0
DEBUG=true
```

### Production Environment
For production, use:
- Managed database (AWS RDS, Google Cloud SQL)
- Persistent Redis or managed service (ElastiCache, Redis Cloud)
- Change `ENV=production`
- Use strong `SECRET_KEY`
- Set `DEBUG=false`

---

## Troubleshooting

### Port Already in Use
```bash
# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9

# Or use different ports in docker-compose.yml
# Change "8000:8000" to "8001:8000"
```

### Redis Connection Refused
```bash
# Verify Redis is running
docker-compose ps redis

# Check Redis logs
docker-compose logs redis

# Restart Redis
docker-compose restart redis
```

### Celery Worker Not Processing Tasks
1. Check Redis is running: `docker-compose logs -f redis`
2. Check worker is connected: `docker-compose logs -f celery_worker`
3. Verify task is in queue: Check backend logs for `POST /users/{id}/...` calls

### Frontend Cannot Connect to Backend
```bash
# Check backend is running
docker-compose ps backend

# Check backend logs
docker-compose logs -f backend

# Verify CORS is enabled (it is by default)
curl -X GET http://localhost:8000/docs
```

### Database Not Initialized
```bash
# Restart backend to initialize SQLite
docker-compose restart backend

# Check database file exists
docker-compose exec backend ls -la clothing_database.db
```

### Celery Beat Not Scheduling Tasks
1. Verify Celery beat is running: `docker-compose ps celery_beat`
2. Check beat schedule: `docker-compose logs celery_beat`
3. Verify Redis is connected: `docker-compose logs redis`

---

## Performance Tips

1. **Use Docker volumes** for database persistence:
   ```yaml
   volumes:
     backend_db:
   ```

2. **Limit log output** for faster performance:
   ```bash
   docker-compose logs --tail=50 -f
   ```

3. **Use `.dockerignore`** to exclude unnecessary files:
   - Reduces image size
   - Faster builds and context transfer

4. **Multi-stage builds** for production (optional):
   - Build Node/Python dependencies in separate stage
   - Smaller final image size

---

## Production Deployment

For deploying to production:

1. **Update docker-compose.yml**:
   - Remove `--reload` flags
   - Remove `volumes` mounts
   - Use `COPY` instead of mounting code

2. **Set environment variables**:
   ```bash
   export ENV=production
   export SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')
   ```

3. **Use external database**:
   ```
   DATABASE_URL=mysql+pymysql://user:pass@rds.amazonaws.com:3306/fashion
   ```

4. **Use production Redis**:
   ```
   REDIS_URL=redis://your-redis-instance:6379/0
   ```

5. **Deploy**:
   ```bash
   docker-compose -f docker-compose.yml up -d
   ```

---

## Useful Docker Commands

### View Container Stats
```bash
docker stats fashion-backend fashion-celery-worker
```

### Execute Command in Container
```bash
docker-compose exec backend python -c "import sys; print(sys.version)"
```

### Interactive Shell
```bash
docker-compose exec backend bash
docker-compose exec frontend sh
```

### Inspect Network
```bash
docker network ls
docker network inspect fashion_network
```

### View Image Details
```bash
docker images | grep fashion
docker inspect fashion-backend
```

---

## Monitoring

### Check All Services Running
```bash
docker-compose ps
```

Expected output:
```
NAME                COMMAND                  SERVICE          STATUS      PORTS
fashion-backend     "python -m uvicorn..." backend          running     0.0.0.0:8000->8000/tcp
fashion-frontend    "npm run dev..."         frontend         running     0.0.0.0:5173->5173/tcp
fashion-redis       "redis-server"           redis            running     0.0.0.0:6379->6379/tcp
fashion-celerybeat  "celery -A worker..."    celery_beat      running
fashion-celery-wrk  "celery -A worker..."    celery_worker    running
```

### Health Check Redis
```bash
docker-compose exec redis redis-cli ping
# Expected: PONG
```

### View Celery Tasks
```bash
docker-compose logs celery_worker | grep Task
```

---

## Next Steps

1. **Start services**: `docker-compose up -d`
2. **Open frontend**: http://localhost:5173
3. **Test API**: http://localhost:8000/docs
4. **Monitor logs**: `docker-compose logs -f`
5. **Make code changes** and watch auto-reload!

**That's it! Your entire app is running in Docker with fully functional learning system!** 🚀
