# Upstream Contribution Tracker

Base branch: `cb6/v0.6.5-alpha-stable`
Validation environment: CB6 (desktop, iOS, Android)
Approach: adapt useful upstream/community code; avoid wholesale replacement.

## Branches created

- `contrib/security/dependency-hardening`
  - Scope: dependency updates, security lint/hardening, low-risk fixes
  - PR target: upstream maintenance/security

- `contrib/reliability/token-refresh-guardrails`
  - Scope: token refresh edge cases, expiry/refresh race handling, safer fallback paths
  - PR target: upstream auth reliability

- `contrib/reliability/login-logout-state-consistency`
  - Scope: stale session cleanup, logout/login sequencing consistency, deterministic state transitions
  - PR target: upstream auth/session consistency

## Merge discipline

1. Small focused commits
2. One concern per PR
3. Include reproduction + fix + CB6 test evidence
4. Prefer cherry-picking useful upstream/community bits over rewrites

## Test gate (required before PR)

- [ ] Desktop login + logout + relogin
- [ ] iOS login + logout + relogin
- [ ] Android login + logout + relogin
- [ ] Token refresh on idle/expiry window
- [ ] HA restart behavior
- [ ] No login loop / blank screen / forced reauth spikes

## Submission order

1. Security/dependency hardening
2. Token refresh guardrails
3. Login/logout consistency
