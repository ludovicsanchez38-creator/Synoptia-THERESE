"""Garde-fous de l'ordre de publication et du mode sans comptes de signature."""
import importlib.util
import json
import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


class PipelineTests(unittest.TestCase):
    def test_release_and_license_job_actions_are_pinned(self):
        for filename in ['ci.yml', 'release.yml']:
            source = (ROOT / '.github/workflows' / filename).read_text()
            jobs = yaml.safe_load(source)['jobs']
            for job in jobs.values():
                steps = job.get('steps', [])
                for step in steps:
                    action = step.get('uses', '')
                    if not action or action.startswith('./'):
                        continue
                    with self.subTest(workflow=filename, action=action):
                        self.assertRegex(action, r'@[a-f0-9]{40}$')
                        if action.startswith(('actions/', 'Swatinem/')):
                            self.assertRegex(source, re.escape(action) + r'\s+# v\d+\.\d+\.\d+')

    def test_no_run_folds_two_script_calls_into_one_line(self):
        # Un scalaire YAML simple sur deux lignes est replié en une seule
        # commande : `a.py verifier b.py check` part en arguments de a.py.
        for path in sorted((ROOT / '.github/workflows').glob('*.yml')):
            jobs = yaml.safe_load(path.read_text())['jobs']
            for job_name, job in jobs.items():
                for step in job.get('steps', []) or []:
                    run = step.get('run')
                    if not isinstance(run, str):
                        continue
                    for line in run.splitlines():
                        calls = re.findall(r'(?:^|\s)\S*python3?(?:\.exe)?\s+\S+\.py\b', line)
                        with self.subTest(workflow=path.name, job=job_name, step=step.get('name')):
                            self.assertLessEqual(len(calls), 1, line)

    def test_rust_ci_job_provides_every_untracked_tauri_resource(self):
        # Le build script Tauri refuse une ressource absente. La CI analyse le
        # code Rust sans build Python : chaque ressource non versionnée doit y
        # avoir un factice, sinon clippy (porte de release.yml) échoue.
        import subprocess
        tracked = set(subprocess.run(['git', 'ls-files'], cwd=ROOT, capture_output=True,
                                     text=True, check=True).stdout.splitlines())
        jobs = yaml.safe_load((ROOT / '.github/workflows/ci.yml').read_text())['jobs']
        factices = next(s['run'] for s in jobs['rust']['steps'] if s.get('name') == 'Sidecar et dist factices')
        tauri = ROOT / 'src/frontend/src-tauri'
        for name in ['tauri.conf.json', 'tauri.linux.conf.json']:
            resources = json.loads((tauri / name).read_text())['bundle'].get('resources', {})
            for source in resources:
                if '*' in source:
                    continue
                path = (tauri / source).resolve().relative_to(ROOT.resolve()).as_posix()
                if path in tracked:
                    continue
                with self.subTest(config=name, resource=source):
                    self.assertIn(source, factices)

    def test_backend_spec_loads_system_libraries_with_its_sibling_modules(self):
        # Le spec charge system_libraries.py par chemin ; ce module importe
        # cpython_components. Sans le dossier scripts/ importable, PyInstaller
        # échouait sur les trois plateformes (relevé à blanc, run 42243611488).
        import subprocess
        import sys
        import tempfile
        spec = (ROOT / 'src/backend/backend.spec').read_text(encoding='utf-8')
        start = spec.index('# Enregistrer la provenance avant strip')
        end = spec.index('_system_module.record_analysis(')
        snippet = ('import importlib.util, os, sys\n'
                   f'backend_dir = {str(ROOT / "src/backend")!r}\n' + spec[start:end] +
                   'print(_system_module.cpython_components.CATALOG)\n')
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run([sys.executable, '-I', '-c', snippet], cwd=tmp,
                                    capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr[-600:])
        self.assertEqual(result.stdout.strip(), 'licenses/cpython-components.lock.json')

    def test_pytest_ceiling_keeps_margin_and_fits_its_timeouts(self):
        # Réserve 4 de la relecture 0.83 : 1 027 s mesurées pour un plafond de
        # 1 080 s. Le plafond garde au moins 25 % de marge sur cette mesure,
        # et l'étape puis le job laissent le temps à `timeout` de conclure.
        job = yaml.safe_load((ROOT / '.github/workflows/ci.yml').read_text())['jobs']['backend-tests']
        step = next(s for s in job['steps'] if s.get('name') == 'Tests unitaires (pytest)')
        ceiling = int(re.search(r'timeout (\d+) uv run pytest', step['run']).group(1))
        self.assertGreaterEqual(ceiling, 1027 * 1.25)
        self.assertIn(f'après {ceiling // 60} min', step['run'])
        self.assertGreater(step['timeout-minutes'] * 60, ceiling + 60)
        self.assertGreater(job['timeout-minutes'], step['timeout-minutes'] + 3)

    def test_release_build_pins_the_reviewed_cpython(self):
        # "3.13" résout 3.13.18 sur ubuntu-22.04 depuis fin octobre 2026 : les
        # octets CPython ne seraient plus ceux du catalogue relu (3.13.17).
        catalog = json.loads((ROOT / 'licenses/cpython-components.lock.json').read_text(encoding='utf-8'))
        steps = yaml.safe_load((ROOT / '.github/workflows/release.yml').read_text())['jobs']['build']['steps']
        setup = next(s for s in steps if s.get('uses', '').startswith('actions/setup-python@'))
        self.assertEqual(setup['with']['python-version'], catalog['version'])

    def test_no_upload_before_platform_checks(self):
        jobs = yaml.safe_load((ROOT / '.github/workflows/release.yml').read_text())['jobs']
        steps = jobs['build']['steps']
        build = next(s for s in steps if 'tauri-apps/tauri-action@' in s.get('uses', ''))
        self.assertNotIn('tagName', build.get('with', {}))
        names = [s.get('name', '') for s in steps]
        self.assertLess(names.index('Finaliser la signature macOS'), names.index('Publier les artefacts vérifiés'))
        self.assertLess(names.index('Vérifier Authenticode'), names.index('Publier les artefacts vérifiés'))
        self.assertLess(names.index('Contrôler les licences tierces'), names.index('Build THÉRÈSE (Tauri)'))

    def test_copyleft_guards_and_release_asset_precede_binary_publication(self):
        ci = yaml.safe_load((ROOT / '.github/workflows/ci.yml').read_text())['jobs']
        steps = ci['licences-signature']['steps']
        self.assertTrue(any('copyleft_sources.py verifier' in s.get('run', '') and
                            not s.get('continue-on-error') for s in steps))
        release = yaml.safe_load((ROOT / '.github/workflows/release.yml').read_text())['jobs']
        self.assertIn('sources-copyleft', release['build']['needs'])
        steps = release['sources-copyleft']['steps']
        runs = [s.get('run', '') for s in steps]
        verify = next(i for i, r in enumerate(runs) if 'copyleft_sources.py verifier' in r)
        assemble = next(i for i, r in enumerate(runs) if 'copyleft_sources.py assembler' in r)
        upload = next(i for i, r in enumerate(runs) if 'gh release upload' in r)
        self.assertLess(verify, assemble)
        self.assertLess(assemble, upload)
        self.assertTrue(any('THERESE-sources-copyleft.tar.gz' in r for r in runs))
        self.assertFalse(any(s.get('continue-on-error') for s in steps))

    def test_system_inventory_and_sources_gate_every_release(self):
        jobs = yaml.safe_load((ROOT / '.github/workflows/release.yml').read_text())['jobs']
        steps = jobs['build']['steps']
        runs = [s.get('run', '') for s in steps]
        inventory = next(i for i, r in enumerate(runs) if 'system_libraries.py inventory' in r)
        build = next(i for i, s in enumerate(steps) if 'tauri-apps/tauri-action@' in s.get('uses', ''))
        verify = next(i for i, r in enumerate(runs) if 'verify_packaged_licenses.py' in r)
        publish = next(i for i, r in enumerate(runs) if 'publish_release_artifacts.py' in r)
        self.assertLess(inventory, build)
        self.assertLess(build, verify)
        self.assertLess(verify, publish)
        self.assertFalse(steps[inventory].get('continue-on-error'))
        self.assertFalse(steps[verify].get('continue-on-error'))
        source_runs = '\n'.join(s.get('run', '') for s in jobs['sources-copyleft']['steps'])
        self.assertIn('system_libraries.py assemble-sources', source_runs)
        self.assertIn('THERESE-sources-systeme-linux.tar.gz', source_runs)

    def test_installer_verifier_runs_where_pyinstaller_is_installed(self):
        # Run 42355341201 : le moteur onefile ne s'ouvre qu'avec PyInstaller,
        # installé dans .venv par uv ; le Python de setup-python ne l'a pas.
        steps = yaml.safe_load((ROOT / '.github/workflows/release.yml').read_text())['jobs']['build']['steps']
        step = next(s for s in steps if s.get('name') == 'Vérifier les licences dans les installeurs')
        self.assertEqual(step.get('shell'), 'bash')
        lines = [line.strip() for line in step['run'].splitlines()]
        self.assertIn('.venv/Scripts/python.exe scripts/verify_packaged_licenses.py --platform "${{ runner.os }}"', lines)
        self.assertIn('.venv/bin/python scripts/verify_packaged_licenses.py --platform "${{ runner.os }}"', lines)
        self.assertIn('elif [ "${{ runner.os }}" = "macOS" ]; then', lines)
        self.assertIsNone(step.get('if'))

    def test_dry_run_builds_and_checks_but_never_publishes(self):
        workflow = yaml.safe_load((ROOT / '.github/workflows/release.yml').read_text())
        dry = workflow[True]['workflow_dispatch']['inputs']['dry_run']
        self.assertEqual((dry['type'], dry['default']), ('boolean', False))
        jobs = workflow['jobs']
        guard = jobs['preflight']['steps'][0]
        self.assertEqual(guard['if'], '${{ inputs.dry_run }}')
        self.assertIn('a-blanc-*)', guard['run'])
        self.assertEqual(jobs['manifeste-updater']['if'], '${{ !inputs.dry_run }}')
        publishing = re.compile(r'gh release (create|upload|edit|delete)|publish_release_artifacts\.py|git (tag|push)')
        for job_name, job in jobs.items():
            for step in job.get('steps', []):
                if publishing.search(step.get('run', '')):
                    with self.subTest(job=job_name, step=step.get('name')):
                        self.assertTrue(step.get('if') == '${{ !inputs.dry_run }}'
                                        or job.get('if') == '${{ !inputs.dry_run }}')
        # Les gardes de licence et de signature restent inconditionnelles.
        for name in ('Vérifier les licences dans les installeurs', 'Inventorier les bibliothèques réellement embarquées',
                     'Contrôler les licences tierces'):
            step = next(s for s in jobs['build']['steps'] if s.get('name') == name)
            self.assertNotIn('dry_run', str(step.get('if', '')))
        tauri = next(s for s in jobs['build']['steps'] if 'tauri-apps/tauri-action@' in s.get('uses', ''))
        self.assertFalse({'tagName', 'releaseId'} & set(tauri['with']))

    def test_inventory_precedes_cleanup_and_final_verifier_keeps_python(self):
        steps = yaml.safe_load((ROOT / '.github/workflows/release.yml').read_text())['jobs']['build']['steps']
        inventory = next(i for i, s in enumerate(steps) if 'system_libraries.py inventory' in s.get('run', ''))
        cleanup = next(i for i, s in enumerate(steps) if s.get('name') == 'Libérer espace après PyInstaller (Linux)')
        self.assertLess(inventory, cleanup)
        self.assertNotIn('/opt/hostedtoolcache/Python', steps[cleanup]['run'])

    def test_microsoft_action_is_official_and_pinned(self):
        steps = yaml.safe_load((ROOT / '.github/workflows/release.yml').read_text())['jobs']['build']['steps']
        actions = [s for s in steps if s.get('uses', '').startswith('Azure/artifact-signing-action@')]
        self.assertEqual(len(actions), 2)
        for step in actions:
            self.assertRegex(step['uses'].split('@')[1], r'^[a-f0-9]{40}$')
            self.assertIn('pyd', step['with']['files-folder-filter'])
            self.assertIn('windows-signing.outputs.enabled', step['if'])

    def test_licenses_are_resources_on_all_platforms(self):
        base = ROOT / 'src/frontend/src-tauri'
        for name in ['tauri.conf.json', 'tauri.linux.conf.json']:
            resources = json.loads((base / name).read_text())['bundle']['resources']
            self.assertIsInstance(resources, dict)
            self.assertEqual(resources['../../../THIRD_PARTY_LICENSES'], 'THIRD_PARTY_LICENSES')

    def test_publication_refuses_incomplete_platform(self):
        import tempfile
        spec = importlib.util.spec_from_file_location('publish', ROOT / 'scripts/publish_release_artifacts.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'dmg').mkdir()
            (root / 'dmg/test.dmg').write_bytes(b'dmg')
            with self.assertRaises(ValueError):
                module.artifacts(root, 'macOS')
            (root / 'macos').mkdir()
            (root / 'macos/test.app.tar.gz').write_bytes(b'archive')
            self.assertEqual(len(module.artifacts(root, 'macOS')), 2)

    def test_license_fingerprints_are_stable_on_windows_checkout(self):
        import subprocess
        paths = ['package-lock.json', 'src/frontend/package-lock.json',
                 'src/frontend/src-tauri/Cargo.lock', 'uv.lock',
                 'licenses/overrides.json', 'licenses/native-components.lock.json',
                 'licenses/runtime-wheels.lock.json', 'THIRD_PARTY_LICENSES',
                 'licenses/system-libraries.lock.json', 'licenses/system-linux/readline.copyright',
                 'licenses/LISEZMOI-SOURCES.txt']
        result = subprocess.run(['git', 'check-attr', '-z', 'eol', '--', *paths],
                                cwd=ROOT, text=True, capture_output=True, check=True)
        values = result.stdout.split('\0')[2::3]
        self.assertEqual(values, ['lf'] * len(paths))

    def test_windows_no_secrets_never_enables_sign_command(self):
        spec = importlib.util.spec_from_file_location('prepare', ROOT / 'scripts/prepare_windows_signing.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.configuration({}, Path('test.ps1')), (False, {}))
        self.assertEqual(module.configuration({'AZURE_CLIENT_ID': 'test'}, Path('test.ps1')), (False, {}))
        enabled, config = module.configuration(dict.fromkeys(module.SECRETS, 'test'), Path('space here/test.ps1'))
        self.assertTrue(enabled)
        self.assertEqual(config['bundle']['windows']['signCommand']['args'][-2:], ['space here/test.ps1', '%1'])


if __name__ == '__main__':
    unittest.main()
