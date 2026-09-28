import tempfile
import unittest
from pathlib import Path

from konnaxion_diag.worlds_audit import ENGINE_FILES, HOST_FILES, audit_worlds


class WorldsAuditTests(unittest.TestCase):
    def _fixture(self, workspace: Path) -> tuple[Path, Path, Path]:
        host = workspace / "Konnaxion"
        worlds_repo = workspace / "Konnaxion_Worlds"
        frontend = host / "frontend"
        backend = host / "backend"
        frontend.mkdir(parents=True)
        backend.mkdir(parents=True)

        for relative in HOST_FILES.values():
            path = host / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture\n", encoding="utf-8")
        for relative in ENGINE_FILES.values():
            path = worlds_repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture\n", encoding="utf-8")

        (frontend / "lib/worlds.ts").write_text(
            "parseWorldPath getUniverseKeyFromPathname getWorldKeyFromPathname stripWorldPrefix withWorldPath "
            "UNIVERSE_WORLD_PATH_RE StaleUniverseResponseError StaleWorldResponseError StaleWorldReleaseError "
            "assertCurrentWorldResponse kxUniverse kxWorldReleaseId isGlobalApiPath scopeApiPath scopeBrowserApiUrl "
            "GLOBAL_API_PREFIXES u/${universeKey}/w/${worldKey} scopeWorldWebSocketPath resolveWorldWebSocketUrl /ws/${context}\n",
            encoding="utf-8",
        )
        (frontend / "context/WorldContext.tsx").write_text(
            "usePathname routeUniverseKey getWorldKeyFromPathname(pathname) switchUniverse switchWorld switchWorldPath "
            "window.location.search window.location.hash window.location.assign\n",
            encoding="utf-8",
        )
        (frontend / "components/worlds/WorldSwitcher.tsx").write_text(
            "k-universe-select k-world-select switchUniverse switchWorld\n", encoding="utf-8"
        )
        (frontend / "components/layout-components/Header.tsx").write_text(
            "import WorldSwitcher from 'x'; <WorldSwitcher />\n", encoding="utf-8"
        )
        (frontend / "components/layout-components/MainLayout.tsx").write_text(
            "useWorld appPath detectSuite(appPath\n", encoding="utf-8"
        )
        (frontend / "components/layout-components/Menu.tsx").write_text(
            "useWorld appPath href(route.path)\n", encoding="utf-8"
        )
        (frontend / "middleware.ts").write_text(
            "context.universeKey context.worldKey isGlobalApiPath NextResponse.rewrite "
            "/api/u/${context.universeKey}/w/${context.worldKey}/ isUiCarryoverCandidate withWorldPath NextResponse.redirect\n",
            encoding="utf-8",
        )
        (frontend / "next.config.ts").write_text(
            "source: '/u/:universe/w/:world' source: '/u/:universe/w/:world/:path*' "
            "source: '/w/:world' destination: '/:path*'\n",
            encoding="utf-8",
        )
        (frontend / "routes/suites.test.ts").write_text(
            "/w/demo-alpha/konsensus ethikos sidebar override\n", encoding="utf-8"
        )
        (frontend / "lib/__tests__/worlds.test.ts").write_text(
            "canonical and legacy World routes Universe/World API scoping scopeWorldWebSocketPath "
            "/u/christianity/w/theology\n",
            encoding="utf-8",
        )

        (backend / "config/urls.py").write_text(
            "api/control/ api/u/ /w/ config.world_urls\n", encoding="utf-8"
        )
        (backend / "config/settings/base.py").write_text(
            '"konnaxion.worlds.apps.WorldsConfig"\n'
            '"django.contrib.auth.middleware.AuthenticationMiddleware"\n'
            '"konnaxion.worlds.middleware.WorldRouteMiddleware"\n'
            'KONNAXION_WORLDS_DATA_PLANE_ENABLED = env.bool("KONNAXION_WORLDS_DATA_PLANE_ENABLED", default=False)\n'
            'KONNAXION_WORLDS_ENFORCE_SCOPED_API = env.bool("KONNAXION_WORLDS_ENFORCE_SCOPED_API", default=True)\n'
            'KONNAXION_WORLDS_SCENARIO_IMPORTER KONNAXION_WORLDS_FIXTURE_LOADER '
            'KONNAXION_WORLDS_FIXTURE_CHECKSUM_PROVIDER\n',
            encoding="utf-8",
        )
        (backend / "config/world_urls.py").write_text(
            'path("", include("konnaxion.worlds.runtime_urls"))\n'
            "KONNAXION_WORLDS_DATA_PLANE_ENABLED WORLD_DATA_PLANE_NOT_READY status=503\n",
            encoding="utf-8",
        )
        (backend / "config/world_api_router.py").write_text(
            "canonical_urlpatterns _GLOBAL_ROUTE_NAME_PREFIXES urlpatterns\n", encoding="utf-8"
        )
        (backend / "config/world_adapters.py").write_text(
            "import_world_scenario load_world_auxiliary_fixture world_auxiliary_fixture_checksum\n",
            encoding="utf-8",
        )
        (backend / "konnaxion/__init__.py").write_text(
            "from pkgutil import extend_path\n__path__ = extend_path(__path__, __name__)\n",
            encoding="utf-8",
        )
        (host / "scripts/check_worlds_ownership.py").write_text(
            "Konnaxion_Worlds backend konnaxion worlds Technical-Reference\n", encoding="utf-8"
        )

        engine = worlds_repo / "backend/konnaxion/worlds"
        (worlds_repo / "backend/pyproject.toml").write_text(
            'name = "konnaxion-worlds"\ninclude = ["konnaxion.worlds*"]\nnamespaces = true\n',
            encoding="utf-8",
        )
        (worlds_repo / "backend/worlds_config/settings.py").write_text(
            'KONNAXION_WORLDS_ENFORCE_SCOPED_API = _bool("KONNAXION_WORLDS_ENFORCE_SCOPED_API", True)\n',
            encoding="utf-8",
        )
        (engine / "__init__.py").write_text('ARCHITECTURE_LOCK = "KX-UNIVERSES-1"\n', encoding="utf-8")
        (engine / "models.py").write_text(
            "class Universe( class UniverseMembership( class WorldRelation( class WorldPublication( "
            "class WorldSubscription( universe = models.ForeignKey\n",
            encoding="utf-8",
        )
        (engine / "migrations/0004_universes.py").write_text(
            "Universe UniverseMembership WorldRelation WorldPublication WorldSubscription\n", encoding="utf-8"
        )
        (engine / "runtime.py").write_text(
            "@dataclass(frozen=True ContextVar WorldContextRequired WorldContextConflict universe_id universe_key world_id release_id\n",
            encoding="utf-8",
        )
        (engine / "db.py").write_text(
            "SET LOCAL search_path transaction.atomic ekoh_schema domain_schema\n", encoding="utf-8"
        )
        (engine / "middleware.py").write_text(
            "X-Konnaxion-Universe X-Konnaxion-World X-Konnaxion-World-Release X-Konnaxion-World-Release-Id "
            "X-Konnaxion-World-Dirty _UNIVERSE_WORLD_ROUTE_RE universe_key _LEGACY_WORLD_ROUTE_RE resolve_world_runtime\n",
            encoding="utf-8",
        )
        (engine / "urls.py").write_text(
            'path("universes/" relations/ publications/ subscriptions/ path("worlds/"\n', encoding="utf-8"
        )
        (engine / "services/health.py").write_text(
            'KX-UNIVERSES-1 Universe "universes" "worlds"\n', encoding="utf-8"
        )
        (engine / "services/tasks.py").write_text(
            "world_task_scope world_id release_id select_for_update STATUS_CURRENT\n", encoding="utf-8"
        )
        for relative in (
            "services/builder.py",
            "services/snapshots.py",
            "management/commands/worlds_build.py",
            "management/commands/worlds_queue_catalog.py",
        ):
            (engine / relative).write_text(
                'metadata_json = {"architecture_lock": "KX-UNIVERSES-1"}\n', encoding="utf-8"
            )
        (engine / "tests/test_multiworld_isolation.py").write_text(
            "Universe.objects.create domain_schema != ekoh_schema !=\n", encoding="utf-8"
        )
        (engine / "tests/test_universes.py").write_text(
            "test_runtime_resolves_universe_world_release_tuple test_relation_cannot_cross_universes "
            "test_subscription_cannot_cross_universes test_publication_release_must_belong_to_source_world\n",
            encoding="utf-8",
        )
        (engine / "tests/test_strict_routing.py").write_text(
            "KONNAXION_WORLDS_ENFORCE_SCOPED_API=True WORLD_REQUIRED\n", encoding="utf-8"
        )
        (worlds_repo / "scripts/check_repo_boundaries.py").write_text(
            "Konnaxion_Worlds repository boundary frontend/components/worlds/WorldSwitcher.tsx\n",
            encoding="utf-8",
        )
        (worlds_repo / "docs/Technical-Reference/Worlds/20_UNIVERSES.md").write_text(
            "KX-UNIVERSES-1 Universe WorldRelation WorldPublication\n", encoding="utf-8"
        )
        (worlds_repo / "docs/Technical-Reference/Worlds/AI_LOCK.yaml").write_text(
            "KX-UNIVERSES-1\n", encoding="utf-8"
        )
        return frontend, backend, worlds_repo

    def test_complete_worlds_contract(self):
        with tempfile.TemporaryDirectory() as d:
            frontend, backend, worlds_repo = self._fixture(Path(d))
            report = audit_worlds(frontend, backend, worlds_repo=worlds_repo)
            self.assertTrue(report["detected"])
            self.assertTrue(report["ok"], report["failed_contracts"])
            self.assertEqual(report["missing_files"], [])
            self.assertEqual(report["forbidden_present"], [])

    def test_missing_world_context_is_reported(self):
        with tempfile.TemporaryDirectory() as d:
            frontend, backend, worlds_repo = self._fixture(Path(d))
            (frontend / "context/WorldContext.tsx").unlink()
            report = audit_worlds(frontend, backend, worlds_repo=worlds_repo)
            self.assertFalse(report["ok"])
            self.assertIn("Konnaxion/frontend/context/WorldContext.tsx", report["missing_files"])

    def test_overlap_in_host_is_reported(self):
        with tempfile.TemporaryDirectory() as d:
            frontend, backend, worlds_repo = self._fixture(Path(d))
            vendored = backend / "konnaxion/worlds"
            vendored.mkdir(parents=True)
            report = audit_worlds(frontend, backend, worlds_repo=worlds_repo)
            self.assertFalse(report["ok"])
            self.assertTrue(report["forbidden_present"])
            self.assertFalse(report["ownership"]["host_does_not_vendor_engine"])


if __name__ == "__main__":
    unittest.main()
