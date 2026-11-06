"""Le relevé à blanc des runners ne publie rien et copie les bons octets."""
import hashlib
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
WORKFLOW = ROOT / '.github/workflows/releve-natif.yml'


class ReleveNatifWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.source = WORKFLOW.read_text(encoding='utf-8')
        self.data = yaml.safe_load(self.source)

    def test_releve_natif_ne_publie_rien(self):
        triggers = self.data[True]
        self.assertEqual(set(triggers), {'workflow_dispatch', 'push'})
        push = triggers['push']
        self.assertNotIn('tags', push)
        self.assertTrue(all(b != 'main' and not b.startswith('v') for b in push['branches']))
        self.assertEqual(self.data['permissions'], {'contents': 'read'})
        # Aucun secret, ni nommé ni hérité : sans eux, rien ne peut signer ni publier.
        self.assertNotIn('secrets', self.source)
        for forbidden in ['tauri-action', 'action-gh-release', 'gh release', 'upload-release',
                          'releases/', 'git push', 'git tag', 'contents: write']:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, self.source)
        for job in self.data['jobs'].values():
            self.assertNotIn('permissions', job)
            if 'uses' in job:
                self.assertIn(job['uses'], {'./.github/workflows/ci.yml',
                                            './.github/workflows/tests-e2e.yml'})
                called = yaml.safe_load((ROOT / job['uses']).read_text(encoding='utf-8'))
                self.assertEqual(called['permissions'], {'contents': 'read'})

    def test_releve_natif_actions_epinglees(self):
        for step in self.data['jobs']['releve']['steps']:
            action = step.get('uses', '')
            if action:
                with self.subTest(action=action):
                    self.assertRegex(action, r'@[a-f0-9]{40}$')
                    self.assertRegex(self.source, re.escape(action) + r'\s+# v\d+\.\d+\.\d+')

    def test_releve_natif_suit_le_build_de_la_release(self):
        release = yaml.safe_load((ROOT / '.github/workflows/release.yml').read_text(encoding='utf-8'))
        build = {s.get('name'): s for s in release['jobs']['build']['steps'] if s.get('name')}
        steps = {s.get('name'): s for s in self.data['jobs']['releve']['steps'] if s.get('name')}
        for name in ['Installer UV et dépendances Python', 'Installer torch CPU-only (réduction ~1 Go)',
                     'Contrôler les licences tierces', 'Build sidecar (PyInstaller)',
                     'Copier le sidecar dans Tauri', 'Signer et vérifier le moteur macOS']:
            with self.subTest(step=name):
                self.assertEqual(steps[name]['run'], build[name]['run'])
        self.assertEqual(steps['Inventorier les bibliothèques réellement embarquées']['run'],
                         build['Inventorier les bibliothèques réellement embarquées']['run'])
        self.assertEqual(self.data['jobs']['releve']['strategy']['matrix'],
                         release['jobs']['build']['strategy']['matrix'])

    def test_releve_natif_epingle_la_version_du_catalogue_cpython(self):
        catalog = json.loads((ROOT / 'licenses/cpython-components.lock.json').read_text(encoding='utf-8'))
        setup = next(s for s in self.data['jobs']['releve']['steps']
                     if s.get('uses', '').startswith('actions/setup-python@'))
        self.assertEqual(setup['with']['python-version'], catalog['version'])


class ReleveRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import releve_runner
        cls.m = releve_runner

    def test_copie_les_natifs_hors_record_et_liste_les_autres(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            libre, roue = base / 'libpython.dylib', base / 'roue.so'
            libre.write_bytes(b'\xcf\xfa\xed\xfecpython')
            roue.write_bytes(b'\x7fELFwheel')
            digest = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in (libre, roue)}
            origins = {n: {'path': str(p.resolve()), 'sha256': digest[p]}
                       for n, p in [('libpython.dylib', libre), ('pkg/roue.so', roue)]}
            installed = {roue.resolve(): ('pkg', '1.0', digest[roue])}
            report = self.m.survey(origins, installed, base / 'out')
            self.assertEqual(report['hors_record'], 1)
            rows = {r['name']: r for r in report['files']}
            self.assertEqual(rows['pkg/roue.so']['record']['distribution'], 'pkg')
            self.assertNotIn('copie', rows['pkg/roue.so'])
            copied = base / 'out' / rows['libpython.dylib']['copie']
            self.assertEqual(copied.read_bytes(), libre.read_bytes())

    def test_refuse_une_origine_modifiee_depuis_analysis(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'lib.dll'
            path.write_bytes(b'MZchanged')
            origins = {'lib.dll': {'path': str(path), 'sha256': '0' * 64}}
            with self.assertRaisesRegex(ValueError, 'Origine modifiée'):
                self.m.survey(origins, {}, Path(tmp) / 'out')


if __name__ == '__main__':
    unittest.main()
