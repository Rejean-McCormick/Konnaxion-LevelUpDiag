import tempfile, unittest
from pathlib import Path
from konnaxion_diag.source_audit import audit, auth_contract_audit

class SourceAuditTests(unittest.TestCase):
    def test_register_helpers_and_contract_findings(self):
        with tempfile.TemporaryDirectory() as d:
            tmp_path=Path(d); fe=tmp_path/"frontend"; be=tmp_path/"backend"; fe.mkdir(); be.mkdir()
            (be/"urls.py").write_text("register_required(router, 'users', V)\nregister_optional(router, 'admin/stats', V)\n",encoding="utf-8")
            (fe/"x.ts").write_text("fetch('/api/home/x', {method:'POST', credentials:'include'}); const x='/api/api/admin/stats';",encoding="utf-8")
            r=audit(fe,be)
            self.assertIn('/api/users',r['backend_prefixes']); self.assertTrue(r['double_api']); self.assertTrue(r['forbidden']); self.assertTrue(r['csrf_risk_files'])


    def test_common_auth_contract(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            fe = root / "frontend"
            be = root / "backend"
            (fe / "app/providers").mkdir(parents=True)
            (fe / "components/auth0-components").mkdir(parents=True)
            (fe / "lib").mkdir(parents=True)
            (be / "config/settings").mkdir(parents=True)
            (be / "konnaxion/users").mkdir(parents=True)
            (be / "requirements").mkdir(parents=True)

            (fe / "package.json").write_text('{"dependencies":{}}', encoding="utf-8")
            (fe / "env.production.example").write_text("NEXT_PUBLIC_API_BASE=/api\n", encoding="utf-8")
            (be / "config/settings/base.py").write_text(
                '\n'.join([
                    '"allauth.socialaccount.providers.openid_connect",',
                    'COMMON_OIDC_ENABLED = env.bool("COMMON_OIDC_ENABLED", default=False)',
                    'SOCIALACCOUNT_ONLY = False',
                    'SOCIALACCOUNT_EMAIL_AUTHENTICATION = False',
                    'SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = False',
                    'SOCIALACCOUNT_PROVIDERS["openid_connect"] = {"APPS": [{"settings": {"uid_field": "sub"}}]}',
                ]),
                encoding="utf-8",
            )
            (be / "config/settings/production.py").write_text(
                'CSRF_COOKIE_SECURE = True\nCSRF_COOKIE_HTTPONLY = False\nCSRF_COOKIE_NAME = "csrftoken"\nDJANGO_ADMIN_FORCE_ALLAUTH = True\n',
                encoding="utf-8",
            )
            (be / "config/urls.py").write_text(
                'path("accounts/", include("allauth.urls"))\n',
                encoding="utf-8",
            )
            (be / "konnaxion/users/models.py").write_text(
                'def can_interactive_login(self): pass\n',
                encoding="utf-8",
            )
            (be / "konnaxion/users/adapters.py").write_text(
                'x = user.can_interactive_login\n',
                encoding="utf-8",
            )
            (be / "requirements/base.txt").write_text(
                'django-allauth[mfa,socialaccount]==65.9.0\n',
                encoding="utf-8",
            )

            result = auth_contract_audit(fe, be)
            self.assertTrue(result["allauth_oidc_provider"])
            self.assertTrue(result["oidc_uid_sub"])
            self.assertTrue(result["oidc_optional"])
            self.assertTrue(result["email_auto_connect_disabled"])
            self.assertTrue(result["accounts_route"])
            self.assertFalse(result["legacy_token_endpoint"])
            self.assertTrue(result["interactive_policy"])
            self.assertTrue(result["csrf_browser_contract"])
            self.assertTrue(result["admin_allauth"])
            self.assertTrue(result["same_origin_api"])
            self.assertTrue(result["requirements_oidc"])
            self.assertEqual(result["auth0_residue"], [])
