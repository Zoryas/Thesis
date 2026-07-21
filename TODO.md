# TODO - Step 3 Migration (`readwise_token` -> cookie session)

- [x] Confirm existing `app.py` auth/session flow points to update
- [x] Confirm existing `api.js` token/header flow points to update
- [ ] Update backend auth to prioritize server session cookie (HttpOnly/Secure/SameSite policy already configured)
- [ ] Keep temporary token fallback for compatibility during rollout
- [ ] Update frontend request layer to stop persistent localStorage token usage
- [ ] Ensure frontend requests include cookies (`credentials: "include"`)
- [ ] Ensure login/logout/me flows work with cookie session as source of truth
- [ ] Run critical-path validation:
  - [ ] Login creates authenticated session
  - [ ] `/api/auth/me` works after refresh via cookie
  - [ ] Logout clears session and rejects subsequent `/api/auth/me`
  - [ ] Invalid/no token header does not break session-based auth
- [ ] Summarize Step 3 result in simple terms (classroom + deployment ready)
