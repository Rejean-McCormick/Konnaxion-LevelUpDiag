from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


WRAPPER = Path(__file__).resolve().parents[1] / "scripts" / "run_isolated_django_pytest.py"
SPEC = importlib.util.spec_from_file_location("levelupdiag_isolated_pytest", WRAPPER)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PytestWrapperTempTests(unittest.TestCase):
    def test_normalizer_strips_target_basetemp_forms(self):
        self.assertEqual(
            MODULE._normalize_pytest_args([
                "--basetemp", "C:/shared/pytest", "-q", "--basetemp=C:/other", "tests",
            ]),
            ["-q", "tests"],
        )

    def test_normalizer_strips_reuse_and_create_db(self):
        self.assertEqual(
            MODULE._normalize_pytest_args(["--reuse-db", "--create-db", "-q"]),
            ["-q"],
        )


if __name__ == "__main__":
    unittest.main()
