# Incident Response Runbook

Use this runbook when the API, model pipeline, or worker queue degrades. The goal is to restore service quickly, then investigate root cause after the system is stable.

## Severity Levels

- **SEV-1:** Complete outage, data loss, or security incident
- **SEV-2:** Major feature outage, widespread 5xxs, retraining failure with customer impact
- **SEV-3:** Degraded performance, high latency, repeated rate limits, partial learning-system failure
- **SEV-4:** Minor bug or warning with no immediate user impact

## First 10 Minutes

1. Confirm the incident with the dashboard and recent logs.
2. Identify the blast radius: API, worker queue, model retraining, or database.
3. Check whether the issue is new deploy-related, load-related, or data-related.
4. If user-facing impact is high, pause nonessential background jobs.
5. Start an incident log with timestamp, symptom, and suspected cause.

## Triage Checklist

- API health endpoint returns successfully
- 5xx rate and p95 latency are within target
- Rate limiting is not suppressing valid traffic
- Celery worker queue is healthy
- Redis is reachable
- Database connections are available
- Retraining and metrics tasks are completing
- Model registry shows a valid active version

## Common Failure Modes

### 1. API Overload

Symptoms:
- p95 latency spikes
- 503 overload responses on image endpoints
- Increased rate-limit events

Actions:
- Scale API replicas if possible
- Reduce image-processing concurrency temporarily
- Verify Redis and Celery are healthy
- Confirm whether a bad client or bot is driving load

### 2. Worker Queue Backlog

Symptoms:
- retraining jobs delayed
- inference jobs stuck in queued state
- Celery worker errors

Actions:
- Restart failed workers
- Check Redis connectivity
- Reduce scheduled retraining cadence if backlog persists
- Disable noncritical jobs until the queue clears

### 3. Model Regression

Symptoms:
- drift score exceeds threshold
- model metrics fall below baseline
- user feedback becomes negative after deploy

Actions:
- Compare candidate vs control experiment record
- Roll back to the previous active model version using the registry
- Freeze automatic promotion until root cause is understood
- Re-run evaluation on the candidate version if needed

### 4. Database Problems

Symptoms:
- 500s on write-heavy endpoints
- connection timeout errors
- metrics or feedback writes failing

Actions:
- Check connection pool saturation
- Verify database availability
- Pause retraining if it is amplifying load
- Restore from backup only if corruption or data loss is confirmed

## Rollback Procedure

1. Identify the current active model version.
2. Restore the previous active version from the model registry.
3. Confirm the rollback event was written to lineage logs.
4. Validate recommendations and classification endpoints with smoke tests.
5. Leave automatic promotion disabled until the issue is reviewed.

## Communication Plan

- **SEV-1:** Notify the team immediately and post status updates every 15 minutes.
- **SEV-2:** Notify within 15 minutes and update every 30 minutes.
- **SEV-3:** Notify in the team channel and update at least once during remediation.

## Resolution Criteria

An incident can be closed when:

- User-facing error rate is back to baseline
- Latency is within target for at least 30 minutes
- Queue backlog is cleared or controlled
- Root cause is documented
- Follow-up tasks are created

## Post-Incident Review

Capture:

- What happened
- How it was detected
- What was impacted
- What fixed it
- What prevented faster detection or recovery
- What instrumentation or guardrails should be added next

## Ownership

- API incidents: backend maintainer
- Worker incidents: ML/worker maintainer
- Database incidents: platform or ops owner
- Security incidents: treat as SEV-1 until proven otherwise