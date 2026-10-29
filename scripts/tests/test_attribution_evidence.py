"""Le statut sans titulaire doit être prouvé par les octets, pas un booléen."""
import io
import json
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
import third_party_licenses as licenses  # noqa: E402


class AbsenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.links = {}
        self.commit = 'a' * 40
        self.crate = {'crate/.cargo_vcs_info.json': json.dumps({
            'git': {'sha1': self.commit}, 'path_in_vcs': 'framework-crates/example'}).encode(),
            'crate/Cargo.toml': b'[package]\nname="example"\nversion="1"\n',
            'crate/Cargo.toml.orig': b'[package]\nname="example"\nversion="1"\n',
            'crate/src/lib.rs': b'pub fn example() {}\n'}
        self.tree = {'repo/Cargo.toml': b'[workspace.package]\nauthors=["Mads Marquart <mads@marquart.dk>"]\n',
                     'repo/LICENSE.md': b'This project is licensed under MIT.\n',
                     'repo/framework-crates/example/src/lib.rs': b'pub fn example() {}\n'}
        self.row = {'id': 'cargo:example@1', 'artifact': 'https://example.test/crate',
                    'license': 'MIT', 'attribution_missing': True,
                    'attribution_status': 'no-holder-named-upstream',
                    'notices': [{'path': 'LICENSE.md', 'text': self.tree['repo/LICENSE.md'].decode().strip()},
                                {'path': 'MIT', 'text': (licenses.ROOT / 'licenses/supplements/MIT.txt').read_text().strip()}]}

    def archive(self, name, files):
        with tarfile.open(self.root / name, 'w:gz') as out:
            for path, data in files.items():
                member = tarfile.TarInfo(path)
                member.size = len(data)
                out.addfile(member, io.BytesIO(data))
            if name == 'tree.tar.gz':
                for path, target in self.links.items():
                    member = tarfile.TarInfo(path)
                    member.type = tarfile.SYMTYPE
                    member.linkname = target
                    out.addfile(member)
        return licenses.digest((self.root / name).read_bytes())

    def proof(self):
        # Le constructeur ne décide pas de l'acceptation : le validateur rescane.
        import attribution_evidence as evidence
        crate_hash = self.archive('crate.tar.gz', self.crate)
        self.archive('tree.tar.gz', self.tree)
        self.row['integrity'] = 'sha256:' + crate_hash
        return evidence.record(self.row, self.root, 'crate.tar.gz', 'tree.tar.gz',
                               'https://example.test/tree/' + self.commit, self.commit)

    def validate(self, proof):
        # Les tests du scan autorisent explicitement leur archive synthétique.
        # Les tests de la politique, plus bas, n'installent pas cette exception.
        import attribution_evidence as evidence
        allowed = {('example', '1', self.commit): licenses.digest((self.root / 'tree.tar.gz').read_bytes())}
        with patch.object(evidence, 'ALLOWED_ABSENCES', allowed, create=True):
            licenses.validate_inventory([self.row], [self.row], attribution_sources=proof, root=self.root)

    def test_status_without_proof_is_rejected(self):
        self.row['integrity'] = 'sha256:' + 'b' * 64
        with self.assertRaises(ValueError):
            licenses.validate_inventory([self.row], [self.row], root=self.root)

    def test_exact_proof_is_accepted(self):
        proof = self.proof()
        self.validate([proof])
        import attribution_evidence as evidence
        with patch.object(evidence, 'ALLOWED_ABSENCES', {('example', '1', self.commit): proof['tree_sha256']}, create=True):
            output = licenses.render([self.row], 'hash', attribution_sources=[proof], root=self.root)
        self.assertNotIn('PROVISOIRE', output.splitlines()[0])
        self.assertIn("Aucun titulaire n'est nommé par le projet amont au commit " + self.commit, output)
        self.assertGreater(output.index("Aucun titulaire n'est nommé"),
                           output.index(self.row['notices'][1]['text']))

    def test_relecture_example_is_rejected_even_with_well_formed_proof(self):
        proof = self.proof()
        with self.assertRaises(ValueError):
            licenses.validate_inventory([self.row], [self.row], attribution_sources=[proof], root=self.root)

    def test_cargo_identity_must_match_both_manifests(self):
        for manifest in ('Cargo.toml', 'Cargo.toml.orig'):
            for field, value in (('name', 'other'), ('version', '2')):
                with self.subTest(manifest=manifest, field=field):
                    path = 'crate/' + manifest
                    original = self.crate[path]
                    self.crate[path] = original.replace(
                        (f'{field}="' + ('example' if field == 'name' else '1') + '"').encode(),
                        f'{field}="{value}"'.encode())
                    with self.assertRaises(ValueError):
                        self.validate([self.proof()])
                    self.crate[path] = original

    def test_reference_tree_hash_cannot_be_replaced_by_recomputed_proof(self):
        import attribution_evidence as evidence
        original = self.proof()
        self.tree['repo/extra'] = b'no attribution here'
        proof = self.proof()
        allowed = {('example', '1', self.commit): original['tree_sha256']}
        with patch.object(evidence, 'ALLOWED_ABSENCES', allowed, create=True), self.assertRaises(ValueError):
            licenses.validate_inventory([self.row], [self.row], attribution_sources=[proof], root=self.root)

    def test_cargo_inherited_version_is_resolved_from_verified_tree(self):
        self.crate['crate/Cargo.toml.orig'] = b'[package]\nname="example"\nversion.workspace=true\n'
        self.tree['repo/Cargo.toml'] += b'version="1"\n'
        self.validate([self.proof()])
        self.tree['repo/Cargo.toml'] = self.tree['repo/Cargo.toml'].replace(b'version="1"', b'version="2"')
        with self.assertRaises(ValueError):
            self.validate([self.proof()])

    def test_attribution_in_archive_or_tree_rejects_even_updated_hashes(self):
        for scope in ('crate', 'tree'):
            for marker in ('Copyright 2026 Alice', '© 2026 Alice', '(c) 2026 Alice',
                           '(C) Alice', 'SPDX-FileCopyrightText: 2026 Alice', 'Authors: Alice'):
                with self.subTest(scope=scope, marker=marker):
                    files = self.crate if scope == 'crate' else self.tree
                    path = 'crate/OTHER' if scope == 'crate' else 'repo/framework-crates/example/OTHER'
                    files[path] = marker.encode()
                    with self.assertRaises(ValueError):
                        self.validate([self.proof()])
                    del files[path]

    def test_linked_generated_sources_are_part_of_the_crate(self):
        self.links['repo/framework-crates/example/src/generated'] = '../../../generated/Example'
        self.tree['repo/generated/Example/lib.rs'] = b'pub fn example() {}'
        self.validate([self.proof()])
        self.tree['repo/generated/Example/lib.rs'] = b'Copyright 2026 Alice'
        with self.assertRaises(ValueError):
            self.validate([self.proof()])

    def test_authors_in_either_cargo_manifest_reject(self):
        for name in ('Cargo.toml', 'Cargo.toml.orig'):
            with self.subTest(name=name):
                path = 'crate/' + name
                original = self.crate[path]
                self.crate[path] += b'authors = ["Alice"]\n'
                with self.assertRaises(ValueError):
                    self.validate([self.proof()])
                self.crate[path] = original

    def test_relecture_author_lists_in_archive_and_tree_are_not_prose(self):
        self.validate([self.proof()])
        fixtures = [('AUTHORS', 'Authors\nAlice\n'), ('AUTHORS', '/// Authors: Alice\n')]
        fixtures += [(filename, 'Alice\n') for filename in ('AUTHORS', 'CONTRIBUTORS', 'MAINTAINERS')]
        fixtures += [('src/credits.rs', prefix + 'Authors: Alice\n')
                     for prefix in ('/// ', '//! ', '# ', '* ')]
        fixtures += [('README.md', 'Authors\nAlice\n')]
        for scope in ('crate', 'tree'):
            for filename, text in fixtures:
                with self.subTest(scope=scope, filename=filename, text=text):
                    files = self.crate if scope == 'crate' else self.tree
                    path = ('crate/' if scope == 'crate' else 'repo/framework-crates/example/') + filename
                    files[path] = text.encode()
                    with self.assertRaises(ValueError):
                        self.validate([self.proof()])
                    del files[path]

    def test_tampered_proof_archive_tree_commit_count_and_notice_reject(self):
        for kind in ('archive', 'tree', 'commit', 'count', 'notice'):
            with self.subTest(kind=kind):
                proof = self.proof()
                if kind in ('archive', 'tree'):
                    path = self.root / ('crate.tar.gz' if kind == 'archive' else 'tree.tar.gz')
                    path.write_bytes(path.read_bytes() + b'tampered')
                elif kind == 'commit':
                    proof['commit'] = 'f' * 40
                elif kind == 'count':
                    proof['archive_scan']['files_read'] += 1
                else:
                    proof['notices'][0]['sha256'] = '0' * 64
                with self.assertRaises(ValueError):
                    self.validate([proof])


class RealAbsenceTests(unittest.TestCase):
    def test_nine_real_triplets_still_pass_without_test_exception(self):
        import attribution_evidence as evidence
        root = SCRIPTS.parent
        rows = {r['id']: r for r in json.loads((root / licenses.INVENTORY).read_text())['packages']}
        proofs = [p for p in json.loads((root / 'licenses/attribution-sources.json').read_text())
                  if p.get('status') == evidence.STATUS]
        self.assertEqual(len(proofs), 9)
        self.assertEqual(len(evidence.ALLOWED_ABSENCES), 9)
        for proof in proofs:
            with self.subTest(package=proof['package']):
                self.assertTrue(evidence.accepted(rows[proof['package']], [proof], root))


if __name__ == '__main__':
    unittest.main()
