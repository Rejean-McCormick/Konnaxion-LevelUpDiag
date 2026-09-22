from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


CORE_FILES = {
    "frontend_worlds_lib": "frontend/lib/worlds.ts",
    "frontend_world_context": "frontend/context/WorldContext.tsx",
    "frontend_world_switcher": "frontend/components/worlds/WorldSwitcher.tsx",
    "frontend_header": "frontend/components/layout-components/Header.tsx",
    "frontend_main_layout": "frontend/components/layout-components/MainLayout.tsx",
    "frontend_menu": "frontend/components/layout-components/Menu.tsx",
    "frontend_next_middleware": "frontend/middleware.ts",
    "frontend_next_config": "frontend/next.config.ts",
    "frontend_suite_tests": "frontend/routes/suites.test.ts",
    "frontend_world_tests": "frontend/lib/__tests__/worlds.test.ts",
    "backend_worlds_runtime": "backend/konnaxion/worlds/runtime.py",
    "backend_worlds_db": "backend/konnaxion/worlds/db.py",
    "backend_worlds_middleware": "backend/konnaxion/worlds/middleware.py",
    "backend_world_urls": "backend/config/world_urls.py",
    "backend_urls": "backend/config/urls.py",
    "backend_settings": "backend/config/settings/base.py",
    "backend_world_isolation_test": "backend/konnaxion/worlds/tests/test_multiworld_isolation.py",
}


def _text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _has_all(text: str, needles: tuple[str, ...]) -> bool:
    return all(needle in text for needle in needles)


def _bool_default_false(settings_text: str, name: str) -> bool:
    pattern = re.compile(
        rf"{re.escape(name)}\s*=\s*env\.bool\(\s*[\"']{re.escape(name)}[\"']\s*,\s*default\s*=\s*False\s*,?\s*\)",
        re.S,
    )
    return bool(pattern.search(settings_text))


def audit_worlds(frontend: Path, backend: Path) -> dict[str, Any]:
    root = frontend.parent if frontend.parent == backend.parent else None

    def p(relative: str) -> Path:
        if root is not None:
            return root / relative
        if relative.startswith("frontend/"):
            return frontend / relative.removeprefix("frontend/")
        return backend / relative.removeprefix("backend/")

    files = {name: p(relative) for name, relative in CORE_FILES.items()}
    exists = {name: path.is_file() for name, path in files.items()}
    detected = any(
        exists.get(key, False)
        for key in (
            "frontend_worlds_lib",
            "frontend_world_context",
            "backend_worlds_runtime",
            "backend_worlds_middleware",
        )
    )
    missing = [CORE_FILES[name] for name, present in exists.items() if not present]

    worlds_ts = _text(files["frontend_worlds_lib"])
    context_tsx = _text(files["frontend_world_context"])
    switcher_tsx = _text(files["frontend_world_switcher"])
    header_tsx = _text(files["frontend_header"])
    main_layout_tsx = _text(files["frontend_main_layout"])
    menu_tsx = _text(files["frontend_menu"])
    next_middleware_ts = _text(files["frontend_next_middleware"])
    next_config_ts = _text(files["frontend_next_config"])
    suite_tests_ts = _text(files["frontend_suite_tests"])
    world_tests_ts = _text(files["frontend_world_tests"])

    runtime_py = _text(files["backend_worlds_runtime"])
    db_py = _text(files["backend_worlds_db"])
    middleware_py = _text(files["backend_worlds_middleware"])
    world_urls_py = _text(files["backend_world_urls"])
    urls_py = _text(files["backend_urls"])
    settings_py = _text(files["backend_settings"])
    isolation_test_py = _text(files["backend_world_isolation_test"])

    auth_index = settings_py.find("django.contrib.auth.middleware.AuthenticationMiddleware")
    worlds_index = settings_py.find("konnaxion.worlds.middleware.WorldRouteMiddleware")

    frontend_contracts = {
        "url_is_world_authority": _has_all(
            worlds_ts,
            (
                "parseWorldPath",
                "getWorldKeyFromPathname",
                "stripWorldPrefix",
                "withWorldPath",
            ),
        ) and _has_all(context_tsx, ("usePathname", "getWorldKeyFromPathname(pathname)")),
        "hard_world_switch": "window.location.assign" in context_tsx and "switchWorldPath" in context_tsx,
        "switch_preserves_query_hash": _has_all(
            context_tsx,
            ("window.location.search", "window.location.hash", "window.location.assign"),
        ),
        "stale_world_release_guard": _has_all(
            worlds_ts,
            (
                "StaleWorldResponseError",
                "StaleWorldReleaseError",
                "assertCurrentWorldResponse",
                "kxWorldReleaseId",
            ),
        ),
        "api_scope_helpers": _has_all(
            worlds_ts,
            ("isGlobalApiPath", "scopeApiPath", "scopeBrowserApiUrl", "GLOBAL_API_PREFIXES"),
        ),
        "next_api_safety_net": _has_all(
            next_middleware_ts,
            ("sourceWorld", "isGlobalApiPath", "/api/w/${worldKey}/", "NextResponse.rewrite"),
        ),
        "next_ui_world_carryover": _has_all(
            next_middleware_ts,
            ("isUiCarryoverCandidate", "withWorldPath", "NextResponse.redirect"),
        ),
        "next_world_rewrite": _has_all(
            next_config_ts,
            ("source: '/w/:world'", "source: '/w/:world/:path*'", "destination: '/:path*'"),
        ),
        "world_switcher_in_header": "WorldSwitcher" in header_tsx and "<WorldSwitcher" in header_tsx,
        "sidebar_uses_app_path": _has_all(main_layout_tsx, ("useWorld", "appPath", "detectSuite(appPath"))
        and _has_all(menu_tsx, ("useWorld", "appPath", "href(route.path)")),
        "sidebar_cross_module_tests": _has_all(
            suite_tests_ts,
            ("/w/demo-alpha/konsensus", "ethikos", "sidebar override"),
        ),
        "world_helper_tests": _has_all(
            world_tests_ts,
            ("preserves query/hash", "scopes World-owned APIs exactly once", "control/worlds/"),
        ),
        "switcher_present": bool(switcher_tsx.strip()),
    }

    backend_contracts = {
        "worlds_app_registered": "konnaxion.worlds.apps.WorldsConfig" in settings_py,
        "middleware_after_auth": auth_index >= 0 and worlds_index > auth_index,
        "control_and_world_routes": _has_all(
            urls_py,
            ('path("api/control/", include("konnaxion.worlds.urls"))', 'path("api/w/<slug:world_key>/", include("config.world_urls"))'),
        ),
        "immutable_runtime_context": _has_all(
            runtime_py,
            ("@dataclass(frozen=True", "ContextVar", "WorldContextRequired", "WorldContextConflict"),
        ),
        "transaction_local_search_path": _has_all(
            db_py,
            ("SET LOCAL search_path", "transaction.atomic", "ekoh_schema", "domain_schema"),
        ),
        "response_world_headers": _has_all(
            middleware_py,
            (
                "X-Konnaxion-World",
                "X-Konnaxion-World-Release",
                "X-Konnaxion-World-Release-Id",
                "X-Konnaxion-World-Dirty",
            ),
        ),
        "unscoped_api_enforcement": _has_all(
            middleware_py,
            ("KONNAXION_WORLDS_ENFORCE_SCOPED_API", "WORLD_REQUIRED", "_WORLD_OWNED_API_PREFIXES"),
        ),
        "data_plane_default_off": _bool_default_false(settings_py, "KONNAXION_WORLDS_DATA_PLANE_ENABLED"),
        "scoped_api_default_off": _bool_default_false(settings_py, "KONNAXION_WORLDS_ENFORCE_SCOPED_API"),
        "data_plane_fail_closed_503": _has_all(
            world_urls_py,
            ("WORLD_DATA_PLANE_NOT_READY", "status=503", "KONNAXION_WORLDS_DATA_PLANE_ENABLED"),
        ),
        "runtime_always_mounted": 'path("", include("konnaxion.worlds.runtime_urls"))' in world_urls_py,
        "multiworld_isolation_test": _has_all(
            isolation_test_py,
            ("test_alpha_beta_release_isolation_end_to_end", "domain_schema !=", "ekoh_schema !="),
        ),
    }

    jobs_services = _text(backend / "konnaxion/worlds/services/tasks.py")
    jobs_contracts = {
        "release_pinned_task_scope": _has_all(
            jobs_services,
            ("world_task_scope", "world_id", "release_id", "select_for_update", "STATUS_CURRENT"),
        )
    }

    all_contracts = {
        **{f"frontend.{key}": value for key, value in frontend_contracts.items()},
        **{f"backend.{key}": value for key, value in backend_contracts.items()},
        **{f"jobs.{key}": value for key, value in jobs_contracts.items()},
    }

    return {
        "detected": detected,
        "required_files": {name: str(path) for name, path in files.items()},
        "missing_files": missing,
        "frontend": frontend_contracts,
        "backend": backend_contracts,
        "jobs": jobs_contracts,
        "failed_contracts": [name for name, ok in all_contracts.items() if not ok],
        "ok": detected and not missing and all(all_contracts.values()),
    }


def summarize_worlds_audit(report: dict[str, Any]) -> str:
    return json.dumps(
        {
            "detected": report.get("detected"),
            "missing_files": report.get("missing_files", []),
            "failed_contracts": report.get("failed_contracts", []),
        },
        sort_keys=True,
    )


def _http_json(url: str, *, timeout: float = 5.0) -> dict[str, Any]:
    import urllib.error
    import urllib.request

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "LevelUpDiag-Konnaxion-Worlds/3.2"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(65536)
            status = int(response.status)
            headers = {str(k).lower(): str(v) for k, v in response.headers.items()}
    except urllib.error.HTTPError as exc:
        raw = exc.read(65536)
        status = int(exc.code)
        headers = {str(k).lower(): str(v) for k, v in exc.headers.items()} if exc.headers else {}
    except Exception as exc:
        return {
            "status": None,
            "json": None,
            "headers": {},
            "error": f"{type(exc).__name__}: {exc}",
        }

    try:
        payload = json.loads(raw.decode("utf-8", errors="replace")) if raw else None
    except json.JSONDecodeError:
        payload = None
    return {
        "status": status,
        "json": payload,
        "headers": headers,
        "error": "",
    }


def _backend_api_base(config: Any) -> str | None:
    section = config.get("konnaxion", {})
    if not isinstance(section, dict):
        return None
    worlds = section.get("worlds", {})
    if isinstance(worlds, dict):
        explicit = worlds.get("backend_api_base_url")
        if isinstance(explicit, str) and explicit.strip():
            return explicit.rstrip("/") + "/"
    urls = section.get("local_urls", [])
    if isinstance(urls, list):
        for value in urls:
            if isinstance(value, str) and "/api" in value:
                base = value.split("/api", 1)[0].rstrip("/")
                return f"{base}/api/"
    return None


def probe_worlds_control_plane(config: Any, paths: dict[str, Any]) -> dict[str, Any]:
    """Read-only local runtime probes for the Worlds control/runtime plane.

    The probe never creates Worlds or Releases. A concrete runtime World is
    only checked when `konnaxion.worlds.runtime_probe_world_key` is configured.
    """
    import os
    from urllib.parse import urljoin

    section = config.get("konnaxion", {})
    section = section if isinstance(section, dict) else {}
    worlds_cfg = section.get("worlds", {})
    worlds_cfg = worlds_cfg if isinstance(worlds_cfg, dict) else {}
    base = _backend_api_base(config)
    required = os.environ.get("LEVELUPDIAG_CAMPAIGN", "") == "world-switch"
    expected_lock = str(worlds_cfg.get("architecture_lock", "KX-WORLDS-1"))
    timeout = float(worlds_cfg.get("http_timeout_seconds", 5) or 5)
    findings: list[dict[str, Any]] = []

    if not base:
        findings.append({
            "id": "kx.worlds.runtime.control-live",
            "severity": "FAIL" if required else "WARN",
            "message": "Cannot derive the local backend /api base URL for Worlds probes.",
            "recommendation": "Configure konnaxion.worlds.backend_api_base_url or konnaxion.local_urls.",
        })
        return {"base_url": None, "findings": findings}

    for suffix, kind in (("control/health/live/", "liveness"), ("control/health/ready/", "readiness")):
        url = urljoin(base, suffix)
        result = _http_json(url, timeout=timeout)
        payload = result.get("json") if isinstance(result.get("json"), dict) else {}
        ok = (
            result.get("status") == 200
            and payload.get("architecture_lock") == expected_lock
            and payload.get("kind") == kind
            and payload.get("ok") is True
        )
        findings.append({
            "id": f"kx.worlds.runtime.control-{kind}",
            "severity": "PASS" if ok else ("FAIL" if required else "WARN"),
            "message": f"Worlds control-plane {kind} probe {'passed' if ok else 'failed'}.",
            "path": url,
            "evidence": json.dumps({
                "status": result.get("status"),
                "architecture_lock": payload.get("architecture_lock"),
                "kind": payload.get("kind"),
                "ok": payload.get("ok"),
                "error": result.get("error"),
                "errors": payload.get("errors"),
            }, sort_keys=True),
            "recommendation": "Start the local PostgreSQL-backed Konnaxion runtime and repair Worlds readiness before accepting the overlay." if not ok else None,
        })

    world_key = str(worlds_cfg.get("runtime_probe_world_key", "")).strip()
    if not world_key:
        findings.append({
            "id": "kx.worlds.runtime.world",
            "severity": "SKIP",
            "message": "No runtime probe World configured; control-plane probes completed without mutating the catalog.",
            "recommendation": "Set konnaxion.worlds.runtime_probe_world_key after promoting a local test World to validate World/Release response headers end to end.",
        })
        return {"base_url": base, "world_key": None, "findings": findings}

    runtime_url = urljoin(base, f"w/{world_key}/runtime/")
    runtime_result = _http_json(runtime_url, timeout=timeout)
    runtime_payload = runtime_result.get("json") if isinstance(runtime_result.get("json"), dict) else {}
    headers = runtime_result.get("headers", {}) if isinstance(runtime_result.get("headers"), dict) else {}
    release = runtime_payload.get("release") if isinstance(runtime_payload.get("release"), dict) else {}
    world = runtime_payload.get("world") if isinstance(runtime_payload.get("world"), dict) else {}
    runtime_ok = (
        runtime_result.get("status") == 200
        and runtime_payload.get("architecture_lock") == expected_lock
        and str(world.get("key", "")).lower() == world_key.lower()
        and release.get("id") is not None
        and str(headers.get("x-konnaxion-world", "")).lower() == world_key.lower()
        and str(headers.get("x-konnaxion-world-release-id", "")) == str(release.get("id"))
    )
    findings.append({
        "id": "kx.worlds.runtime.world",
        "severity": "PASS" if runtime_ok else "FAIL",
        "message": f"World runtime/header probe {'passed' if runtime_ok else 'failed'} for {world_key}.",
        "path": runtime_url,
        "evidence": json.dumps({
            "status": runtime_result.get("status"),
            "world": world.get("key"),
            "release_id": release.get("id"),
            "header_world": headers.get("x-konnaxion-world"),
            "header_release_id": headers.get("x-konnaxion-world-release-id"),
            "error": runtime_result.get("error"),
        }, sort_keys=True),
        "recommendation": "Promote the configured probe World and ensure WorldRouteMiddleware emits matching World/Release headers." if not runtime_ok else None,
    })

    data_plane_path = str(worlds_cfg.get("data_plane_probe_path", "")).strip().lstrip("/")
    if runtime_ok and data_plane_path:
        data_url = urljoin(base, f"w/{world_key}/{data_plane_path}")
        data_result = _http_json(data_url, timeout=timeout)
        capabilities = runtime_payload.get("capabilities") if isinstance(runtime_payload.get("capabilities"), dict) else {}
        enabled = capabilities.get("data_plane_enabled") is True
        data_payload = data_result.get("json") if isinstance(data_result.get("json"), dict) else {}
        if enabled:
            data_ok = data_result.get("status") != 503
            message = "Enabled World data plane does not return the fail-closed 503 sentinel."
        else:
            data_ok = data_result.get("status") == 503 and data_payload.get("error") == "WORLD_DATA_PLANE_NOT_READY"
            message = "Disabled World data plane returns the expected fail-closed 503 sentinel."
        findings.append({
            "id": "kx.worlds.runtime.data-plane-state",
            "severity": "PASS" if data_ok else "FAIL",
            "message": message if data_ok else "World data-plane runtime behavior does not match advertised capabilities.",
            "path": data_url,
            "evidence": json.dumps({
                "data_plane_enabled": enabled,
                "status": data_result.get("status"),
                "error_code": data_payload.get("error"),
            }, sort_keys=True),
        })

    return {
        "base_url": base,
        "world_key": world_key,
        "findings": findings,
    }
