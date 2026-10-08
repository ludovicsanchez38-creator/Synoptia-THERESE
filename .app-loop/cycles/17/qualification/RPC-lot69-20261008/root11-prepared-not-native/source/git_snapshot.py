"""Git physique en lecture seule. Aucun import G1, fork ou écriture.

Le snapshot doit être émis/épinglé par root avant admission. Son champ
provided_by n'authentifie pas root. Les références/binding externes le font.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import stat

SCHEMA = 'c17-wrapper-physical-git-snapshot-v1'


def need(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def read_regular(path: Path) -> bytes:
    need(path.is_absolute() and path.resolve(strict=True) == path, 'Chemin Git non canonique')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        before = os.fstat(stream.fileno())
        need(stat.S_ISREG(before.st_mode), 'Référence Git non régulière')
        raw = stream.read()
        after = os.fstat(stream.fileno())
        named = path.lstat()
        need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
             (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) and
             (named.st_dev, named.st_ino) == (before.st_dev, before.st_ino), 'Référence Git changée')
        return raw


def reference(path: Path) -> dict:
    raw = read_regular(path)
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def checked(reference_: dict) -> bytes:
    need(type(reference_) is dict and set(reference_) == {'path', 'sha256', 'bytes'}, 'Référence Git exacte requise')
    path = Path(reference_['path'])
    need(path.is_relative_to('/private/tmp') and any(part.startswith('therese-c17-') for part in path.parts), 'Référence hors QA')
    raw = read_regular(path)
    need(hashlib.sha256(raw).hexdigest() == reference_['sha256'] and len(raw) == reference_['bytes'], 'Référence Git SHA/bytes divergente')
    return raw


def object_id(kind: bytes, payload: bytes) -> str:
    return hashlib.sha1(kind + b' ' + str(len(payload)).encode() + b'\0' + payload).hexdigest()


def parse_tree(raw: bytes) -> list[tuple[str, str, bytes]]:
    need(raw.endswith(b'\0') and raw, 'Arbre Git nul/terminaison absente')
    entries, names = [], set()
    for entry in raw[:-1].split(b'\0'):
        description, name = entry.split(b'\t', 1)
        mode, kind, blob = description.decode('ascii').split()
        parts = name.split(b'/')
        need(mode in {'100644', '100755', '120000'} and kind == 'blob' and
             re.fullmatch('[0-9a-f]{40}', blob) is not None and
             all(part not in {b'', b'.', b'..'} for part in parts) and name not in names,
             'Mode/blob/chemin Git invalide ou doublon')
        names.add(name)
        entries.append((mode, blob, name))
    return entries


def tree_id(raw: bytes) -> str:
    """Reconstruit les objets tree depuis le ls-tree récursif exact, sans Git."""
    trie = {}
    for mode, blob, name in parse_tree(raw):
        node = trie
        parts = name.split(b'/')
        for part in parts[:-1]:
            node = node.setdefault(part, {})
            need(type(node) is dict, 'Fichier/répertoire Git en collision')
        need(parts[-1] not in node, 'Chemin Git en collision')
        node[parts[-1]] = (mode, blob)

    def encode(node: dict) -> str:
        entries = []
        for name, item in node.items():
            if type(item) is dict:
                mode, oid, key = b'40000', encode(item), name + b'/'
            else:
                mode, oid, key = item[0].encode(), item[1], name
            entries.append((key, mode + b' ' + name + b'\0' + bytes.fromhex(oid)))
        return object_id(b'tree', b''.join(value for _, value in sorted(entries)))
    return encode(trie)


class GitSnapshot:
    def __init__(self, snapshot_ref: dict, source: Path):
        self.snapshot_ref = dict(snapshot_ref)
        self.source = Path(source)
        self.data = json.loads(checked(snapshot_ref))
        need(self.data.get('schema') == SCHEMA and self.data.get('source_root') == str(self.source)
             and self.source.resolve(strict=True) == self.source
             and self.source.is_relative_to('/private/tmp'), 'Snapshot Git autre source/schéma')
        self.recheck()

    def recheck(self) -> str:
        need(json.loads(checked(self.snapshot_ref)) == self.data, 'Snapshot remplacé')
        head = checked(self.data['head_stdout']).decode('ascii').strip()
        need(re.fullmatch('[0-9a-f]{40}', head) is not None and head == self.data['head'], 'HEAD Git divergent')
        commit = checked(self.data['commit_raw'])
        raw = checked(self.data['tree_raw'])
        need(object_id(b'commit', commit) == head and commit.split(b'\n', 1)[0] ==
             b'tree ' + tree_id(raw).encode(), 'Commit/arbre Git non liés cryptographiquement')
        refs = self.data['physical_refs']
        need(type(refs) is list and refs and refs[0]['path'] == str(self.source / '.git/HEAD'), 'HEAD physique absent')
        values = [checked(item).decode('ascii').strip() for item in refs]
        for index, value in enumerate(values[:-1]):
            need(value.startswith('ref: refs/') and '..' not in Path(value[5:]).parts
                 and refs[index + 1]['path'] == str(self.source / '.git' / value[5:]), 'Chaîne refs Git divergente')
        need(values[-1] == head, 'HEAD physique changé ; aucun fallback packed/Git')
        return head

    def tree(self) -> bytes:
        self.recheck()
        return checked(self.data['tree_raw'])

    def verify_worktree(self) -> dict:
        """Vérifie aussi payload, lien et bit exécutable ; n'écrit aucune copie."""
        before = self.recheck()
        observed = {}
        for mode, blob, name in parse_tree(self.tree()):
            path = self.source / os.fsdecode(name)
            for parent in path.parents:
                if parent == self.source:
                    break
                need(not parent.is_symlink(), 'Parent Git symlink')
            info = path.lstat()
            if mode == '120000':
                need(stat.S_ISLNK(info.st_mode), 'Lien Git remplacé')
                payload = os.fsencode(os.readlink(path))
                need(not Path(os.fsdecode(payload)).is_absolute() and
                     (path.parent / os.fsdecode(payload)).resolve().is_relative_to(self.source), 'Lien Git sortant')
            else:
                payload = read_regular(path)
                need(bool(info.st_mode & 0o111) == (mode == '100755'), 'Mode exécutable Git différent')
            need(object_id(b'blob', payload) == blob, 'Blob courant différent de HEAD : ' + os.fsdecode(name))
            observed[os.fsdecode(name)] = {'git_blob': blob, 'mode': mode, 'sha256': hashlib.sha256(payload).hexdigest()}
        need(self.recheck() == before, 'HEAD changé pendant vérification')
        return observed


def from_environment(source: Path) -> GitSnapshot:
    return GitSnapshot(json.loads(os.environ['C17_AUX_GIT_SNAPSHOT_REF']), source)
