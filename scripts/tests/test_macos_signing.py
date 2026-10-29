"""Ordre et refus de signature testés sur Linux avec un exécuteur simulé."""
import importlib.util
import tempfile
import unittest
from pathlib import Path


class SigningTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('signing', Path(__file__).resolve().parents[1] / 'sign_macos.py')
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)

    def test_partial_secrets_fall_back_to_adhoc(self):
        self.assertFalse(self.m.apple_ready({}))
        self.assertFalse(self.m.apple_ready({'APPLE_CERTIFICATE': 'test'}))
        self.assertTrue(self.m.apple_ready(dict.fromkeys(self.m.APPLE_SECRETS, 'test')))

    def test_sign_inside_out_then_verify_each_binary(self):
        with tempfile.TemporaryDirectory() as td:
            app = Path(td) / 'Example.app'
            lib = app / 'Contents/Resources/python/lib.so'
            binary = app / 'Contents/MacOS/example'
            for p in [lib, binary]:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(bytes.fromhex('cffaedfe') + b'test')
            (lib.parent / 'alias.so').symlink_to(lib.name)
            calls = []
            self.m.sign_tree(app, '-', Path('entitlements.plist'), run=lambda args: calls.append(args))
            signed = [c[-1] for c in calls if '--sign' in c]
            self.assertEqual(signed, [str(lib), str(binary), str(app)])
            self.assertEqual(sum('--verify' in c for c in calls), 3)
            self.assertTrue(all('--options' in c and 'runtime' in c and '--entitlements' in c for c in calls if '--sign' in c))
            self.assertFalse(any('--deep' in c for c in calls if '--sign' in c))

    def test_rejected_notarization_never_staples(self):
        calls = []
        def run(args):
            calls.append(args)
            return '{"status":"Invalid"}'
        with self.assertRaises(RuntimeError):
            self.m.notarize(Path('app.dmg'), run=run)
        self.assertFalse(any('stapler' in c for c in calls))

    def test_acceptance_staples_and_validates(self):
        calls = []
        def run(args):
            calls.append(args)
            return '{"status":"Accepted"}'
        self.m.notarize(Path('app.dmg'), run=run)
        self.assertTrue(any('staple' in c for c in calls))
        self.assertTrue(any('validate' in c for c in calls))


if __name__ == '__main__':
    unittest.main()
