"""Contrôles purs du seul lookup dirhelper Chrome WRAPPER13.

Le constructeur est importé pour ses prédicats, jamais exécuté ; G1 n'est pas importé.
"""
from __future__ import annotations

import ast
import difflib
import hashlib
import importlib.util
from pathlib import Path
import unittest


HERE = Path(__file__).resolve().parents[1]
ROOT = Path('/private/tmp/therese-c17-wrapper-canary-8612f55886284332a3ac6a7bc9615021')
SPEC = importlib.util.spec_from_file_location('wrapper13_builder_static', HERE / 'build_fresh_wrapper.py')
assert SPEC is not None and SPEC.loader is not None
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


class Wrapper13Static(unittest.TestCase):
    def test_profile_only_one_literal_mach_lookup(self):
        old = (HERE / 'preimages/chrome-main12.sb').read_bytes()
        new = (HERE / 'profile/chrome.sb').read_bytes()
        rule = b'(allow mach-lookup (global-name "com.apple.bsd.dirhelper"))\n'
        self.assertEqual(new, old + rule)
        self.assertEqual(new.count(rule), 1)
        self.assertEqual(len(old), 2439)
        self.assertEqual(len(new), 2499)
        self.assertEqual(hashlib.sha256(new).hexdigest(), builder.CHROME_PROFILE['sha256'])
        self.assertEqual(new, Path(builder.CHROME_GETCONF_PROFILE['path']).read_bytes())

    def test_real_chrome_derivation_accepts_exact_profile(self):
        _, candidate = builder.checked_chrome_successor(builder.CHROME_PROFILE)
        self.assertEqual(candidate.encode(), (HERE / 'profile/chrome.sb').read_bytes())

    def test_profile_broadening_or_other_class_refused(self):
        original = builder.checked
        raw = (HERE / 'profile/chrome.sb').read_bytes()
        try:
            for mutant in (
                raw.replace(b'(global-name "com.apple.bsd.dirhelper")', b'(global-name "*")'),
                raw.replace(b'(global-name "com.apple.bsd.dirhelper")', b'(global-name "com.apple.SystemConfiguration.configd")'),
                raw + b'(allow file-read-data (subpath (param "AUXILIARY_PARENT")))\n',
                raw.replace(b'localhost:17594', b'localhost:17595'),
            ):
                builder.checked = lambda ref, mutant=mutant: mutant if ref == builder.CHROME_PROFILE else original(ref)
                with self.assertRaisesRegex(ValueError, 'dirhelper mesuré'):
                    builder.checked_chrome_successor(builder.CHROME_PROFILE)
        finally:
            builder.checked = original

    def test_wrong_main12_or_getconf_origin_refused(self):
        original = builder.checked
        try:
            builder.checked = lambda ref: (b'changed\n' if ref == builder.CHROME_MAIN12_PROFILE else original(ref))
            with self.assertRaisesRegex(ValueError, 'Préimage MAIN12'):
                builder.checked_chrome_successor(builder.CHROME_PROFILE)
            builder.checked = lambda ref: (b'changed\n' if ref == builder.CHROME_GETCONF_PROFILE else original(ref))
            with self.assertRaisesRegex(ValueError, 'dirhelper mesuré'):
                builder.checked_chrome_successor(builder.CHROME_PROFILE)
        finally:
            builder.checked = original

    def test_g1_parameter_is_chrome_only_and_reversible(self):
        frozen = (builder.PREP / 'g1-26/runtime_session.py').read_text()
        qa = builder.g1_chrome_executable_guard(builder.g1_chrome_copy_delta(frozen))
        derived = builder.g1_auxiliary_parent_delta(qa)
        inserted = (
            '        auxiliary_parent = root / "auxiliary"\n'
            '        require(auxiliary_parent.resolve(strict=True) == auxiliary_parent\n'
            '                and child_path(root, auxiliary_parent) == auxiliary_parent,\n'
            '                "Parent auxiliaire Chrome hors QA exact")\n'
            '        extra.extend(["-D", "AUXILIARY_PARENT=" + str(auxiliary_parent)])\n'
        )
        self.assertEqual(derived.count(inserted), 1)
        self.assertEqual(derived.replace(inserted, '', 1), qa)
        tree = ast.parse(derived)
        sandbox = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'sandbox')
        branch = next(n for n in sandbox.body if isinstance(n, ast.If)
                      and ast.unparse(n.test) == "mode == 'chrome'")
        self.assertIn('AUXILIARY_PARENT=', ast.unparse(branch.body))
        self.assertNotIn('AUXILIARY_PARENT=', ast.unparse(branch.orelse))

    def test_g1_changed_anchor_refused(self):
        frozen = (builder.PREP / 'g1-26/runtime_session.py').read_text()
        qa = builder.g1_chrome_executable_guard(builder.g1_chrome_copy_delta(frozen))
        with self.assertRaisesRegex(ValueError, 'Ancre paramètres Chrome'):
            builder.g1_auxiliary_parent_delta(qa.replace('key + "=" + value', 'key + "=" + str(value)'))

    def test_historical_three_routes_are_archival_not_native(self):
        pins, _, observations = builder.validate_indexes()
        self.assertEqual(len(observations), 3)
        self.assertEqual({(o['origin'], o['pointer']) for o in observations},
                         {(str(builder.CHROME_ROOTDOMAIN_INDEX), '/origin_refs/4'),
                          *{(str(path), '/source_refs/267') for path in builder.HISTORICAL_REPLAYS}})
        self.assertNotIn(builder.HISTORICAL_IPS['path'], pins)
        self.assertEqual(pins[str(builder.ARCHIVED_IPS)]['sha256'], builder.HISTORICAL_IPS['sha256'])
        red = next(o for o in observations if o['kind'] == 'pure_replay_red')
        self.assertIs(red['passed'], False)
        self.assertEqual(red['errors'], 3)
        self.assertTrue(all(o['old_path_absent'] and not o['runtime_qualification']
                            and not o['close6_receipt_provenance_claimed'] for o in observations))

    def test_historical_wrong_pointer_or_ref_refused(self):
        origin = builder.CHROME_ROOTDOMAIN_INDEX
        with self.assertRaises(ValueError):
            builder.historical_ips_archive(origin, '/origin_refs/3', builder.HISTORICAL_IPS)
        wrong = dict(builder.HISTORICAL_IPS, sha256='0' * 64)
        with self.assertRaises(ValueError):
            builder.historical_ips_archive(origin, '/origin_refs/4', wrong)
        with self.assertRaises(ValueError):
            builder.historical_ips_archive(HERE / 'INDEX.json', '/origin_refs/4', builder.HISTORICAL_IPS)

    def test_future_root_is_one_exact_closed_path_without_allocation(self):
        self.assertFalse(ROOT.exists())
        self.assertEqual(builder.future_root(ROOT), ROOT)
        with self.assertRaises(ValueError):
            builder.future_root(Path(str(ROOT).replace('wrapper-canary-', 'wrapper12-canary-')))
        with self.assertRaises(ValueError):
            builder.future_root(Path('/private/tmp/therese-c17-wrapper-canary-9818b6b4163e451892dbd3956e1bb492'))

    def test_forward_inverse_diffs_exact(self):
        for prefix, old, new in (
            ('builder', HERE / 'preimages/build_fresh_wrapper-main12.py', HERE / 'build_fresh_wrapper.py'),
            ('profile', HERE / 'preimages/chrome-main12.sb', HERE / 'profile/chrome.sb'),
        ):
            for suffix, before, after in (('forward', old, new), ('inverse', new, old)):
                expected = ''.join(difflib.unified_diff(
                    before.read_text().splitlines(True), after.read_text().splitlines(True),
                    fromfile=str(before), tofile=str(after)))
                actual_lines = (HERE / 'diffs' / f'{prefix}-{suffix}.diff').read_text().splitlines(True)
                expected_lines = expected.splitlines(True)
                self.assertEqual(actual_lines[0].rstrip('\n').split('\t')[0], expected_lines[0].rstrip('\n'))
                self.assertEqual(actual_lines[1].rstrip('\n').split('\t')[0], expected_lines[1].rstrip('\n'))
                self.assertEqual(actual_lines[2:], expected_lines[2:])


if __name__ == '__main__':
    unittest.main(verbosity=2)
