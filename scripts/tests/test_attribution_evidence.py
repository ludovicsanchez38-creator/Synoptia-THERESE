"""Le statut sans titulaire doit être prouvé par les octets, pas un booléen."""
import io
import json
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

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
        licenses.validate_inventory([self.row], [self.row], attribution_sources=proof, root=self.root)

    def test_status_without_proof_is_rejected(self):
        self.row['integrity'] = 'sha256:' + 'b' * 64
        with self.assertRaises(ValueError):
            self.validate([])

    def test_exact_proof_is_accepted(self):
        proof = self.proof()
        self.validate([proof])
        output = licenses.render([self.row], 'hash', attribution_sources=[proof], root=self.root)
        self.assertNotIn('PROVISOIRE', output.splitlines()[0])
        self.assertIn("Aucun titulaire n'est nommé par le projet amont au commit " + self.commit, output)

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


if __name__ == '__main__':
    unittest.main()
