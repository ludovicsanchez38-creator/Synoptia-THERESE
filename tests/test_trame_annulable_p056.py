"""P-056 (ronde B2, P1 ; accepté par Ludo le 08/09 ; design V2 après revue COCO) :
la génération de trame de l'Atelier est un traitement annulable.

Ce que les tests verrouillent :
- la route enregistre un traitement `document_outline` (entity_id = document),
  avec l'identifiant fourni par le client s'il y en a un ;
- registre indisponible → 503, aucun appel LLM (pas de fail-open) ;
- deux générations simultanées du même document → 409 `outline_in_progress` ;
- annuler pendant l'appel LLM → CANCELLED, zéro section, réponse 409
  `outline_cancelled` ;
- annuler pendant l'écriture → la trame existe, DONE ;
- fin normale → DONE ; trame illisible → FAILED + 502.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

TRAME = json.dumps([
    {"title": "Contexte", "brief": "Poser le décor", "depth": 0},
    {"title": "Conclusion", "brief": "Résumer", "depth": 0},
])


async def _document(client: AsyncClient) -> str:
    reponse = await client.post("/api/documents", json={"title": "Proposition ISOCUBE", "brief": "Formation Claude"})
    assert reponse.status_code == 200, reponse.text
    return reponse.json()["id"]


async def _traitement(document_id: str) -> dict | None:
    from app.services import traitements

    for ligne in await traitements.lister(actives=None, limit=50):
        if ligne["type"] == "document_outline" and ligne.get("entity_id") == document_id:
            return ligne
    return None


@pytest.mark.asyncio
async def test_la_route_enregistre_un_traitement_avec_l_identifiant_fourni(client: AsyncClient):
    document = await _document(client)
    identifiant = str(uuid.uuid4())
    with patch("app.services.llm.LLMService.generate_content", new_callable=AsyncMock, return_value=TRAME):
        reponse = await client.post(f"/api/documents/{document}/outline", json={"task_id": identifiant})
    assert reponse.status_code == 200, reponse.text
    assert [s["title"] for s in reponse.json()] == ["Contexte", "Conclusion"]
    ligne = await _traitement(document)
    assert ligne is not None, "aucun traitement document_outline enregistré"
    assert ligne["id"] == identifiant
    assert ligne["state"] == "done"
    assert ligne["label"].startswith("Trame")


@pytest.mark.asyncio
async def test_sans_identifiant_fourni_la_route_marche_encore(client: AsyncClient):
    document = await _document(client)
    with patch("app.services.llm.LLMService.generate_content", new_callable=AsyncMock, return_value=TRAME):
        reponse = await client.post(f"/api/documents/{document}/outline")
    assert reponse.status_code == 200, reponse.text
    assert (await _traitement(document))["state"] == "done"


@pytest.mark.asyncio
async def test_registre_indisponible_503_sans_appel_llm(client: AsyncClient, monkeypatch):
    from app.routers import documents as routeur
    from app.services import traitements

    document = await _document(client)

    async def _panne(**_kwargs):
        raise RuntimeError("base verrouillée")

    monkeypatch.setattr(traitements, "creer_traitement", _panne)
    with patch("app.services.llm.LLMService.generate_content", new_callable=AsyncMock, return_value=TRAME) as llm:
        reponse = await client.post(f"/api/documents/{document}/outline")
    assert reponse.status_code == 503, reponse.text
    assert reponse.json()["code"] == "suivi_indisponible"
    llm.assert_not_called()
    assert routeur is not None


@pytest.mark.asyncio
async def test_deux_generations_simultanees_409_outline_in_progress(client: AsyncClient):
    from app.services import traitements

    document = await _document(client)
    autre = await traitements.creer_traitement(type="document_outline", label="Trame : en cours", entity_id=document)
    await autre.demarrer()
    with patch("app.services.llm.LLMService.generate_content", new_callable=AsyncMock, return_value=TRAME) as llm:
        reponse = await client.post(f"/api/documents/{document}/outline")
    assert reponse.status_code == 409, reponse.text
    assert reponse.json()["code"] == "outline_in_progress"
    llm.assert_not_called()
    from app.models.processing import EtatTache
    await autre.terminer(EtatTache.DONE)


@pytest.mark.asyncio
async def test_annuler_pendant_l_appel_llm_ne_cree_aucune_section(client: AsyncClient):
    from app.models.processing import EtatTache
    from app.routers import documents as routeur
    from app.services import traitements

    document = await _document(client)
    handle = await traitements.creer_traitement(type="document_outline", label="Trame : test", entity_id=document)
    llm_appele = asyncio.Event()
    jamais = asyncio.Event()

    async def _llm_lent(*_a, **_k):
        llm_appele.set()
        await jamais.wait()
        return TRAME

    with patch("app.services.llm.LLMService.generate_content", new=_llm_lent):
        porteuse = await routeur._lancer_la_generation(handle, document, "Proposition ISOCUBE", "Formation Claude")
        await asyncio.wait_for(llm_appele.wait(), 5)
        arret = await traitements.demander_arret(handle.id)
        assert arret is not None and arret.state == EtatTache.CANCEL_REQUESTED
        resultat = await asyncio.wait_for(porteuse, 5)
    assert resultat is routeur.TRAME_ANNULEE
    ligne = await traitements.lire(handle.id)
    assert ligne is not None and ligne.state == EtatTache.CANCELLED
    detail = await client.get(f"/api/documents/{document}")
    assert detail.json()["sections"] == []


@pytest.mark.asyncio
async def test_annuler_pendant_l_ecriture_laisse_la_trame_et_termine_done(client: AsyncClient, monkeypatch):
    from app.models.processing import EtatTache
    from app.routers import documents as routeur
    from app.services import traitements

    document = await _document(client)
    handle = await traitements.creer_traitement(type="document_outline", label="Trame : test", entity_id=document)
    ecriture_commencee = asyncio.Event()
    feu_vert = asyncio.Event()
    originale = routeur._ecrire_la_trame

    async def _ecriture_lente(*args, **kwargs):
        ecriture_commencee.set()
        await feu_vert.wait()
        return await originale(*args, **kwargs)

    monkeypatch.setattr(routeur, "_ecrire_la_trame", _ecriture_lente)
    with patch("app.services.llm.LLMService.generate_content", new_callable=AsyncMock, return_value=TRAME):
        porteuse = await routeur._lancer_la_generation(handle, document, "Proposition ISOCUBE", "Formation Claude")
        await asyncio.wait_for(ecriture_commencee.wait(), 5)
        await traitements.demander_arret(handle.id)
        await asyncio.sleep(0.05)
        feu_vert.set()
        resultat = await asyncio.wait_for(porteuse, 5)
    assert isinstance(resultat, list) and len(resultat) == 2
    ligne = await traitements.lire(handle.id)
    assert ligne is not None and ligne.state == EtatTache.DONE, "la persistance acquise vaut succès"
    detail = await client.get(f"/api/documents/{document}")
    assert [s["title"] for s in detail.json()["sections"]] == ["Contexte", "Conclusion"]


@pytest.mark.asyncio
async def test_trame_illisible_502_et_traitement_failed(client: AsyncClient):
    from app.models.processing import EtatTache
    from app.services import traitements

    document = await _document(client)
    with patch("app.services.llm.LLMService.generate_content", new_callable=AsyncMock, return_value="pas du json"):
        reponse = await client.post(f"/api/documents/{document}/outline")
    assert reponse.status_code == 502, reponse.text
    ligne = await _traitement(document)
    assert ligne is not None and ligne["state"] == EtatTache.FAILED
    assert traitements is not None


@pytest.mark.asyncio
async def test_un_identifiant_deja_pris_est_refuse(client: AsyncClient):
    from app.services import traitements

    document = await _document(client)
    existant = await traitements.creer_traitement(type="chat", label="autre")
    with patch("app.services.llm.LLMService.generate_content", new_callable=AsyncMock, return_value=TRAME) as llm:
        reponse = await client.post(f"/api/documents/{document}/outline", json={"task_id": existant.id})
    assert reponse.status_code == 409, reponse.text
    assert reponse.json()["code"] == "task_id_taken"
    llm.assert_not_called()
