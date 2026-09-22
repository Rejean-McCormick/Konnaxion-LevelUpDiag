import unittest
from pathlib import Path
from levelupdiag_core.manifest import load_manifest,validate_manifest,get_level
ROOT=Path(__file__).resolve().parents[1]
class ManifestTests(unittest.TestCase):
    def test_taxonomy(self):
        m=load_manifest(ROOT); self.assertEqual(validate_manifest(m),[]); self.assertEqual([x['id'] for x in m['levels']],[f'N{i:02d}' for i in range(12)])
    def test_dependencies(self):
        m=load_manifest(ROOT)
        self.assertEqual(m['levels'][0]['depends_on'],[])
        for level in m['levels'][1:]:
            expected = ['N00', 'N03'] if level['id'] == 'N05' else ['N00']
            self.assertEqual(level['depends_on'], expected)
    def test_connection_sequence(self):
        m=load_manifest(ROOT); self.assertEqual(m['campaigns']['connection-debug']['levels'],['N00','N01','N02','N03','N04','N05','N06','N11']); self.assertEqual(m['campaigns']['connection-debug']['execution'],'sequential')
    def test_recommended_sequence(self):
        m=load_manifest(ROOT); self.assertEqual(m['sequences']['recommended-debug']['campaigns'],['source-audit','auth-debug','connection-debug','full-local'])
    def test_world_switch_campaign(self):
        m=load_manifest(ROOT); self.assertEqual(m['campaigns']['world-switch']['levels'],['N00','N01','N02','N03','N04','N05','N06','N07','N10','N11']); self.assertEqual(m['campaigns']['world-switch']['execution'],'sequential')

    def test_i18n_validation_campaign(self):
        m=load_manifest(ROOT); self.assertEqual(m['campaigns']['i18n-validation']['levels'],['N00','N01','N03','N05','N11']); self.assertEqual(m['campaigns']['i18n-validation']['execution'],'sequential')
