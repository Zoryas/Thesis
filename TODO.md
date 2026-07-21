# TODO - Step 2 Migration (`readwise_user_v1` cache strategy)

- [ ] Confirm existing `api.js` user cache/auth flow points to update
- [ ] Update `api.js` so cached user is fast fallback only
- [ ] Ensure server re-hydration (`/api/auth/me`) is always attempted when authenticated
- [ ] Ensure login/profile mutation paths refresh cache from server-authoritative data
- [ ] Ensure logout clears token + cached user consistently
- [ ] Run critical-path validation:
  - [ ] Login flow (cached paint + server refresh)
  - [ ] Profile update flow refreshes cache/UI
  - [ ] Logout clears cache and token
- [ ] Summarize Step 2 result in simple terms
