import importlib.util
import tempfile
import unittest
from pathlib import Path


class PackagedLicensesTests(unittest.TestCase):
    def test_absent_or_stale_installed_notice_is_rejected(self):
        spec = importlib.util.spec_from_file_location('packaged', Path(__file__).resolve().parents[1] / 'verify_packaged_licenses.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with self.assertRaises(ValueError):
                module.check_directory(root, b'notice')
            notice = root / 'THIRD_PARTY_LICENSES'
            notice.write_bytes(b'stale')
            with self.assertRaises(ValueError):
                module.check_directory(root, b'notice')
            notice.write_bytes(b'notice')
            self.assertEqual(module.check_directory(root, b'notice'), 1)
