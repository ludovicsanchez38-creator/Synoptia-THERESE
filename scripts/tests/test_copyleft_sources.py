"""Sources correspondantes : couverture hors réseau et archives vérifiées."""
import copy
import hashlib
import importlib.util
import io
import json
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

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
                                         'status': 'available', 'recipes': [], 'evidence': 'Fixture exacte.',
                                         'required_supporting_sources': []}],
                         'exclusions': [], 'supporting_sources': []}
        self.inventory_patch = patch.object(self.m, 'checked_inventory', return_value=self.rows)
        self.inventory_patch.start()
        self.addCleanup(self.inventory_patch.stop)
        source_patch = patch.object(self.m, 'locked_sources', return_value={
            'python:example@1': {**self.resource, 'version': '1'}})
        source_patch.start()
        self.addCleanup(source_patch.stop)
        self.manifest['evidence_files'] = [{'path': 'licenses/evidence.json',
                                          'sha256': hashlib.sha256(b'{"version":"1"}').hexdigest()}]
        self.temp_root = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_root.cleanup)
        self.root = Path(self.temp_root.name)
        (self.root / 'licenses').mkdir()
        (self.root / 'licenses/evidence.json').write_bytes(b'{"version":"1"}')

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
                    self.m.assemble(manifest, Path(td), root=self.root)
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
            self.m.assemble(self.manifest, root, root=self.root)
            self.assertEqual((root / 'archives/source.tar.gz').read_bytes(), self.archive)
            self.assertEqual(json.loads((root / 'copyleft-sources.json').read_text()), self.manifest)
            readme = (root / 'LISEZMOI-SOURCES.txt').read_text()
            self.assertIn('example', readme)
            self.assertIn('trois ans', readme)

    def test_recipe_member_reference_is_resolved_in_the_verified_archive(self):
        buffer = io.BytesIO()
        raw = b'build the fixture'
        with tarfile.open(fileobj=buffer, mode='w:gz') as archive:
            member = tarfile.TarInfo('example/build.py')
            member.size = len(raw)
            archive.addfile(member, io.BytesIO(raw))
        data = buffer.getvalue()
        self.resource['sha256'] = hashlib.sha256(data).hexdigest()
        item = self.manifest['components'][0]
        for kind in ('exact', 'missing', 'changed'):
            with self.subTest(kind=kind):
                item['recipe_refs'] = [{'resource': 'source.tar.gz',
                                        'member': 'absent.py' if kind == 'missing' else 'build.py',
                                        'sha256': 'a' * 64 if kind == 'changed' else hashlib.sha256(raw).hexdigest()}]
                destination = self.root / kind
                with (patch.object(self.m, 'download', return_value=data),
                      patch.object(self.m, 'locked_sources', return_value={
                          'python:example@1': {**self.resource, 'version': '1'}})):
                    if kind == 'exact':
                        self.m.assemble(self.manifest, destination, root=self.root)
                    else:
                        with self.assertRaisesRegex(ValueError, 'Membre de recette'):
                            self.m.assemble(self.manifest, destination, root=self.root)
                        self.assertFalse((destination / 'copyleft-sources.json').exists())


class CorpusTests(unittest.TestCase):
    """Contre-épreuves de relecture-4, seules mutations du manifeste en mémoire."""

    @classmethod
    def setUpClass(cls):
        import copyleft_sources
        cls.m = copyleft_sources
        cls.root = SCRIPTS.parent
        cls.original = json.loads((cls.root / cls.m.MANIFEST).read_text())
        cls.rows = json.loads((cls.root / cls.m.licenses.INVENTORY).read_text())['packages']

    def setUp(self):
        self.manifest = copy.deepcopy(self.original)

    def omit_support(self, filename):
        self.manifest['supporting_sources'] = [
            r for r in self.manifest['supporting_sources'] if r['filename'] != filename]

    def test_relecture_removing_only_ffmpeg_or_libiconv_archive_blocks_verifier(self):
        original_read = Path.read_text
        for filename in ('pyav-ffmpeg-8.1.1-2-build-tree.tar.gz',
                         'mingw-w64-libiconv-1.19-1.src.tar.zst'):
            with self.subTest(filename=filename):
                self.manifest = copy.deepcopy(self.original)
                self.omit_support(filename)
                errors = self.m.verify_manifest(self.manifest, self.rows, self.root)
                self.assertTrue(any(filename in error for error in errors), errors)
                def read(path, *args, **kwargs):
                    if path == self.root / self.m.MANIFEST:
                        return json.dumps(self.manifest)
                    return original_read(path, *args, **kwargs)

                # La vraie main(), seule sa lecture du manifeste est substituée.
                with (patch.object(Path, 'read_text', read),
                      patch.object(sys, 'argv', ['copyleft_sources.py', 'verifier']),
                      self.assertRaisesRegex(ValueError, filename)):
                    self.m.main()

    def test_incomplete_corpus_is_rejected_before_assembly_writes_or_downloads(self):
        for filename in ('pyav-ffmpeg-8.1.1-2-build-tree.tar.gz',
                         'mingw-w64-libiconv-1.19-1.src.tar.zst'):
            with self.subTest(filename=filename):
                self.manifest = copy.deepcopy(self.original)
                self.omit_support(filename)
                folder = Mock()
                folder.mkdir.side_effect = AssertionError('Écriture avant validation')
                with (patch.object(self.m, 'download', side_effect=AssertionError('Téléchargement avant validation')) as download,
                      self.assertRaisesRegex(ValueError, filename)):
                    self.m.assemble(self.manifest, folder, root=self.root)
                folder.mkdir.assert_not_called()
                download.assert_not_called()

    def test_required_support_reference_cannot_be_removed_or_redirected(self):
        for replacement in (None, [], ['inconnue.tar.gz']):
            with self.subTest(replacement=replacement):
                item = next(c for c in self.manifest['components'] if c['component'] == 'ffmpeg')
                if replacement is None:
                    item.pop('required_supporting_sources', None)
                else:
                    item['required_supporting_sources'] = replacement
                self.assertTrue(self.m.verify_manifest(self.manifest, self.rows, self.root))

    def test_relecture_piper_141_with_recurring_source_is_rejected(self):
        piper = next(c for c in self.manifest['components'] if c['component'] == 'piper-tts')
        recurring = next(c for c in self.manifest['components'] if c['component'] == 'recurring-ical-events')
        piper['version'] = '1.4.1'
        piper['source'] = copy.deepcopy(recurring['source'])
        self.assertTrue(self.m.verify_manifest(self.manifest, self.rows, self.root))

    def test_relecture_empty_evidence_files_is_rejected(self):
        self.manifest['evidence_files'] = []
        self.assertTrue(self.m.verify_manifest(self.manifest, self.rows, self.root))

    def test_locked_url_hash_and_version_are_checked_individually(self):
        for component in ('piper-tts', 'cssparser@0.29.6'):
            for field in ('url', 'sha256', 'version'):
                with self.subTest(component=component, field=field):
                    manifest = copy.deepcopy(self.original)
                    item = next(c for c in manifest['components'] if c['component'] == component)
                    if field == 'version':
                        item['version'] = '0'
                    else:
                        item['source'][field] = 'https://example.test/source' if field == 'url' else 'a' * 64
                    errors = self.m.verify_manifest(manifest, self.rows, self.root)
                    self.assertTrue(any('différente du verrou' in e for e in errors), errors)

    def test_source_comparison_reads_the_lock_even_if_inventory_is_changed(self):
        rows = copy.deepcopy(self.rows)
        item = next(c for c in self.manifest['components'] if c['component'] == 'piper-tts')
        row = next(r for r in rows if r['id'] == 'python:piper-tts@1.4.2')
        row['artifact'] = item['source']['url'] = 'https://example.test/replaced.tar.gz'
        row['integrity'] = 'sha256:' + 'a' * 64
        item['source']['sha256'] = 'a' * 64
        self.manifest['inventory_sha256'] = self.m.inventory_digest(rows)
        errors = self.m.verify_manifest(self.manifest, rows, self.root)
        self.assertTrue(any('différente du verrou' in e for e in errors), errors)

    def test_all_reviewed_components_supports_and_references_are_required(self):
        self.assertEqual(self.m.verify_manifest(self.original, self.rows, self.root), [])
        for component in self.original['components']:
            for reference in component['required_supporting_sources']:
                with self.subTest(component=component['component'], reference=reference):
                    manifest = copy.deepcopy(self.original)
                    item = next(c for c in manifest['components'] if c['component'] == component['component'])
                    item['required_supporting_sources'].remove(reference)
                    errors = self.m.verify_manifest(manifest, self.rows, self.root)
                    self.assertTrue(any('Référence de construction obligatoire absente' in e for e in errors), errors)
        for resource in self.original['supporting_sources']:
            with self.subTest(resource=resource['filename']):
                self.manifest = copy.deepcopy(self.original)
                self.omit_support(resource['filename'])
                errors = self.m.verify_manifest(self.manifest, self.rows, self.root)
                self.assertTrue(any('Archive de construction requise absente' in e for e in errors), errors)

    def test_external_sources_require_evidence_and_recipe_references(self):
        for field in ('evidence_refs', 'recipe_refs'):
            for value in (None, [], ['absent']):
                with self.subTest(field=field, value=value):
                    item = next(c for c in self.manifest['components'] if c['component'] == 'axe-core')
                    if value is None:
                        item.pop(field, None)
                    else:
                        item[field] = value
                    self.assertTrue(self.m.verify_manifest(self.manifest, self.rows, self.root))


if __name__ == '__main__':
    unittest.main()
