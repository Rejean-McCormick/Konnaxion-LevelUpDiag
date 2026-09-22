# Upgrade notes from Konnaxion Mega Pack v2

## Retained Konnaxion logic

The `konnaxion_diag/` domain implementation and N00..N11 taxonomy are retained. The upgraded package changes the LevelUpDiag engine around them rather than replacing the Konnaxion tests with generic diagnostics.

## Evidence retention

Historical LevelUpDiag runtime evidence is not migrated. On each campaign start, current-only retention removes generated directories from earlier/legacy runs under the configured `.levelupdiag` control directory. This is intentional: the diagnostic sequence and current evidence are the source of truth.

## Correlation change

N11 previously treated all N01..N10 as expected even for focused campaigns. N00 now records the active campaign and ordered expected levels. N11 reports missing evidence only for levels actually expected in that campaign.

## Compatibility

`scripts/run_konnaxion.py <campaign>` still works. New direct CLI usage is `python levelupdiag.py run <campaign>`.

## 3.1.0 — Common authentication alignment (2026-09-11)

- N04 audits Konnaxion standalone-first django-allauth/OIDC source invariants.
- N07 runs `konnaxion/users/tests/test_auth_policy.py`.
- `auth-debug` now includes N07.
- Legacy DRF password-token and Auth0 residue are surfaced explicitly.
- Production CSRF, admin-allauth and same-origin API conventions are checked.

## 3.2.0 — Worlds-aware qualification (2026-09-22)

- Added `world-switch` campaign while retaining the exact N00..N11 taxonomy.
- N01 detects incomplete World Switch overlay surfaces.
- N02 runs `konnaxion/worlds/tests` when Worlds is present and requires it in the focused campaign.
- N03 runs the dedicated World URL/sidebar routing Jest tests.
- N04 audits URL authority, API scoping, stale response guards, Next safety-net routing, backend runtime/middleware contracts and release-pinned task support.
- N05 probes Worlds control-plane liveness/readiness and optionally a configured promoted World without mutating the catalog.
- N06 validates release-pinned `world_id + release_id` task scope.
- N07 validates fail-closed data-plane/security invariants.
- N10 runs the Alpha/Beta multi-World isolation test explicitly.
- N11 recognizes Worlds routing/isolation/release failures as a dedicated correlation hypothesis.
- Existing campaigns remain ordered and compatible.
