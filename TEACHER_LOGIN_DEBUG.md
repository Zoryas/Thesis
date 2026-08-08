# Teacher Login / Sidebar Debug

## Purpose

This file documents the temporary debug changes added to help diagnose why teacher login appears to redirect back to the login page and why the teacher sidebar still shows placeholder values.

## Files changed

- `login.js`
- `api.js`

## What was added

### `login.js`
- Added `console.debug("login result:", result);` after the login response is received.
- This logs the exact object returned by `/api/auth/login`.

### `api.js`
- Added debug output in `ReadWiseAPI.me()`:
  - initial cached user and token state
  - refresh call response when a cached user exists
  - server response when no cached user exists

## Why this helps

The teacher pages rely on a valid authenticated teacher user object from `ReadWiseAPI.me()`.
If the login page succeeds but the teacher page still redirects to `../login.html`, the console logs will show whether:

- the login response included a valid user object
- the auth token was saved into `localStorage`
- the `me()` call returned a fresh authenticated user
- the user object contains `role: "teacher"` and `teacher.fullName`

## How to use

1. Open the browser DevTools console.
2. Log in as a teacher.
3. Observe the logged objects under:
   - `login result:`
   - `ReadWiseAPI.me() start`
   - `ReadWiseAPI.me() refresh response`
   - `ReadWiseAPI.me() server response`
4. Confirm the responses include a teacher user object and token.

## Expected results

A successful teacher login should show:

- `login result:` with `data.user.role === "teacher"`
- `data.user.teacher.fullName` and `data.user.teacher.department`
- `ReadWiseAPI.me()` returning a valid teacher user object

If the teacher page still redirects, the logs should reveal whether the problem is in the login response, cache/token storage, or the `/api/auth/me` authentication check.
