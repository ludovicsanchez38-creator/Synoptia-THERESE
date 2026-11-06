"""Le runtime VC++ du moteur Windows vient d'une source officielle épinglée."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))


class WindowsRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import windows_runtime
        cls.m = windows_runtime

    def _visual_studio(self, root, versions=('14.38.33130', '14.44.35208')):
        for version in versions:
            base = root / 'VS/VC/Redist/MSVC' / version / 'x64'
            (base / 'Microsoft.VC143.CRT').mkdir(parents=True)
            (base / 'Microsoft.VC143.OpenMP').mkdir(parents=True)
            (base / 'Microsoft.VC143.CRT/msvcp140.dll').write_bytes(b'MZ')
        (root / 'VS/VC/Redist/MSVC/v143').mkdir(parents=True)  # dossier sans version : ignoré
        vswhere = root / 'vswhere.exe'
        vswhere.write_bytes(b'')
        def run(args, **_):
            self.assertEqual(args[0], str(vswhere))
            return subprocess.CompletedProcess(args, 0, stdout=str(root / 'VS') + '\n')
        return vswhere, run

    def test_redist_dirs_are_the_latest_msvc_crt_and_openmp(self):
        with tempfile.TemporaryDirectory() as tmp:
            vswhere, run = self._visual_studio(Path(tmp))
            dirs = self.m.redist_dirs(vswhere, run=run)
            self.assertEqual([d.name for d in dirs], ['Microsoft.VC143.CRT', 'Microsoft.VC143.OpenMP'])
            self.assertTrue(all('14.44.35208' in str(d) for d in dirs))

    def test_missing_visual_studio_refuses_instead_of_guessing(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, 'Visual Studio'):
                self.m.redist_dirs(Path(tmp) / 'absent.exe')

    def test_top_level_runtime_from_the_path_is_refused(self):
        # Relevé du 06/11/2026 : msvcp140.dll du JDK, msvcp140_1/vcomp140 d'ImageMagick.
        allowed = [Path('C:/Python313'), Path('C:/VS/Redist/Microsoft.VC143.CRT')]
        good = [('vcruntime140.dll', 'C:/Python313/vcruntime140.dll', 'BINARY'),
                ('msvcp140.dll', 'C:/VS/Redist/Microsoft.VC143.CRT/msvcp140.dll', 'BINARY'),
                ('sklearn/.libs/vcomp140.dll', 'C:/venv/sklearn/.libs/vcomp140.dll', 'BINARY'),
                ('python313.dll', 'C:/Python313/python313.dll', 'BINARY')]
        self.m.check_sources(good, allowed)
        for name, source in [('msvcp140.dll', 'C:/jdk/17.0.21-9/x64/bin/msvcp140.dll'),
                             ('VCOMP140.DLL', 'C:/Program Files/ImageMagick-7.1.2-Q16-HDRI/vcomp140.dll'),
                             ('MSVCP140_1.dll', 'C:/Program Files/ImageMagick-7.1.2-Q16-HDRI/msvcp140_1.dll')]:
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, name):
                self.m.check_sources([*good, (name, source, 'BINARY')], allowed)

    def test_backend_spec_prefers_redist_and_checks_sources_on_windows(self):
        spec = (ROOT / 'src/backend/backend.spec').read_text(encoding='utf-8')
        analysis = spec.index('a = Analysis(')
        prefer = spec.index('_windows_runtime.redist_dirs(')
        check = spec.index('_windows_runtime.check_sources(a.binaries')
        self.assertLess(prefer, analysis)
        self.assertLess(analysis, check)
        self.assertLess(check, spec.index('_system_module.record_analysis('))


if __name__ == '__main__':
    unittest.main()
