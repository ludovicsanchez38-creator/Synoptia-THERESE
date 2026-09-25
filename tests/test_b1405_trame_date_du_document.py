"""B-1405 (persona Zoé, cycle 13) : la génération de trame n'avançait pas la
date du document.

`_touch_document` est appelé par chaque geste qui fait vivre un document
(section créée, retouchée, réordonnée, validée, piste) ; l'écriture de la trame
générée l'oubliait. Une trame régénérée sur un vieux document le laissait en
bas de la liste, triée par `updated_at`.
"""

import json
from unittest.mock import AsyncMock, patch

import pytest

from tests.test_documents_router import _create_document


@pytest.mark.asyncio
async def test_la_trame_generee_avance_la_date_du_document(client):
    doc = await _create_document(client, title="Zoé document triple-clic")
    trame = json.dumps([{"title": "Introduction", "brief": "Poser le sujet", "depth": 0}])

    with patch("app.services.llm.LLMService.generate_content", new_callable=AsyncMock, return_value=trame):
        reponse = await client.post(f"/api/documents/{doc['id']}/outline")
    assert reponse.status_code == 200, reponse.text

    relu = (await client.get(f"/api/documents/{doc['id']}")).json()
    assert relu["updated_at"] > doc["updated_at"]
