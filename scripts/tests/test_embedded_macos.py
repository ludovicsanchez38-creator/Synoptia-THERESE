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
            toc = {'../../library.so': (0, 'b'), 'image.png': (0, 'x'), 'lib.bin': (0, 'b'), 'data-library.so': (0, 'x')}
            def extract(self, name):
                return b'PNG image' if name == 'image.png' else bytes.fromhex('cffaedfe') + b'library'
        calls = []
        def command(args):
            calls.append(args)
            return 'flags=runtime com.apple.security.cs.disable-library-validation'
        with tempfile.TemporaryDirectory() as td:
            directory = Path(td) / 'extracted'
            count = self.m.verify_embedded(Path('backend'), directory, reader=lambda _: Archive(), command=command)
            self.assertEqual(count, 3)
            self.assertEqual({p.name for p in directory.iterdir()}, {'binary-0', 'binary-1', 'binary-2'})
            self.assertEqual(sum('--verify' in c for c in calls), 4)

    @staticmethod
    def _macho(filetype):
        # En-tête Mach-O 64 bits petit-boutiste : magic, cputype, cpusubtype, filetype.
        import struct
        return bytes.fromhex('cffaedfe') + struct.pack('<iiI', 0x0100000C, 0, filetype) + b'\0' * 16

    def _verify(self, toc, details_for):
        class Archive:
            pass
        archive = Archive()
        archive.toc = {name: (0, 'b') for name in toc}
        archive.extract = lambda name: toc[name]
        def command(args):
            if '--display' in args:
                return details_for(args[-1])
            return ''
        with tempfile.TemporaryDirectory() as td:
            return self.m.verify_embedded(Path('backend'), Path(td), reader=lambda _: archive, command=command)

    def test_library_needs_hardened_runtime_but_cannot_carry_entitlements(self):
        # codesign n'inscrit les entitlements que dans un exécutable (MH_EXECUTE) :
        # mesuré sur un vrai onefile, 310 bibliothèques sur 313 Mach-O en sont dépourvues.
        toc = {'lib/libtorch.dylib': self._macho(6), 'mod.so': self._macho(8)}
        count = self._verify(toc, lambda path: 'flags=0x10002(adhoc,runtime)'
                             if not path.endswith('backend') else
                             'flags=runtime com.apple.security.cs.disable-library-validation')
        self.assertEqual(count, 2)

    def test_refusals_name_every_offending_macho(self):
        toc = {'lib/sans-runtime.dylib': self._macho(6), 'bin/outil': self._macho(2),
               'lib/correcte.dylib': self._macho(6)}
        def details(path):
            if path.endswith('backend'):
                return 'flags=runtime com.apple.security.cs.disable-library-validation'
            return '' if path.endswith('binary-0') else 'flags=0x10002(adhoc,runtime)'
        with self.assertRaises(RuntimeError) as caught:
            self._verify(toc, details)
        message = str(caught.exception)
        self.assertIn('lib/sans-runtime.dylib', message)
        self.assertIn('bin/outil', message)
        self.assertNotIn('lib/correcte.dylib', message)

    def test_outer_executable_must_carry_engine_entitlements(self):
        toc = {'lib/libtorch.dylib': self._macho(6)}
        with self.assertRaisesRegex(RuntimeError, 'moteur'):
            self._verify(toc, lambda path: 'flags=0x10002(adhoc,runtime)')

    def test_empty_archive_fails_instead_of_claiming_success(self):
        class Archive:
            toc = {}
        with tempfile.TemporaryDirectory() as td, self.assertRaises(RuntimeError):
            self.m.verify_embedded(Path('backend'), Path(td), reader=lambda _: Archive(), command=lambda _: '')
