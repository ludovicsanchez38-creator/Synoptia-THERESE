"""Extension d'instrument préparée : lie chaque nouvel artefact au nodeid réel.

Non exécutée. À charger comme plugin uniquement par le runner SQLCipher privé
relu root. Aucun ancien PDF, UUID ou nodeid n'est attribué rétroactivement.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import pytest

@pytest.fixture(autouse=True)
def lier_export_au_cas(request, monkeypatch):
    if request.node.module.__name__.split('.')[-1] != 'test_b1760_echeance_mentions':
        yield
        return
    actor = os.environ['C16_ACTOR']
    round_id = os.environ['C16_ROUND_ID']
    assert actor == '/root'
    assert round_id
    head = os.environ['C16_EXECUTION_HEAD']
    assert head == '2d69e30c9c6dd18823ee6102271876003a6a67cc'
    assert Path.home().resolve().is_relative_to(Path('/private/tmp'))
    module = request.node.module
    original = module._dossier_preuve
    module_path = Path(module.__file__).resolve()
    module_sha = hashlib.sha256(module_path.read_bytes()).hexdigest()
    def observed(identifier, nature):
        destination = original(identifier, nature)
        if destination is not None:
            module._base_chiffree()
            database_path = Path(module.db.settings.db_path).resolve()
            assert database_path.is_relative_to(Path('/private/tmp'))
            (destination/'c16-nodeid.json').write_text(json.dumps({
                'cycle':17, 'actor':actor,'round_id':round_id,'head':head,
                'test_nodeid':request.node.nodeid,'invoice_id':identifier,'artifact_kind':nature,
                'executed_test_source':{'path':str(module_path),'sha256':module_sha},
                'sqlcipher':{'active':module.db._db_cipher_active,
                    'encrypted_header':module.db.db_is_encrypted(database_path),
                    'database_path':str(database_path)},
                'historical_case_relabelled':False, 'plateau_accepted':False,
            },ensure_ascii=False,indent=2)+'\n')
        return destination
    monkeypatch.setattr(module, '_dossier_preuve', observed)
    yield
    assert hashlib.sha256(module_path.read_bytes()).hexdigest() == module_sha
