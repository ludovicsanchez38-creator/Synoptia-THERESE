"""Contrats du générateur, exécutables sans le backend ni le réseau."""
import importlib.util
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'third_party_licenses.py'


class LicensesTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('licenses', SCRIPT)
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)

    def test_copyleft_expressions_and_notices(self):
        self.assertEqual(self.m.copyleft('MIT OR LGPL-2.1-or-later'), ['LGPL'])
        self.assertEqual(self.m.copyleft('AGPL-3.0-only AND GPL-2.0-or-later'), ['AGPL', 'GPL'])
        self.assertEqual(self.m.copyleft('MIT'), [])
        self.assertEqual(self.m.copyleft('GNU GENERAL PUBLIC LICENSE\nVersion 3'), ['GPL'])

    def test_archive_paths_are_not_extracted(self):
        self.assertTrue(self.m.is_notice('../../LICENSE'))
        self.assertFalse(self.m.is_notice('src/license_checker.py'))
        self.assertTrue(self.m.is_notice('package/licenses/THIRD_PARTY.txt'))

    def test_missing_changed_and_stale_output_fail(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / 'THIRD_PARTY_LICENSES'
            with self.assertRaises(ValueError):
                self.m.check_output(target, 'expected')
            target.write_text('stale')
            with self.assertRaises(ValueError):
                self.m.check_output(target, 'expected')
            target.write_text('expected')
            self.m.check_output(target, 'expected')

    def test_check_rejects_platform_dependent_line_endings(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / 'THIRD_PARTY_LICENSES'
            target.write_bytes('Licence tierce\r\nTexte complet\r\n'.encode('utf-8'))
            with self.assertRaises(ValueError):
                self.m.check_output(target, 'Licence tierce\nTexte complet\n')
            target.write_bytes('Licence tierce\nTexte complet\n'.encode('utf-8'))
            self.m.check_output(target, 'Licence tierce\nTexte complet\n')

    def test_inventory_rejects_missing_package_and_empty_text(self):
        packages = [{'id': 'npm:a@1', 'artifact': 'https://example.test/a', 'integrity': 'sha256:a'}]
        with self.assertRaises(ValueError):
            self.m.validate_inventory(packages, [])
        with self.assertRaises(ValueError):
            self.m.validate_inventory(packages, [{'id': 'npm:a@1', 'notices': []}])

    def test_authors_alone_are_not_a_license(self):
        row = {'id': 'cargo:example@1', 'artifact': 'https://example.test/a', 'integrity': 'sha256:a'}
        with self.assertRaises(ValueError):
            self.m.validate_inventory([row], [{**row, 'notices': [{'path': 'AUTHORS', 'text': 'Authors list'}]}])

    def assert_invalid_notice(self, path, text):
        row = {'id': 'cargo:example@1', 'artifact': 'https://example.test/a', 'integrity': 'sha256:a'}
        with self.assertRaises(ValueError):
            self.m.validate_inventory([row], [{**row, 'notices': [{'path': path, 'text': text}]}])

    def test_link_alone_is_not_a_license(self):
        self.assert_invalid_notice('COPYING', 'Copyright 2026 Example. See https://opensource.org/licenses/MIT')

    def test_todo_is_not_a_license(self):
        self.assert_invalid_notice('LICENSE', 'TODO')

    def test_todo_is_rejected_even_alongside_full_terms(self):
        text = (self.m.ROOT / 'licenses/supplements/MIT.txt').read_text()
        self.assert_invalid_notice('LICENSE', 'TODO\n' + text)

    def test_copyright_alone_is_not_a_license(self):
        self.assert_invalid_notice('copyright', 'Copyright 2026 Example Authors')

    def test_generic_attribution_blocks_release(self):
        text = next(n['text'] for r in json.loads((self.m.ROOT / self.m.INVENTORY).read_text())['packages']
                    for n in r['notices'] if 'Permission is hereby granted, free of charge' in n['text'])
        self.assert_invalid_notice('LICENSE', 'Copyright <year> <copyright holders>\n' + text)

    def test_unresolved_attribution_is_provisional_and_blocks_release(self):
        row = deepcopy(json.loads((self.m.ROOT / self.m.INVENTORY).read_text())['packages'][0])
        row['attribution_missing'] = True
        self.assertIn('PROVISOIRE', self.m.render([row], 'digest').splitlines()[0])
        with self.assertRaises(ValueError):
            self.m.validate_inventory([row], [row])

    def test_siphasher_and_rsa_have_full_terms_and_original_attributions(self):
        rows = {r['id']: r for r in json.loads((self.m.ROOT / self.m.INVENTORY).read_text())['packages']}
        for key in ['cargo:siphasher@0.3.11', 'cargo:siphasher@1.0.1', 'python:rsa@4.9.1']:
            with self.subTest(key=key):
                text = '\n'.join(n['text'] for n in rows[key]['notices'])
                self.assertIn('TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION', text)
                self.assertIn('Limitation of Liability', text)
                if key.startswith('cargo:'):
                    self.assertIn('Permission is hereby granted, free of charge', text)
                    self.assertIn('Frank Denis', text)
                    self.assertIn('The Rust Project Developers', text)
                else:
                    self.assertIn('Sybren A. Stüvel', text)

    def test_authors_with_full_mit_terms_are_accepted(self):
        text = (self.m.ROOT / 'licenses/supplements/MIT.txt').read_text()
        row = {'id': 'cargo:example@1', 'artifact': 'a', 'integrity': 'sha256:a',
               'notices': [{'path': 'AUTHORS', 'text': 'Copyright 2026 Example\n' + text}]}
        self.m.validate_inventory([row], [row])

    def test_normative_appendix_is_not_a_component_attribution(self):
        text = (self.m.ROOT / 'licenses/supplements/Apache-2.0.txt').read_text()
        self.assertFalse(self.m.generic_attribution(text))

    def test_generic_after_a_full_license_is_not_hidden_by_its_appendix(self):
        text = (self.m.ROOT / 'licenses/supplements/Apache-2.0.txt').read_text()
        self.assertTrue(self.m.generic_attribution(text + '\nMIT License\nCopyright <year> <copyright holders>'))

    def test_apache_appendix_does_not_exempt_another_component(self):
        apache = (self.m.ROOT / 'licenses/supplements/Apache-2.0.txt').read_text()
        for year in ['[yyyy]', '2026']:
            with self.subTest(year=year):
                self.assert_invalid_notice('LICENSE', apache +
                                           '\nAUTRE COMPOSANT\nCopyright ' + year + ' [name of copyright owner]')

    def test_rtf_apache_example_is_scoped_to_its_normative_paragraph(self):
        apache = (self.m.ROOT / 'licenses/supplements/Apache-2.0.txt').read_text()
        rtf = apache.replace('\n', '\\par\n').replace('Copyright [yyyy]', '\\pard\\li180 Copyright [yyyy]')
        self.assertFalse(self.m.generic_attribution(rtf))
        for year in ['[yyyy]', '2026']:
            with self.subTest(year=year):
                self.assertTrue(self.m.generic_attribution(rtf +
                                '\nAUTRE COMPOSANT\nCopyright ' + year + ' [name of copyright owner]'))

    def test_each_declared_license_requires_full_terms(self):
        mit = (self.m.ROOT / 'licenses/supplements/MIT.txt').read_text()
        for expression in ['MIT OR Apache-2.0', 'MIT/Apache-2.0', 'MIT AND Apache-2.0']:
            row = {'id': 'cargo:example@1', 'artifact': 'a', 'integrity': 'sha256:a',
                   'license': expression, 'notices': [
                       {'path': 'LICENSE-MIT', 'text': mit},
                       {'path': 'LICENSE-APACHE', 'text': 'Copyright 2026 Example. Licensed under the Apache License, Version 2.0; https://www.apache.org/licenses/LICENSE-2.0'}]}
            with self.subTest(expression=expression), self.assertRaisesRegex(ValueError, 'Apache-2.0'):
                self.m.validate_inventory([row], [row])

    def test_named_unknown_or_clear_bsd_cannot_be_hidden_by_mit(self):
        mit = (self.m.ROOT / 'licenses/supplements/MIT.txt').read_text()
        for name in ['LicenseRef-Unknown', 'BSD-3-Clause-Clear']:
            row = {'id': 'cargo:example@1', 'artifact': 'a', 'integrity': 'sha256:a',
                   'license': 'MIT OR ' + name, 'notices': [{'path': 'LICENSE', 'text': mit}]}
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, name):
                self.m.validate_inventory([row], [row])

    def test_unknown_license_classifier_is_not_hidden_by_a_known_one(self):
        row = {'id': 'python:example@1', 'artifact': 'a', 'integrity': 'sha256:a',
               'license': 'License :: OSI Approved :: MIT License; License :: Other :: Unknown',
               'notices': [{'path': 'LICENSE', 'text': (self.m.ROOT / 'licenses/supplements/MIT.txt').read_text()}]}
        with self.assertRaisesRegex(ValueError, 'Unknown'):
            self.m.validate_inventory([row], [row])

    def verbatim_fixture(self):
        text = ('Copyright 2026 Named Author\n' +
                (self.m.ROOT / 'licenses/supplements/MIT.txt').read_text().strip() +
                '\nCopyright <year> <copyright holders>')
        row = {'id': 'npm:example@1', 'artifact': 'https://example.test/a.tgz',
               'integrity': 'sha256:' + 'a' * 64, 'license': 'MIT',
               'notices': [{'path': 'package/LICENSE', 'text': text}]}
        proof = {'status': 'upstream-verbatim', 'package': row['id'],
                 'archive': row['artifact'], 'archive_integrity': row['integrity'],
                 'archive_sha256': 'a' * 64, 'path': 'package/LICENSE',
                 'member_sha256': self.m.digest(text.encode()),
                 'notice_sha256': self.m.digest(text.encode()),
                 'lines': [{'archive_line': len(text.splitlines()),
                            'notice_line': len(text.splitlines()),
                            'text': text.splitlines()[-1]}]}
        return row, proof

    def test_upstream_placeholder_without_proof_is_rejected(self):
        row, _ = self.verbatim_fixture()
        with self.assertRaises(ValueError):
            self.m.validate_inventory([row], [row])

    def test_upstream_placeholder_exact_proof_is_accepted(self):
        row, proof = self.verbatim_fixture()
        self.m.validate_inventory([row], [row], attribution_sources=[proof])
        self.assertNotIn('PROVISOIRE', self.m.render([row], 'hash', attribution_sources=[proof]))
        self.assertIn('texte amont reproduit tel quel', self.m.render([row], 'hash', attribution_sources=[proof]))

    def test_upstream_placeholder_mismatched_proof_is_rejected(self):
        row, proof = self.verbatim_fixture()
        for field, value in [('notice_sha256', '0' * 64), ('archive_integrity', 'sha256:' + 'b' * 64),
                             ('path', 'other/LICENSE'), ('package', 'npm:another@1'),
                             ('lines', [{'archive_line': 1, 'notice_line': 1, 'text': 'wrong'}])]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.m.validate_inventory([row], [row], attribution_sources=[{**proof, field: value}])

    def test_proof_member_bytes_and_archive_hash_must_match(self):
        row, proof = self.verbatim_fixture()
        for field in ['member_sha256', 'archive_sha256']:
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.m.validate_inventory([row], [row], attribution_sources=[{**proof, field: 'b' * 64}])

    def test_upstream_proof_cannot_exempt_a_shared_supplement_or_new_placeholder(self):
        row, proof = self.verbatim_fixture()
        row['notices'].append({'path': 'licenses/supplements/local.txt',
                               'text': 'Copyright <year> <copyright holders>'})
        with self.assertRaises(ValueError):
            self.m.validate_inventory([row], [row], attribution_sources=[proof])

    def test_other_normative_examples_do_not_hide_component_placeholders(self):
        gnu = (self.m.ROOT / 'licenses/supplements/GPL-3.0.txt').read_text()
        rows = json.loads((self.m.ROOT / self.m.INVENTORY).read_text())['packages']
        freetype = next(n['text'] for r in rows for n in r['notices']
                        if 'Please replace <year> with the value from the FreeType version' in n['text'])
        for text, extra in [(gnu, 'Copyright (C) <year> <name of author>'),
                            (freetype, 'copyright © <year> The FreeType')]:
            with self.subTest(extra=extra):
                self.assertFalse(self.m.generic_attribution(text))
                self.assertTrue(self.m.generic_attribution(text + '\nAUTRE COMPOSANT\n' + extra))

    def test_local_supplement_requires_its_exact_hash(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'MIT.txt').write_text('modified')
            override = {'notices': [{'local_path': 'MIT.txt', 'integrity': 'sha256:incorrect'}]}
            with self.assertRaises(ValueError):
                self.m.override_notices(override, root)

    def test_json_supplement_preserves_upstream_spaces(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            raw = json.dumps({'text': 'Upstream  \nlicense\n'}).encode()
            (root / 'source.json').write_bytes(raw)
            override = {'notices': [{'local_path': 'source.json', 'json_text': True,
                                     'integrity': 'sha256:' + self.m.digest(raw)}]}
            self.assertEqual(self.m.override_notices(override, root),
                             [{'path': 'source.json', 'text': 'Upstream  \nlicense'}])

    def test_refresh_applies_supplements_even_to_a_valid_cached_notice(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'licenses').mkdir()
            terms = (self.m.ROOT / 'licenses/supplements/MIT.txt').read_text()
            (root / 'MIT.txt').write_text(terms)
            row = {'id': 'cargo:example@1', 'artifact': 'a', 'integrity': 'sha256:a',
                   'license': 'MIT', 'notices': [{'path': 'COPYING', 'text': terms}]}
            override = {'license': 'MIT', 'reason': 'test', 'attribution_missing': True,
                        'retain_archive_notices': True,
                        'notices': [{'local_path': 'MIT.txt', 'integrity': 'sha256:' + self.m.digest(terms.encode())}]}
            (root / 'licenses/overrides.json').write_text(json.dumps({row['id']: override}))
            with patch.object(self.m, 'locked_packages', return_value=[row]), \
                    patch.object(self.m, 'lock_digest', return_value='test'), \
                    patch.object(self.m, 'collect', return_value=row), \
                    patch.object(self.m, 'fetch', side_effect=AssertionError('network forbidden')):
                with patch('sys.argv', ['licenses', 'refresh', '--root', str(root), '--cache', str(root / 'cache')]):
                    self.m.main()
                output = (root / 'THIRD_PARTY_LICENSES').read_text()
                self.assertTrue(output.startswith('PROVISOIRE'))
                saved = json.loads((root / 'licenses/inventory.json').read_text())['packages'][0]
                self.assertEqual({n['path'] for n in saved['notices']}, {'COPYING', 'MIT.txt'})
                with patch('sys.argv', ['licenses', 'check', '--root', str(root)]), \
                        self.assertRaisesRegex(ValueError, 'PROVISOIRE'):
                    self.m.main()

    def test_unknown_python_source_is_not_silently_omitted(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for file in ['package-lock.json', 'src/frontend/package-lock.json']:
                path = root / file
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps({'packages': {}}))
            cargo = root / 'src/frontend/src-tauri/Cargo.lock'
            cargo.parent.mkdir(parents=True)
            cargo.write_text('package = []')
            (root / 'uv.lock').write_text(
                '[[package]]\nname = "thirdparty"\nversion = "1"\n'
                '[package.source]\ngit = "https://example.invalid/library"\n'
            )
            (root / 'licenses').mkdir()
            for name in ['native-components.lock.json', 'runtime-wheels.lock.json']:
                (root / 'licenses' / name).write_text('[]')
            with self.assertRaises(ValueError):
                self.m.locked_packages(root)

    def test_lock_digest_changes_even_if_versions_do_not(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'uv.lock').write_text('version = 1')
            first = self.m.lock_digest(root, ['uv.lock'])
            (root / 'uv.lock').write_text('version = 2')
            self.assertNotEqual(first, self.m.lock_digest(root, ['uv.lock']))

    def test_deterministic_text_deduplication(self):
        rows = [{'id': 'npm:b@1', 'license': 'MIT', 'notices': [{'path': 'LICENSE', 'text': 'same'}]},
                {'id': 'npm:a@1', 'license': 'GPL-3.0', 'notices': [{'path': 'COPYING', 'text': 'same'}]}]
        self.assertEqual(self.m.render(rows, 'digest'), self.m.render(list(reversed(rows)), 'digest'))
        self.assertEqual(self.m.render(rows, 'digest').count('\nsame\n'), 1)
        self.assertIn('GPL', self.m.render(rows, 'digest'))


if __name__ == '__main__':
    unittest.main()
