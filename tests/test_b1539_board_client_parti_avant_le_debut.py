"""B-1539 (RFC P-125 V4, R-125-10) : une délibération du Board dont le client
part avant le premier octet restait « en attente » jusqu'au redémarrage.

La ligne de suivi est créée dans le corps de la route ; le générateur qui la
démarre et la termine ne s'exécute jamais si la réponse est annulée avant son
premier pas (une tâche annulée avant son premier pas n'entre jamais dans son
`try`). L'appel est fait directement en ASGI, dans la boucle du test : le
client envoie sa requête puis se déconnecte aussitôt.
"""

import asyncio
import json

import httpx
import pytest


async def _deliberer_puis_partir(depart_apres_s: float = 0.0) -> None:
    from app.main import app

    corps = json.dumps({"question": "Faut-il embaucher un second salarié ?"}).encode()
    messages = [
        {"type": "http.request", "body": corps, "more_body": False},
        {"type": "http.disconnect"},
    ]

    async def recevoir():
        if messages:
            message = messages.pop(0)
            if message["type"] == "http.disconnect":
                await asyncio.sleep(depart_apres_s)
            return message
        await asyncio.sleep(3600)

    async def envoyer(_message):
        return None

    scope = {
        "type": "http", "asgi": {"version": "3.0", "spec_version": "2.3"}, "http_version": "1.1",
        "method": "POST", "scheme": "http", "path": "/api/board/deliberate",
        "raw_path": b"/api/board/deliberate", "query_string": b"", "root_path": "",
        "headers": [(b"content-type", b"application/json"), (b"host", b"test"),
                    (b"content-length", str(len(corps)).encode())],
        "client": ("127.0.0.1", 50000), "server": ("test", 80),
    }
    await asyncio.wait_for(app(scope, recevoir, envoyer), 10)


@pytest.mark.asyncio
async def test_une_deliberation_quittee_avant_le_debut_ne_reste_pas_en_attente(client):
    from app.main import app
    from app.models.processing import EtatTache

    await _deliberer_puis_partir()
    await asyncio.sleep(0.2)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as meme_boucle:
        lignes = (await meme_boucle.get("/api/processing-tasks")).json()["traitements"]
    board = [ligne for ligne in lignes if ligne["type"] == "board"]

    assert board, "aucune ligne de délibération : le test ne mesure rien"
    assert all(ligne["state"] in EtatTache.terminaux() for ligne in board), [ligne["state"] for ligne in board]


@pytest.mark.asyncio
async def test_la_deliberation_lancee_avant_le_depart_du_client_est_annulee(client, monkeypatch):
    """La tâche porteuse est créée avant le démarrage du suivi : un client
    parti à ce moment laissait la délibération tourner sans lecteur (appels
    aux modèles payés pour rien, décision éventuellement enregistrée)."""
    from app.services.board import BoardService

    commencee = asyncio.Event()
    annulee = asyncio.Event()

    async def deliberation_longue(self, *args, **kwargs):
        commencee.set()
        try:
            await asyncio.sleep(3600)
        finally:
            annulee.set()
        yield  # pragma: no cover

    monkeypatch.setattr(BoardService, "deliberate", deliberation_longue)
    await _deliberer_puis_partir()
    await asyncio.sleep(0.3)

    assert commencee.is_set(), "la délibération n'a pas démarré : le test ne mesure rien"
    assert annulee.is_set(), "la délibération tourne encore sans client"


@pytest.mark.asyncio
async def test_une_ligne_demarree_puis_abandonnee_avant_la_boucle_est_close(client, monkeypatch):
    """Le client part après le démarrage du suivi mais avant la boucle
    d'événements : la ligne est en cours et plus aucun producteur ne la
    clora. La clôture la termine en « cancelled »."""
    from app.main import app
    from app.models.processing import EtatTache
    from app.services.traitements import TraitementHandle

    vraie_liaison = TraitementHandle.lier_adaptateur

    async def liaison_lente(self, adaptateur):
        await asyncio.sleep(0.5)  # le départ du client tombe ici, après demarrer()
        return await vraie_liaison(self, adaptateur)

    monkeypatch.setattr(TraitementHandle, "lier_adaptateur", liaison_lente)
    await _deliberer_puis_partir(depart_apres_s=0.3)
    await asyncio.sleep(0.2)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as meme_boucle:
        lignes = (await meme_boucle.get("/api/processing-tasks")).json()["traitements"]
    board = [ligne for ligne in lignes if ligne["type"] == "board"]

    assert [ligne["state"] for ligne in board] == [EtatTache.CANCELLED], [ligne["state"] for ligne in board]
