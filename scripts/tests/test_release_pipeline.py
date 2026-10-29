"""Garde-fous de l'ordre de publication et du mode sans comptes de signature."""
import importlib.util
import json
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


class PipelineTests(unittest.TestCase):
    def test_no_upload_before_platform_checks(self):
        jobs = yaml.safe_load((ROOT / '.github/workflows/release.yml').read_text())['jobs']
        steps = jobs['build']['steps']
        build = next(s for s in steps if 'tauri-apps/tauri-action@' in s.get('uses', ''))
        self.assertNotIn('tagName', build.get('with', {}))
        names = [s.get('name', '') for s in steps]
        self.assertLess(names.index('Finaliser la signature macOS'), names.index('Publier les artefacts vérifiés'))
        self.assertLess(names.index('Vérifier Authenticode'), names.index('Publier les artefacts vérifiés'))
        self.assertLess(names.index('Contrôler les licences tierces'), names.index('Build THÉRÈSE (Tauri)'))

    def test_microsoft_action_is_official_and_pinned(self):
        steps = yaml.safe_load((ROOT / '.github/workflows/release.yml').read_text())['jobs']['build']['steps']
        actions = [s for s in steps if s.get('uses', '').startswith('Azure/artifact-signing-action@')]
        self.assertEqual(len(actions), 2)
        for step in actions:
            self.assertRegex(step['uses'].split('@')[1], r'^[a-f0-9]{40}$')
            self.assertIn('pyd', step['with']['files-folder-filter'])
            self.assertIn('windows-signing.outputs.enabled', step['if'])

    def test_licenses_are_resources_on_all_platforms(self):
        base = ROOT / 'src/frontend/src-tauri'
        for name in ['tauri.conf.json', 'tauri.linux.conf.json']:
            resources = json.loads((base / name).read_text())['bundle']['resources']
            self.assertIsInstance(resources, dict)
            self.assertEqual(resources['../../../THIRD_PARTY_LICENSES'], 'THIRD_PARTY_LICENSES')

    def test_publication_refuses_incomplete_platform(self):
        import tempfile
        spec = importlib.util.spec_from_file_location('publish', ROOT / 'scripts/publish_release_artifacts.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'dmg').mkdir()
            (root / 'dmg/test.dmg').write_bytes(b'dmg')
            with self.assertRaises(ValueError):
                module.artifacts(root, 'macOS')
            (root / 'macos').mkdir()
            (root / 'macos/test.app.tar.gz').write_bytes(b'archive')
            self.assertEqual(len(module.artifacts(root, 'macOS')), 2)

    def test_license_fingerprints_are_stable_on_windows_checkout(self):
        import subprocess
        paths = ['package-lock.json', 'src/frontend/package-lock.json',
                 'src/frontend/src-tauri/Cargo.lock', 'uv.lock',
                 'licenses/overrides.json', 'licenses/native-components.lock.json',
                 'licenses/runtime-wheels.lock.json', 'THIRD_PARTY_LICENSES']
        result = subprocess.run(['git', 'check-attr', '-z', 'eol', '--', *paths],
                                cwd=ROOT, text=True, capture_output=True, check=True)
        values = result.stdout.split('\0')[2::3]
        self.assertEqual(values, ['lf'] * len(paths))

    def test_windows_no_secrets_never_enables_sign_command(self):
        spec = importlib.util.spec_from_file_location('prepare', ROOT / 'scripts/prepare_windows_signing.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.configuration({}, Path('test.ps1')), (False, {}))
        self.assertEqual(module.configuration({'AZURE_CLIENT_ID': 'test'}, Path('test.ps1')), (False, {}))
        enabled, config = module.configuration(dict.fromkeys(module.SECRETS, 'test'), Path('space here/test.ps1'))
        self.assertTrue(enabled)
        self.assertEqual(config['bundle']['windows']['signCommand']['args'][-2:], ['space here/test.ps1', '%1'])


if __name__ == '__main__':
    unittest.main()
