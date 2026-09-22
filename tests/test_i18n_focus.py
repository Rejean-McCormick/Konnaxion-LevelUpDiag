from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from konnaxion_diag.checks import _current_campaign, _i18n_focused, _worlds_focused


class I18nFocusTests(unittest.TestCase):
    def setUp(self):
        self.config = object()

    def test_i18n_campaign_is_detected(self):
        with patch.dict(os.environ, {"LEVELUPDIAG_CAMPAIGN": "i18n-validation"}, clear=False):
            self.assertEqual(_current_campaign(self.config), "i18n-validation")
            self.assertTrue(_i18n_focused(self.config))
            self.assertFalse(_worlds_focused(self.config))

    def test_worker_environment_beats_stale_active_session(self):
        with patch.dict(os.environ, {"LEVELUPDIAG_CAMPAIGN": "i18n-validation"}, clear=False), \
             patch("konnaxion_diag.checks.active_session", return_value={"campaign": "frontend"}) as session:
            self.assertEqual(_current_campaign(self.config), "i18n-validation")
            session.assert_not_called()

    def test_active_session_is_fallback_when_environment_missing(self):
        with patch.dict(os.environ, {}, clear=True), \
             patch("konnaxion_diag.checks.active_session", return_value={"campaign": "frontend"}):
            self.assertEqual(_current_campaign(self.config), "frontend")

    def test_worlds_campaign_is_distinct(self):
        with patch.dict(os.environ, {"LEVELUPDIAG_CAMPAIGN": "world-switch"}, clear=False):
            self.assertTrue(_worlds_focused(self.config))
            self.assertFalse(_i18n_focused(self.config))


if __name__ == "__main__":
    unittest.main()
