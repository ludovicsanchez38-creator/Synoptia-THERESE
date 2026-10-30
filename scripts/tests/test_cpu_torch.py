import importlib.util
import unittest
from pathlib import Path


class CpuWheelTests(unittest.TestCase):
    def test_only_the_locked_cpu_wheel_is_selected(self):
        spec = importlib.util.spec_from_file_location('cpu', Path(__file__).resolve().parents[1] / 'install_cpu_torch.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        rows = [{'id': 'python:torch@2.9.1/wheel-cpu-linux', 'artifact': 'https://download.pytorch.org/linux.whl', 'integrity': 'sha256:abc'},
                {'id': 'python:torch@2.9.1/wheel-cpu-windows', 'artifact': 'https://download.pytorch.org/windows.whl', 'integrity': 'sha256:def'}]
        self.assertEqual(module.wheel_url(rows, 'linux', '2.9.1'), 'https://download.pytorch.org/linux.whl#sha256=abc')
        self.assertEqual(module.wheel_url(rows, 'win32', '2.9.1'), 'https://download.pytorch.org/windows.whl#sha256=def')
        with self.assertRaises(ValueError):
            module.wheel_url(rows, 'linux', '2.10.0')
