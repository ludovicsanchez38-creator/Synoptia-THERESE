import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


class EmbeddedTests(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        spec = importlib.util.spec_from_file_location('embedded', Path(__file__).resolve().parents[1] / 'verify_embedded_macos.py')
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)

    def test_each_embedded_macho_is_verified_and_paths_are_contained(self):
        class Archive:
            toc = {'../../library.so': (0, 'b'), 'image.png': (0, 'x'), 'lib.bin': (0, 'b')}
            def extract(self, name):
                return bytes.fromhex('cffaedfe') + b'library'
        calls = []
        def command(args):
            calls.append(args)
            return 'flags=runtime com.apple.security.cs.disable-library-validation'
        with tempfile.TemporaryDirectory() as td:
            directory = Path(td) / 'extracted'
            count = self.m.verify_embedded(Path('backend'), directory, reader=lambda _: Archive(), command=command)
            self.assertEqual(count, 2)
            self.assertEqual({p.name for p in directory.iterdir()}, {'binary-0', 'binary-1'})
            self.assertEqual(sum('--verify' in c for c in calls), 3)

    def test_empty_archive_fails_instead_of_claiming_success(self):
        class Archive:
            toc = {}
        with tempfile.TemporaryDirectory() as td, self.assertRaises(RuntimeError):
            self.m.verify_embedded(Path('backend'), Path(td), reader=lambda _: Archive(), command=lambda _: '')
