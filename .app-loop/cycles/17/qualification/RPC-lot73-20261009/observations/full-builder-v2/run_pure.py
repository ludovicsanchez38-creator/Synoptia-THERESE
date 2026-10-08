"""Runner stdlib pur ; sinks directs et sources avant/après, pas de sous-processus."""
from __future__ import annotations
import argparse
import contextlib
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent

def ref(path):
    raw=path.read_bytes(); return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}

def blocked(*args,**kwargs):
    raise AssertionError('Processus/réseau interdits dans ce runner pur')

def names(suite):
    return [name for test in suite for name in (names(test) if isinstance(test,unittest.TestSuite) else [test.id()])]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--actor',required=True)
    args=parser.parse_args()
    if re.fullmatch(r'/root(?:/[a-z][a-z0-9_]*)?',args.actor) is None:
        parser.error('acteur de relecture canonique explicite requis')
    origins=json.loads((HERE/'assets.json').read_text())['assets']
    paths={Path(item['path']) for item in origins.values()} | {HERE/'assets.json',HERE/'build_full_round.py',HERE/'run_pure.py',HERE/'tests/test_builder.py',HERE/'fixtures/chrome-candidate.sb'}
    before={str(path):ref(path) for path in sorted(paths)}
    out=Path(tempfile.mkdtemp(prefix='pure-',dir=HERE/'proofs')); os.chmod(out,0o700)
    started=datetime.now(UTC).isoformat(); clock=time.monotonic()
    with (out/'stdout.log').open('x',encoding='utf-8') as stdout, (out/'stderr.log').open('x',encoding='utf-8') as stderr:
        with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr),patch.object(subprocess,'Popen',blocked),patch.object(socket,'socket',blocked),patch.object(os,'system',blocked):
            suite=unittest.defaultTestLoader.discover(str(HERE/'tests'),pattern='test_builder.py')
            test_names=names(suite)
            result=unittest.TextTestRunner(stream=stderr,verbosity=2).run(suite)
        stdout.flush(); stderr.flush(); os.fsync(stdout.fileno()); os.fsync(stderr.fileno())
    after={str(path):ref(path) for path in sorted(paths)}
    value={'schema':'c17-full-physical-builder-pure-receipt-v1','actor':args.actor,
        'actor_provenance':'explicit_cli_declaration_only_not_runtime_authority',
        'started_at':started,'completed_at':datetime.now(UTC).isoformat(),'elapsed_seconds':time.monotonic()-clock,
        'tests_run':result.testsRun,'test_names':test_names,
        'failures':[(test.id(),error) for test,error in result.failures],
        'errors':[(test.id(),error) for test,error in result.errors],
        'skipped':[(test.id(),reason) for test,reason in result.skipped],
        'passed':result.wasSuccessful() and before==after,'sources_before':before,'sources_after':after,
        'stdout':ref(out/'stdout.log'),'stderr':ref(out/'stderr.log'),
        'fixture_scope':'synthetic Git/source/Chrome identity only; actual definitions rendered in memory',
        'G1_imported':False,'product_imported':False,'process_or_network_calls':0,
        'actual_round_allocated':False,'runtime_admitted':False,'FULL':False,'release':False}
    with (out/'receipt.json').open('x',encoding='utf-8') as stream:
        stream.write(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n'); stream.flush(); os.fsync(stream.fileno())
    print(json.dumps({'receipt':ref(out/'receipt.json'),'tests':result.testsRun,'passed':value['passed']}))
    return 0 if value['passed'] else 1

if __name__=='__main__': raise SystemExit(main())
