"""Cycle 6, lot 5 (10/09/2026) : candidats des secondes lectures, confirmés par Grok.

- rédaction en flux : un flux qui casse après le marqueur `PISTES:` ne laisse pas
  le marqueur ni les pistes dans le contenu de la section ;
- trame : deux lancements simultanés sur un document vide n'écrivent pas deux
  trames (un seul passe, l'autre reçoit 409 `outline_in_progress`) ;
- OpenRouter : `finish_reason` `content_filter` ou `length` sans contenu ne produit
  qu'UN événement d'erreur, pas un second au `[DONE]`.
"""

from __future__ import annotations

import asyncio
import json
from unittest.mock import patch

import pytest

from tests.test_documents_draft_validate import (
    _create_document,
    _create_section,
    _fake_stream_response,
)
from tests.test_provider_tools import _collect, _FakeClient

TRAME = json.dumps([{"title": "Contexte", "brief": "Poser le décor", "depth": 0}, {"title": "Conclusion", "brief": "Résumer", "depth": 0}])


@pytest.mark.asyncio
async def test_un_flux_qui_casse_apres_le_marqueur_pistes_ne_le_laisse_pas_dans_la_section(client):
    doc = await _create_document(client)
    section = await _create_section(client, doc["id"], "Financement bancaire", order=10.0)
    chunks = ["Le prêt bancaire reste la voie classique.", "\n\nPISTES:\n- Comparer avec le crédit-bail\n"]
    with patch("app.services.llm.LLMService.stream_response", new=_fake_stream_response(chunks, then_raise=RuntimeError("panne du fournisseur"))):
        reponse = await client.post(f"/api/documents/sections/{section['id']}/draft", json={"instruction": None})
    assert reponse.status_code == 200, reponse.text
    detail = await client.get(f"/api/documents/{doc['id']}")
    contenu = detail.json()["sections"][0]["content"]
    assert "PISTES" not in contenu and "crédit-bail" not in contenu, contenu
    assert contenu.strip() == "Le prêt bancaire reste la voie classique."


@pytest.mark.asyncio
async def test_deux_reservations_simultanees_de_trame_n_en_accordent_qu_une(client):
    """La réservation (actif_pour puis creer_traitement) est atomique par document :
    deux demandes qui se croisent sur un document vide ne passent pas toutes les deux."""
    from app.routers import documents as routeur
    from app.services import traitements

    doc = await client.post("/api/documents", json={"title": "Proposition ISOCUBE", "brief": "Formation"})
    document = doc.json()["id"]
    # Forcer l'entrelacement : chaque vérification cède la main avant de répondre.
    verification = traitements.actif_pour

    async def _lente(type, entity_id):
        resultat = await verification(type, entity_id)
        await asyncio.sleep(0.05)
        return resultat

    traitements.actif_pour = _lente
    try:
        resultats = await asyncio.gather(
            routeur._reserver_la_trame(document, "Trame : test", None),
            routeur._reserver_la_trame(document, "Trame : test", None),
        )
    finally:
        traitements.actif_pour = verification
    handles = [r for r in resultats if isinstance(r, traitements.TraitementHandle)]
    refus = [r for r in resultats if not isinstance(r, traitements.TraitementHandle)]
    assert len(handles) == 1 and len(refus) == 1, resultats
    assert refus[0].status_code == 409 and b"outline_in_progress" in refus[0].body
    from app.models.processing import EtatTache
    await handles[0].terminer(EtatTache.CANCELLED)


def _openrouter(client):
    from app.services.providers.base import LLMConfig, LLMProvider
    from app.services.providers.openrouter import OpenRouterProvider

    return OpenRouterProvider(LLMConfig(provider=LLMProvider.OPENROUTER, model="x/y", api_key="k"), client=client)


@pytest.mark.asyncio
@pytest.mark.parametrize("raison", ["content_filter", "length"])
async def test_un_arret_sans_contenu_ne_produit_qu_une_erreur(raison):
    lignes = [
        "data: " + json.dumps({"choices": [{"delta": {}, "finish_reason": raison}]}),
        "data: [DONE]",
    ]
    events = await _collect(_openrouter(_FakeClient(lignes)).stream(None, [{"role": "user", "content": "x"}]))
    erreurs = [e for e in events if e.type == "error"]
    assert len(erreurs) == 1, [e.content for e in erreurs]
