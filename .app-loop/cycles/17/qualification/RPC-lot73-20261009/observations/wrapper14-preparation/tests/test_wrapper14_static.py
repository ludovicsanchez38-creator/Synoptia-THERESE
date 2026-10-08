"""Purs ROOT14 : vrais corps sélectionnés, doubles explicitement synthétiques.

Aucun G1 entier importé, aucun constructeur/build/VM/browser/profil exécuté.
"""
from __future__ import annotations

import ast
import copy
import difflib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
ORIGIN = Path('/private/tmp/therese-c17-wrapper13-dirhelper-P5WQpQ')
spec = importlib.util.spec_from_file_location('wrapper14_definition_only', HERE / 'build_fresh_wrapper.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
old_spec = importlib.util.spec_from_file_location('wrapper13_definition_only', HERE / 'preimages/build_fresh_wrapper-13.py')
old = importlib.util.module_from_spec(old_spec)
old_spec.loader.exec_module(old)


class SyntheticPath(type(Path())):
    """Path double : aucune observation physique de ROOT14 ni de chemin personnel."""
    redirects = {}
    non_directories = set()

    def resolve(self, strict=False):
        return type(self)(self.redirects.get(str(self), str(self)))

    def is_dir(self):
        return str(self) not in self.non_directories


def selected_environment(source):
    tree = ast.parse(source)
    names = {'CHROME_JOBS', 'AUXILIARY_NAMES', 'ENV_CONSTANTS', 'ENV_PATHS',
             'ENV_CONTEXT', 'REQUIRED_ENV', 'WRAPPER_PATTERN'}
    nodes = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in ('validate_environment', 'child_path'):
            nodes.append(node)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            target = node.target if isinstance(node, ast.AnnAssign) else node.targets[0]
            if isinstance(target, ast.Name) and target.id in names:
                nodes.append(node)
    def require(ok, why):
        if not ok:
            raise ValueError(why)
    namespace = {'Path': SyntheticPath, 'os': os, 're': re, 'require': require,
                 'SOURCE': builder.QA,
                 'NODE_ROOT': Path('/Users/synoptia/.nvm/versions/node/v22.19.0')}
    exec(compile(ast.Module(nodes, type_ignores=[]), '<selected-real-G1-pure-bodies>', 'exec'), namespace)
    return namespace


class MemoryEmitter:
    """Aucune écriture : bytes et refs synthétiques, explicitement non natives."""
    def __init__(self, root):
        self.root = root
        self.objects = {}

    def write(self, name, raw):
        self.objects[name] = raw
        return {'path': str(self.root / name), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

    def json(self, name, value):
        return self.write(name, builder.encoded(value))


class Wrapper14Static(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = (builder.PREP / 'g1-26/runtime_session.py').read_text()
        cls.qa_before = old.g1_auxiliary_parent_delta(old.g1_chrome_executable_guard(old.g1_chrome_copy_delta(cls.base)))
        cls.qa_after = builder.g1_chromium_tmpdir_delta(cls.qa_before)
        cls.before_ns = selected_environment(cls.qa_before)
        cls.after_ns = selected_environment(cls.qa_after)
        spec = importlib.util.spec_from_file_location('chrome_contract_definition_only', builder.CHROME_CONTRACT_QA_REF['path'])
        cls.contract = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.contract)

    def setUp(self):
        SyntheticPath.redirects = {}
        SyntheticPath.non_directories = set()

    def rows(self, definition=builder):
        emitter = MemoryEmitter(builder.FUTURE_ROOT)
        vm_calls, mkdir_calls = [], []
        def vm(command, **kwargs):
            vm_calls.append((command, kwargs))
            payload = json.loads(kwargs['input'])
            argv = {row['job']: [payload['executable'], '--user-data-dir=' + row['profile'],
                    '--remote-debugging-port=17594', '--remote-debugging-address=127.0.0.1']
                    for row in payload['jobs']}
            return subprocess.CompletedProcess(command, 0, json.dumps(argv), '')
        gpu = {'path': '/synthetic/gpu', 'sha256': '1' * 64, 'bytes': 16}
        original_checked = definition.checked
        def checked(ref):
            return b'Metal: Supported' if ref == gpu else original_checked(ref)
        with patch.object(definition, 'checked', checked), patch.object(subprocess, 'run', vm), \
             patch.object(Path, 'mkdir', lambda path, **kw: mkdir_calls.append((str(path), kw))):
            rows, files_ref, manifest_ref = definition.chrome_prepare(emitter, self.contract, gpu, definition.CHROME_QA_COPY_REF)
        self.assertEqual(len(vm_calls), 1)
        self.assertEqual(len(mkdir_calls), 15)
        return rows, emitter.objects, files_ref, manifest_ref

    def validate(self, env, *, root=None, mode='chrome', stage=None, namespace=None):
        namespace = namespace or self.after_ns
        root = SyntheticPath(root or builder.FUTURE_ROOT)
        stage = stage or 'aux-chrome-' + builder.JOBS[0]
        return namespace['validate_environment'](root, env, mode, '/root', root.name,
                                                  source_root=builder.QA, stage=stage)

    def environment(self, index=0):
        rows, *_ = self.rows()
        return copy.deepcopy(rows[builder.JOBS[index]]['env'])

    def test_01_origin_builder_and_profile_byte_exact(self):
        raw = (HERE / 'preimages/build_fresh_wrapper-13.py').read_bytes()
        self.assertEqual(raw, (ORIGIN / 'build_fresh_wrapper.py').read_bytes())
        self.assertEqual(hashlib.sha256(raw).hexdigest(), 'f76830c89475c58ea63599d7633d9a5031777a0655b2c0c3a838bdea96fe5719')
        self.assertEqual((HERE / 'profile/chrome.sb').read_bytes(), (ORIGIN / 'profile/chrome.sb').read_bytes())
        self.assertEqual(hashlib.sha256((HERE / 'profile/chrome.sb').read_bytes()).hexdigest(), '2ecae3a24ec871a44827b3f712ced1ef5e84d8f778906c37b3a5b51bb374dcdf')

    def test_02_exact_root_absent_no_allocation(self):
        self.assertEqual(str(builder.FUTURE_ROOT), '/private/tmp/therese-c17-wrapper-canary-187602c63a0b498a95d25c19843000a8')
        self.assertFalse(builder.FUTURE_ROOT.exists())
        self.assertFalse(builder.FUTURE_ROOT.is_symlink())
        self.assertEqual(builder.future_root(builder.FUTURE_ROOT), builder.FUTURE_ROOT)
        with self.assertRaises(ValueError):
            builder.future_root(old.FUTURE_ROOT)

    def test_03_actual_chrome_prepare_only_env_key_changes(self):
        before, before_objects, before_files, before_manifest = self.rows(old)
        after, objects, files, manifest = self.rows()
        self.assertEqual(set(after), set(builder.JOBS))
        for job in builder.JOBS:
            row = copy.deepcopy(after[job])
            value = row['env'].pop('MAC_CHROMIUM_TMPDIR')
            self.assertEqual(value, row['env']['TMPDIR'])
            self.assertEqual(value, str(builder.FUTURE_ROOT / 'auxiliary' / row['name'] / 'tmp'))
            self.assertEqual(row, before[job])
        self.assertEqual(files, before_files)
        # Seule attestation contenant les cinq environments doit différer.
        key = 'authorization/chrome-preparation.json'
        left, right = dict(before_objects), dict(objects)
        left.pop(key); right.pop(key)
        self.assertEqual(left, right)
        body = json.loads(objects[key])
        for job in builder.JOBS:
            self.assertEqual(body['auxiliary_descriptors'][job]['env'], after[job]['env'])
        self.assertIs(body['FULL'], False)
        self.assertIs(body['runtime_executed'], False)

    def test_04_old_real_guard_refuses_added_key(self):
        with self.assertRaisesRegex(ValueError, 'hors allowlist'):
            self.validate(self.environment(), namespace=self.before_ns)

    def test_05_new_real_guard_accepts_exact_five_envs(self):
        rows, *_ = self.rows()
        for job in builder.JOBS:
            row = rows[job]
            self.assertEqual(self.validate(row['env'], stage=row['name']), row['env'])

    def test_06_missing_key_refused(self):
        env = self.environment(); env.pop('MAC_CHROMIUM_TMPDIR')
        with self.assertRaisesRegex(ValueError, 'MAC_CHROMIUM_TMPDIR'):
            self.validate(env)

    def test_07_other_modes_refused(self):
        for mode in ('sql', 'web'):
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, 'hors allowlist'):
                self.validate(self.environment(), mode=mode)

    def test_08_other_root_refused(self):
        with self.assertRaisesRegex(ValueError, 'hors allowlist'):
            self.validate(self.environment(), root=old.FUTURE_ROOT)

    def test_09_unknown_or_leaf_stage_refused(self):
        for stage in ('backend', 'vite', builder.JOBS[0], 'aux-chrome-unknown', 'calibrate'):
            with self.subTest(stage=stage), self.assertRaisesRegex(ValueError, 'hors allowlist'):
                self.validate(self.environment(), stage=stage)

    def test_10_wrong_value_refused_without_personal_path_read(self):
        for value in ('/synthetic/not-QA', str(builder.FUTURE_ROOT / 'tmp'), '', 'relative'):
            env = self.environment(); env['MAC_CHROMIUM_TMPDIR'] = value
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'MAC_CHROMIUM_TMPDIR'):
                self.validate(env)

    def test_11_both_values_wrong_stage_path_refused(self):
        env = self.environment()
        env['MAC_CHROMIUM_TMPDIR'] = env['TMPDIR'] = str(builder.FUTURE_ROOT / 'auxiliary' / ('aux-chrome-' + builder.JOBS[1]) / 'tmp')
        with self.assertRaisesRegex(ValueError, 'MAC_CHROMIUM_TMPDIR'):
            self.validate(env)

    def test_12_synthetic_symlink_target_refused(self):
        env = self.environment()
        SyntheticPath.redirects[env['TMPDIR']] = '/synthetic/redirected-target'
        with self.assertRaisesRegex(ValueError, 'MAC_CHROMIUM_TMPDIR'):
            self.validate(env)

    def test_13_synthetic_missing_directory_refused(self):
        env = self.environment(); SyntheticPath.non_directories.add(env['TMPDIR'])
        with self.assertRaisesRegex(ValueError, 'MAC_CHROMIUM_TMPDIR'):
            self.validate(env)

    def test_14_extra_key_refused(self):
        env = self.environment(); env['MAC_CHROMIUM_OTHER'] = env['TMPDIR']
        with self.assertRaisesRegex(ValueError, 'hors allowlist'):
            self.validate(env)

    def test_15_existing_constant_refusal_preserved(self):
        env = self.environment(); env['LANG'] = 'fr_FR.UTF-8'
        with self.assertRaisesRegex(ValueError, 'Valeur env constante'):
            self.validate(env)

    def test_16_no_global_env_set_changed(self):
        for key in ('ENV_CONSTANTS', 'ENV_PATHS', 'ENV_CONTEXT', 'REQUIRED_ENV'):
            self.assertEqual(self.before_ns[key], self.after_ns[key])
            self.assertNotIn('MAC_CHROMIUM_TMPDIR', self.after_ns[key])

    def test_17_only_g1_validate_environment_ast_changed(self):
        before, after = ast.parse(self.qa_before), ast.parse(self.qa_after)
        a = next(n for n in before.body if isinstance(n, ast.FunctionDef) and n.name == 'validate_environment')
        b = next(n for n in after.body if isinstance(n, ast.FunctionDef) and n.name == 'validate_environment')
        self.assertNotEqual(ast.dump(a), ast.dump(b))
        b.body = a.body
        self.assertEqual(ast.dump(before, include_attributes=False), ast.dump(after, include_attributes=False))
        builder.validate_closed_g1(self.qa_after)

    def test_18_non_chrome_env_without_key_unchanged(self):
        env = self.environment(); env.pop('MAC_CHROMIUM_TMPDIR')
        for mode in ('sql', 'web'):
            self.assertEqual(self.validate(env, mode=mode, stage='backend'), self.validate(env, mode=mode, stage='backend', namespace=self.before_ns))

    def test_19_anchors_changed_or_duplicate_refused(self):
        for mutant in (self.qa_before.replace('REQUIRED_ENV <= env.keys()', 'REQUIRED_ENV < env.keys()'), self.qa_before + self.qa_before):
            with self.assertRaisesRegex(ValueError, 'Ancre environnement'):
                builder.g1_chromium_tmpdir_delta(mutant)

    def test_20_builder_only_allowed_functions_and_root_changed(self):
        before, after = ast.parse((ORIGIN / 'build_fresh_wrapper.py').read_text()), ast.parse((HERE / 'build_fresh_wrapper.py').read_text())
        before_nodes = {n.name: ast.dump(n, include_attributes=False) for n in before.body if isinstance(n, ast.FunctionDef)}
        after_nodes = {n.name: ast.dump(n, include_attributes=False) for n in after.body if isinstance(n, ast.FunctionDef)}
        self.assertEqual(set(after_nodes) - set(before_nodes), {'g1_chromium_tmpdir_delta'})
        self.assertEqual({name for name in before_nodes if before_nodes[name] != after_nodes[name]}, {'chrome_prepare', 'build'})
        for tree in (before, after):
            for node in tree.body:
                if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'FUTURE_ROOT' for t in node.targets):
                    node.value = ast.Constant(None)
            tree.body = [n for n in tree.body if not isinstance(n, ast.FunctionDef)]
        self.assertEqual(ast.dump(before, include_attributes=False), ast.dump(after, include_attributes=False))

    def test_21_helpers_binding_equality_actual_body_preserved(self):
        raw = self.qa_after
        source = (builder.PREP / 'coordinator/run_wrapper_canary.py').read_text()
        function = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)
                        and n.name == 'compose_26_commands')
        namespace = {'Path': Path, 'require': builder.need, 'CHROME_JOBS': builder.JOBS,
                     'blueprint': SimpleNamespace(QA_SOURCE=builder.QA)}
        exec(compile(ast.Module([function], type_ignores=[]), '<actual-compose26-pure-body>', 'exec'), namespace)
        rows, *_ = self.rows()
        synthetic_base21 = {'synthetic-' + str(i): {'env': {'SYNTHETIC': 'no_native_launch'}} for i in range(21)}
        commands = namespace['compose_26_commands'](builder.FUTURE_ROOT, synthetic_base21, rows)
        self.assertEqual(len(commands), 26)
        for job, row in rows.items():
            self.assertEqual(commands[row['name']]['env'], row['env'])
            self.assertEqual(commands[row['name']]['env']['MAC_CHROMIUM_TMPDIR'], row['env']['TMPDIR'])
            self.assertEqual(commands[row['name']]['argv'], row['argv'])
            self.assertEqual(commands[row['name']]['timeout_seconds'], 50)
        self.assertTrue(all('MAC_CHROMIUM_TMPDIR' not in commands[name]['env'] for name in synthetic_base21))
        self.assertIn('"env": row["env"]', raw)
        self.assertIn('validate_environment(root, row["env"], "chrome"', raw)
        self.assertIn('env=dict(spec["env"])', raw)
        self.assertIn('"env": environment', raw)
        self.assertIn('env=entry["environment"]', raw)
        self.assertIn('os.execve(command[0], command, os.environ)', (builder.PREP / 'g1-26/runtime_launch_gate.py').read_text())
        self.assertIn('"timeout_seconds": 50, "env": row["env"]', (builder.PREP / 'coordinator/run_wrapper_canary.py').read_text())

    def test_22_sources79_and_three_historical_routes_unchanged(self):
        for name in ('join_sources79', 'historical_ips_archive', 'validate_indexes', 'checked_chrome_successor'):
            left = next(n for n in ast.parse((ORIGIN / 'build_fresh_wrapper.py').read_text()).body if isinstance(n, ast.FunctionDef) and n.name == name)
            right = next(n for n in ast.parse((HERE / 'build_fresh_wrapper.py').read_text()).body if isinstance(n, ast.FunctionDef) and n.name == name)
            self.assertEqual(ast.dump(left, include_attributes=False), ast.dump(right, include_attributes=False))

    def test_23_forward_inverse_diffs_exact(self):
        for kind, before, after in (
            ('builder', HERE / 'preimages/build_fresh_wrapper-13.py', HERE / 'build_fresh_wrapper.py'),
            ('g1', HERE / 'preimages/runtime_session-before-env.py', HERE / 'preview/runtime_session-after-env.py'),
        ):
            for suffix, a, b in (('forward', before, after), ('inverse', after, before)):
                expected = ''.join(difflib.unified_diff(a.read_text().splitlines(True), b.read_text().splitlines(True), fromfile=str(a), tofile=str(b)))
                self.assertEqual((HERE / 'diffs' / f'{kind}-{suffix}.diff').read_text(), expected)


if __name__ == '__main__':
    unittest.main(verbosity=2)
