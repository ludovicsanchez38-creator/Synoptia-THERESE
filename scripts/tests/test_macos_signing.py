"""Ordre et refus de signature testés sur Linux avec un exécuteur simulé."""
import base64
import contextlib
import importlib.util
import io
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

PEM = '-----BEGIN PRIVATE KEY-----\nZml4dHVyZQ==\n-----END PRIVATE KEY-----\n'
DEVELOPER_ID = 'Developer ID Application: SYNOPTIA (ABCDE12345)'
FIND_IDENTITY = f'  1) 0123456789ABCDEF0123456789ABCDEF01234567 "{DEVELOPER_ID}"\n     1 valid identities found\n'


class SigningTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('signing', Path(__file__).resolve().parents[1] / 'sign_macos.py')
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)

    def certificate_values(self):
        return {'APPLE_CERTIFICATE': base64.b64encode(b'certificate').decode(), 'APPLE_CERTIFICATE_PASSWORD': 'fixture',
                'APPLE_SIGNING_IDENTITY': DEVELOPER_ID, 'APPLE_TEAM_ID': 'ABCDE12345'}

    def prepare_with(self, values, td):
        """Lance prepare() avec un exécuteur simulé ; rend (appels, GITHUB_ENV, sortie, octets du P12 importé)."""
        root = Path(td)
        env_file = root / 'github-env-fixture'
        calls, imported = [], {}

        def run(args, check=True):
            args = [str(a) for a in args]
            calls.append(args)
            if args[:2] == ['security', 'import']:
                imported['p12'] = Path(args[2]).read_bytes()
            if args[:2] == ['security', 'find-identity']:
                return FIND_IDENTITY
            if args[:3] == ['xcrun', 'notarytool', 'store-credentials'] and '--key' in args:
                key = Path(args[args.index('--key') + 1])
                imported['p8'] = key.read_bytes()
                imported['p8_path'] = key
            return ''
        out = io.StringIO()
        with patch.dict(os.environ, {**values, 'RUNNER_TEMP': td, 'GITHUB_ENV': str(env_file)}, clear=True), \
                patch.object(self.m, 'run', run), contextlib.redirect_stdout(out):
            self.m.prepare()
        written = env_file.read_text() if env_file.exists() else ''
        return calls, written, out.getvalue(), imported

    def test_partial_secrets_fall_back_to_adhoc(self):
        self.assertFalse(self.m.apple_ready({}))
        self.assertFalse(self.m.apple_ready({'APPLE_CERTIFICATE': 'test'}))
        self.assertTrue(self.m.apple_ready(dict.fromkeys(self.m.APPLE_SECRETS, 'test')))

    def test_modes_api_key_preferred_apple_id_fallback(self):
        cert = dict.fromkeys(self.m.APPLE_CERTIFICATE_SECRETS, 'x')
        api = dict.fromkeys(self.m.APPLE_API_SECRETS, 'x')
        apple_id = dict.fromkeys(self.m.APPLE_ID_SECRETS, 'x')
        self.assertEqual(self.m.apple_mode({}), 'adhoc')
        self.assertEqual(self.m.apple_mode({**cert, **api}), 'api')
        self.assertEqual(self.m.apple_mode({**cert, **apple_id}), 'apple-id')
        self.assertEqual(self.m.apple_mode({**cert, **api, **apple_id}), 'api')
        self.assertEqual(self.m.apple_mode(cert), 'partiel')
        self.assertEqual(self.m.apple_mode({**api, **apple_id}), 'partiel')
        self.assertEqual(self.m.apple_mode({**cert, 'APPLE_API_KEY': 'x'}), 'partiel')

    def test_missing_secrets_names_never_values(self):
        cert = dict.fromkeys(self.m.APPLE_CERTIFICATE_SECRETS, 'valeur-secrete')
        self.assertEqual(self.m.missing_secrets(cert), list(self.m.APPLE_API_SECRETS))
        self.assertEqual(self.m.missing_secrets({**cert, 'APPLE_ID': 'valeur-secrete'}), ['APPLE_PASSWORD'])
        self.assertNotIn('valeur-secrete', ' '.join(self.m.missing_secrets({'APPLE_TEAM_ID': 'valeur-secrete'})))

    def test_wrapped_base64_certificate_is_accepted(self):
        with tempfile.TemporaryDirectory() as td:
            values = self.certificate_values()
            values.update(APPLE_CERTIFICATE='Y2VydGlm\naWNhdGU=\n', APPLE_API_KEY='KEYID12345',
                          APPLE_API_ISSUER='00000000-0000-0000-0000-000000000000', APPLE_API_PRIVATE_KEY=PEM)
            _, _, _, imported = self.prepare_with(values, td)
            self.assertEqual(imported['p12'], b'certificate')
            # Fichiers sensibles retirés une fois rangés dans le trousseau.
            self.assertFalse((Path(td) / 'therese-signing/certificate.p12').exists())

    def test_api_key_notarization_profile_and_key_file_removed(self):
        with tempfile.TemporaryDirectory() as td:
            values = {**self.certificate_values(), 'APPLE_API_KEY': 'KEYID12345',
                      'APPLE_API_ISSUER': '00000000-0000-0000-0000-000000000000',
                      'APPLE_API_PRIVATE_KEY': base64.b64encode(PEM.encode()).decode()}
            calls, written, out, imported = self.prepare_with(values, td)
            store = next(c for c in calls if c[:3] == ['xcrun', 'notarytool', 'store-credentials'])
            self.assertIn('--key-id', store)
            self.assertIn('--issuer', store)
            self.assertNotIn('--apple-id', store)
            self.assertEqual(imported['p8'], PEM.encode())
            self.assertFalse(imported['p8_path'].exists())
            self.assertIn('MACOS_NOTARIZE=true', written)
            self.assertIn(f'MACOS_SIGNING_IDENTITY={DEVELOPER_ID}', written)
            self.assertIn('clé d\'API App Store Connect', out)
            # L'identité est contrôlée avant la création du profil de notarisation.
            names = [' '.join(c[:3]) for c in calls]
            self.assertLess(names.index('security find-identity -v'), names.index('xcrun notarytool store-credentials'))

    def test_apple_id_fallback_profile(self):
        with tempfile.TemporaryDirectory() as td:
            values = {**self.certificate_values(), 'APPLE_ID': 'compte@example.invalid', 'APPLE_PASSWORD': 'fixture'}
            calls, written, _, _ = self.prepare_with(values, td)
            store = next(c for c in calls if c[:3] == ['xcrun', 'notarytool', 'store-credentials'])
            self.assertIn('--apple-id', store)
            self.assertNotIn('--key', store)
            self.assertIn('MACOS_NOTARIZE=true', written)

    def test_partial_configuration_warns_and_stays_adhoc(self):
        with tempfile.TemporaryDirectory() as td:
            calls, written, out, _ = self.prepare_with(self.certificate_values(), td)
            self.assertEqual(calls, [])
            self.assertIn('MACOS_NOTARIZE=false', written)
            self.assertIn('MACOS_SIGNING_IDENTITY=-', written)
            self.assertIn('::warning', out)
            self.assertIn('APPLE_API_PRIVATE_KEY', out)
            self.assertNotIn(DEVELOPER_ID, out)

    def test_signature_obligatoire_refuses_adhoc_and_partial(self):
        for values in ({}, self.certificate_values()):
            with self.subTest(secrets=sorted(values)), tempfile.TemporaryDirectory() as td, self.assertRaises(ValueError):
                self.prepare_with({**values, 'SIGNATURE_OBLIGATOIRE': 'true'}, td)

    def test_no_secret_is_adhoc_without_warning(self):
        with tempfile.TemporaryDirectory() as td:
            calls, written, out, _ = self.prepare_with({}, td)
            self.assertEqual(calls, [])
            self.assertIn('MACOS_NOTARIZE=false', written)
            self.assertNotIn('::warning', out)

    def test_api_key_formats(self):
        self.assertEqual(self.m.decode_api_key(PEM), PEM.encode())
        self.assertEqual(self.m.decode_api_key(base64.b64encode(PEM.encode()).decode()), PEM.encode())
        for value in ('pas une clé', base64.b64encode(b'autre chose').decode()):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.m.decode_api_key(value)

    def test_identity_must_be_developer_id_application(self):
        self.m.check_identity('k', DEVELOPER_ID, run=lambda a, check=True: FIND_IDENTITY)
        self.m.check_identity('k', '0123456789abcdef0123456789abcdef01234567', run=lambda a, check=True: FIND_IDENTITY)
        development = '  1) 0123 "Apple Development: Ludo (ABCDE12345)"\n'
        with self.assertRaises(ValueError):
            self.m.check_identity('k', 'Apple Development: Ludo (ABCDE12345)', run=lambda a, check=True: development)
        with self.assertRaises(ValueError):
            self.m.check_identity('k', 'Developer ID Application: AUTRE (ZZZZZ99999)', run=lambda a, check=True: FIND_IDENTITY)

    def test_sign_inside_out_then_verify_each_binary(self):
        with tempfile.TemporaryDirectory() as td:
            app = Path(td) / 'Example.app'
            lib = app / 'Contents/Resources/python/lib.so'
            binary = app / 'Contents/MacOS/example'
            for p in [lib, binary]:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(bytes.fromhex('cffaedfe') + b'test')
            (lib.parent / 'alias.so').symlink_to(lib.name)
            calls = []
            self.m.sign_tree(app, '-', Path('entitlements.plist'), run=lambda args, check=True: calls.append(args))
            signed = [c[-1] for c in calls if '--sign' in c]
            self.assertEqual(signed, [str(lib), str(binary), str(app)])
            self.assertEqual(sum('--verify' in c for c in calls), 3)
            self.assertTrue(all('--options' in c and 'runtime' in c and '--entitlements' in c for c in calls if '--sign' in c))
            self.assertFalse(any('--deep' in c for c in calls if '--sign' in c))

    def test_rejected_notarization_never_staples(self):
        calls = []
        def run(args, check=True):
            calls.append(args)
            return '{"status":"Invalid"}'
        with self.assertRaises(RuntimeError):
            self.m.notarize(Path('app.dmg'), run=run)
        self.assertFalse(any('stapler' in c for c in calls))

    def test_rejection_prints_apple_log_without_raising_on_exit_code(self):
        calls = []
        def run(args, check=True):
            calls.append((args, check))
            if 'submit' in args:
                return '{"id":"0000-fixture","status":"Invalid"}'
            return '{"statusSummary":"Archive contains critical validation errors","issues":[{"severity":"error","path":"THERESE.app/Contents/MacOS/backend","message":"The signature does not include a secure timestamp."}]}'
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(RuntimeError):
            self.m.notarize(Path('app.dmg'), run=run)
        self.assertIn('secure timestamp', out.getvalue())
        self.assertTrue(any('log' in a and '0000-fixture' in a for a, _ in calls))
        # Le statut se lit même quand notarytool sort en erreur.
        self.assertTrue(all(check is False for a, check in calls if 'submit' in a or 'log' in a))
        self.assertFalse(any('stapler' in a for a, _ in calls))

    def test_acceptance_staples_and_validates(self):
        calls = []
        def run(args, check=True):
            calls.append(args)
            return '{"status":"Accepted"}'
        self.m.notarize(Path('app.dmg'), run=run)
        self.assertTrue(any('staple' in c for c in calls))
        self.assertTrue(any('validate' in c for c in calls))

    def test_distribution_signature_requires_developer_id_and_team(self):
        good = f'Executable=x\nAuthority={DEVELOPER_ID}\nAuthority=Developer ID Certification Authority\nTimestamp=3 nov. 2026\nTeamIdentifier=ABCDE12345\nflags=0x10000(runtime)\n'
        self.m.check_distribution_signature(Path('THERESE.app'), 'ABCDE12345', run=lambda a, check=True: good)
        for details, team in (('Signature=adhoc\nTeamIdentifier=not set\n', 'ABCDE12345'),
                              (good.replace('ABCDE12345', 'ZZZZZ99999'), 'ABCDE12345'),
                              (good.replace('flags=0x10000(runtime)', 'flags=0x0(none)'), 'ABCDE12345')):
            with self.subTest(details=details[:30]), self.assertRaises(RuntimeError):
                self.m.check_distribution_signature(Path('THERESE.app'), team, run=lambda a, check=True, d=details: d)

    def test_updater_archive_is_checked_after_extraction(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / 'src'
            (source / 'THERESE.app/Contents').mkdir(parents=True)
            (source / 'THERESE.app/Contents/Info.plist').write_text('fixture')
            archive = Path(td) / 'THERESE.app.tar.gz'
            subprocess.run(['tar', '-czf', str(archive), '-C', str(source), 'THERESE.app'], check=True)
            for notarized in (True, False):
                calls = []

                def run(args, check=True, calls=calls):
                    args = [str(a) for a in args]
                    if args[0] == 'tar':
                        subprocess.run(args, check=True)
                    else:
                        calls.append(args)
                    return ''
                with self.subTest(notarized=notarized), patch.dict(os.environ, {'RUNNER_TEMP': td}), \
                        contextlib.redirect_stdout(io.StringIO()):
                    self.m.check_updater_archive(archive, notarized, run=run)
                    verified = [c for c in calls if c[0] == 'codesign']
                    self.assertTrue(verified and verified[0][-1].endswith('THERESE.app'))
                    self.assertEqual(any(c[:3] == ['xcrun', 'stapler', 'validate'] for c in calls), notarized)
                    self.assertEqual(any(c[0] == 'spctl' for c in calls), notarized)

    def test_finish_notarized_order_app_then_dmg_then_updater_archive(self):
        details = f'Authority={DEVELOPER_ID}\nTimestamp=3 nov. 2026\nTeamIdentifier=ABCDE12345\nflags=0x10000(runtime)\n'
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td) / 'bundle'
            app = bundle / 'macos/THERESE.app'
            (app / 'Contents/MacOS').mkdir(parents=True)
            (app / 'Contents/MacOS/therese').write_bytes(bytes.fromhex('cffaedfe') + b'gui')
            (bundle / 'dmg').mkdir()
            (bundle / 'dmg/THERESE_0.0.0_aarch64.dmg').write_bytes(b'ancien dmg')
            (bundle / 'macos/THERESE.app.tar.gz').write_bytes(b'ancienne archive')
            calls = []

            def run(args, check=True):
                args = [str(a) for a in args]
                calls.append(args)
                if args[0] == 'tar':
                    subprocess.run(args, check=True)
                if 'submit' in args:
                    return '{"id":"fixture","status":"Accepted"}'
                if args[0] == 'codesign' and '--display' in args:
                    return details
                return ''
            env = {'MACOS_SIGNING_IDENTITY': DEVELOPER_ID, 'MACOS_NOTARIZE': 'true',
                   'MACOS_SIGNING_TEAM_ID': 'ABCDE12345', 'MACOS_SIGNING_KEYCHAIN': 'k', 'RUNNER_TEMP': td}
            with patch.dict(os.environ, env, clear=True), patch.object(self.m, 'run', run), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.m.finish(bundle)
            flat = [' '.join(c) for c in calls]

            def first(fragment, after=-1):
                return next(i for i, c in enumerate(flat) if i > after and fragment in c)
            submit_app = first('notarytool submit')
            self.assertIn('notarization.zip', flat[submit_app])
            staple_app = first('stapler staple', submit_app)
            self.assertTrue(flat[staple_app].endswith('THERESE.app'))
            dmg = first('hdiutil create', staple_app)
            submit_dmg = first('notarytool submit', dmg)
            self.assertIn('.dmg', flat[submit_dmg])
            archive = first('tar -czf', submit_dmg)
            self.assertTrue(flat[archive].endswith('THERESE.app'))
            # L'archive updater est relue après sa création : bundle agrafé.
            first('stapler validate', archive)
            self.assertNotEqual((bundle / 'macos/THERESE.app.tar.gz').read_bytes(), b'ancienne archive')

    def test_empty_updater_archive_fails(self):
        with tempfile.TemporaryDirectory() as td:
            empty = Path(td) / 'vide'
            empty.mkdir()
            archive = Path(td) / 'vide.tar.gz'
            subprocess.run(['tar', '-czf', str(archive), '-C', str(empty), '.'], check=True)
            def run(args, check=True):
                if str(args[0]) == 'tar':
                    subprocess.run([str(a) for a in args], check=True)
                return ''
            with patch.dict(os.environ, {'RUNNER_TEMP': td}), self.assertRaises(RuntimeError):
                self.m.check_updater_archive(archive, True, run=run)


class RecetteContractTests(unittest.TestCase):
    def test_recette_expects_exactly_the_versioned_entitlements(self):
        # Run 42360779924 : le micro ajouté à Entitlements.plist le 29/10 n'était
        # pas dans le contrat de la recette, qui refusait la signature effective.
        import plistlib
        root = Path(__file__).resolve().parents[2]
        spec = importlib.util.spec_from_file_location('recette', root / 'scripts/recette-macos.py')
        recette = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(recette)
        with (root / 'src/frontend/src-tauri/Entitlements.plist').open('rb') as f:
            self.assertEqual(recette.DROITS_ATTENDUS, plistlib.load(f))
        self.assertNotIn('com.apple.security.cs.allow-jit', recette.DROITS_ATTENDUS)
        self.assertNotIn('com.apple.security.cs.allow-unsigned-executable-memory', recette.DROITS_ATTENDUS)

if __name__ == '__main__':
    unittest.main()
