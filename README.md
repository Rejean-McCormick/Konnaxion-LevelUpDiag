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
├── Konnaxion/
│   ├── frontend/
│   └── backend/
└── Konnaxion_Worlds/
    └── backend/
```

`Konnaxion` remains the primary target. `Konnaxion_Worlds` is resolved separately through `konnaxion.worlds.repo_dir` (default `../Konnaxion_Worlds`).

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

## 3.2 — Historical Worlds qualification

v3.2 introduced the `world-switch` campaign and the first World-scoping checks. That architecture assumed the Worlds engine lived inside the Konnaxion backend. **That ownership model is superseded by v3.4 / `KX-UNIVERSES-1`.** The campaign name is retained as a compatibility alias, but current qualification follows the split-repository model documented below.

## 3.2.2 — Accurate sequence verdicts and target-protection visibility

Sequence aggregation already treats warning-only campaigns as `WARN`. v3.2.2 fixes the hidden post-run target-protection edge case that could still turn a warning-only sequence into `ERROR` after N11.

- `frontend/next-env.d.ts` is ignored by tracked-file protection because Next can regenerate this declaration during `next build`; this is a known build-tool side effect, not application-source drift.
- Any other tracked-file change during diagnostics remains a blocking `ERROR`.
- `triage-current` now prints `TARGET_PROTECTION ERROR` with the before/after Git status when such drift occurs.
- Additional safe generated paths can be configured through `execution.protect_tracked_ignore_paths` in a local config when needed.

Therefore a sequence whose actual campaign results are only `PASS`/`WARN` now terminates as `WARN`, while real source mutation is still surfaced as `ERROR`.


## 3.3.0 — Bilingual UI / i18n qualification

LevelUpDiag now treats the Konnaxion FR/EN runtime as a first-class diagnostic surface.

Focused run:

```powershell
python levelupdiag.py run i18n-validation
```

N03 performs catalog alignment, placeholder parity, CSS/styled-jsx safety and stable-value checks before the normal i18n script, TypeScript, ESLint, Jest and Next build gates. N05 performs a real Chromium FR/EN switch and verifies `html[lang]`, translated accessibility text, localStorage, cookie persistence and reload persistence. See `docs/I18N_VALIDATION.md`.


### v3.3.3 focused i18n isolation

`i18n-validation` treats the worker `LEVELUPDIAG_CAMPAIGN` as authoritative. N05 only ensures the frontend runtime is available and executes the dedicated FR/EN browser-switch probe. It does not run the generic Ethikos Playwright smoke, Ethikos seed, backend readiness, or Worlds runtime probe. `doctor` prints the effective `suite_version`.

## 3.4.0 — KX-UNIVERSES-1 / split Universe-World qualification

LevelUpDiag now validates the architecture actually used by Konnaxion:

```text
Konnaxion
  owns: product frontend + Universe/World switcher + host adapters
       │
       └── consumes installed package
             │
Konnaxion_Worlds
  owns: Universe → World → WorldRelease engine, migrations, control plane and canonical spec
```

The focused campaign remains:

```powershell
python levelupdiag.py run world-switch
```

It now validates all of the following:

- the sibling `Konnaxion_Worlds` repository is present and packageable;
- Konnaxion **does not** contain `backend/konnaxion/worlds` or the canonical `docs/Technical-Reference/Worlds` tree;
- both repository boundary guards execute successfully;
- Konnaxion extends the `konnaxion` namespace so the separately installed `konnaxion.worlds` package is importable;
- the browser shell supports the canonical `/u/<universe>/w/<world>/...` route and temporary `/w/<world>/...` compatibility route;
- Universe and World switching use strong navigation and preserve query/hash state;
- API and WebSocket paths carry Universe + World context;
- stale responses are rejected using Universe + World + Release identity;
- `Konnaxion_Worlds` contains the `Universe`, `UniverseMembership`, `WorldRelation`, `WorldPublication` and `WorldSubscription` model primitives plus migration `0004_universes`;
- runtime context is immutable and includes `universe_id`, `universe_key`, `world_id` and `release_id`;
- PostgreSQL search-path scoping remains transaction-local;
- middleware emits `X-Konnaxion-Universe`, `X-Konnaxion-World` and release headers;
- cross-Universe relations/subscriptions and publication provenance are covered by engine tests;
- task execution stays pinned to `world_id + release_id`;
- the disabled product data plane continues to fail closed.

### Runtime probe configuration

The read-only N05 probe verifies control-plane liveness/readiness plus `control/universes/`. It never creates, promotes or mutates a Universe/World. To probe an existing promoted World through the canonical route:

```json
{
  "konnaxion": {
    "worlds": {
      "repo_dir": "../Konnaxion_Worlds",
      "architecture_lock": "KX-UNIVERSES-1",
      "runtime_probe_universe_key": "mine-alpha",
      "runtime_probe_world_key": "engineering"
    }
  }
}
```

N05 then calls `/api/u/mine-alpha/w/engineering/runtime/` and requires the payload and response headers to agree on Universe, World and Release. If only `runtime_probe_world_key` is configured, the legacy `/api/w/<world>/runtime/` compatibility path may still be probed during U1.

### Backend test ownership

Konnaxion application checks still run from `Konnaxion/backend`. Universe/World engine tests run from `Konnaxion_Worlds/backend` with `worlds_config.settings`. The isolated pytest wrapper therefore selects the Django settings module according to the repository being tested rather than assuming every Django test belongs to Konnaxion.

For full qualification plus product regression:

```powershell
python levelupdiag.py run-sequence world-switch-validation
```



## KX-UNIVERSES-1 quick post-overlay check

After an overlay and zombie cleanup, run:

```powershell
python levelupdiag.py run universe-quick
```

Or double-click `RUN_KONNAXION_UNIVERSE_QUICK.bat`.

This runs only `N00 -> N01 -> N11`: repository ownership/boundary checks without Django DB, OpenAPI pytest, frontend build, Playwright or deep scans.

For deeper source/API qualification, `source-audit` remains available. Its isolated Django pytest wrapper now composes the sibling `Konnaxion_Worlds/backend` source root, preserving the KX-UNIVERSES-1 split without vendoring the engine back into Konnaxion.

## SecurityDiag integration

N07 now invokes SecurityDiag S04 against the Konnaxion target and requires fresh `PASS` web-trust evidence. Missing SecurityDiag or any S04 blocker fails N07 by default. Configure `konnaxion.securitydiag_repo` when SecurityDiag is not installed under `Konnaxion/securitydiag`.
