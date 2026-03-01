# DELIVERY_[FEATURE_NAME].md

> **Status:** 🔄 UPDATES_PENDING | ✅ UPDATES_COMPLETE
> **Delivered:** YYYY-MM-DD HH:MM
> **Grooming Handoff:** (inline analysis — single session model)
> **CC Session:** [session identifier if trackable]

---

## Summary

**What was delivered:**
[1-2 sentence summary of what CC actually built]

**Deviation from spec:** None | Minor | Significant
[If any, brief explanation]

---

## Completed Items

### Features Implemented
- [x] [Feature 1 — specific]
- [x] [Feature 2]
- [x] [Feature 3]

### Files Created
| File | Purpose |
|------|---------|
| `path/to/file.ts` | [what it does] |

### Files Modified
| File | Changes |
|------|---------|
| `path/to/file.ts` | [what changed] |

---

## Deployments

- [ ] Database migration run
- [ ] Backend functions deployed
- [ ] Frontend deployed to host
- [ ] CDN cache invalidated
- [ ] Code committed
- [ ] N/A — no deployment needed

> Skip items that don't apply. Note failures in Blocked Items.

---

## Tests

| Test File | Type | Status |
|-----------|------|--------|
| `tests/e2e/[name].test.ts` | E2E | ✅ Passing / ⚠️ Skipped / ❌ Failing |
| `tests/unit/[name].test.ts` | Unit | ✅ / ⚠️ / ❌ |

**Coverage notes:** [Any gaps or areas needing manual testing]

---

## Blocked Items

> Items that could NOT be completed — need resolution before feature is fully live

| Item | Reason | Action Required |
|------|--------|-----------------|
| [Blocked thing] | [Why blocked] | [What needs to happen] |

---

## Future TODOs

> Items explicitly deferred — add to ROADMAP or next grooming cycle

| Item | Phase | Notes |
|------|-------|-------|
| [Deferred feature] | Phase 2 / Pre-launch / Future | [Why deferred] |

---

## Catalog Updates (per EXECUTOR_STANDARDS Section 7)

> If this task was tagged as JM_NEW_UF, JM_NEW, or DEFERRED_PROMOTED during breakdown,
> the executor MUST update the catalog docs below. Check each that applies.

### USER_FLOWS.md
- [ ] Found `[PLANNED]` entry with flow ID: `flow-{draft_id}` → Updated to `[IMPLEMENTED]`
- [ ] Filled in `Steps:` with actual implemented steps
- [ ] Updated `Test file:` with Playwright test path
- [ ] Updated `Verification:` from TBD to playwright/manual/mixed
- [ ] N/A — this task does not serve a [PLANNED] user flow

### JOURNEY_MAPPINGS.md
- [ ] Found `[PLANNED]` journey entry → Updated to `IN PROGRESS` or `IMPLEMENTED`
- [ ] Added step definitions
- [ ] N/A — this task does not introduce a new journey

---

## Documentation Updates Needed

> The update phase should update these docs based on this delivery

| Document | Update Type | Details |
|----------|-------------|---------|
| `ARCHITECTURE.md` | Add section / Update feature log | [what to add] |
| `docs/USER_FLOWS.md` | Update flow status | [which flows — see Catalog Updates above] |
| `docs/JOURNEY_MAPPINGS.md` | Update journey status | [which journeys — see Catalog Updates above] |
| `ROADMAP.md` | Mark complete | [which items] |
