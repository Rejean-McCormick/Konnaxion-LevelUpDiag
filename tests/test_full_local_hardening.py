from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from konnaxion_diag.checks import (
    _powershell_supports_deep_only,
    _pytest_args,
    _pytest_clean_db_command,
    _pytest_isolated_command,
    _pytest_isolated_db_name,
    _pytest_probe_with_clean_db_retry,
    _pytest_schema_is_stale,
)
from levelupdiag_core.verdicts import FAIL, PASS


class FullLocalHardeningTests(unittest.TestCase):
    def test_schema_missing_is_recognized_as_stale_test_db(self):
        step = SimpleNamespace(
            verdict=FAIL,
            output_tail='django.db.utils.ProgrammingError: relation "worlds_world" does not exist',
            error='',
        )
        self.assertTrue(_pytest_schema_is_stale(step))

    def test_normal_assertion_failure_is_not_called_stale_schema(self):
        step = SimpleNamespace(
            verdict=FAIL,
            output_tail='AssertionError: expected 3 got 6',
            error='',
        )
        self.assertFalse(_pytest_schema_is_stale(step))

    def test_passing_step_never_triggers_clean_db_retry(self):
        step = SimpleNamespace(verdict=PASS, output_tail='', error='')
        self.assertFalse(_pytest_schema_is_stale(step))

    def test_create_db_is_added_once_to_pytest_command(self):
        cmd = _pytest_clean_db_command(['python', '-m', 'pytest', 'konnaxion/worlds/tests', '-q', '--reuse-db'])
        self.assertEqual(cmd.count('--create-db'), 1)
        self.assertNotIn('--reuse-db', cmd)
        cmd2 = _pytest_clean_db_command(cmd)
        self.assertEqual(cmd2.count('--create-db'), 1)

    def test_non_pytest_command_is_not_rewritten(self):
        self.assertIsNone(_pytest_clean_db_command(['python', 'manage.py', 'check']))


    def test_pytest_args_are_extracted_from_python_module_command(self):
        self.assertEqual(
            _pytest_args(['python', '-m', 'pytest', 'konnaxion/worlds/tests', '-q']),
            ['konnaxion/worlds/tests', '-q'],
        )

    def test_isolated_db_name_is_stable_per_run_and_distinct_per_probe(self):
        with patch.dict('os.environ', {'LEVELUPDIAG_RUN_ID': 'run-123'}, clear=False):
            first = _pytest_isolated_db_name('kx.worlds.backend-tests')
            second = _pytest_isolated_db_name('kx.worlds.backend-tests')
            other = _pytest_isolated_db_name('kx.worlds.deep-isolation')
        self.assertEqual(first, second)
        self.assertNotEqual(first, other)
        self.assertTrue(first.startswith('test_kx_lud_'))
        self.assertLessEqual(len(first), 63)

    def test_isolated_command_uses_wrapper_and_drops_reuse_db_flag(self):
        class FakeConfig:
            diagnostics_root_path = Path(__file__).resolve().parents[1]
            def get(self, key, default=None):
                return {} if key == 'konnaxion' else default

        with patch.dict('os.environ', {'LEVELUPDIAG_RUN_ID': 'run-123'}, clear=False):
            isolated = _pytest_isolated_command(
                FakeConfig(),
                ['python', '-m', 'pytest', 'konnaxion/worlds/tests', '-q', '--reuse-db'],
                finding_id='kx.worlds.backend-tests',
                project_root=Path('C:/fake/konnaxion/backend'),
            )
        self.assertIsNotNone(isolated)
        command, db_name = isolated
        self.assertIn('run_isolated_django_pytest.py', command[1])
        self.assertIn('--db-name', command)
        self.assertIn(db_name, command)
        self.assertNotIn('--reuse-db', command)
        self.assertIn('--project-root', command)
        self.assertIn(str(Path('C:/fake/konnaxion/backend')), command)

    def test_isolated_probe_runs_once_and_records_database_metadata(self):
        class FakeConfig:
            diagnostics_root_path = Path(__file__).resolve().parents[1]
            def get(self, key, default=None):
                return {} if key == 'konnaxion' else default

        passed_step = SimpleNamespace(
            verdict=PASS, output_tail='12 passed', error='', command=('python',), duration_seconds=1.0
        )
        passed_finding = SimpleNamespace(severity=PASS, data=None, recommendation=None)
        with patch.dict('os.environ', {'LEVELUPDIAG_RUN_ID': 'run-123'}, clear=False), \
             patch('konnaxion_diag.checks.command_probe', return_value=(passed_finding, passed_step)) as probe:
            finding, step = _pytest_probe_with_clean_db_retry(
                FakeConfig(),
                finding_id='kx.worlds.backend-tests',
                label='World tests',
                command=['python', '-m', 'pytest', 'konnaxion/worlds/tests', '-q'],
                cwd=Path('.'),
                timeout=10,
                optional=True,
            )
        self.assertEqual(probe.call_count, 1)
        self.assertTrue(finding.data['isolated_test_database'])
        self.assertTrue(finding.data['target_reuse_db_disabled'])
        self.assertTrue(finding.data['test_database_name'].startswith('test_kx_lud_'))
        self.assertIs(step, passed_step)

    def test_deep_only_capability_is_detected(self):
        with tempfile.TemporaryDirectory() as td:
            script = Path(td) / 'full-scan.ps1'
            script.write_text('param([switch]$DeepOnly)\n', encoding='utf-8')
            self.assertTrue(_powershell_supports_deep_only(script))
            script.write_text('param([switch]$KeepFrontend)\n', encoding='utf-8')
            self.assertFalse(_powershell_supports_deep_only(script))

    def test_clean_db_retry_recovers_missing_relation(self):
        stale_step = SimpleNamespace(
            verdict=FAIL,
            output_tail='ProgrammingError: relation "worlds_world" does not exist',
            error='',
            command=('python', '-m', 'pytest', 'konnaxion/worlds/tests', '-q'),
            duration_seconds=1.0,
        )
        passed_step = SimpleNamespace(
            verdict=PASS,
            output_tail='12 passed',
            error='',
            command=('python', '-m', 'pytest', 'konnaxion/worlds/tests', '-q', '--create-db'),
            duration_seconds=2.0,
        )
        first_finding = SimpleNamespace(severity=FAIL)
        second_finding = SimpleNamespace(severity=PASS, data=None, recommendation=None)
        with patch('konnaxion_diag.checks._pytest_isolated_command', return_value=None), \
             patch('konnaxion_diag.checks.command_probe', side_effect=[(first_finding, stale_step), (second_finding, passed_step)]) as probe:
            finding, step = _pytest_probe_with_clean_db_retry(
                object(),
                finding_id='x',
                label='World tests',
                command=['python', '-m', 'pytest', 'konnaxion/worlds/tests', '-q'],
                cwd=Path('.'),
                timeout=10,
                optional=True,
            )
        self.assertEqual(probe.call_count, 2)
        self.assertEqual(finding.severity, PASS)
        self.assertTrue(finding.data['recovered_from_stale_test_db'])
        self.assertIn('--create-db', step.command)

    def test_clean_db_retry_does_not_mask_normal_failure(self):
        failed_step = SimpleNamespace(
            verdict=FAIL,
            output_tail='AssertionError: expected 3 got 6',
            error='',
        )
        failed_finding = SimpleNamespace(severity=FAIL)
        with patch('konnaxion_diag.checks._pytest_isolated_command', return_value=None), \
             patch('konnaxion_diag.checks.command_probe', return_value=(failed_finding, failed_step)) as probe:
            finding, step = _pytest_probe_with_clean_db_retry(
                object(),
                finding_id='x',
                label='Tests',
                command=['python', '-m', 'pytest', '-q'],
                cwd=Path('.'),
                timeout=10,
                optional=True,
            )
        self.assertEqual(probe.call_count, 1)
        self.assertIs(finding, failed_finding)
        self.assertIs(step, failed_step)


if __name__ == '__main__':
    unittest.main()
