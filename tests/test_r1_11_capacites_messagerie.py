"""R1-11 : le système décrit uniquement les accès réellement branchés."""
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.models.entities import EmailAccount
from app.services.llm import LLMService
from app.services.providers.base import LLMConfig, LLMProvider, StreamEvent


@pytest.mark.asyncio
@pytest.mark.parametrize('branchee', [False, True])
async def test_outils_et_prompt_suivent_la_messagerie(client, db_session, monkeypatch, branchee):
    from app.routers import chat
    if branchee:
        db_session.add(EmailAccount(email='recette@example.invalid', provider='imap', imap_host='imap.invalid', imap_password='factice', smtp_host='smtp.invalid'))
        await db_session.commit()
    captures = []
    class Fournisseur:
        async def stream(self, system_prompt, messages, tools, **kwargs):
            captures.append((system_prompt, tools))
            yield StreamEvent(type='text', content='Je peux rédiger ton texte.')
            yield StreamEvent(type='done', stop_reason='end_turn')
    llm = LLMService(LLMConfig(LLMProvider.OLLAMA, 'factice'), bascule_circuit=False)
    llm._provider = Fournisseur()
    mcp = MagicMock()
    mcp.get_tools_for_llm.return_value = []
    monkeypatch.setattr(chat, 'get_llm_service', lambda: llm)
    monkeypatch.setattr(chat, 'get_mcp_service', lambda: mcp)
    monkeypatch.setattr(chat, 'web_tools', lambda: [])
    monkeypatch.setattr(chat, '_extract_entities_background', AsyncMock())
    reponse = await client.post('/api/chat/send', json={'message': 'Que peux-tu faire avec mes mails ?', 'stream': True, 'include_memory': False})
    assert reponse.status_code == 200
    assert captures, reponse.text
    prompt, outils = captures[0]
    noms = {o['function']['name'] for o in outils}
    assert {'list_tasks', 'create_task', 'create_invoice'} <= noms
    assert 'Pour les factures et devis, utilise create_invoice' in prompt
    assert ('read_emails' in noms) is branchee
    assert ('send_email' in noms) is branchee
    assert ('Aucune boîte mail' in prompt) is not branchee
