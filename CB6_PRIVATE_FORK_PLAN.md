# CB6 Plan — `hass-oidc-auth` Private Fork (stability-first)

## Goal
Run a **stable, security-maintained fork** for CB6 on top of `v0.6.5-alpha`, validate on CB6 end-to-end, then submit a focused upstream PR only after successful field testing.

## Repository Setup
- Upstream: `christiaangoossens/hass-oidc-auth` (`origin`)
- Fork: `shad0wca7/hass-oidc-auth` (`fork`)
- Local path: `projects/code/hass-oidc-auth-cb6`

## Strategy (narrow scope)
1. Baseline from `v0.6.5-alpha` (or nearest compatible commit if tag is unavailable).
2. Keep patch set small:
   - security fixes
   - auth/session reliability
   - minimal UX tweaks only (no deep frontend injection rewrite)
3. Test on CB6 against desktop + mobile clients.
4. Only then prepare PR(s), ideally split by concern (security vs reliability vs UX).

---

## Branch Model

### Long-lived branches
- `main` → tracking upstream default branch (read-only locally)
- `cb6/v0.6.5-alpha-base` → pinned baseline for CB6
- `cb6/v0.6.5-alpha-stable` → integration branch for tested fixes

### Working branches (short-lived)
- `fix/security/<topic>`
- `fix/reliability/<topic>`
- `fix/ux/<topic>`

### PR branches (upstream-ready)
- `pr/<ticket-or-scope>` from cleaned commits (squashed/cherry-picked)

---

## Execution Steps

## Phase 0 — Baseline pin
1. Fetch all tags and locate baseline:
   - Preferred: `v0.6.5-alpha`
   - Fallback: nearest known-good 0.6.5-alpha commit
2. Create base branch:
   - `cb6/v0.6.5-alpha-base`
3. Create integration branch:
   - `cb6/v0.6.5-alpha-stable`

## Phase 1 — Hardening patch set
Implement only low-risk changes:
- dependency/security patches (non-breaking)
- token refresh robustness
- logout/login flow consistency
- clearer error handling and logging around OIDC callback/session edges

## Phase 2 — CB6 regression matrix
For each candidate patch branch merged into `cb6/v0.6.5-alpha-stable`, run:

### Environments
- Home Assistant desktop web
- iOS companion app
- Android companion app

### Test cases
1. Fresh login
2. Logout → login
3. Token refresh on session age/expiry
4. Restart HA, then reconnect session behavior
5. Invalid/expired token handling (graceful redirect/error)
6. Multi-attempt login race (quick repeated taps)

### Pass criteria
- No auth dead-end loops
- No blank login surface on mobile
- No unexpected forced re-auth during normal use window
- Logs are actionable (clear errors, no noisy stack spam)

## Phase 3 — Soak test on CB6
- Run the stable branch for 3–7 days on CB6
- Capture:
  - auth failures/day
  - forced relogins
  - mobile login regressions
  - any crash/restart correlation

Go/no-go for upstream PR:
- **Go**: zero critical auth blockers + reproducible fixes
- **No-go**: unresolved mobile/frontend behavior requiring deep injection work

## Phase 4 — Upstream PR prep
- Split changes into minimal thematic PRs:
  1. security/maintenance
  2. reliability/auth flow
  3. tiny UX (if universally safe)
- Rebase/cherry-pick onto latest upstream tag/branch
- Include concise reproduction + test evidence from CB6

---

## Rollback Plan (CB6)
If regression appears after deploy:
1. Revert HA custom component to previous known-good commit/tag.
2. Restart HA service.
3. Verify login still works on desktop + both mobile clients.
4. Keep incident note with timestamp, commit hash, and symptom.

Rollback command pattern (example):
- Checkout prior commit on `cb6/v0.6.5-alpha-stable`
- redeploy custom component
- restart HA

---

## Rebase/Sync Policy
- Sync from upstream **tagged releases only** (not every commit on `main`).
- Re-run full regression matrix after each rebase.
- Keep fork diff small and documented in this file.

---

## Deliverables
- [ ] `cb6/v0.6.5-alpha-base` branch created and pinned
- [ ] `cb6/v0.6.5-alpha-stable` integration branch active
- [ ] Security/reliability patch branches merged into stable branch
- [ ] Regression results doc added (`CB6_TEST_RESULTS.md`)
- [ ] Soak test summary added (`CB6_SOAK_REPORT.md`)
- [ ] Upstream PR branch prepared after successful CB6 validation

---

## Notes
- We are explicitly **not** committing to full `v0.7` frontend injection rework yet.
- If mobile UX remains blocked after narrow fixes, open a separate `v0.7-experimental` track with explicit maintenance budget.
