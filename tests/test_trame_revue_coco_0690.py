"""Revue adversariale COCO du diff v0.68.0-alpha..HEAD (09/09/2026), findings 1, 3, 5 et 8
sur la trame annulable (P-056). Ce que ces tests verrouillent :

- une section ajoutée à la main PENDANT la génération est préservée (la relecture
  dans la transaction d'écriture ne supprime que les sections vides connues au
  lancement) ;
- une annulation qui touche la porteuse avant son premier pas clôt quand même le
  traitement (sinon il reste `cancel_requested`, non annulable, et bloque toute
  nouvelle génération du document) ;
- une annulation pendant l'écriture de l'état DONE reste un succès : la trame est
  en base, la réponse la renvoie ;
- un échec de clôture du suivi ne verrouille pas la génération suivante.
"""

from __future__ import annotations

import asyncio
import json
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


@pytest.mark.asyncio
async def test_une_section_ajoutee_pendant_la_generation_est_preservee(client: AsyncClient):
    from app.models.processing import EtatTache
    from app.routers import documents as routeur
    from app.services import traitements

    document = await _document(client)
    handle = await traitements.creer_traitement(type="document_outline", label="Trame : test", entity_id=document)
    llm_appele = asyncio.Event()
    feu_vert = asyncio.Event()

    async def _llm_lent(*_a, **_k):
        llm_appele.set()
        await feu_vert.wait()
        return TRAME

    with patch("app.services.llm.LLMService.generate_content", new=_llm_lent):
        porteuse = await routeur._lancer_la_generation(handle, document, "Proposition ISOCUBE", "Formation Claude")
        await asyncio.wait_for(llm_appele.wait(), 5)
        ajout = await client.post(
            f"/api/documents/{document}/sections",
            json={"title": "Annexe tarifaire", "brief": "Grille 2026", "order": 10.0, "depth": 0},
        )
        assert ajout.status_code == 200, ajout.text
        feu_vert.set()
        resultat = await asyncio.wait_for(porteuse, 5)
    assert isinstance(resultat, list)
    assert [s.title for s in resultat] == ["Contexte", "Conclusion", "Annexe tarifaire"], "la section ajoutée pendant la génération a été supprimée"
    assert (await traitements.lire(handle.id)).state == EtatTache.DONE
    detail = await client.get(f"/api/documents/{document}")
    sections = detail.json()["sections"]
    assert [s["title"] for s in sections] == ["Contexte", "Conclusion", "Annexe tarifaire"]
    assert next(s for s in sections if s["title"] == "Annexe tarifaire")["brief"] == "Grille 2026"


@pytest.mark.asyncio
async def test_une_annulation_avant_le_premier_pas_de_la_porteuse_clot_le_traitement(client: AsyncClient, monkeypatch):
    from app.models.processing import EtatTache
    from app.routers import documents as routeur
    from app.services import traitements

    document = await _document(client)
    handle = await traitements.creer_traitement(type="document_outline", label="Trame : test", entity_id=document)
    from app.services import task_registry

    async def _rejoue_une_demande(self, adaptateur):
        # La fenêtre du finding 3 : la demande d'arrêt rejouée par
        # `lier_adaptateur` touche une porteuse qui n'a pas encore fait un pas.
        task_registry.inscrire(self.id, adaptateur)
        adaptateur._tache.cancel()

    monkeypatch.setattr(traitements.TraitementHandle, "lier_adaptateur", _rejoue_une_demande)
    with patch("app.services.llm.LLMService.generate_content", new_callable=AsyncMock, return_value=TRAME) as llm:
        porteuse = await routeur._lancer_la_generation(handle, document, "Proposition ISOCUBE", "Formation Claude")
        # Son `try` n'est jamais entré : personne, dans la coroutine, ne pose l'état terminal.
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(asyncio.shield(porteuse), 5)
        for _ in range(20):
            await asyncio.sleep(0.05)
            ligne = await traitements.lire(handle.id)
            if ligne is not None and ligne.state in EtatTache.terminaux():
                break
    ligne = await traitements.lire(handle.id)
    assert ligne is not None and ligne.state == EtatTache.CANCELLED, f"traitement resté {ligne.state if ligne else None}"
    assert not await traitements.actif_pour("document_outline", document), "le document reste bloqué"
    llm.assert_not_called()


@pytest.mark.asyncio
async def test_une_annulation_pendant_la_cloture_done_reste_un_succes(client: AsyncClient, monkeypatch):
    from app.models.processing import EtatTache
    from app.routers import documents as routeur
    from app.services import traitements

    document = await _document(client)
    handle = await traitements.creer_traitement(type="document_outline", label="Trame : test", entity_id=document)
    cloture_commencee = asyncio.Event()
    feu_vert = asyncio.Event()
    originale = routeur._terminer_temoin

    async def _cloture_lente(h, etat, **kwargs):
        if etat == EtatTache.DONE:
            cloture_commencee.set()
            await feu_vert.wait()
        await originale(h, etat, **kwargs)

    monkeypatch.setattr(routeur, "_terminer_temoin", _cloture_lente)
    with patch("app.services.llm.LLMService.generate_content", new_callable=AsyncMock, return_value=TRAME):
        porteuse = await routeur._lancer_la_generation(handle, document, "Proposition ISOCUBE", "Formation Claude")
        await asyncio.wait_for(cloture_commencee.wait(), 5)
        await traitements.demander_arret(handle.id)
        await asyncio.sleep(0.05)
        feu_vert.set()
        resultat = await asyncio.wait_for(porteuse, 5)
    assert isinstance(resultat, list) and [s.title for s in resultat] == ["Contexte", "Conclusion"], "la trame est en base : la réponse doit la renvoyer"
    ligne = await traitements.lire(handle.id)
    assert ligne is not None and ligne.state == EtatTache.DONE, f"état {ligne.state if ligne else None}"


@pytest.mark.asyncio
async def test_un_echec_de_cloture_ne_bloque_pas_la_generation_suivante(client: AsyncClient, monkeypatch):
    from app.routers import documents as routeur
    from app.services import traitements

    document = await _document(client)
    handle = await traitements.creer_traitement(type="document_outline", label="Trame : test", entity_id=document)

    async def _base_verrouillee(self, etat, *, error=None):
        raise RuntimeError("database is locked")

    monkeypatch.setattr(traitements.TraitementHandle, "terminer", _base_verrouillee)
    with patch("app.services.llm.LLMService.generate_content", new_callable=AsyncMock, return_value=TRAME):
        porteuse = await routeur._lancer_la_generation(handle, document, "Proposition ISOCUBE", "Formation Claude")
        resultat = await asyncio.wait_for(porteuse, 10)
    assert isinstance(resultat, list) and len(resultat) == 2
    monkeypatch.undo()
    # La ligne est restée « running » sans producteur : elle ne doit pas
    # passer pour une génération en cours.
    assert not await traitements.actif_pour("document_outline", document), "une ligne orpheline bloque la génération suivante"
    # Un nouveau document (la trame de celui-ci existe déjà) : la route doit accepter.
    autre = await _document(client)
    orphelin = await traitements.creer_traitement(type="document_outline", label="Trame : orphelin", entity_id=autre)
    await orphelin.demarrer()
    with patch("app.services.llm.LLMService.generate_content", new_callable=AsyncMock, return_value=TRAME):
        reponse = await client.post(f"/api/documents/{autre}/outline")
    assert reponse.status_code == 200, reponse.text
