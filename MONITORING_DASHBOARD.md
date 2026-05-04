# Monitoring Dashboard Specification

This project already records model metrics, feedback volume, structured request logs, and rate-limit events. This document turns those signals into an operational dashboard so performance issues are visible instead of buried in logs.

## Data Sources

- `GET /admin/metrics/models` for model accuracy, helpful rate, drift, and deployment history
- `GET /admin/metrics/feedback-volume` for feedback throughput and learning-system health
- Structured application logs for request latency, 5xx errors, overload events, and rate limiting
- Celery worker logs for retraining job failures and queue backlog
- Database table `model_metrics` for historical model monitoring

## Recommended Panels

### 1. API Health

- Request rate per minute
- p50 / p95 / p99 request latency
- 4xx and 5xx response counts
- Rate-limit events per route
- Overload rejections from image-processing paths

### 2. Learning System Health

- Feedback points collected in the last 7 / 30 days
- Outfit rating count
- Recommendation helpful rate
- Model drift score
- Retraining job success/failure count

### 3. Model Performance

- Latest accuracy for `outfit_scoring`
- Latest helpful rate for recommendation models
- Version deployed for each model
- Time since last successful retrain
- Candidate vs control experiment outcomes

### 4. Infrastructure Signals

- Celery worker queue depth
- Celery worker failures
- Redis availability
- Database connection errors
- Image-job saturation events

## Alert Thresholds

Use alerts that are actionable, not noisy.

- API 5xx rate > 2% for 5 minutes
- p95 latency > 1500 ms for 10 minutes
- Rate-limit events spike 3x above baseline
- Image overload rejections > 10 in 10 minutes
- Retraining job failure
- Model drift score > 0.10
- Feedback volume falls to zero for 3 consecutive days
- No successful retrain for 14 days when feedback volume is healthy

## Dashboard Layout

### Row 1: User-Facing Health

- Requests / minute
- p95 latency
- 5xx errors
- Rate limits

### Row 2: Learning Pipeline

- Feedback volume
- Helpful rate
- Model drift
- Retraining success rate

### Row 3: Deployment and Rollback

- Current active model version
- Last deploy time
- Last rollback time
- Experiment decisions

### Row 4: Worker and Queue

- Celery queue depth
- Worker uptime
- Worker failures
- Redis status

## Suggested Implementation

This repo does not require a brand-new metrics stack to start. You can build the first version with:

- Grafana dashboards backed by Prometheus or log-based metrics
- Log aggregation from the structured JSON logs emitted by the API
- A small admin page that reads the existing `/admin/metrics/...` endpoints

## Operating Rule

If a metric does not lead to a decision, remove it from the dashboard. The goal is faster incident detection and clearer retraining decisions, not more charts.