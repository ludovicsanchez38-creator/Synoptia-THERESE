"""B-1520 : un travail de fond écrivait après « Effacer toutes mes données ».

La purge attendait les créations du chat et les indexations de fiches,
pas une délibération du Board, une mission d'Atelier, une trame ou une
extraction de fichier : leur écriture de fin (la décision du Board, question
comprise) arrivait dans la base qu'on venait de vider. La purge demande
désormais l'arrêt de chaque traitement vivant et attend son état terminal
avant d'effacer.

La route et l'écrivain tournent dans LA MÊME boucle, comme sous uvicorn.
Avec le client synchrone de la fixture (`TestClient`), la route tourne dans
la boucle du portail anyio, sur un autre thread, et l'appel bloque la boucle
du test : un écrivain créé ici ne pouvait pas avancer pendant la purge,
quelle que soit l'attente côté serveur (mesuré : son `sleep(0.3)` finissait
après le 503 du plafond).
"""

import asyncio

import httpx
import pytest


async def _purger_dans_la_meme_boucle() -> httpx.Response:
    from app.main import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as meme_boucle:
        return await meme_boucle.delete("/api/data/all?confirm=true")


@pytest.mark.asyncio
async def test_un_travail_de_fond_n_ecrit_rien_apres_la_purge(client):
    from app.models.database import get_session_context
    from app.models.entities import Conversation
    from app.models.processing import EtatTache
    from app.services import traitements
    from app.services.task_registry import TravailNonInterruptible, retirer

    traitement = await traitements.creer_traitement(type="board", label="Faut-il embaucher ?")
    await traitement.demarrer()
    ecrit = asyncio.Event()

    async def deliberation() -> None:
        await asyncio.sleep(0.3)  # un travail qui ne s'interrompt pas
        async with get_session_context() as session:
            session.add(Conversation(id="conv-b1520", title="Décision : faut-il embaucher ?"))
            await session.commit()
        ecrit.set()
        await traitement.terminer(EtatTache.DONE)

    tache = asyncio.create_task(deliberation())
    await traitement.lier_adaptateur(TravailNonInterruptible(lambda: None))
    try:
        purge = await _purger_dans_la_meme_boucle()
        await tache
    finally:
        tache.cancel()
        retirer(traitement.id)

    assert purge.status_code == 200, purge.text
    assert ecrit.is_set(), "l'écrivain n'a pas écrit : le test ne mesure rien"
    async with get_session_context() as session:
        assert await session.get(Conversation, "conv-b1520") is None


@pytest.mark.asyncio
async def test_un_traitement_inscrit_pendant_l_attente_est_attendu_aussi(client):
    """Un travail qui s'inscrit pendant que la purge en attend un autre
    n'était pas dans l'instantané du registre : il écrivait après."""
    from app.models.database import get_session_context
    from app.models.entities import Conversation
    from app.models.processing import EtatTache
    from app.services import traitements
    from app.services.task_registry import TravailNonInterruptible, retirer

    premier = await traitements.creer_traitement(type="board", label="Premier")
    await premier.demarrer()
    identifiants = [premier.id]
    ecrits: list[str] = []

    async def ecrire_puis_terminer(traitement, delai: float, conv_id: str) -> None:
        await asyncio.sleep(delai)
        async with get_session_context() as session:
            session.add(Conversation(id=conv_id, title="Écrit par un travail de fond"))
            await session.commit()
        ecrits.append(conv_id)
        await traitement.terminer(EtatTache.DONE)

    async def second_travail() -> None:
        await asyncio.sleep(0.1)  # la purge attend déjà le premier
        second = await traitements.creer_traitement(type="board", label="Second")
        identifiants.append(second.id)
        await second.demarrer()
        await second.lier_adaptateur(TravailNonInterruptible(lambda: None))
        await ecrire_puis_terminer(second, 0.4, "conv-b1520-second")

    taches = [
        asyncio.create_task(ecrire_puis_terminer(premier, 0.3, "conv-b1520-premier")),
        asyncio.create_task(second_travail()),
    ]
    await premier.lier_adaptateur(TravailNonInterruptible(lambda: None))
    try:
        purge = await _purger_dans_la_meme_boucle()
        await asyncio.gather(*taches)
    finally:
        for tache in taches:
            tache.cancel()
        for identifiant in identifiants:
            retirer(identifiant)

    assert purge.status_code == 200, purge.text
    assert sorted(ecrits) == ["conv-b1520-premier", "conv-b1520-second"], ecrits
    async with get_session_context() as session:
        assert await session.get(Conversation, "conv-b1520-premier") is None
        assert await session.get(Conversation, "conv-b1520-second") is None


@pytest.mark.asyncio
async def test_une_entree_perimee_du_registre_ne_retient_pas_la_purge(client, monkeypatch):
    """Une entrée restée au registre sans ligne en base (producteur parti,
    base remise à neuf) ne produira plus rien : l'état en base fait foi, pas
    la présence au registre. Sans cela, chaque purge attendait le plafond
    et répondait 503 (vu en suite complète, les tests précédents laissant
    des entrées derrière eux)."""
    from app.routers import data
    from app.services.task_registry import TravailNonInterruptible, inscrire, retirer

    monkeypatch.setattr(data, "DELAI_MAX_TRAVAUX_DE_FOND_S", 2.0)
    inscrire("b1520-entree-perimee", TravailNonInterruptible(lambda: None))
    try:
        purge = await _purger_dans_la_meme_boucle()
    finally:
        retirer("b1520-entree-perimee")

    assert purge.status_code == 200, purge.text


@pytest.mark.asyncio
async def test_la_decision_protegee_du_board_n_ecrit_rien_apres_la_purge(client):
    """Le chemin réel du Board : l'adaptateur vise la tâche porteuse
    (routers/board.py, `AnnulationParTacheAsyncio(tache)`), qui quitte le
    registre dès qu'elle est annulée ; la décision est commitée par une
    tâche séparée sous `shield` (services/board.py, `_persistance_en_cours`),
    et la route ne pose l'état terminal qu'après cette persistance. Attendre
    la seule sortie du registre laissait passer la décision."""
    from app.models.database import get_session_context
    from app.models.entities import BoardDecisionDB
    from app.models.processing import EtatTache
    from app.services import traitements
    from app.services.task_registry import AnnulationParTacheAsyncio, retirer

    traitement = await traitements.creer_traitement(
        type="board", label="Faut-il embaucher ?", entity_id="dec-b1520"
    )
    await traitement.demarrer()
    persistances: list[asyncio.Task[None]] = []

    async def persister() -> None:
        await asyncio.sleep(0.3)
        async with get_session_context() as session:
            session.add(
                BoardDecisionDB(
                    id="dec-b1520",
                    question="Faut-il embaucher ?",
                    opinions="[]",
                    synthesis="{}",
                    confidence="high",
                    recommendation="Oui",
                )
            )
            await session.commit()

    async def porteur() -> None:
        persistance = asyncio.create_task(persister())
        persistances.append(persistance)
        await asyncio.shield(persistance)

    async def cloture() -> None:
        await asyncio.gather(porteuse, return_exceptions=True)
        await asyncio.gather(*persistances, return_exceptions=True)
        async with get_session_context() as session:
            sauvee = await session.get(BoardDecisionDB, "dec-b1520") is not None
        await traitement.terminer(EtatTache.DONE if sauvee else EtatTache.CANCELLED)

    porteuse = asyncio.create_task(porteur())
    await asyncio.sleep(0)  # la porteuse lance sa persistance et attend le shield
    await traitement.lier_adaptateur(AnnulationParTacheAsyncio(porteuse))
    route = asyncio.create_task(cloture())
    try:
        purge = await _purger_dans_la_meme_boucle()
        await route
    finally:
        route.cancel()
        porteuse.cancel()
        retirer(traitement.id)

    assert purge.status_code == 200, purge.text
    assert persistances and persistances[0].done() and not persistances[0].cancelled(), (
        "la décision n'a pas été commitée : le test ne mesure rien"
    )
    async with get_session_context() as session:
        assert await session.get(BoardDecisionDB, "dec-b1520") is None


@pytest.mark.asyncio
async def test_au_plafond_la_purge_dit_les_travaux_qu_elle_a_arretes(client, monkeypatch):
    """Au plafond, les fiches arrêtées reprennent (B-1283), mais un
    traitement arrêté (délibération, mission) ne reprend pas : « rien n'a été
    modifié » devenait faux. Le 503 dit l'arrêt."""
    from app.routers import data
    from app.services import traitements
    from app.services.task_registry import TravailNonInterruptible, retirer

    monkeypatch.setattr(data, "DELAI_MAX_TRAVAUX_DE_FOND_S", 0.5)
    traitement = await traitements.creer_traitement(type="board", label="Ne finit jamais")
    await traitement.demarrer()
    await traitement.lier_adaptateur(TravailNonInterruptible(lambda: None))
    try:
        purge = await _purger_dans_la_meme_boucle()
    finally:
        retirer(traitement.id)

    assert purge.status_code == 503, purge.text
    assert "rien n'a été modifié" not in purge.text
    assert "arrêtés" in purge.text
