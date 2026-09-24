from __future__ import annotations
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from levelupdiag_core.runner import (
    _restore_tracked_paths,
    _snapshot_tracked_paths,
    _tracked_compare_ignore_paths,
    _tracked_ignore_paths,
    _tracked_restore_paths,
    _tracked_status,
)
from levelupdiag_core.verdicts import PASS, WARN, aggregate_verdicts


@unittest.skipUnless(shutil.which('git'), 'git is required for tracked-state protection tests')
class TargetProtectionTests(unittest.TestCase):
    def test_next_env_generation_is_ignored_but_source_drift_is_not(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            subprocess.run(['git', 'init', '-q'], cwd=root, check=True)
            (root / 'frontend').mkdir()
            (root / 'frontend' / 'next-env.d.ts').write_text('v1\n', encoding='utf-8')
            (root / 'source.py').write_text('x = 1\n', encoding='utf-8')
            subprocess.run(['git', 'add', '.'], cwd=root, check=True)

            ignored = _tracked_ignore_paths({})
            before = _tracked_status(root, ignored_paths=ignored)
            self.assertIsNotNone(before)

            (root / 'frontend' / 'next-env.d.ts').write_text('v2\n', encoding='utf-8')
            after_generated = _tracked_status(root, ignored_paths=ignored)
            self.assertEqual(before, after_generated)

            (root / 'source.py').write_text('x = 2\n', encoding='utf-8')
            after_source = _tracked_status(root, ignored_paths=ignored)
            self.assertNotEqual(before, after_source)



    def test_storage_state_is_restored_to_pre_diagnostic_state(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            state_file = root / 'frontend' / 'storageState.json'
            state_file.parent.mkdir(parents=True)
            state_file.write_text('{"before": true}\n', encoding='utf-8')

            paths = _tracked_restore_paths({})
            self.assertIn('frontend/storageState.json', paths)
            snapshot = _snapshot_tracked_paths(root, paths)

            state_file.write_text('{"after": true}\n', encoding='utf-8')
            restored = _restore_tracked_paths(root, snapshot)

            self.assertIn('frontend/storageState.json', restored)
            self.assertEqual(state_file.read_text(encoding='utf-8'), '{"before": true}\n')

    def test_absent_storage_state_created_by_diagnostics_is_removed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            state_file = root / 'frontend' / 'storageState.json'
            state_file.parent.mkdir(parents=True)
            snapshot = _snapshot_tracked_paths(root, _tracked_restore_paths({}))

            state_file.write_text('{"generated": true}\n', encoding='utf-8')
            restored = _restore_tracked_paths(root, snapshot)

            self.assertIn('frontend/storageState.json', restored)
            self.assertFalse(state_file.exists())


    def test_restore_paths_are_excluded_from_git_drift_comparison(self):
        ignored = _tracked_compare_ignore_paths({})
        self.assertIn('frontend/next-env.d.ts', ignored)
        self.assertIn('frontend/storageState.json', ignored)
        self.assertEqual(len(ignored), len(set(ignored)))

    def test_warning_only_aggregate_stays_warn(self):
        self.assertEqual(aggregate_verdicts([PASS, WARN, PASS]), WARN)

    def test_config_can_add_safe_ignored_paths(self):
        ignored = _tracked_ignore_paths({'protect_tracked_ignore_paths': ['frontend/generated.txt']})
        self.assertIn('frontend/next-env.d.ts', ignored)
        self.assertIn('frontend/generated.txt', ignored)
        self.assertEqual(len(ignored), len(set(ignored)))


if __name__ == '__main__':
    unittest.main()


class DependencyBlockingTests(unittest.TestCase):
    def test_fail_is_hard_dependency(self):
        from levelupdiag_core.runner import _HARD_DEP
        from levelupdiag_core.verdicts import FAIL
        self.assertIn(FAIL, _HARD_DEP)
