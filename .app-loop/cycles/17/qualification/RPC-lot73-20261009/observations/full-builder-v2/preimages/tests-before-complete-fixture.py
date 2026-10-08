"""Tests purs, fixtures SYNTHÉTIQUES, aucune construction de racine A/B.

Les définitions sont rendues réellement en mémoire. Aucun G1/produit n'est
importé ; ni Popen, Git, Node, socket, libproc ou Chrome n'est appelé.
"""
from __future__ import annotations

import ast
from copy import deepcopy
from datetime import UTC, datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pure_full_builder', HERE / 'build_full_round.py')
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


class BuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='therese-c17-direct-source-pure-', dir='/private/tmp')
        cls.base = Path(cls.temp.name)
        cls.qa = cls.base / 'source'; cls.qa.mkdir()
        (cls.qa / '.git').mkdir()
        (cls.qa / 'src/frontend').mkdir(parents=True)
        vite = "import {defineConfig} from 'vite';\nimport react from '@vitejs/plugin-react';\nimport tailwindcss from '@tailwindcss/vite';\nimport {resolve} from 'node:path';\nexport default defineConfig({plugins:[react(),tailwindcss()],resolve:{alias:{'@':resolve(__dirname, 'src')}}});\n"
        (cls.qa / 'src/frontend/vite.config.ts').write_text(vite)
        (cls.qa / 'tests').mkdir(); (cls.qa / 'tests/witness.py').write_text('value = 1\n')
        cls.assets = json.loads((HERE / 'assets.json').read_text())['assets']
        for ref in cls.assets.values(): b.checked(ref)
        tree_parts, rows, modes = [], [], {}
        for relative in ('src/frontend/vite.config.ts', 'tests/witness.py'):
            path = cls.qa / relative; raw = path.read_bytes()
            blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
            tree_parts.append(('100644 blob ' + blob + '\t' + relative).encode() + b'\0')
            rows.append(dict(b.planned_ref(path, raw), git_blob=blob)); modes[str(path)] = '100644'
        cls.tree = b''.join(tree_parts)
        funcs = b.selected_definitions(b.checked(cls.assets['source/git_snapshot.py']),
            ('need', 'object_id', 'parse_tree', 'tree_id'), {'hashlib':hashlib,'re':re})
        cls.commit = ('tree ' + funcs['tree_id'](cls.tree) + '\nauthor Synthetic <fixture@invalid> 0 +0000\ncommitter Synthetic <fixture@invalid> 0 +0000\n\nfixture only\n').encode()
        cls.head = hashlib.sha1(b'commit ' + str(len(cls.commit)).encode() + b'\0' + cls.commit).hexdigest()
        (cls.qa / '.git/HEAD').write_text(cls.head + '\n')
        (cls.base / 'commit.raw').write_bytes(cls.commit); (cls.base / 'tree.raw').write_bytes(cls.tree)
        cls.manifest = {'schema':'c17-root-fresh-git-source-manifest-v1','status':'PASS',
            'head':cls.head,'product_source_root':str(cls.qa),'git_head_ref':b.reference(cls.qa / '.git/HEAD'),
            'git_commit_ref':b.reference(cls.base / 'commit.raw'),'git_tree_ref':b.reference(cls.base / 'tree.raw'),
            'git_tree_verified':True,'files':rows,'modes':modes,'synthetic_fixture':True}
        (cls.base / 'manifest.json').write_bytes(b.encoded(cls.manifest))
        cls.request = {'schema':'c17-full-ab-construction-request-v1',
            'root':'/private/tmp/therese-c17-direct-round-a-010203040506', 'campaign':'A','actor':'/root',
            'expected_head':cls.head,'qa_source':str(cls.qa),'ports':dict(b.PORTS),
            'other_round':{'root':'/private/tmp/therese-c17-direct-round-b-060504030201','campaign':'B',
                           'actor':'/root/environment_routes','expected_head':cls.head},
            'git_head_ref':cls.manifest['git_head_ref'],'git_commit_ref':cls.manifest['git_commit_ref'],
            'git_tree_ref':cls.manifest['git_tree_ref'],'git_manifest_ref':b.reference(cls.base / 'manifest.json'),
            'profiles':{name:b.reference(Path(cls.assets['g1/' + name + '.sb']['path'])) for name in ('web','sql','chrome')},
            'copied_chrome':'/private/tmp/therese-c17-chrome-qa-copy-pure-unused/Google Chrome.app',
            'chrome_tree_ref':b.planned_ref(cls.base/'synthetic-not-emitted-chrome-tree.json',b'[]'),
            'rpc_contract_ref':cls.assets['runtime78-successor/rpc-abi-contract.json']}
        api = {'schema':'c17-runtime78-session-api-v1','features':['definition_only'],
               'runtime_admitted':False,'synthetic_fixture':True}
        (cls.base / 'api.json').write_bytes(b.encoded(api)); cls.request['session_contract_ref'] = b.reference(cls.base / 'api.json')
        table = ast.parse(b.checked(cls.assets['g1/ab_auxiliary_table.py']))
        constants = [n for n in table.body if isinstance(n, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id in ('RPC_JOBS','DIRECT_SITES','JOBS') for t in n.targets)]
        env = {}; exec(compile(ast.Module(body=constants,type_ignores=[]),'<pure-table>', 'exec'),env)
        cls.request['auxiliary_jobs'] = list(env['JOBS']); cls.request['direct_sites'] = list(env['DIRECT_SITES'])
        cls.source = b.source_inputs(cls.request, cls.assets)
        cls.deps = {'node':{'frontend_dep_versions':{'node_modules/vite':{'version':'fixture'}},
                           'playwright_dep_versions':{'node_modules/playwright':{'version':'fixture'}}}}
        cls.chrome = {'executable':cls.request['copied_chrome'] + '/Contents/MacOS/Google Chrome', 'files':[]}
        cls.out = b.payloads(cls.request, cls.assets, cls.source, cls.deps, cls.chrome)
        cls.contract = types.ModuleType('full_rpc_contract')
        exec(compile(cls.out['runtime78-successor/full_rpc_contract.py'],'<pure-contract>','exec'),cls.contract.__dict__)
        with patch.dict(sys.modules,full_rpc_contract=cls.contract):
            cls.blueprint_module = types.ModuleType('full_rpc_blueprint')
            exec(compile(cls.out['runtime78-successor/full_rpc_blueprint.py'],'<pure-blueprint>','exec'),cls.blueprint_module.__dict__)
        cls.blueprint = cls.blueprint_module.FullRpcBlueprint(json.loads(cls.out['prepared-config.json']),
            json.loads(cls.out['authorization/source-checkout.json']),json.loads(cls.out['runtime/pile-reprise.json']),expected_head=cls.head)
        cls.contexts = json.loads(cls.out['authorization/auxiliary-definition-table.json'])['context_refs']
        cls.git_ref = b.planned_ref(Path(cls.request['root'])/'authorization/git-snapshot.json',cls.out['authorization/git-snapshot.json'])
        cls.metadata = cls.blueprint.auxiliary_metadata(Path(cls.request['root']),git_ref=cls.git_ref,
            chrome_context_refs={job:cls.contexts[job] for job in cls.request['auxiliary_jobs'][:5]})
        cls.envelopes = {name:b.planned_ref(Path(cls.request['root'])/'session-rpc/envelope'/ (name+'.json'),b'fixture-only')
                         for name in cls.contract.REQUESTERS}
        cls.descriptors = cls.blueprint.descriptors(Path(cls.request['root']),{'context_id':'1'*32},cls.envelopes,
            metadata_by_job=cls.metadata,source_refs=[b.planned_ref(Path(cls.request['root'])/'runtime78-successor/full_rpc_blueprint.py',cls.out['runtime78-successor/full_rpc_blueprint.py'])])

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def mutate(self, **updates):
        req = deepcopy(self.request); req.update(updates); return req

    def test_identity_logical_physical(self):
        ident = b.identity(self.request)
        self.assertEqual(ident['round_id'],'c17-direct-round-a-010203040506')
        self.assertEqual(ident['root'],self.request['root'])

    def test_identity_b_distinct_actor(self):
        req = self.mutate(**self.request['other_round'])
        req['other_round'] = {k:self.request[k] for k in ('root','actor','campaign','expected_head')}
        self.assertEqual(b.identity(req)['campaign'],'B')

    def test_identical_actors_refused(self):
        req = self.mutate(); req['other_round']['actor'] = req['actor']
        with self.assertRaisesRegex(ValueError,'distincts'): b.identity(req)

    def test_author_as_executor_refused(self):
        with self.assertRaisesRegex(ValueError,'acteur'): b.identity(self.mutate(actor='/root/cycle17_gate_review'))

    def test_physical_campaign_mismatch_refused(self):
        with self.assertRaisesRegex(ValueError,'Campagne'): b.identity(self.mutate(campaign='B'))

    def test_port_mutations_refused(self):
        for key, value in (('backend',17293),('cdp',17595),('frontend',True)):
            with self.subTest(key=key):
                req = self.mutate(); req['ports'][key] = value
                with self.assertRaisesRegex(ValueError,'Ports'): b.identity(req)

    def test_head_not_inferred_from_old_definition(self):
        with self.assertRaisesRegex(ValueError,'HEAD'): b.identity(self.mutate(expected_head=b.OLD_HEAD.upper()))

    def test_personal_source_refused(self):
        with self.assertRaisesRegex(ValueError,'Source QA'): b.identity(self.mutate(qa_source='/Users/synoptia/.therese'))

    def test_exact_ref_rehash(self):
        self.assertEqual(b.checked(self.manifest['git_commit_ref']),self.commit)

    def test_extra_ref_key_refused(self):
        with self.assertRaises(ValueError): b.checked(dict(self.manifest['git_commit_ref'], extra=True))

    def test_wrong_digest_refused(self):
        with self.assertRaisesRegex(ValueError,'SHA/bytes'): b.checked(dict(self.manifest['git_commit_ref'],sha256='0'*64))

    def test_ref_symlink_refused(self):
        link = self.base / 'link'; link.symlink_to('commit.raw')
        with self.assertRaisesRegex(ValueError,'symlink'): b.checked(b.planned_ref(link,self.commit))

    def test_git_raw_tree_blobs_verified(self):
        observed = b.source_inputs(self.request,self.assets)
        self.assertEqual(observed['product_sources']['tests/witness.py'],hashlib.sha256(b'value = 1\n').hexdigest())

    def test_git_wrong_requested_head_refused(self):
        with self.assertRaisesRegex(ValueError,'HEAD'): b.source_inputs(self.mutate(expected_head='1'*40),self.assets)

    def test_git_other_raw_ref_refused(self):
        req = self.mutate(git_tree_ref=self.manifest['git_commit_ref'])
        with self.assertRaisesRegex(ValueError,'Origines'): b.source_inputs(req,self.assets)

    def test_git_mode_mutation_refused(self):
        path = self.qa / 'tests/witness.py'; original = path.stat().st_mode
        try:
            path.chmod(0o755)
            with self.assertRaisesRegex(ValueError,'Mode/type'): b.source_inputs(self.request,self.assets)
        finally: path.chmod(stat.S_IMODE(original))

    def test_git_body_mutation_refused(self):
        path = self.qa / 'tests/witness.py'; raw = path.read_bytes()
        try:
            path.write_bytes(b'value = 2\n')
            with self.assertRaisesRegex(ValueError,'changée'): b.source_inputs(self.request,self.assets)
        finally: path.write_bytes(raw)

    def test_profiles_are_unmodified(self):
        for name, ref in self.request['profiles'].items():
            self.assertEqual(self.out['g1/' + name + '.sb'], b.checked(ref))

    def test_g1_uuid_only_and_closed_flags(self):
        raw = self.out['g1/runtime_session.py']; tree = ast.parse(raw)
        self.assertEqual(sum(isinstance(n,ast.Import) and any(a.name=='uuid' for a in n.names) for n in tree.body),1)
        original = b.checked(self.assets['g1/runtime_session.py']).decode()
        expected = b.contextualize(b.derive_g1(original,self.request), self.request).encode()
        self.assertEqual(raw,expected)
        constants = {}
        for n in tree.body:
            if isinstance(n,(ast.Assign,ast.AnnAssign)):
                target = n.targets[0] if isinstance(n,ast.Assign) else n.target
                if isinstance(target,ast.Name):
                    try: constants[target.id] = ast.literal_eval(n.value)
                    except (ValueError,TypeError): pass
        self.assertIs(constants['RUNTIME_ENABLED'],False); self.assertIs(constants['OS_STARTUP_QUALIFIED'],False)
        self.assertEqual(constants['ADMISSION_TABLE'],{}); self.assertEqual(constants['WRAPPER_ADMISSION_TABLE'],{})
        self.assertTrue(all(v is False for v in constants['CAPABILITIES'].values()))

    def test_uuid_existing_preimage_refused(self):
        raw = b.checked(self.assets['g1/runtime_session.py']).decode().replace('import time\n','import time\nimport uuid\n')
        with self.assertRaisesRegex(ValueError,'uuid'): b.derive_g1(raw,self.request)

    def test_chrome_is_explicit_copy(self):
        text = self.out['g1/runtime_session.py'].decode()
        self.assertIn('CHROME = Path('+repr(self.chrome['executable'])+')',text)
        self.assertNotIn('bundle = Path("/Applications/Google Chrome.app")',text)

    def test_python_definitions_all_parse_no_import(self):
        candidates = [name for name in self.out if name.endswith('.py') and not name.startswith('construction-preimages/')]
        self.assertGreaterEqual(len(candidates),50)
        for name in candidates: ast.parse(self.out[name],filename=name)

    def test_prepare_has_no_legacy_launch_or_git(self):
        text = self.out['runtime/runtime.py'].decode()
        self.assertIn("sys.argv[1:] != ['prepare']",text)
        self.assertIn("source/'.git/HEAD'",text)
        self.assertNotIn('subprocess',text); self.assertNotIn('from common',text)

    def test_prepare_script_true_body_synthetic(self):
        root = self.base / 'prepare-fixture'; (root/'runtime').mkdir(parents=True)
        (root/'prepared-config.json').write_bytes(b.encoded({'qa_source':str(self.qa),'head':self.head}))
        (root/'runtime/pile-reprise.json').write_bytes(b.encoded({'status':'prepared','repo':str(self.qa),'head_at_preparation':self.head}))
        with patch('sys.argv',['runtime.py','prepare']), patch('builtins.print') as printed:
            exec(compile(self.out['runtime/runtime.py'],'<prepare-synthetic>','exec'),{'__file__':str(root/'runtime/runtime.py')})
        self.assertEqual(json.loads(printed.call_args.args[0])['status'],'prepared')
        with patch('sys.argv',['runtime.py','start']):
            with self.assertRaisesRegex(SystemExit,'Legacy'): exec(compile(self.out['runtime/runtime.py'],'<prepare-synthetic>','exec'),{'__file__':str(root/'runtime/runtime.py')})

    def test_species_are_definitions_only(self):
        data = json.loads(self.out['complements/b1760-identites-historiques-completes.json'])
        self.assertIs(data['historical_results_not_imported'],True)
        self.assertEqual(set(data['historical_exports'][0]),{'obligation_id','historical_mode','historical_nodeid','candidate_species','mapping_limit'})

    def test_exact_seven_identity_anchors_retained(self):
        anchors = json.loads(b.checked(self.assets['runtime78-successor/identity-anchors.json']))['anchors']
        text = self.out['runtime/couverture-ecran-c17.mjs'].decode()
        self.assertEqual(len(anchors),7)
        for row in anchors: self.assertEqual(text.count(row['after']),1)

    def test_fourteen_chrome_contexts_no_birth(self):
        table = json.loads(self.out['authorization/auxiliary-definition-table.json'])
        self.assertEqual(len(table['jobs']),14); self.assertEqual(len(table['context_refs']),14)
        self.assertEqual({row['port'] for row in table['jobs'].values()},{17594})
        for job, ref in table['context_refs'].items():
            name = str(Path(ref['path']).relative_to(self.request['root']))
            body = json.loads(self.out[name]); self.assertEqual(body['stage'],job)
            self.assertEqual(body['scope'],'runtime78_exact_round'); self.assertNotIn('birth',body)

    def test_source_checkout_round_join(self):
        data = json.loads(self.out['authorization/source-checkout.json'])
        self.assertEqual(data['round_id'],'c17-direct-round-a-010203040506')
        self.assertEqual(data['qa_root'],self.request['root']); self.assertEqual(data['git_head'],self.head)
        self.assertEqual(data['source_manifest_ref'],b.planned_ref(Path(self.request['root'])/'authorization/source-files.json',self.out['authorization/source-files.json']))

    def test_runtime_rpc_plan_not_fabricated(self):
        data = json.loads(self.out['authorization/rpc-construction-inputs.json'])
        self.assertEqual((data['required_sites'],data['required_auxiliaries']),(15,14))
        self.assertIsNone(data['owner_identity']); self.assertIsNone(data['plan']); self.assertEqual(data['enrollments'],[])
        self.assertFalse(any(name.endswith('go.json') or name.startswith('ledger/') for name in self.out))

    def test_fifteen_actual_blueprint_descriptors(self):
        self.assertEqual(len(self.descriptors),15)
        self.assertEqual([row['label'] for row in self.descriptors],list(self.contract.SITE_SPECS))
        self.assertEqual(len({row['nonce'] for row in self.descriptors}),15)
        self.assertEqual(len({row[k] for row in self.descriptors for k in ('stdout_path','stderr_path')}),30)
        self.assertEqual([row['timeout_seconds'] for row in self.descriptors],[700]*4+[90]*4+[180]*4+[240]*3)

    def test_business_environment_exact_common_blueprint(self):
        stack = json.loads(self.out['runtime/pile-reprise.json'])
        methods = b.selected_definitions(self.out['auxiliary-ports/runtime/common.py'],('environment',),
            {'Path':Path,'NODE':self.blueprint_module.NODE,'REPO':self.qa,
             'OUT':Path(self.request['root'])/'auxiliary-ports/runtime','manifest':lambda:stack})
        self.assertEqual(methods['environment'](),self.blueprint.web_environment(Path(self.request['root'])))
        test_data = Path(stack['temporary_root'])/'test-data'
        self.assertEqual(methods['environment'](test_data),self.blueprint.web_environment(Path(self.request['root']),data_dir=test_data))

    def test_real_calibrate_wrapper_four_rpc_calls_match(self):
        rows = self.descriptors[:4]; seen=[]; root=Path(self.request['root'])
        common = types.ModuleType('common'); common.NODE=self.blueprint_module.NODE
        common.OUT=root/'auxiliary-ports/runtime'; common.PYTHON=self.blueprint.python; common.REPO=self.qa
        stack=json.loads(self.out['runtime/pile-reprise.json']); stack['status']='running'  # synthetic data only
        common.manifest=lambda:stack; common.head=lambda:self.head; common.new_run=lambda _:None
        common.environment=lambda:self.blueprint.web_environment(root)
        common.save=lambda *_:None
        nested=types.ModuleType('nested_capture'); allocated=self.base/'wrapper-all-output'; allocated.mkdir()
        nested.reserved_path=lambda label:allocated
        nested.session_child_env=lambda base: dict(rows[len(seen)]['environment']) if all(rows[len(seen)]['environment'].get(k)==v for k,v in base.items()) else (_ for _ in ()).throw(ValueError('env'))
        def capture(argv,**kwargs):
            row=rows[len(seen)]; name=row['label'].removeprefix('all-')
            self.assertEqual(argv,row['argv']); self.assertEqual(str(kwargs['cwd']),row['cwd'])
            self.assertEqual(kwargs['env'],row['environment']); self.assertEqual(kwargs['timeout'],row['timeout_seconds'])
            self.assertEqual(kwargs['label'],row['label'])
            self.assertEqual(kwargs['stdout_path'].name,name+'.stdout'); self.assertEqual(kwargs['stderr_path'].name,name+'.stderr')
            seen.append(row['id']); return subprocess.CompletedProcess(argv,0,'fixture stdout\n','')
        nested.capture_nested=capture
        with patch.dict(sys.modules,common=common,nested_capture=nested), patch('builtins.print'):
            with self.assertRaises(SystemExit) as ended:
                exec(compile(self.out['auxiliary-ports/runtime/calibrate-all.py'],'<real-wrapper-pure>','exec'),{'__name__':'__main__'})
        self.assertEqual(ended.exception.code,0); self.assertEqual(seen,[row['id'] for row in rows])

    def test_sql_paths_fresh_qa_and_oracles_not_changed(self):
        for name in ('preparer-et-executer-harness-root-stack.py','preparer-harness-b1753-power.py'):
            text=self.out['auxiliary-ports/complements/instruments/'+name].decode()
            self.assertNotIn(b.OLD_SOURCE,text)
            self.assertIn(str(self.qa/'.venv-conforme/bin/python'),text)
            self.assertIn('--reviewed-contract-sha',text)
            self.assertIn('timeout=240',text)
        power=self.out['auxiliary-ports/complements/instruments/preparer-harness-b1753-power.py'].decode()
        self.assertIn('returncode==1',power.replace(' ',''))

    def test_rpc_contract_reader_derived_only(self):
        data = json.loads(self.out['runtime78-successor/rpc-abi-contract.json'])
        before = b.read_json(self.request['rpc_contract_ref'])
        expected = b.planned_ref(Path(self.request['root'])/'runtime78-successor/rpc_abi_reader.py', self.out['runtime78-successor/rpc_abi_reader.py'])
        self.assertEqual(data['reader'],expected)
        del data['reader']; del before['reader']; self.assertEqual(data,before)

    def test_vite_config_from_source_not_old_repo(self):
        text = self.out['runtime/vite.canonique.mjs'].decode()
        self.assertIn(str(self.qa/'src/frontend/node_modules/vite/dist/node/index.js'),text)
        self.assertIn("host: '127.0.0.1', port: 5173, strictPort: true",self.out['runtime/vite.runtime.config.mjs'].decode())

    def test_vite_anchor_change_refused(self):
        with self.assertRaisesRegex(ValueError,'Ancre'): b.vite_texts(self.request,'export default {}')

    def test_diff_ledger_covers_final_modified_definitions(self):
        origin = json.loads(self.out['full-construction-origin.json'])
        self.assertIn('construction-diffs/runtime__runtime.py.diff',origin['diffs'])
        for diff in origin['diffs']:
            self.assertTrue(self.out[diff].startswith(b'--- ')); self.assertIn(b'+++ ',self.out[diff])
        for name, ref in self.assets.items():
            if name in self.out and self.out[name] != b.checked(ref):
                self.assertIn('construction-diffs/'+name.replace('/','__')+'.diff',origin['diffs'])

    def test_source_and_output_pins_immutable(self):
        frozen = json.loads(self.out['runtime78-successor/frozen-inputs.json'])
        for path,digest in frozen['sources'].items():
            raw = self.out[str(Path(path).relative_to(self.request['root']))]
            self.assertEqual(hashlib.sha256(raw).hexdigest(),digest)
        for ref in self.assets.values(): b.checked(ref)

    def test_missing_authority_refuses_before_allocation(self):
        request = self.mutate(); request['request_ref'] = b.planned_ref(self.base/'request.json',b'fixture')
        with self.assertRaises(ValueError): b.authority(request,b.planned_ref(self.base/'not-authority.json',b'fixture'),b.reference(HERE/'assets.json'))
        self.assertFalse(Path(request['root']).exists())

    def test_guarded_no_process_socket_import(self):
        names = {n.names[0].name for n in ast.parse((HERE/'build_full_round.py').read_text()).body if isinstance(n,ast.Import)}
        self.assertFalse(names & {'subprocess','socket','ctypes','runtime_session'})


if __name__ == '__main__':
    unittest.main()
