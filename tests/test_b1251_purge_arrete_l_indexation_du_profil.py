"""B-1251 : jumeau de B-1222 pour le profil. La purge n'arrêtait que les
indexations de fiches ; celle du profil, lancée par une sauvegarde juste avant,
calculait son vecteur dans un fil et écrivait `owner_profile` (nom, entreprise,
rôle, courriel) dans l'index recréé APRÈS la réponse 200 de « Effacer toutes
mes données ». Contre-épreuve de la revue adverse du diff, passe 4."""
import asyncio
import threading
import time

import pytest


def _espion_du_profil(monkeypatch):
    import app.services.qdrant as mq
    from app.services import user_profile

    # Le verrou de module se lie à la boucle de sa première attente : chaque
    # test a la sienne (celle du client), il lui faut donc un verrou neuf.
    monkeypatch.setattr(user_profile, "_VERROU_INDEXATION", asyncio.Lock())

    ecritures: list[tuple[str, float]] = []
    demarre = threading.Event()

    def ecrire(entity_id):
        demarre.set()
        time.sleep(0.8)
        ecritures.append((entity_id, time.monotonic()))

    async def ajout(**kw):
        await asyncio.to_thread(ecrire, kw.get("entity_id"))
        return "p"

    monkeypatch.setattr(mq._qdrant_service, "async_add_memory", ajout)
    return ecritures, demarre


@pytest.mark.asyncio
async def test_le_profil_en_vol_n_ecrit_plus_apres_la_purge(client, monkeypatch):
    ecritures, demarre = _espion_du_profil(monkeypatch)
    r = await client.post("/api/config/profile", json={"name": "Marie Exemple", "company": "Exemple SARL"})
    assert r.status_code == 200, r.text
    for _ in range(100):
        if demarre.is_set():
            break
        await asyncio.sleep(0.02)
    assert demarre.is_set(), "l'indexation du profil n'a pas démarré : le test ne mesure rien"

    p = await client.delete("/api/data/all?confirm=true")
    fin = time.monotonic()
    assert p.status_code == 200, p.text
    await asyncio.sleep(1.2)
    apres = [e for e, t in ecritures if t > fin]
    assert not apres, f"profil réécrit dans l'index après la purge : {apres}"


@pytest.mark.asyncio
async def test_le_profil_en_attente_n_ecrit_pas_apres_la_purge(client, monkeypatch):
    """Une seconde sauvegarde attend le verrou derrière la première. B-1282 :
    déjà en file, elle passe avant la purge (verrou FIFO), que la purge efface
    ensuite ; rien ne doit s'écrire après la réponse."""
    ecritures, demarre = _espion_du_profil(monkeypatch)
    r = await client.post("/api/config/profile", json={"name": "Marie Exemple"})
    assert r.status_code == 200, r.text
    for _ in range(100):
        if demarre.is_set():
            break
        await asyncio.sleep(0.02)
    assert demarre.is_set(), "l'indexation du profil n'a pas démarré : le test ne mesure rien"
    r = await client.post("/api/config/profile", json={"name": "Marie Exemple", "company": "Exemple SARL"})
    assert r.status_code == 200, r.text

    p = await client.delete("/api/data/all?confirm=true")
    fin = time.monotonic()
    assert p.status_code == 200, p.text
    await asyncio.sleep(2.0)
    assert not [e for e, t in ecritures if t > fin], f"profil écrit après la purge : {ecritures}"
