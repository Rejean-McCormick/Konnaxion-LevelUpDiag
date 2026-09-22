import tempfile
import unittest
from pathlib import Path

from konnaxion_diag.worlds_audit import CORE_FILES, audit_worlds


class WorldsAuditTests(unittest.TestCase):
    def _fixture(self, root: Path) -> tuple[Path, Path]:
        frontend = root / "frontend"
        backend = root / "backend"
        frontend.mkdir()
        backend.mkdir()
        for relative in CORE_FILES.values():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture\n", encoding="utf-8")

        (frontend / "lib/worlds.ts").write_text(
            "parseWorldPath getWorldKeyFromPathname stripWorldPrefix withWorldPath "
            "StaleWorldResponseError StaleWorldReleaseError assertCurrentWorldResponse "
            "kxWorldReleaseId isGlobalApiPath scopeApiPath scopeBrowserApiUrl GLOBAL_API_PREFIXES\n",
            encoding="utf-8",
        )
        (frontend / "context/WorldContext.tsx").write_text(
            "usePathname getWorldKeyFromPathname(pathname) switchWorldPath "
            "window.location.search window.location.hash window.location.assign\n",
            encoding="utf-8",
        )
        (frontend / "components/worlds/WorldSwitcher.tsx").write_text("export default function WorldSwitcher(){}\n", encoding="utf-8")
        (frontend / "components/layout-components/Header.tsx").write_text("import WorldSwitcher from 'x'; <WorldSwitcher />\n", encoding="utf-8")
        (frontend / "components/layout-components/MainLayout.tsx").write_text("useWorld appPath detectSuite(appPath\n", encoding="utf-8")
        (frontend / "components/layout-components/Menu.tsx").write_text("useWorld appPath href(route.path)\n", encoding="utf-8")
        (frontend / "middleware.ts").write_text(
            "sourceWorld isGlobalApiPath /api/w/${worldKey}/ NextResponse.rewrite "
            "isUiCarryoverCandidate withWorldPath NextResponse.redirect\n",
            encoding="utf-8",
        )
        (frontend / "next.config.ts").write_text(
            "source: '/w/:world' source: '/w/:world/:path*' destination: '/:path*'\n",
            encoding="utf-8",
        )
        (frontend / "routes/suites.test.ts").write_text(
            "/w/demo-alpha/konsensus ethikos sidebar override\n",
            encoding="utf-8",
        )
        (frontend / "lib/__tests__/worlds.test.ts").write_text(
            "preserves query/hash scopes World-owned APIs exactly once control/worlds/\n",
            encoding="utf-8",
        )

        (backend / "konnaxion/worlds/runtime.py").write_text(
            "@dataclass(frozen=True ContextVar WorldContextRequired WorldContextConflict\n",
            encoding="utf-8",
        )
        (backend / "konnaxion/worlds/db.py").write_text(
            "SET LOCAL search_path transaction.atomic ekoh_schema domain_schema\n",
            encoding="utf-8",
        )
        (backend / "konnaxion/worlds/middleware.py").write_text(
            "X-Konnaxion-World X-Konnaxion-World-Release X-Konnaxion-World-Release-Id "
            "X-Konnaxion-World-Dirty KONNAXION_WORLDS_ENFORCE_SCOPED_API WORLD_REQUIRED _WORLD_OWNED_API_PREFIXES\n",
            encoding="utf-8",
        )
        (backend / "config/world_urls.py").write_text(
            'path("", include("konnaxion.worlds.runtime_urls"))\n'
            "KONNAXION_WORLDS_DATA_PLANE_ENABLED WORLD_DATA_PLANE_NOT_READY status=503\n",
            encoding="utf-8",
        )
        (backend / "config/urls.py").write_text(
            'path("api/control/", include("konnaxion.worlds.urls"))\n'
            'path("api/w/<slug:world_key>/", include("config.world_urls"))\n',
            encoding="utf-8",
        )
        (backend / "config/settings/base.py").write_text(
            '"konnaxion.worlds.apps.WorldsConfig"\n'
            '"django.contrib.auth.middleware.AuthenticationMiddleware"\n'
            '"konnaxion.worlds.middleware.WorldRouteMiddleware"\n'
            'KONNAXION_WORLDS_DATA_PLANE_ENABLED = env.bool("KONNAXION_WORLDS_DATA_PLANE_ENABLED", default=False)\n'
            'KONNAXION_WORLDS_ENFORCE_SCOPED_API = env.bool("KONNAXION_WORLDS_ENFORCE_SCOPED_API", default=False)\n',
            encoding="utf-8",
        )
        (backend / "konnaxion/worlds/tests/test_multiworld_isolation.py").write_text(
            "test_alpha_beta_release_isolation_end_to_end domain_schema != ekoh_schema !=\n",
            encoding="utf-8",
        )
        task_path = backend / "konnaxion/worlds/services/tasks.py"
        task_path.parent.mkdir(parents=True, exist_ok=True)
        task_path.write_text(
            "world_task_scope world_id release_id select_for_update STATUS_CURRENT\n",
            encoding="utf-8",
        )
        return frontend, backend

    def test_complete_worlds_contract(self):
        with tempfile.TemporaryDirectory() as d:
            frontend, backend = self._fixture(Path(d))
            report = audit_worlds(frontend, backend)
            self.assertTrue(report["detected"])
            self.assertTrue(report["ok"], report["failed_contracts"])
            self.assertEqual(report["missing_files"], [])

    def test_missing_world_context_is_reported(self):
        with tempfile.TemporaryDirectory() as d:
            frontend, backend = self._fixture(Path(d))
            (frontend / "context/WorldContext.tsx").unlink()
            report = audit_worlds(frontend, backend)
            self.assertFalse(report["ok"])
            self.assertIn("frontend/context/WorldContext.tsx", report["missing_files"])


if __name__ == "__main__":
    unittest.main()
