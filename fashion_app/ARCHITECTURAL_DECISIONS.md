# Architectural Decision Records (ADRs)

This document records key architectural decisions made for the Fashion App project.

## ADR-001: FastAPI + React Separation

**Status:** ADOPTED  
**Date:** 2024-2025  
**Context:**  
The project needed to build a responsive web application with computer vision capabilities. The team evaluated monolithic architectures (e.g., Django/Jinja) vs. decoupled frontend-backend.

**Decision:**  
Use FastAPI for the backend API and React with Vite for the frontend SPA (Single Page Application).

**Rationale:**
- FastAPI provides automatic API documentation (/docs), async support, and modern Python async/await
- React + Vite offers fast development iteration, component reusability, and easy deployment to CDNs
- Decoupled architecture allows independent scaling and independent deployments
- REST API makes it easier to add mobile clients in future (React Native, Flutter, etc.)

**Consequences:**
- ✅ Fast API iteration, good DX with FastAPI auto-docs
- ✅ Frontend deployable to static hosts (Vercel, Netlify, Cloudflare Pages)
- ⚠️ Must manage CORS carefully between separate origins
- ⚠️ Session management via JWT instead of cookies

**Related:** Legacy mobile folder (see ADR-003)

---

## ADR-002: SQLAlchemy ORM + SQLite/PostgreSQL

**Status:** ADOPTED  
**Date:** 2024-2025  
**Context:**  
Need to support development (lightweight) and production (robust) database setups. Application requires persistent storage of user profiles, wardrobe items, and analysis results.

**Decision:**  
Use SQLAlchemy ORM with SQLite as default (development) and PostgreSQL for production.

**Rationale:**
- SQLAlchemy abstracts database differences; `DATABASE_URL` env var determines provider
- SQLite requires zero setup for local development
- PostgreSQL provides ACID guarantees, better concurrency for production
- ORM handles migrations and schema management cleanly
- CRUD operations isolated in `database/crud.py` for easy testing

**Consequences:**
- ✅ Easy to switch databases via environment variable
- ✅ Testable data layer with fixtures
- ✅ Schema validated at application startup
- ⚠️ ORM adds slight overhead (acceptable for this use case)
- ⚠️ Must ensure schema backfills work for existing databases

**Related:** `DATABASE_URL` environment variable, `backend/database/` module

---

## ADR-003: Legacy Mobile Folder - Archived Reference

**Status:** ARCHIVED / REFERENCE ONLY  
**Date:** 2024-2025  
**Context:**  
Early in development, a React Native scaffold was created to explore mobile platform capabilities. However, the project pivoted to focus on the web platform (React + Vite) as the primary product surface.

**Decision:**  
Keep the legacy React Native scaffold in `/legacy-mobile/` as archived reference code, but do NOT actively maintain or wire it into the build system.

**Rationale:**
- Provides a reference for future mobile platform consideration
- Demonstrates intent to support mobile in the future without active maintenance burden
- Clearly signals status to new team members
- Avoids dead code confusion in the active codebase

**Consequences:**
- ✅ Clear signal that mobile is "future consideration"
- ✅ Code preserved if mobile is needed later
- ⚠️ Outdated dependencies (React Native version may drift)
- ⚠️ TypeScript types may become stale

**Recommendation:**  
If mobile development becomes a priority, create a dedicated mobile-specific repository or sub-project rather than reviving this scaffold.

**Related:** `legacy-mobile/README.md`

---

## ADR-004: Modular Backend Architecture

**Status:** ADOPTED  
**Date:** May 2025  
**Context:**  
Original main.py grew to 1770 lines, mixing configuration, models, authentication, and 50+ endpoints. Difficult to maintain, test, and extend.

**Decision:**  
Refactor backend into modular structure:
- `config.py` - Configuration constants
- `schemas.py` - Pydantic validation models
- `auth_utils.py` - Authentication utilities
- `utils.py` - Shared utilities
- `routers/` - Domain-specific endpoint routers
- `database/` - ORM models and CRUD operations
- `services/` - Business logic (vision, recommendations)

**Rationale:**
- Single Responsibility Principle: each module has clear purpose
- Improved testability: can test routers independently
- Better code reuse: utilities shared across routers
- Easier onboarding: new team members find code quickly
- Scales better: add new endpoints without modifying main.py

**Consequences:**
- ✅ 93% reduction in main.py (1770 → 110 lines)
- ✅ 100% type hint coverage (up from 30%)
- ✅ Clear import paths and dependencies
- ⚠️ Slight increase in total number of files (but worth it)
- ⚠️ New pattern for adding endpoints (but well documented)

**Related:** `CODE_QUALITY_REFACTORING.md`, `REFACTORED_CODEBASE_GUIDE.md`

---

## ADR-005: JWT + Session Tracking

**Status:** ADOPTED  
**Date:** 2024-2025  
**Context:**  
Application needs secure authentication with user session management. Must support logging out individual sessions and all sessions.

**Decision:**  
Use JWT (JSON Web Tokens) for stateless authentication combined with a refresh token rotation strategy and session tracking in database.

**Rationale:**
- JWT enables stateless API (no session server needed)
- Access tokens (short-lived) minimize exposure if compromised
- Refresh tokens (long-lived) in database allow revocation
- Session tracking allows granular logout (revoke specific device, revoke all)
- Support for multiple devices simultaneously

**Consequences:**
- ✅ Scalable: stateless backend can run multiple instances
- ✅ Secure: short-lived access tokens limit damage window
- ✅ Flexible: support mobile + web simultaneously
- ⚠️ Revoked tokens only checked at refresh (not immediately)
- ⚠️ Logout is eventual consistency (not instantaneous across clients)

**Related:** `routers/auth.py`, `database/models.py` (RefreshToken)

---

## ADR-006: CI/CD Pipeline with GitHub Actions

**Status:** ADOPTED  
**Date:** May 2025  
**Context:**  
Tests were not running consistently. No automated checks before merge. Manual testing prone to human error.

**Decision:**  
Implement GitHub Actions workflow to:
- Run tests on Python 3.9, 3.10, 3.11
- Generate coverage reports
- Run linting (flake8, black, isort)
- Upload coverage to Codecov

**Rationale:**
- Automated testing catches regressions early
- Coverage tracking motivates test writing
- Code quality checks enforce consistency
- Works on every commit and PR

**Consequences:**
- ✅ Confidence in code quality before merge
- ✅ Consistent formatting and linting
- ✅ Coverage visibility (motivates testing)
- ⚠️ May take 3-5 min per commit (acceptable)
- ⚠️ Failed checks block merge (by design)

**Related:** `.github/workflows/tests.yml`, `pytest.ini`

---

## ADR-007: Encrypted Image Storage

**Status:** ADOPTED  
**Date:** 2024-2025  
**Context:**  
Application handles sensitive user images (profile photos, wardrobe items). Images should not be accessible without authentication or direct server access.

**Decision:**  
Encrypt images at rest using AES-256-GCM with user-specific encryption keys derived from secret key + user ID. Store encrypted images in `backend/.images_secure/` with metadata in database.

**Rationale:**
- User images are PII; encryption at rest adds security layer
- Images served through authenticated API endpoint only
- Encryption key tied to app secret, not stored with images
- Easy to migrate: re-encrypt with new key if needed

**Consequences:**
- ✅ Images not accessible without authentication
- ✅ Images not readable even if disk is compromised
- ⚠️ Encryption/decryption on every image access (CPU cost)
- ⚠️ Image data always encrypted in memory (complex)

**Related:** `services/secure_image_storage.py`, `routers/images.py`

---

## ADR-008: Vision Services as Separate Layer

**Status:** ADOPTED  
**Date:** 2024-2025  
**Context:**  
Application needs to classify clothing, analyze skin tone, estimate body shape. These tasks are CPU-intensive and could block API responses if done synchronously.

**Decision:**  
Implement vision services in separate layer (`services/`) with two execution modes:
1. Synchronous: For simple analysis (dev mode or low load)
2. Async via Celery queue: For production (heavy analysis offloaded to workers)

**Rationale:**
- Services testable independently of HTTP layer
- Can scale workers independently based on load
- Separates concerns: API handling vs. ML/CV processing
- Easy to add new analysis features (add new service)

**Consequences:**
- ✅ Non-blocking API responses
- ✅ Scales to handle many concurrent analyses
- ✅ Easy to add new vision services
- ⚠️ Requires Redis + Celery for production
- ⚠️ Async mode adds complexity (job tracking)

**Related:** `services/`, `config.py` (INFERENCE_QUEUE_ENABLED), `routers/jobs.py`

---

## ADR-009: Environment-Based Configuration

**Status:** ADOPTED  
**Date:** 2024-2025  
**Context:**  
Application must work across development, staging, and production environments with different settings (database, SMTP, API keys, etc.).

**Decision:**  
Use environment variables for all configuration. Load from `.env` file in development, from system environment in production. Central `config.py` validates and provides defaults.

**Rationale:**
- Single deployment artifact works in any environment
- Secrets never committed to git
- Easy to override per environment
- Clear contract of required variables

**Consequences:**
- ✅ Secure: secrets in .env (gitignored)
- ✅ Flexible: same code runs everywhere
- ✅ Clear: `config.py` documents all settings
- ⚠️ Requires discipline: always use config.py, not direct env access
- ⚠️ Must document all required env vars

**Related:** `config.py`, `.env.example`, deployment documentation

---

## ADR-010: Type Hints for Code Quality

**Status:** ADOPTED  
**Date:** May 2025  
**Context:**  
Code lacked type information, making it hard to understand function contracts and catch errors early.

**Decision:**  
Mandate full type hints on all public functions:
- Parameter types: `def func(param: str, count: int) -> None:`
- Return types: always specified
- Complex types: `Dict[str, Any]`, `Optional[List[str]]`, etc.
- Docstrings: Args, Returns, Raises

**Rationale:**
- IDE auto-completion improves developer experience
- Type checker (mypy) catches errors before runtime
- Self-documenting code: function signature is clear contract
- Easier refactoring: type checker prevents breaking changes

**Consequences:**
- ✅ Fewer runtime errors
- ✅ Better IDE support
- ✅ Self-documenting code
- ⚠️ More verbose (acceptable trade-off)
- ⚠️ Requires discipline in code review

**Related:** All modules in `backend/`, type checking configured in IDE

---

## ADR-011: Rate Limiting Strategy

**Status:** ADOPTED  
**Date:** 2024-2025  
**Context:**  
API endpoints are public and need protection against abuse (brute force, DDoS, excessive analysis jobs).

**Decision:**  
Implement rate limiting using SlowAPI library with two-tier strategy:
1. **Per-endpoint:** Different limits based on endpoint cost (auth: 10/min, analysis: 10/min, health: 120/min)
2. **Per-key:** Prefer authenticated user ID over IP for limits (encourages auth, punishes bad actors)

**Rationale:**
- Lightweight: in-memory rate limiter
- Flexible: per-endpoint and per-key limits
- User-aware: different limits for auth vs. anon
- Easy to configure: one decorator per endpoint

**Consequences:**
- ✅ Protects against brute force attacks
- ✅ Prevents abuse of expensive endpoints
- ✅ Scales to multiple instances (with shared Redis)
- ⚠️ In-memory limits don't work across multiple API instances (need Redis)
- ⚠️ Resets on app restart

**Related:** `config.py` (limiter config), `utils.py` (get_rate_limit_key)

---

## Decisions Under Review (Future ADRs)

- Mobile platform: When/if to revive legacy-mobile or create new solution
- GraphQL vs REST: Stick with REST or add GraphQL layer?
- Real-time features: Should we add WebSocket support for live updates?
- Microservices: Scale beyond monolith or maintain single codebase?

---

## How to Add a New ADR

1. Identify an architectural decision that affects multiple systems
2. Create new section with:
   - **ADR-XXX:** Short title
   - **Status:** PROPOSED/ADOPTED/REJECTED
   - **Context:** Why this decision is needed
   - **Decision:** What was decided
   - **Rationale:** Why this decision
   - **Consequences:** Trade-offs and effects
   - **Related:** Links to related code

3. Update main README to reference key ADRs
4. Share with team for review and discussion

---

**Last Updated:** May 2025  
**Maintainer:** Development Team
