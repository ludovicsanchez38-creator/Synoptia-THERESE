"""R1-4 : le résultat de la confirmation est destiné au fil et à son aperçu."""
import json
from unittest.mock import AsyncMock

import pytest
from app.services.tool_confirmations import register_pending


@pytest.mark.asyncio
@pytest.mark.parametrize('brut,attendu', [
    (json.dumps({'success': True, 'message': 'Contact Marie créé.'}), 'Contact Marie créé.'),
    (json.dumps({'success': False, 'message': 'Le contact existe déjà.'}), 'Le contact existe déjà.'),
    (json.dumps({'success': True, 'contact_id': 'interne'}), 'Contact créé.'),
    ('Événement créé.', 'Événement créé.'),
])
async def test_resultat_de_confirmation_lisible(client, monkeypatch, brut, attendu):
    from app.routers import chat
    monkeypatch.setattr(chat, 'execute_memory_tool', AsyncMock(return_value=brut))
    identifiant = register_pending('create_contact', {'first_name': 'Marie'})
    reponse = await client.post('/api/chat/confirm-tool', json={'confirmation_id': identifiant, 'approved': True})
    assert reponse.status_code == 200, reponse.text
    assert reponse.json()['result'] == attendu
