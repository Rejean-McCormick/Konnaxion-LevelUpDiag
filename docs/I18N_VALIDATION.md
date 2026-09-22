# Konnaxion FR/EN validation — LevelUpDiag 3.3

Run the focused bilingual UI qualification with:

```powershell
python levelupdiag.py run i18n-validation
```

Sequence:

```text
N00 -> N01 -> N03 -> N05 -> N11
```

## N03 — static + compile gates

When `frontend/i18n/locales/en.json` / `fr.json` are detected, N03 now validates:

- both JSON catalogs parse;
- EN/FR expose the exact same leaf-key set;
- no empty/non-string leaves;
- interpolation placeholders such as `{name}` match between languages;
- CSS was not accidentally extracted into translations;
- `<style jsx>` is not fed from `t()` / `i18nT()`;
- translated display strings are not used as technical `value` identifiers;
- `npm/pnpm run i18n:check` passes;
- TypeScript, ESLint, Jest and Next build still pass.

This specifically catches migration failures such as translating `value: '7d'` into a localized label or replacing static styled-jsx CSS with a translation call.

## N05 — live browser switch

When the local frontend is available, N05 launches an isolated Chromium context using the frontend's Playwright dependency and verifies:

1. the FR/EN segmented control is visible in the application shell;
2. changing language updates `html[lang]` between `fr-CA` and `en-CA`;
3. the toggle's translated `aria-label` changes;
4. `localStorage['konnaxion.language']` is updated;
5. the `konnaxion.language` cookie is updated;
6. the selected language survives a page reload.

Default probe route:

```text
/ekoh/dashboard?sidebar=ekoh
```

Override it in `levelupdiag.config.local.json` if needed:

```json
{
  "konnaxion": {
    "i18n_browser_probe_path": "/ethikos/insights?sidebar=ethikos",
    "i18n_browser_probe_timeout_seconds": 180,
    "i18n_browser_probe_required": true
  }
}
```

The browser probe is intentionally required by default when the i18n runtime is detected. If Chromium is not installed, run the Konnaxion frontend Playwright install command first.

## Target protection

Playwright may rewrite `frontend/storageState.json`. LevelUpDiag snapshots and restores that tracked runtime artifact automatically before comparing Git state, so diagnostics remain non-mutating. Additional paths can be configured with `execution.protect_tracked_restore_paths`.
