# Legacy Mobile Scaffold (Archived)

**Status:** ARCHIVED / REFERENCE ONLY  
**Active Product:** See `frontend/` (React web) and `backend/` (FastAPI)

---

## What This Is

This folder contains an early-stage React Native scaffold that was created during initial exploration of mobile platform capabilities. It is **NOT actively maintained** and is **NOT wired into the current product**.

## Why It's Here

1. **Reference:** Shows intent to support mobile platforms in the future
2. **Preserved:** Code retained if mobile becomes a priority later
3. **Documented:** Clear status prevents confusion for new team members

## Current Status

- ❌ Not actively developed
- ❌ Not included in build pipeline
- ❌ Dependencies may be outdated (React Native versions drift)
- ❌ TypeScript types may be stale
- ✅ Safe to ignore for current development
- ✅ Available as reference if needed

## If Mobile Becomes a Priority

**DO NOT** revive this scaffold directly. Instead:

1. **Create new repo** for mobile app (separate from web)
2. **Use current tooling:** React Native CLI, Expo, or Flutter
3. **Share API layer:** Use same backend (`backend/` FastAPI)
4. **Separate concerns:** Mobile has own package.json, build scripts, CI/CD

### Example Structure for Future Mobile

```
fashion-app/
├── backend/          # Shared API
├── frontend/         # React web (active)
├── mobile/           # React Native (if revived)
│   ├── package.json  # Separate dependencies
│   ├── app.json      # Expo config
│   └── ...
└── docs/             # Shared documentation
```

## Recommendations

- **For now:** Ignore this folder during development
- **If cleaning up:** Move to separate repo if not needed
- **If reviving:** Start fresh with current tooling, share backend only

---

See `ARCHITECTURAL_DECISIONS.md` (ADR-003) for architectural decision on legacy mobile.

**Last Updated:** May 2025
