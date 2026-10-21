"""Oracles de budget en octets : Unicode, outils, documents et repli."""
from types import SimpleNamespace

import pytest
from app.services.context import ContextWindow
from app.services.providers.base import LLMProvider, Message


def config(fenetre=5000):
    return SimpleNamespace(provider=LLMProvider.OPENAI, model='factice', max_tokens=100, context_window=fenetre)


def carte(contenu='Préférence entière 😀', kind='preference', identifiant='p'):
    return {'id': identifiant, 'kind': kind, 'title': 'Titre', 'content': contenu, 'reason': '', 'version': 1}


def test_borne_utf8_outils_et_frontiere_exacte():
    from app.services.memory_card_context import borner_payload, compter_payload
    c = ContextWindow(messages=[Message(role='user', content='é😀')], system_prompt='Système')
    outils = [{'type': 'function', 'function': {'name': 'f', 'parameters': {'type': 'object'}}}]
    borner_payload(c, [carte()], config(), outils)
    minimum = compter_payload(c, config(), outils)
    assert minimum >= len('é😀'.encode())
    juste = config(minimum + 100)
    c2 = ContextWindow(messages=[Message(role='user', content='é😀')], system_prompt='Système')
    borner_payload(c2, [carte()], juste, outils)
    assert compter_payload(c2, juste, outils) == minimum
    with pytest.raises(Exception, match='fenêtre'):
        c3 = ContextWindow(messages=[Message(role='user', content='é😀')], system_prompt='Système')
        borner_payload(c3, [carte()], config(minimum + 99), outils)


def test_documents_trop_longs_et_quota_souple_preservent_correction_et_histoire():
    from app.services.memory_card_context import borner_payload, compter_payload
    c = ContextWindow(messages=[Message(role='user', content='passé'), Message(role='assistant', content='réponse'),
                                Message(role='user', content='demande')], system_prompt='Identité')
    c.memory_documents = 'Document volumineux ' * 2000
    borner_payload(c, [carte(kind='correction'), carte('Fait ' * 500, kind='fait', identifiant='f')], config(2000), [])
    assert 'Préférence entière 😀' in c.system_prompt
    assert len(c.messages) == 3
    assert len(c.system_prompt) < 2000
    assert c.memory_used == ['p']
    assert compter_payload(c, config(2000), []) <= 1900
    with pytest.raises(Exception, match='fenêtre'):
        borner_payload(c, [carte('Très long ' * 150, kind='correction')], config(1000), [])
