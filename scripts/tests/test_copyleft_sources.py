"""Sources correspondantes : couverture hors réseau et archives vérifiées."""
import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))


class SourceTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('copyleft_sources', SCRIPTS / 'copyleft_sources.py')
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)
        self.rows = [{'id': 'python:example@1', 'license': 'GPL-3.0-or-later',
                      'artifact': 'https://example.test/bin.whl', 'integrity': 'sha256:' + 'a' * 64,
                      'notices': [{'path': 'LICENSE', 'text': 'GNU GENERAL PUBLIC LICENSE'}]}]
        self.archive = b'exact source archive fixture'
        self.resource = {'url': 'https://example.test/source.tar.gz',
                         'sha256': hashlib.sha256(self.archive).hexdigest(), 'filename': 'source.tar.gz'}
        self.manifest = {'schema': 1, 'inventory_sha256': self.m.inventory_digest(self.rows),
                         'components': [{'component': 'example', 'version': '1', 'license': 'GPL-3.0-or-later',
                                         'packages': ['python:example@1'], 'source': self.resource,
                                         'status': 'available', 'recipes': [], 'evidence': 'Fixture exacte.'}],
                         'exclusions': [], 'supporting_sources': []}

    def test_exact_manifest_passes_without_network(self):
        with patch('urllib.request.urlopen', side_effect=AssertionError('network')):
            self.assertEqual(self.m.verify_manifest(self.manifest, self.rows), [])

    def test_missing_component_and_stale_inventory_block(self):
        for kind in ('missing', 'changed', 'unknown', 'duplicate'):
            manifest = copy.deepcopy(self.manifest)
            if kind == 'missing':
                manifest['components'] = []
            elif kind == 'changed':
                manifest['inventory_sha256'] = '0' * 64
            elif kind == 'unknown':
                manifest['components'][0]['packages'] = ['python:other@1']
            else:
                manifest['components'].append(copy.deepcopy(manifest['components'][0]))
            with self.subTest(kind=kind):
                self.assertTrue(self.m.verify_manifest(manifest, self.rows))

    def test_missing_version_archive_hash_or_recipe_block(self):
        for kind in ('version', 'hash', 'status', 'recipe'):
            manifest = copy.deepcopy(self.manifest)
            item = manifest['components'][0]
            if kind == 'version':
                item['version'] = ''
            elif kind == 'hash':
                item['source']['sha256'] = 'invalid'
            elif kind == 'status':
                item['status'] = 'missing'
                item['missing_reason'] = 'Version exacte introuvable.'
            else:
                item['recipes'] = [{**self.resource, 'commit': 'main'}]
            with self.subTest(kind=kind):
                self.assertTrue(self.m.verify_manifest(manifest, self.rows))

    def test_license_in_notices_is_not_silently_ignored(self):
        self.rows[0]['license'] = 'MIT'
        self.manifest['inventory_sha256'] = self.m.inventory_digest(self.rows)
        self.manifest['components'] = []
        self.assertTrue(self.m.verify_manifest(self.manifest, self.rows))

    def test_exclusion_needs_reason_and_notice_evidence(self):
        self.manifest['components'] = []
        self.manifest['exclusions'] = [{'packages': ['python:example@1'], 'reason': 'permissive'}]
        self.assertTrue(self.m.verify_manifest(self.manifest, self.rows))

    def test_version_evidence_changed_or_missing_blocks_offline(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'licenses').mkdir()
            target = root / 'licenses/evidence.json'
            exact = b'{"version":"1"}'
            self.manifest['evidence_files'] = [{'path': 'licenses/evidence.json',
                                              'sha256': hashlib.sha256(exact).hexdigest()}]
            self.assertTrue(self.m.verify_manifest(self.manifest, self.rows, root))
            target.write_bytes(exact)
            self.assertEqual(self.m.verify_manifest(self.manifest, self.rows, root), [])
            target.write_bytes(b'{"version":"2"}')
            self.assertTrue(self.m.verify_manifest(self.manifest, self.rows, root))

    def test_assemble_hash_failure_and_path_escape(self):
        with tempfile.TemporaryDirectory() as td:
            for data, filename in [(b'corrupted', 'source.tar.gz'), (self.archive, '../outside')]:
                manifest = copy.deepcopy(self.manifest)
                manifest['components'][0]['source']['filename'] = filename
                with self.subTest(filename=filename), patch.object(self.m, 'download', return_value=data), self.assertRaises(ValueError):
                    self.m.assemble(manifest, Path(td))
            self.assertFalse((Path(td) / 'source.tar.gz').exists())

    def test_assemble_includes_exact_version_evidence(self):
        with tempfile.TemporaryDirectory() as td, patch.object(self.m, 'download', return_value=self.archive):
            root = Path(td)
            (root / 'licenses').mkdir()
            exact = b'{"version":"1"}'
            (root / 'licenses/evidence.json').write_bytes(exact)
            self.manifest['evidence_files'] = [{'path': 'licenses/evidence.json',
                                              'sha256': hashlib.sha256(exact).hexdigest()}]
            self.m.assemble(self.manifest, root / 'bundle', root=root)
            self.assertEqual((root / 'bundle/licenses/evidence.json').read_bytes(), exact)
            (root / 'licenses/evidence.json').write_bytes(b'changed')
            with self.assertRaises(ValueError):
                self.m.assemble(self.manifest, root / 'bundle', root=root)

    def test_assemble_writes_exact_archives_manifest_and_french_readme(self):
        with tempfile.TemporaryDirectory() as td, patch.object(self.m, 'download', return_value=self.archive):
            root = Path(td)
            self.m.assemble(self.manifest, root)
            self.assertEqual((root / 'archives/source.tar.gz').read_bytes(), self.archive)
            self.assertEqual(json.loads((root / 'copyleft-sources.json').read_text()), self.manifest)
            readme = (root / 'LISEZMOI-SOURCES.txt').read_text()
            self.assertIn('example', readme)
            self.assertIn('trois ans', readme)


if __name__ == '__main__':
    unittest.main()
