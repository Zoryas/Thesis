# DB Migration Plan (Client Cache/Session → Database-Backed)

## Objective
Move important runtime state from browser storage (`localStorage`, `sessionStorage`) to database-backed flows where appropriate, while preserving UX and reliability.

---

## 1) Current Inventory (Not Fully DB-Connected)

## A. `api.js`

### 1. `readwise_active_week_v1` (localStorage)
- **Where used**: `api.js`
- **Purpose**: Stores selected active week in browser.
- **Current behavior**: Per-browser preference; not shared across devices/sessions.
- **Risk**: Inconsistent week context if user switches device/browser.

### 2. `readwise_user_v1` (localStorage)
- **Where used**: `api.js`
- **Purpose**: Caches user profile for quick load.
- **Current behavior**: Stale data possible if server-side profile changes.
- **Risk**: UI may temporarily show outdated user data.

### 3. `readwise_token` (localStorage)
- **Where used**: `api.js`
- **Purpose**: Stores auth token for API calls.
- **Current behavior**: Client-managed auth token.
- **Risk**: Token persists in browser storage; security and invalidation concerns.

---

## B. `pages/student-reading.html`

### 4. `readingSecs_<week>_<pid>` (sessionStorage)
- **Where used**: reading timer page
- **Purpose**: Persists in-progress reading timer before submit.
- **Current behavior**: Local only until submit.
- **Risk**: Lost if session is cleared/crashes, not visible cross-device.

### 5. `readingLocked_<week>_<pid>` (sessionStorage)
- **Where used**: reading/assessment lock behavior
- **Purpose**: Prevent returning to passage after proceeding.
- **Current behavior**: Browser-local lock.
- **Risk**: Bypass possible on new browser/device.

### 6. `readingTime_<pid>` (sessionStorage)
- **Where used**: pass formatted reading time to question flow
- **Purpose**: Convenience transfer between pages.
- **Current behavior**: Local only.
- **Risk**: Inconsistent with server source of truth.

### 7. `readingTimeQueue_v1` (localStorage)
- **Where used**: offline/failed save queue
- **Purpose**: Queue reading-time payload when API call fails.
- **Current behavior**: Retry on load/online event.
- **Risk**: Queue stuck indefinitely if failures persist; not visible to server until retry.

---

## 2) Migration Priority

## Priority P1 (Critical integrity / anti-bypass)
1. `readingLocked_<week>_<pid>` → server-side lock
2. `readingSecs_<week>_<pid>` → optional server draft/progress state
3. `readingTimeQueue_v1` observability + retry policy

## Priority P2 (Consistency)
4. `readwise_active_week_v1` → user preference in DB
5. `readwise_user_v1` → shorten TTL/refresh strategy
6. `readingTime_<pid>` → derive from server response/session endpoint

## Priority P3 (Security hardening)
7. `readwise_token` strategy improvements (httpOnly cookies/session tokens if feasible)

---

## 3) Recommended DB-Backed Design

## A. Server-side reading lock (replace browser-only lock)
- Add/extend table (example): `student_reading_sessions`
  - `student_id`, `passage_id`, `week_no`
  - `started_at`, `completed_at`
  - `is_locked` (or derive lock from `completed_at IS NOT NULL`)
- Enforce lock in backend:
  - Reading endpoint returns lock state.
  - Question submission endpoint validates lock transition.
  - Passage read endpoint blocks when already completed if policy requires.

## B. In-progress reading state
- New endpoint example: `POST /api/student/reading-progress`
  - Payload: `passageId`, `week`, `readingSeconds`, `eventId`
- Save periodic progress (e.g., every 10–20s) or on visibility/beforeunload.
- Keep client timer for UX, but server becomes source of truth.

## C. Reliable queue handling
- Keep local queue only as transient fallback.
- Add retry metadata:
  - `attemptCount`, `lastTriedAt`, `createdAt`.
- Add max retry/backoff policy and user-visible warning when stale.
- Optional: server endpoint for bulk flush.

## D. Active week preference in DB
- Add column/table:
  - `users.active_week_preference` or `user_preferences`.
- Sync rules:
  - Load from server on login.
  - Update server on week change.
  - Keep local cache as fallback only.

## E. User cache freshness
- Keep local cache but treat as temporary:
  - refresh on app bootstrap, role-sensitive pages, and after profile updates.
  - optional TTL timestamp in cache.

## F. Auth storage hardening
- Long-term: migrate token handling to secure httpOnly cookie session where possible.
- If token remains in localStorage, enforce short expiry + refresh/revocation strategy.

---

## 4) Proposed API Additions/Adjustments

1. `GET /api/student/reading-state?passageId=&week=`
   - returns: `isLocked`, `readingSeconds`, `completedAt`

2. `POST /api/student/reading-progress`
   - idempotent by `eventId`
   - updates reading seconds

3. `POST /api/student/reading-complete`
   - finalizes reading, sets lock atomically

4. `GET/PUT /api/user/preferences`
   - includes `activeWeek`

5. (Optional) `POST /api/student/reading-progress/bulk`
   - flush multiple queued items

---

## 5) Frontend Migration Steps

1. **Student reading page**
   - Replace `readingLocked_*` checks with server `reading-state`.
   - Save progress periodically to backend.
   - Keep local queue only for temporary offline support.

2. **API layer**
   - Add wrappers for new endpoints.
   - Add retry/backoff policy for queued events.

3. **Week preference**
   - Read/write active week from server preference endpoint.
   - localStorage remains fallback cache only.

4. **User cache**
   - Add freshness policy (refresh triggers + optional TTL).

5. **Auth**
   - Plan secure token/session approach and incremental rollout.

---

## 6) Testing Plan

## Critical-path testing
- Reading lock enforced server-side across browser/device.
- Reading completion persists in DB and redirects correctly.
- Offline save fallback queues then flushes correctly.
- Active week persists across new sessions/device (after DB preference migration).

## Thorough testing
- All reading flows: happy path, cancel path, retries, duplicate events.
- Error paths: network failures, unauthorized, stale tokens.
- Cross-device consistency for lock and preference state.
- API edge cases via curl/Postman:
  - duplicate `eventId`
  - malformed payload
  - unauthorized requests
  - race condition attempts (complete twice)

---

## 7) Rollout Strategy

1. Introduce backend state endpoints and DB columns/tables.
2. Ship frontend reading-state integration behind safe fallback.
3. Monitor logs for queue failures and lock mismatches.
4. Remove/de-emphasize browser-only lock logic after validation.
5. Final hardening pass for auth token strategy.

---

## 8) Success Criteria

- No critical flow depends solely on browser storage.
- Reading lock is enforceable server-side.
- Reading progress and completion are recoverable and auditable in DB.
- User week preference consistent across sessions/devices.
- Local cache remains performance optimization, not source of truth.
