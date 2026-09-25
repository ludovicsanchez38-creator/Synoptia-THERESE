"""B-1260 : une création lancée par le chat (/contact, outil create_contact)
part en geste détaché qui garde sa transaction ouverte pendant le calcul du
vecteur (jusqu'à 19 s). La purge ne l'attendait pas : elle se heurtait au
verrou d'écriture de SQLite, ou laissait survivre la fiche et son vecteur.
Lecteur U, passe 4."""
import asyncio
import threading
import time

import pytest


@pytest.mark.asyncio
async def test_la_purge_attend_une_creation_du_chat_en_vol(client, monkeypatch):
    import app.services.qdrant as mq

    ecritures: list[tuple[str, float]] = []
    demarre = threading.Event()

    def ecrire(entity_id):
        demarre.set()
        time.sleep(6.0)
        ecritures.append((entity_id, time.monotonic()))

    async def ajout(**kw):
        await asyncio.to_thread(ecrire, kw.get("entity_id"))
        return "p"

    monkeypatch.setattr(mq._qdrant_service, "async_add_memory", ajout)
    reponses: dict[str, object] = {}

    def creer():
        reponses["chat"] = client._tc.post(
            "/api/chat/send", json={"message": "/contact Marie Exemple", "stream": False}
        )

    fil = threading.Thread(target=creer)
    fil.start()
    assert demarre.wait(15), "la création du chat n'a pas atteint son vecteur : le test ne mesure rien"

    p = await client.delete("/api/data/all?confirm=true")
    fin = time.monotonic()
    fil.join(20)
    assert p.status_code == 200, p.text
    restants = (await client.get("/api/memory/contacts")).json()
    assert restants == [], f"fiche créée avant la purge encore là : {restants}"
    assert not [e for e, t in ecritures if t > fin], "vecteur écrit après la réponse de la purge"
