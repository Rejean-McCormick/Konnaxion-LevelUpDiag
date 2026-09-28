from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from konnaxion_diag.worlds_audit import audit_worlds


class KxUniversesRegressionTests(unittest.TestCase):
    def _roots(self, root: Path):
        host = root / "Konnaxion"
        engine = root / "Konnaxion_Worlds"
        frontend = host / "frontend"
        backend = host / "backend"
        frontend.mkdir(parents=True)
        backend.mkdir(parents=True)
        return frontend, backend, engine

    def test_engine_namespace_extra_is_forbidden(self):
        with tempfile.TemporaryDirectory() as tmp:
            frontend, backend, engine = self._roots(Path(tmp))
            extra = engine / "backend" / "konnaxion" / "moderation"
            extra.mkdir(parents=True)
            report = audit_worlds(frontend, backend, engine)
            self.assertIn(str(extra), report["forbidden_present"])
            self.assertFalse(report["ownership"]["engine_namespace_is_worlds_only"])

    def test_entire_engine_frontend_is_forbidden(self):
        with tempfile.TemporaryDirectory() as tmp:
            frontend, backend, engine = self._roots(Path(tmp))
            (engine / "frontend").mkdir(parents=True)
            report = audit_worlds(frontend, backend, engine)
            self.assertIn(str(engine / "frontend"), report["forbidden_present"])
            self.assertFalse(report["ownership"]["engine_does_not_vendor_product_frontend"])


if __name__ == "__main__":
    unittest.main()
