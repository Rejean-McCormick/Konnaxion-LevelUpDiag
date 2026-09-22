# Konnaxion LevelUpDiag — Upgraded v3

This package upgrades the Konnaxion LevelUpDiag Mega Pack onto the evolved LevelUpDiag engine while preserving the Konnaxion-specific diagnostic domains and test order.

## Konnaxion target auto-detection

When `target_repo_root` is `auto`, LevelUpDiag supports both common layouts:

```text
<Konnaxion repo>/LevelUpDiag/
```

and the historical workspace layout:

```text
<workspace>/
├── LevelUpDiag/
└── Konnaxion/
    ├── frontend/
    └── backend/
```

It scores Konnaxion markers (`frontend`, `backend`, `package.json`, `manage.py`) and selects the correct target automatically.

## What is preserved

- Exact Konnaxion taxonomy N00..N11.
- Existing Django, Next, TypeScript, ESLint, Jest, OpenAPI, Playwright, Celery/Redis, Capsule Manager and deployed-runtime diagnostics.
- Static source audit: double `/api/api`, forbidden legacy namespaces, CSRF-risk and unmapped endpoint checks.
- Common-auth audit: django-allauth/OIDC (`issuer + sub`), local-login preservation, no email auto-link, interactive human/service/klone policy, CSRF/same-origin production contract, legacy token/Auth0 cleanup.
- `.venv` Python autodetection and `corepack pnpm` fallback.
- Remote diagnostics disabled by default and no destructive deployment/restart/restore operations.
- Original ordered campaigns.

## What is upgraded

- Process isolation: every level runs in its own Python process.
- Explicit sequential campaign execution. Konnaxion test order is never lost to parallel scheduling.
- Campaign/expected-level metadata propagated into N00 session state.
- N11 correlates only the levels expected by the active campaign.
- Current-only evidence retention: old LevelUpDiag `runs`, `logs`, `diagnostics`, `latest`, `current` and stale Konnaxion session evidence are purged at the start of a campaign.
- Bounded/redacted command output, `shell=False`, timeouts and progress heartbeat.
- Modern manifest/config schemas while accepting the previous local Konnaxion config schema during migration.

## Primary campaign

```powershell
python levelupdiag.py run connection-debug
```

Its exact sequence is:

```text
N00 -> N01 -> N02 -> N03 -> N04 -> N05 -> N06 -> N11
```

## Recommended escalation sequence

The existing Konnaxion workflow is preserved:

```text
source-audit -> auth-debug -> connection-debug -> full-local
```

Run it automatically with:

```powershell
python levelupdiag.py run-sequence recommended-debug
```

Each campaign still has its own N00 session and N11 final correlation.

## Configuration

If the `levelupdiag/` directory is copied directly into the Konnaxion repo, the default `target_repo_root: "auto"` diagnoses its parent. For a standalone LevelUpDiag checkout, run the configuration script or set `target_repo_root` in `levelupdiag.config.local.json`.

No application command is guessed outside the Konnaxion command defaults already encoded by this pack.

## Runtime evidence

Only current evidence is retained:

```text
<Konnaxion>/.levelupdiag/current/
<Konnaxion>/.levelupdiag/latest/
```

No historical run archive is maintained by default.

## Console graphique de sélection

Le root inclut maintenant `LEVELUPDIAG_CONSOLE.pyw`. Sous Windows, un double-clic ouvre une console graphique inspirée du modèle fourni :

- sélection d'une campagne depuis le manifest ;
- sélection manuelle de niveaux N00..N11 ;
- presets Source audit, Auth debug, Connection debug et Full local ;
- sortie du diagnostic en direct ;
- arrêt du processus ;
- ouverture directe du dossier de preuves `.levelupdiag/current`.

La console lance le même moteur `levelupdiag.py`; elle ne duplique pas les tests.

## Nettoyage des alias historiques

Les anciens alias `MegaPack` ont été retirés du root et sont supprimés lors d'un upgrade après sauvegarde :

- `INSTALL_AND_CONFIGURE_KONNAXION_MEGAPACK.pyw`
- `CONFIGURE_KONNAXION_MEGAPACK.ps1`
- `INSTALL_MEGAPACK.ps1`

Les noms LevelUpDiag v3 sont désormais les seules entrées d'installation/configuration conservées.

## Authentication diagnostic

The `auth-debug` campaign now validates the Konnaxion common identity implementation. It does not require OIDC to be enabled: federation is optional by design. It requires the OIDC capability to be correctly declared while local django-allauth login remains available.

## 3.2 — Konnaxion Worlds / World Switch validation

LevelUpDiag is now World-aware without changing the N00..N11 taxonomy.

Run the focused qualification campaign after applying the Konnaxion World Switch overlay:

```powershell
python levelupdiag.py run world-switch
```

Exact sequence:

```text
N00 -> N01 -> N02 -> N03 -> N04 -> N05 -> N06 -> N07 -> N10 -> N11
```

The campaign validates:

- `/w/<world>/...` URL ownership and Next rewrite/carry-over safety net;
- current sidebar ownership, including `/konsensus -> ethiKos` and `?sidebar=` preservation tests;
- World-aware API scoping and global/control-plane exclusions;
- stale World/Release response protection;
- Django World middleware ordering and immutable `WorldRuntime` context;
- transaction-local PostgreSQL `search_path`;
- `X-Konnaxion-World*` response headers;
- data-plane fail-closed defaults and the `WORLD_DATA_PLANE_NOT_READY` 503 sentinel;
- release-pinned background task scope;
- frontend World helper/suite tests and backend Worlds tests;
- Alpha/Beta multi-World schema/release isolation in N10.

Control-plane liveness/readiness are probed read-only during N05. By default LevelUpDiag does **not** create or promote a World. To add a concrete end-to-end runtime/header probe after you already have a promoted local test World, set this in `levelupdiag.config.local.json`:

```json
{
  "konnaxion": {
    "worlds": {
      "runtime_probe_world_key": "demo-alpha"
    }
  }
}
```

When a runtime World is configured, N05 also compares the returned World/Release payload to the `X-Konnaxion-World` and `X-Konnaxion-World-Release-Id` headers and checks that data-plane behavior matches the advertised capability state.

For a focused qualification followed by the broad local regression suite:

```powershell
python levelupdiag.py run-sequence world-switch-validation
```

Windows shortcut: `RUN_KONNAXION_WORLD_SWITCH.bat` (or `launchers/KX-world-switch.bat`).

## 3.2.1 — Focused Worlds qualification and immediate triage

`world-switch` is now intentionally focused. It no longer reruns the generic platform smoke suite, full ESLint/Jest sweep, full Playwright smoke gate, full frontend deep scan, or full backend pytest suite. Those remain in `full-local`, which `world-switch-validation` runs only after the focused Worlds campaign passes.

This removes duplicate long-running work and makes a failing Worlds campaign easier to interpret.

After any run, print actionable findings from the retained current evidence with:

```powershell
python levelupdiag.py triage-current
```

Non-PASS findings are also printed immediately after each level in the console, with a concise evidence tail.


## 3.2.2 — Accurate sequence verdicts and target-protection visibility

Sequence aggregation already treats warning-only campaigns as `WARN`. v3.2.2 fixes the hidden post-run target-protection edge case that could still turn a warning-only sequence into `ERROR` after N11.

- `frontend/next-env.d.ts` is ignored by tracked-file protection because Next can regenerate this declaration during `next build`; this is a known build-tool side effect, not application-source drift.
- Any other tracked-file change during diagnostics remains a blocking `ERROR`.
- `triage-current` now prints `TARGET_PROTECTION ERROR` with the before/after Git status when such drift occurs.
- Additional safe generated paths can be configured through `execution.protect_tracked_ignore_paths` in a local config when needed.

Therefore a sequence whose actual campaign results are only `PASS`/`WARN` now terminates as `WARN`, while real source mutation is still surfaced as `ERROR`.
