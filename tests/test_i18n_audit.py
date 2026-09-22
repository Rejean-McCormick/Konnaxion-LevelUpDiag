import json
import tempfile
import unittest
from pathlib import Path

from konnaxion_diag.i18n_audit import audit_i18n, browser_probe_command


class I18nAuditTests(unittest.TestCase):
    def _frontend(self, root: Path) -> Path:
        frontend = root / "frontend"
        (frontend / "i18n" / "locales").mkdir(parents=True)
        (frontend / "app").mkdir(parents=True)
        return frontend

    def test_aligned_catalogs_and_placeholders_pass_static_audit(self):
        with tempfile.TemporaryDirectory() as d:
            frontend = self._frontend(Path(d))
            en = {"common": {"hello": "Hello {name}", "save": "Save"}}
            fr = {"common": {"hello": "Bonjour {name}", "save": "Enregistrer"}}
            (frontend / "i18n/locales/en.json").write_text(json.dumps(en), encoding="utf-8")
            (frontend / "i18n/locales/fr.json").write_text(json.dumps(fr), encoding="utf-8")
            report = audit_i18n(frontend)
            self.assertTrue(report["detected"])
            self.assertEqual(report["missing_in_en"], [])
            self.assertEqual(report["missing_in_fr"], [])
            self.assertEqual(report["placeholder_mismatches"], [])
            self.assertEqual(report["style_translation_calls"], [])
            self.assertEqual(report["translated_value_calls"], [])

    def test_catalog_key_and_placeholder_drift_are_detected(self):
        with tempfile.TemporaryDirectory() as d:
            frontend = self._frontend(Path(d))
            (frontend / "i18n/locales/en.json").write_text(json.dumps({"a": "Hi {name}", "onlyEn": "x"}), encoding="utf-8")
            (frontend / "i18n/locales/fr.json").write_text(json.dumps({"a": "Salut {user}", "onlyFr": "y"}), encoding="utf-8")
            report = audit_i18n(frontend)
            self.assertEqual(report["missing_in_en"], ["onlyFr"])
            self.assertEqual(report["missing_in_fr"], ["onlyEn"])
            self.assertEqual(report["placeholder_mismatches"][0]["key"], "a")

    def test_translation_of_css_and_technical_values_is_detected(self):
        with tempfile.TemporaryDirectory() as d:
            frontend = self._frontend(Path(d))
            (frontend / "i18n/locales/en.json").write_text(json.dumps({"css": "display: -webkit-box; overflow: hidden;", "label": "Planned"}), encoding="utf-8")
            (frontend / "i18n/locales/fr.json").write_text(json.dumps({"css": "display: -webkit-box; overflow: hidden;", "label": "Planifié"}), encoding="utf-8")
            source = """export function X(){ return <><style jsx>{t('css')}</style></>; }\nconst OPTIONS=[{label:t('label'), value:t('label')}];"""
            (frontend / "app/page.tsx").write_text(source, encoding="utf-8")
            report = audit_i18n(frontend)
            self.assertEqual(report["css_like_catalog_values"], ["css"])
            self.assertEqual(len(report["style_translation_calls"]), 1)
            self.assertEqual(len(report["translated_value_calls"]), 1)

    def test_browser_probe_command_runs_from_frontend_node_context(self):
        cmd = browser_probe_command("http://127.0.0.1:3000", "/ekoh/dashboard?sidebar=ekoh")
        self.assertEqual(cmd[:2], ["node", "-e"])
        self.assertIn("@playwright/test", cmd[2])
        self.assertEqual(cmd[-2:], ["http://127.0.0.1:3000", "/ekoh/dashboard?sidebar=ekoh"])


if __name__ == "__main__":
    unittest.main()
