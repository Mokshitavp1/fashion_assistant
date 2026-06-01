# Starting Docker for Fashion App - Windows

## Prerequisites Check

Before starting Docker services, ensure:
- ✅ Docker Compose installed: `docker-compose --version` (v5.1.0+)
- ✅ Docker daemon running (Docker Desktop for Windows)

---

## Option 1: Docker Desktop (Recommended on Windows)

### Start Docker Desktop
1. Open **Windows Start Menu**
2. Search for **"Docker Desktop"**
3. Click to launch application
4. Wait for Docker daemon to start (watch system tray icon)
5. Icon shows whale when ready

### Verify Docker is Running
```powershell
docker ps
# Should list running containers (or empty list if none running)

docker-compose --version
# Should show version 5.1.0 or higher
```

### Start Fashion App
```powershell
cd C:\Users\vpmok\OneDrive\Desktop\projects\fashion_app
docker-compose up -d
```

---

## Option 2: WSL2 + Docker (Alternative)

### Prerequisites
- Windows 10/11 with WSL2 enabled
- Docker Desktop configured for WSL2 backend

### Start Docker in WSL
```bash
# In PowerShell
wsl

# In WSL terminal
sudo service docker start
# Or: sudo systemctl start docker

# Verify
docker ps
```

### Start Fashion App
```powershell
cd C:\Users\vpmok\OneDrive\Desktop\projects\fashion_app
docker-compose up -d
```

---

## Option 3: Individual Containers (Without Docker Compose)

If Docker Compose has issues, run manually:

```powershell
# Terminal 1 - Redis
docker run -d -p 6379:6379 --name fashion-redis redis:latest

# Terminal 2 - Backend
docker run -d -p 8000:8000 `
  -e REDIS_URL=redis://host.docker.internal:6379/0 `
  -v "${pwd}\backend:/app" `
  --name fashion-backend `
  -w /app `
  python:3.13-slim `
  bash -c "pip install -r requirements.txt && python -m uvicorn main:app --host 0.0.0.0 --port 8000"

# Terminal 3 - Frontend
docker run -d -p 5173:5173 `
  -v "${pwd}\frontend:/app" `
  --name fashion-frontend `
  -w /app `
  node:20-alpine `
  bash -c "npm install && npm run dev -- --host 0.0.0.0"
```

---

## Troubleshooting

### "Docker daemon is not running"
```powershell
# Check if Docker Desktop is running
Get-Process | Where-Object {$_.Name -like "*docker*"}

# If not running, start Docker Desktop from Start Menu
```

### Docker Desktop Installation Issues
1. Check Windows version (requires Windows 10 Pro or Windows 11)
2. Enable Hyper-V and WSL2 if needed
3. Download: https://www.docker.com/products/docker-desktop

### Port Already in Use
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process
taskkill /PID {PID} /F

# Or use different port in docker-compose.yml
# Change "8000:8000" to "8001:8000"
```

### Verify Setup is Complete
```powershell
docker --version         # Docker installed
docker-compose --version # Docker Compose installed
docker ps                # Docker daemon running

# All three should return without errors
```

---

## Once Docker is Running

```powershell
# Terminal 1 - Start all services
docker-compose up -d

# Terminal 2 - View logs
docker-compose logs -f

# Verify all services are running
docker-compose ps
```

Expected output:
```
NAME                COMMAND                  SERVICE      STATUS              PORTS
fashion-backend     "python -m uvicorn..."   backend      Up 5 seconds        0.0.0.0:8000->8000/tcp
fashion-celery-be   "celery -A worker..."    celery_beat  Up 3 seconds
fashion-celery-wo   "celery -A worker..."    celery_worker   Up 4 seconds
fashion-frontend    "npm run dev..."         frontend     Up 6 seconds        0.0.0.0:5173->5173/tcp
fashion-redis       "redis-server..."        redis        Up 7 seconds        0.0.0.0:6379->6379/tcp
```

---

## Access Services

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

---

## Common Docker Commands

```powershell
# View running services
docker-compose ps

# View logs from all services
docker-compose logs -f

# View logs from specific service
docker-compose logs -f backend
docker-compose logs -f celery_worker

# Stop all services
docker-compose down

# Stop specific service
docker-compose stop backend

# Restart services
docker-compose restart

# Rebuild images (if dependencies change)
docker-compose build
docker-compose up -d
```

---

**Need help?** Check DOCKER_SETUP.md for detailed configuration options.
