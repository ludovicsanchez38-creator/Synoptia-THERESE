"""B-1154, B-1139 : l'extraction d'entités respecte l'interrupteur et suit
le service de la conversation.

B-1154 : l'interrupteur « Extraction automatique » (Paramètres, Services)
était enregistré sous `auto_extract_entities`, mais aucun code du moteur ne le
lisait. Coupé, il laissait partir chaque message au modèle.

B-1139 : l'extraction relisait le service global au lieu de celui qui venait
de répondre. Si le réglage change entre la réponse et la tâche de fond, le
message d'une conversation locale partait chez un fournisseur en ligne.
Règle arbitrée le 24/09 : l'extraction suit le service de la conversation.
"""

from __future__ import annotations

import pytest
from app.models.entities import Preference
from app.routers import chat as module_chat
from app.services import entity_extractor as module_extracteur

MESSAGE = "J'ai rencontré Paul Durand de la société Brasserie Lumière pour son projet de site."


class _ServiceEspion:
    def __init__(self, nom: str) -> None:
        self.nom = nom
        self.appels = 0

    async def stream_response(self, context):  # noqa: ANN001 - forme du vrai service
        self.appels += 1
        yield '{"contacts": [], "projects": []}'


@pytest.fixture
def services(monkeypatch):
    en_ligne = _ServiceEspion("en ligne")
    monkeypatch.setattr(module_extracteur, "get_llm_service", lambda: en_ligne)
    return en_ligne


@pytest.mark.asyncio
async def test_interrupteur_coupe_aucun_appel_au_modele(db_session, services):
    db_session.add(Preference(key="auto_extract_entities", value="false", category="memory"))
    await db_session.commit()

    await module_chat._extract_entities_background(
        user_message=MESSAGE, conversation_id="conv-b1154", message_id="msg-b1154"
    )

    assert services.appels == 0, "interrupteur coupé, le message est quand même parti au modèle"


@pytest.mark.asyncio
@pytest.mark.parametrize("enregistre", [None, "true"])
async def test_interrupteur_allume_ou_absent_l_extraction_suit_la_conversation(db_session, services, enregistre):
    if enregistre is not None:
        db_session.add(Preference(key="auto_extract_entities", value=enregistre, category="memory"))
        await db_session.commit()
    local = _ServiceEspion("local")

    await module_chat._extract_entities_background(
        user_message=MESSAGE, conversation_id="conv-b1139", message_id="msg-b1139", llm_service=local
    )

    assert local.appels == 1
    assert services.appels == 0, "le message est parti sur le service global au lieu de celui de la conversation"


def test_le_flux_du_chat_passe_son_service_a_l_extraction():
    """Garde textuelle : la tâche de fond reçoit le service qui vient de
    répondre, pas une relecture du service global."""
    import inspect

    source = inspect.getsource(module_chat._do_stream_response)
    appel = source[source.index("_extract_entities_background(") :]
    appel = appel[: appel.index(")")]
    assert "llm_service=llm_service" in appel, appel
