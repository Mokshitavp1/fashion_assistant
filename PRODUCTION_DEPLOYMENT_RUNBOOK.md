# Production Deployment Runbook

Complete step-by-step guide for deploying Fashion App to production.

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Infrastructure Setup](#infrastructure-setup)
3. [Database Migration](#database-migration)
4. [Backend Deployment](#backend-deployment)
5. [Frontend Deployment](#frontend-deployment)
6. [Post-Deployment Verification](#post-deployment-verification)
7. [Rollback Procedures](#rollback-procedures)
8. [Monitoring & Alerts](#monitoring--alerts)
9. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

Before deploying to production, complete these checks:

### Code Quality
- [ ] All tests passing: `pytest backend/ --cov`
- [ ] Coverage > 80%: `pytest backend/ --cov-report=term-missing`
- [ ] No linting errors: `flake8 backend/`
- [ ] Code formatted: `black --check backend/`
- [ ] Imports sorted: `isort --check-only backend/`
- [ ] Type hints valid: `mypy backend/` (if configured)

### Security
- [ ] No hardcoded secrets in code
- [ ] `.env.example` doesn't contain real values
- [ ] `SECRET_KEY` generated (at least 32 chars)
- [ ] `ALLOWED_ORIGINS` includes only expected domains
- [ ] Database password is strong (20+ chars, mix of types)
- [ ] CORS configured correctly (not allow_origins=["*"])

### Deployment Artifacts
- [ ] Latest code committed to git and tagged
- [ ] Docker images built and tested locally
- [ ] Environment variables documented in `.env.example`
- [ ] Database migrations tested locally
- [ ] Frontend build optimized: `npm run build`

### Team Communication
- [ ] Deployment window scheduled
- [ ] Team notified of maintenance window (if needed)
- [ ] Rollback plan communicated
- [ ] On-call person assigned

---

## Infrastructure Setup

### Prerequisites

You'll need:
- Domain name (e.g., fashionapp.example.com)
- HTTPS certificate (Let's Encrypt recommended)
- Production database (PostgreSQL recommended)
- Redis instance (for Celery queue)
- Storage for images (S3 or equivalent)
- Email service (SendGrid, Mailgun, Gmail SMTP)

### Option 1: Heroku Deployment

```bash
# Install Heroku CLI
# https://devcenter.heroku.com/articles/heroku-cli

# Create app
heroku create fashion-app-prod

# Add PostgreSQL addon
heroku addons:create heroku-postgresql:standard-0 --app fashion-app-prod

# Add Redis addon
heroku addons:create heroku-redis:premium-0 --app fashion-app-prod

# Set environment variables
heroku config:set \
  ENV=production \
  SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(48))') \
  ALLOWED_ORIGINS=https://fashionapp.example.com \
  EMAIL_VERIFICATION_REQUIRED=true \
  SMTP_HOST=smtp.gmail.com \
  SMTP_PORT=587 \
  SMTP_USERNAME=your-email@gmail.com \
  SMTP_PASSWORD=your-app-password \
  --app fashion-app-prod
```

### Option 2: AWS Deployment (ECS + RDS)

```bash
# Create RDS PostgreSQL instance
aws rds create-db-instance \
  --db-instance-identifier fashion-app-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --allocated-storage 20 \
  --master-username postgres \
  --master-user-password <STRONG_PASSWORD> \
  --publicly-accessible false

# Create ElastiCache Redis
aws elasticache create-cache-cluster \
  --cache-cluster-id fashion-app-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1

# Create ECS cluster
aws ecs create-cluster --cluster-name fashion-app

# Create ECR repository for images
aws ecr create-repository --repository-name fashion-app-backend
aws ecr create-repository --repository-name fashion-app-frontend
```

### Option 3: DigitalOcean App Platform

```bash
# Create app.yaml
cat > app.yaml << 'EOF'
name: fashion-app
services:
- name: backend
  github:
    repo: YOUR_GITHUB/fashion_app
    branch: main
  build_command: pip install -r requirements.txt
  run_command: uvicorn backend.main:app --host 0.0.0.0 --port 8080
  http_port: 8080
  envs:
  - key: ENV
    value: production
  - key: DATABASE_URL
    scope: RUN_AND_BUILD_TIME
    value: ${db.connection_string}
- name: frontend
  github:
    repo: YOUR_GITHUB/fashion_app
    branch: main
    build_command: cd frontend && npm install && npm run build
  source_dir: frontend/dist
  http_port: 3000

databases:
- name: db
  engine: PG
  version: "14"
  production: true
EOF

# Deploy
doctl apps create --spec app.yaml
```

---

## Database Migration

### Before Deployment

1. **Backup production database** (if not first deployment)
   ```bash
   # PostgreSQL backup
   pg_dump -h <host> -U <user> <database> > backup_$(date +%Y%m%d_%H%M%S).sql
   
   # Test restore locally
   psql <local_db> < backup_20250504_120000.sql
   ```

2. **Test migrations locally**
   ```bash
   # Start fresh PostgreSQL locally
   docker run -e POSTGRES_PASSWORD=test postgres:14
   
   # Run migrations
   DATABASE_URL=postgresql://postgres:test@localhost/test python backend/main.py
   
   # Verify schema
   psql -h localhost -U postgres -d test -c "\dt"
   ```

3. **Plan for zero-downtime migration**
   - Add new columns as nullable first
   - Use feature flags to roll out new code gradually
   - Never drop columns without 2-3 deployments buffer

### During Deployment

```bash
# 1. Connect to production database
export DATABASE_URL=postgresql://user:pass@host:5432/fashion_app

# 2. Run migrations (FastAPI auto-creates schema on startup)
# This happens automatically when backend starts, but verify:
python backend/view_database.py  # Check schema

# 3. If schema changes needed, run manually
python -c "
from backend.database.database import engine
from backend.database import models
models.Base.metadata.create_all(bind=engine)
"
```

### After Deployment

```bash
# Verify tables exist
psql $DATABASE_URL -c "\dt"

# Check for errors in logs
heroku logs --tail  # Or aws logs tail /ecs/fashion-app
```

---

## Backend Deployment

### Using Docker (Recommended)

```bash
# 1. Build image
docker build -t fashion-app-backend:latest -f backend/Dockerfile .

# 2. Tag for registry
docker tag fashion-app-backend:latest your-registry/fashion-app-backend:latest

# 3. Push to registry
docker push your-registry/fashion-app-backend:latest

# 4. Deploy (depends on your platform)
# Heroku
heroku container:push web --app fashion-app-prod
heroku container:release web --app fashion-app-prod

# AWS ECS (update task definition)
aws ecs update-service \
  --cluster fashion-app \
  --service backend \
  --force-new-deployment

# DigitalOcean (auto-deploys from git)
# Just push to main branch
```

### Manual Deployment (Not Recommended)

```bash
# 1. SSH into production server
ssh user@production.server

# 2. Clone/pull latest code
cd /opt/fashion-app
git pull origin main

# 3. Install dependencies
pip install -r backend/requirements.txt

# 4. Run database migrations
python backend/main.py  # Auto-creates schema

# 5. Start service
systemctl restart fashion-app
# OR
supervisorctl restart fashion-app
# OR
systemctl start fashion-app
```

### Environment Variables (Production)

```bash
# Required (no defaults)
ENV=production
SECRET_KEY=<generate with: python -c 'import secrets; print(secrets.token_urlsafe(48))'>
DATABASE_URL=postgresql://user:password@host:5432/fashion_app

# CORS & Origins
ALLOWED_ORIGINS=https://fashionapp.example.com,https://www.fashionapp.example.com

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=noreply@fashionapp.com
SMTP_PASSWORD=<app-specific-password>
SMTP_FROM_ADDRESS=noreply@fashionapp.com
EMAIL_VERIFICATION_REQUIRED=true

# Optional (defaults shown)
ACCESS_TOKEN_EXPIRATION_MINUTES=15
REFRESH_TOKEN_EXPIRATION_DAYS=7
MAX_CONCURRENT_IMAGE_JOBS=4
INFERENCE_QUEUE_ENABLED=true
```

---

## Frontend Deployment

### Build Optimization

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Check bundle size
npm run build
# Review dist/ directory size

# 3. Analyze bundle (optional)
npm install -D rollup-plugin-visualizer
npm run build -- --analyze

# 4. Optimize if needed
# - Code split lazy routes
# - Remove unused dependencies
# - Compress images
```

### Deployment Options

### Option A: Vercel (Recommended for React)

```bash
# 1. Install Vercel CLI
npm install -g vercel

# 2. Create vercel.json
cat > vercel.json << 'EOF'
{
  "buildCommand": "cd frontend && npm run build",
  "outputDirectory": "frontend/dist",
  "env": {
    "VITE_API_BASE_URL": "https://api.fashionapp.example.com"
  }
}
EOF

# 3. Deploy
vercel --prod
```

### Option B: Netlify

```bash
# 1. Create netlify.toml
cat > netlify.toml << 'EOF'
[build]
  command = "cd frontend && npm run build"
  publish = "frontend/dist"

[env.production]
  VITE_API_BASE_URL = "https://api.fashionapp.example.com"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
EOF

# 2. Connect GitHub repo in Netlify dashboard
# Auto-deploys on push to main
```

### Option C: Cloudflare Pages

```bash
# 1. Create wrangler.toml
cat > wrangler.toml << 'EOF'
name = "fashion-app"
type = "javascript"
account_id = "YOUR_ACCOUNT_ID"
workers_dev = true
compatibility_date = "2024-01-01"

[build]
command = "cd frontend && npm run build"
cwd = "."
watch_paths = ["frontend/**/*.tsx"]

[env.production]
vars = { VITE_API_BASE_URL = "https://api.fashionapp.example.com" }
EOF

# 2. Deploy
npx wrangler pages deploy frontend/dist
```

### Option D: AWS S3 + CloudFront

```bash
# 1. Create S3 bucket
aws s3 mb s3://fashion-app-frontend --region us-east-1

# 2. Enable static hosting
aws s3 website s3://fashion-app-frontend \
  --index-document index.html \
  --error-document index.html

# 3. Build and upload
cd frontend
npm run build
aws s3 sync dist/ s3://fashion-app-frontend --delete

# 4. Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id EXXXXX \
  --paths "/*"
```

### Set Backend URL

```bash
# Update backend URL in environment
export VITE_API_BASE_URL=https://api.fashionapp.example.com

# Then deploy
npm run build
```

---

## Post-Deployment Verification

### Health Checks

```bash
# 1. Check backend health
curl https://api.fashionapp.example.com/
# Expected: {"status": "healthy", "version": "1.0.0"}

# 2. Check API docs
curl https://api.fashionapp.example.com/docs
# Expected: 200 OK with Swagger UI

# 3. Check frontend
curl https://fashionapp.example.com/
# Expected: 200 OK with HTML

# 4. Test auth endpoint
curl -X POST https://api.fashionapp.example.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "TestPass123"
  }'
# Expected: 200 OK with registration response
```

### Automated Monitoring

```bash
# 1. Set up uptime monitoring (e.g., Pingdom, StatusPage)
# - Monitor: https://api.fashionapp.example.com/
# - Monitor: https://fashionapp.example.com/
# - Alert on failures

# 2. Set up log monitoring
# Heroku
heroku logs --tail --app fashion-app-prod

# AWS CloudWatch
aws logs tail /ecs/fashion-app --follow

# 3. Set up performance monitoring
# New Relic, DataDog, or similar
```

### Smoke Tests

```bash
# Run basic tests against production
cd backend
pytest tests/ -m smoke --tb=short -v

# Or manual tests
python -c "
import requests
BASE_URL = 'https://api.fashionapp.example.com'

# Test health
r = requests.get(f'{BASE_URL}/')
assert r.status_code == 200, f'Health check failed: {r.text}'

# Test CORS
r = requests.options(f'{BASE_URL}/auth/login', headers={
    'Origin': 'https://fashionapp.example.com'
})
assert 'Access-Control-Allow-Origin' in r.headers

print('✅ All smoke tests passed')
"
```

---

## Rollback Procedures

### Quick Rollback (Last 10 minutes)

```bash
# Heroku - revert to previous release
heroku releases --app fashion-app-prod
# Shows: 1) v50 2025-05-04 10:20 UTC 2) v49 2025-05-04 10:05 UTC
heroku releases:rollback v49 --app fashion-app-prod

# AWS ECS - update to previous image
aws ecs describe-services --cluster fashion-app --services backend
# Get previous task definition
aws ecs update-service \
  --cluster fashion-app \
  --service backend \
  --task-definition fashion-app-backend:49  # Previous version
```

### Full Database Rollback

```bash
# 1. Restore from backup
pg_restore -h <host> -U <user> -d fashion_app < backup_20250504_100000.sql

# 2. Verify restoration
psql -h <host> -U <user> -d fashion_app -c "SELECT COUNT(*) FROM users;"

# 3. Restart backend
heroku restart --app fashion-app-prod
```

### Communication After Rollback

```bash
# 1. Post incident update
echo "We've rolled back to the previous stable version. Service restored at 10:35 UTC."

# 2. Schedule postmortem
# Within 24-48 hours, review:
# - What went wrong?
# - How can we prevent this?
# - What testing was missing?

# 3. Fix and re-deploy
# After fix, redeploy following normal procedure
```

---

## Monitoring & Alerts

### Application Performance

```bash
# CPU usage
docker stats  # If using Docker

# Memory usage
free -h  # Server memory
ps aux | head -20  # Process memory

# Database connections
psql $DATABASE_URL -c "SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;"
```

### Error Rate Monitoring

```bash
# View last N error logs
# Heroku
heroku logs --tail -d api --app fashion-app-prod | grep ERROR

# AWS
aws logs tail /ecs/fashion-app --follow | grep ERROR
```

### Set Up Alerts

```bash
# Example: Alert if error rate > 1%

# 1. Configure in monitoring tool (DataDog, New Relic, etc.)
# 2. Set threshold: 1% error rate
# 3. Configure notifications:
#    - Slack: #incidents channel
#    - Email: ops@example.com
#    - PagerDuty: on-call engineer
```

### Key Metrics to Monitor

- **Uptime:** Should be > 99.9%
- **Response Time:** P95 < 500ms, P99 < 1000ms
- **Error Rate:** < 0.1%
- **Database Connection Pool:** < 80% utilized
- **Disk Space:** > 20% free
- **Memory:** < 85% utilized

---

## Troubleshooting

### Issue: 502 Bad Gateway

```bash
# 1. Check backend is running
curl -v https://api.fashionapp.example.com/

# 2. Check logs
heroku logs --tail --app fashion-app-prod
aws logs tail /ecs/fashion-app --follow

# 3. Common causes:
# - Backend crashed (check memory)
# - Database connection timeout (check DATABASE_URL)
# - CORS misconfigured (check ALLOWED_ORIGINS)

# 4. Restart backend
heroku restart --app fashion-app-prod
# OR
aws ecs update-service --cluster fashion-app --service backend --force-new-deployment
```

### Issue: Slow API Responses

```bash
# 1. Check database query performance
psql $DATABASE_URL -c "
SELECT query, calls, mean_time FROM pg_stat_statements 
ORDER BY mean_time DESC LIMIT 10;
"

# 2. Check image processing queue
redis-cli
> INFO
> LLEN fashion_app:queue

# 3. Scale workers if needed
heroku ps:scale worker=2 --app fashion-app-prod
# OR
aws ecs update-service --cluster fashion-app --service worker --desired-count 2
```

### Issue: Disk Space Full

```bash
# 1. Check disk usage
df -h

# 2. Find large files
du -sh /* | sort -rh | head -10

# 3. Clean up images (if needed)
# Backup encrypted images first
tar -czf images_backup_$(date +%Y%m%d).tar.gz .images_secure/

# 4. Clean old images
find backend/.images_secure/ -mtime +30 -delete  # Delete >30 days old
```

### Issue: Memory Leak

```bash
# 1. Monitor memory over time
watch -n 1 'ps aux | grep python | head -5'

# 2. Check for hung processes
ps aux | grep 'python.*main'

# 3. Restart backend service
heroku restart --app fashion-app-prod

# 4. Enable memory profiling for next deployment
export PYTHONUNBUFFERED=1
export MALLOC_TRIM_THRESHOLD_=100000
```

### Issue: Database Locked

```bash
# 1. Check active connections
psql $DATABASE_URL -c "
SELECT pid, usename, application_name, state FROM pg_stat_activity 
WHERE state != 'idle';
"

# 2. Kill hung connection
psql $DATABASE_URL -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid <> pg_backend_pid();"

# 3. Check for long-running transactions
psql $DATABASE_URL -c "
SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
FROM pg_stat_activity 
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';
"
```

---

## Deployment Checklist (Quick Reference)

Before deploying:
- [ ] Tests passing
- [ ] Security review complete
- [ ] Database backed up
- [ ] Team notified
- [ ] Rollback plan ready

During deployment:
- [ ] Deploy backend (migrations run automatically)
- [ ] Deploy frontend
- [ ] Run smoke tests
- [ ] Monitor error logs

After deployment:
- [ ] Monitor for 1 hour
- [ ] Alert on-call team if issues
- [ ] Document any problems
- [ ] Close deployment ticket

---

**Last Updated:** May 2025  
**Maintainer:** DevOps Team  
**Questions?** Contact #ops or ops@example.com
