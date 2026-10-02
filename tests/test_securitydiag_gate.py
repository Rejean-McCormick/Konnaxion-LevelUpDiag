from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from konnaxion_diag.checks import _securitydiag_web_trust_gate
from levelupdiag_core.config import AppConfig
from levelupdiag_core.models import Finding, StepResult
from levelupdiag_core.verdicts import FAIL, PASS


class SecurityDiagGateTests(unittest.TestCase):
    def _config(self, root: Path, tool: Path):
        return AppConfig({
            "schema": "levelupdiag.config.v2",
            "app_name": "Konnaxion",
            "target_repo_root": str(root),
            "control_dir": ".levelupdiag",
            "konnaxion": {
                "securitydiag_repo": str(tool),
                "securitydiag_required": True,
                "frontend_dir": "frontend",
                "backend_dir": "backend",
                "worlds": {"repo_dir": "../Konnaxion_Worlds"},
            },
            "execution": {},
            "env": {},
        }, tool)

    def test_pass_evidence_is_required(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root, tool = base / "Konnaxion", base / "SecurityDiag"
            root.mkdir(); tool.mkdir()
            (tool / "securitydiag.py").write_text("", encoding="utf-8")
            p = root / ".securitydiag/latest/levels/S04/result.json"
            p.parent.mkdir(parents=True)
            p.write_text(json.dumps({"verdict": "PASS", "findings": []}), encoding="utf-8")
            cfg = self._config(root, tool)
            paths = {"root": root, "securitydiag": tool}
            fake = Finding("run", PASS, "ok", "security")
            with patch("konnaxion_diag.checks.command_probe", return_value=(fake, None)):
                finding, _ = _securitydiag_web_trust_gate(cfg, paths)
            self.assertEqual(finding.severity, PASS)

    def test_blocker_fails_even_if_top_level_claims_pass(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root, tool = base / "Konnaxion", base / "SecurityDiag"
            root.mkdir(); tool.mkdir()
            (tool / "securitydiag.py").write_text("", encoding="utf-8")
            p = root / ".securitydiag/latest/levels/S04/result.json"
            p.parent.mkdir(parents=True)
            p.write_text(json.dumps({"verdict": "PASS", "findings": [{"id": "x", "verdict": "PASS", "release_blocker": True}]}), encoding="utf-8")
            cfg = self._config(root, tool)
            paths = {"root": root, "securitydiag": tool}
            fake = Finding("run", PASS, "ok", "security")
            with patch("konnaxion_diag.checks.command_probe", return_value=(fake, None)):
                finding, _ = _securitydiag_web_trust_gate(cfg, paths)
            self.assertEqual(finding.severity, FAIL)


if __name__ == "__main__":
    unittest.main()
