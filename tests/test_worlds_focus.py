from __future__ import annotations
import os
import unittest
from unittest.mock import patch

from konnaxion_diag.checks import _worlds_focused, _worlds_required


class WorldsCampaignFocusTests(unittest.TestCase):
    def test_world_switch_campaign_is_focused_and_required(self):
        with patch('konnaxion_diag.checks.active_session', return_value={}), patch.dict(os.environ, {'LEVELUPDIAG_CAMPAIGN': 'world-switch'}, clear=False):
            self.assertTrue(_worlds_focused(None))
            self.assertTrue(_worlds_required(None))

    def test_full_local_is_not_focused(self):
        with patch('konnaxion_diag.checks.active_session', return_value={}), patch.dict(os.environ, {'LEVELUPDIAG_CAMPAIGN': 'full-local'}, clear=False):
            self.assertFalse(_worlds_focused(None))
            self.assertFalse(_worlds_required(None))


if __name__ == '__main__':
    unittest.main()
