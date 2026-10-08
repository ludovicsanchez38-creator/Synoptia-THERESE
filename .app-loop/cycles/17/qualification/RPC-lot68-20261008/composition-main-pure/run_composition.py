from __future__ import annotations

import ast
import hashlib
import io
import json
import os
from pathlib import Path
import runpy
import sys
import typing
import unittest

ROOT = Path('/private/tmp/therese-c17-ab-git-listener-4VBlvfDx')
OUT = Path(__file__).resolve().parent
STDLIB = Path(sys.base_prefix).resolve()
INDEX = ROOT / 'INDEX.json'
expected_index = '9b18f54b717430c01f03a4a1c884913f6fe1e41be040b3e910b607de1ce6b62a'


def guard(event: str, args: tuple) -> None:
    if event.startswith(('subprocess.', 'socket.', 'ctypes.', 'os.exec', 'os.spawn')) or event in {
        'os.fork', 'os.forkpty', 'os.posix_spawn', 'os.kill', 'os.killpg', 'os.system',
        'os.remove', 'os.rmdir', 'os.rename', 'os.symlink', 'os.link', 'os.chmod', 'os.chown',
    }:
        raise PermissionError('OS/runtime forbidden: ' + event)
    if event == 'open':
        if not isinstance(args[0], (str, bytes, os.PathLike)):
            raise PermissionError('file descriptor not admitted')
        candidate = Path(os.fsdecode(args[0])).resolve()
        mode = args[1] or ''
        flags = args[2] or 0
        writing = any(x in mode for x in 'wax+') or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
        if writing and not candidate.is_relative_to(OUT):
            raise PermissionError('write outside proof output')
        if not writing and not any(candidate.is_relative_to(base) for base in (ROOT, OUT, STDLIB)):
            raise PermissionError('read outside exact definition and stdlib')


sys.addaudithook(guard)
index_bytes = INDEX.read_bytes()
assert hashlib.sha256(index_bytes).hexdigest() == expected_index
index = json.loads(index_bytes)


def refs(value):
    if isinstance(value, dict):
        if isinstance(value.get('path'), str) and isinstance(value.get('sha256'), str) and isinstance(value.get('bytes'), int):
            yield value
        for child in value.values():
            yield from refs(child)
    elif isinstance(value, list):
        for child in value:
            yield from refs(child)


pins = {}
for ref in refs(index):
    p = Path(ref['path'])
    if not p.is_absolute():
        p = ROOT / p
    if not p.is_relative_to(ROOT):
        continue
    data = p.read_bytes()
    assert len(data) == ref['bytes'] and hashlib.sha256(data).hexdigest() == ref['sha256'], str(p)
    pins[str(p)] = {'sha256': ref['sha256'], 'bytes': ref['bytes']}
test = ROOT / 'tests/test_render_git_listener.py'
test_data = test.read_bytes()
ast.parse(test_data)
namespace = runpy.run_path(str(test), run_name='prepared_test_only')
suite = unittest.defaultTestLoader.loadTestsFromTestCase(namespace['CompositionTests'])
assert suite.countTestCases() == 10
stream = io.StringIO()
result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
for name, ref in pins.items():
    data = Path(name).read_bytes()
    assert len(data) == ref['bytes'] and hashlib.sha256(data).hexdigest() == ref['sha256'], name
assert hashlib.sha256(INDEX.read_bytes()).hexdigest() == expected_index
returned = stream.getvalue()
(OUT / 'unittest-output.log').write_text(returned)
receipt = {
    'schema': 'therese-c17-composition-pure-main-v1',
    'passed': result.wasSuccessful(), 'tests': result.testsRun,
    'errors': len(result.errors), 'failures': len(result.failures),
    'index_sha256': expected_index, 'local_pins_before_after': pins,
    'test_sha256': hashlib.sha256(test_data).hexdigest(),
    'stdout_sha256': hashlib.sha256(returned.encode()).hexdigest(),
    'OS_runtime_forbidden': True, 'definition_only': True,
    'native_admission': False, 'FULL': False, 'rounds': 0, 'release': False,
}
(OUT / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(returned, end='')
print(json.dumps({k: v for k, v in receipt.items() if k != 'local_pins_before_after'}))
raise SystemExit(0 if result.wasSuccessful() else 1)
