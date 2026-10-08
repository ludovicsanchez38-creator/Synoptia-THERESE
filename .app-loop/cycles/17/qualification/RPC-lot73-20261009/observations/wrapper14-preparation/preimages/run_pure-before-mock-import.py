"""Runner pur borné par cas finis, sinks directs, aucun constructeur/runtime."""
from __future__ import annotations
import contextlib
from datetime import datetime, UTC
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
PATHS = ['build_fresh_wrapper.py', 'tests/test_wrapper14_static.py', 'run_pure.py',
         'preimages/build_fresh_wrapper-13.py', 'profile/chrome.sb',
         'preimages/runtime_session-before-env.py', 'preview/runtime_session-after-env.py',
         'diffs/builder-forward.diff', 'diffs/builder-inverse.diff', 'diffs/g1-forward.diff', 'diffs/g1-inverse.diff']
ORIGINS = [Path('/private/tmp/therese-c17-wrapper13-dirhelper-P5WQpQ/build_fresh_wrapper.py'),
           Path('/private/tmp/therese-c17-wrapper13-dirhelper-P5WQpQ/profile/chrome.sb'),
           Path('/private/tmp/therese-c17-wrapper13-dirhelper-P5WQpQ/PLAN-INDEX.json'),
           Path('/private/tmp/therese-c17-rpc-integration-UctqC8UG/g1-26/runtime_session.py'),
           Path('/private/tmp/therese-c17-rpc-integration-UctqC8UG/g1-26/runtime_launch_gate.py'),
           Path('/private/tmp/therese-c17-rpc-integration-UctqC8UG/coordinator/run_wrapper_canary.py'),
           Path('/private/tmp/therese-c17-fresh-wrapper-builder-v8-pB5tPP/preview/chrome_contract-qa.py')]

def ref(path):
    raw = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def main():
    attempts = []
    def deny(name):
        def refused(*args, **kwargs):
            attempts.append(name)
            raise RuntimeError('Forbidden pure-run operation: ' + name)
        return refused
    for owner, names in ((subprocess, ('Popen', 'run')), (socket, ('socket',)), (os, ('system', 'execve', 'kill'))):
        for name in names:
            setattr(owner, name, deny(name))
    paths = [HERE / name for name in PATHS] + ORIGINS
    before = [ref(path) for path in paths]
    start = datetime.now(UTC).isoformat()
    (HERE / 'proofs').mkdir(exist_ok=True)
    out = Path(tempfile.mkdtemp(prefix='pure-', dir=HERE / 'proofs'))
    with (out / 'stdout.log').open('x') as stdout, (out / 'stderr.log').open('x') as stderr:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            suite = unittest.defaultTestLoader.discover(str(HERE / 'tests'))
            def ids(value):
                return sum((ids(test) if isinstance(test, unittest.TestSuite) else [test.id()] for test in value), [])
            names = ids(suite)
            result = unittest.TextTestRunner(stream=stderr, verbosity=2).run(suite)
        stdout.flush(); stderr.flush(); os.fsync(stdout.fileno()); os.fsync(stderr.fileno())
    after = [ref(path) for path in paths]
    forbidden_imports = sorted(name for name in sys.modules if name == 'runtime_session' or name == 'app' or name.startswith('app.'))
    success = result.wasSuccessful() and before == after and not attempts and not forbidden_imports
    receipt = {'schema': 'c17-wrapper14-chromium-tmp-pure-tests-v1', 'actor': '/root/shared4_execution',
               'started_at': start, 'completed_at': datetime.now(UTC).isoformat(),
               'tests': result.testsRun, 'test_ids': names, 'failures': len(result.failures), 'errors': len(result.errors),
               'skipped': len(result.skipped), 'passed': success, 'exit_code': 0 if success else 1,
               'source_before': before, 'source_after': after, 'sources_unchanged': before == after,
               'stdout_ref': ref(out / 'stdout.log'), 'stderr_ref': ref(out / 'stderr.log'),
               'forbidden_attempts': attempts, 'forbidden_imports': forbidden_imports,
               'fixture_identity': 'explicit_synthetic_Paths_and_VM_and_emitter_doubles',
               'G1_imported': False, 'constructor_invoked': False, 'native_executed': False,
               'profile_compiled': False, 'FULL': False, 'release': False}
    (out / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'receipt_ref': ref(out / 'receipt.json'), 'tests': result.testsRun, 'passed': success}, sort_keys=True))
    return 0 if success else 1

if __name__ == '__main__':
    raise SystemExit(main())
