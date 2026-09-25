"""B-1270 : la purge et la restauration attendaient les créations du chat
(B-1260) et les indexations de fiches (B-1234) par `asyncio.gather`. Un
gather annulé annule ses enfants : une purge interrompue (arrêt, déconnexion)
annulait le geste que `shield` protégeait, la requête de chat recevait une
CancelledError, la ligne était abandonnée et le vecteur écrit quand même.
Revue du diff, passe 5 (cas B)."""

import asyncio
import threading
import time

import pytest


def _vecteur_lent(monkeypatch, duree: float) -> threading.Event:
    import app.services.qdrant as mq

    demarre = threading.Event()

    def ecrire():
        demarre.set()
        time.sleep(duree)

    async def ajout(**kw):
        await asyncio.to_thread(ecrire)
        return "p"

    monkeypatch.setattr(mq._qdrant_service, "async_add_memory", ajout)
    return demarre


async def _jusqu_a(evenement: threading.Event) -> None:
    for _ in range(300):
        if evenement.is_set():
            return
        await asyncio.sleep(0.01)
    raise AssertionError("le vecteur n'a pas démarré : le test ne mesure rien")


@pytest.mark.asyncio
async def test_une_attente_annulee_laisse_le_geste_du_chat_finir(db_session, monkeypatch):
    import json

    from app.services import memory_tools as mt

    demarre = _vecteur_lent(monkeypatch, 0.8)
    chat = asyncio.create_task(
        mt.execute_create_contact({"first_name": "Marie", "last_name": "Exemple"}, db_session)
    )
    await _jusqu_a(demarre)
    attente = asyncio.create_task(mt.attendre_les_gestes_de_creation())
    await asyncio.sleep(0.05)
    attente.cancel()
    with pytest.raises(asyncio.CancelledError):
        await attente
    resultat = json.loads(await chat)
    assert resultat.get("success") is True, resultat


@pytest.mark.asyncio
async def test_un_arret_annule_laisse_l_indexation_finir_sa_fiche(db_session, monkeypatch):
    from app.models.entities import Contact
    from app.routers import memory as memoire

    fiche = Contact(first_name="Alice")
    db_session.add(fiche)
    await db_session.commit()
    demarre = _vecteur_lent(monkeypatch, 0.8)
    memoire.indexer_fiches_en_arriere_plan([fiche])
    taches = list(memoire._INDEXATIONS_DE_FICHES)
    await _jusqu_a(demarre)
    arret = asyncio.create_task(memoire.arreter_les_indexations_de_fiches())
    await asyncio.sleep(0.05)
    arret.cancel()
    with pytest.raises(asyncio.CancelledError):
        await arret
    await asyncio.wait(taches)
    assert not any(t.cancelled() for t in taches), "l'indexation en vol a été annulée par l'arrêt annulé"
