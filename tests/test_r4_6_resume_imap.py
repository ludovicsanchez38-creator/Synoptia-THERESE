"""Les listes IMAP ne chargent plus les corps ; le résumé doit les relire."""
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.services import workspace_tools
from app.services.email.imap_smtp_provider import ImapSmtpProvider


@pytest.mark.asyncio
async def test_resume_charge_le_corps_du_seul_mail_selectionne(db_session, monkeypatch):
    provider = ImapSmtpProvider('moi@example.test', 'fictif', 'imap.example.test')
    entete = SimpleNamespace(id='Sent::42', subject='Atelier', from_name=None, from_email='camille@example.test', date=None, body_plain=None, snippet=None)
    complet = SimpleNamespace(**(vars(entete) | {'body_plain': 'Le mot de rendez-vous fictif est LIBELLULE-VERTE.'}))
    monkeypatch.setattr(provider, 'list_messages', AsyncMock(return_value=([entete], None)))
    lecture = AsyncMock(return_value=complet)
    monkeypatch.setattr(provider, 'get_message', lecture)
    monkeypatch.setattr(workspace_tools, '_get_email_provider', AsyncMock(return_value=(provider, None)))
    generation = AsyncMock(return_value='Résumé fictif.')
    from app.services import llm
    monkeypatch.setattr(llm, 'get_llm_service', lambda: SimpleNamespace(generate_content=generation))
    resultat = await workspace_tools._summarize_emails({}, db_session)
    assert resultat == 'Résumé fictif.'
    lecture.assert_awaited_once_with('Sent::42')
    prompt = generation.await_args.kwargs['prompt']
    assert 'LIBELLULE-VERTE' in prompt
    assert '[Source: email]' in prompt
