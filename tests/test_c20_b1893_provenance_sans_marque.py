"""Une provenance absente ne prouve pas l'absence de document."""

from types import SimpleNamespace

import pytest
from app.models.entities import Message
from app.services.provenance_documents import marque_reponse, memoriser_provenance, origine_contexte


@pytest.mark.parametrize('context', [
    SimpleNamespace(messages=[]),
    SimpleNamespace(messages=[], contient_documents=None, documents_averes=False),
], ids=['attribut-absent', 'valeur-inconnue'])
def test_reponse_sans_information_documentaire_reste_prudente(context):
    message = Message(role='assistant', content='Réponse de test', conversation_id='conversation')
    assert origine_contexte(context) == 'documents'
    assert memoriser_provenance(message, marque_reponse(context)) == 'documents'
