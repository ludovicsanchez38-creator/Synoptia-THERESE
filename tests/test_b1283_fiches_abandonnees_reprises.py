"""B-1283 : régression de B-1277. L'arrêt des indexations fait rendre la main
aux fiches restantes ; si l'attente échoue ensuite (plafond expiré sur le
profil, annulation), la purge répond 503 « rien n'a été modifié », mais ces
fiches, bien enregistrées, n'étaient jamais indexées : aucune route ne les
reprenait. Elles sont désormais relancées. Revue du diff, passe 6 (cas B)."""

import asyncio
import time

import pytest


def _vecteurs_lents(monkeypatch, fiche_s: float, profil_s: float) -> list[str]:
    from app.routers import memory as memoire
    from app.services import user_profile as up

    indexees: list[str] = []

    def ecrire(nom, duree):
        time.sleep(duree)
        indexees.append(nom)

    async def embed_contact(c):
        await asyncio.to_thread(ecrire, c.first_name, fiche_s)

    async def embed_profil(p):
        await asyncio.to_thread(ecrire, f"profil:{p.name}", profil_s)

    monkeypatch.setattr(memoire, "_embed_contact", embed_contact)
    monkeypatch.setattr(up, "_embed_profile", embed_profil)
    monkeypatch.setattr(up, "_VERROU_INDEXATION", asyncio.Lock())
    return indexees


async def _fiches(db_session, noms):
    from app.models.entities import Contact

    fiches = [Contact(first_name=nom) for nom in noms]
    for fiche in fiches:
        db_session.add(fiche)
    await db_session.commit()
    return fiches


async def _tout_attendre():
    from app.routers import memory as memoire
    from app.services import user_profile as up

    for _ in range(3):
        taches = list(memoire._INDEXATIONS_DE_FICHES) + list(up._INDEXATIONS_EN_COURS)
        if taches:
            await asyncio.wait(taches)
        await asyncio.sleep(0.05)


@pytest.mark.asyncio
async def test_un_503_reprend_les_fiches_abandonnees(db_session, monkeypatch):
    from app.routers import data as data_router
    from app.routers import memory as memoire
    from app.services import user_profile as up
    from fastapi import HTTPException

    indexees = _vecteurs_lents(monkeypatch, 0.2, 1.2)
    fiches = await _fiches(db_session, ["A1", "A2", "A3"])
    await up.set_user_profile(db_session, up.UserProfile(name="Profil"))
    memoire.indexer_fiches_en_arriere_plan(fiches)
    await asyncio.sleep(0.05)
    monkeypatch.setattr(data_router, "DELAI_MAX_TRAVAUX_DE_FOND_S", 0.6)
    with pytest.raises(HTTPException) as refus:
        await data_router._arreter_les_travaux_de_fond()
    assert refus.value.status_code == 503
    await _tout_attendre()
    assert {"A1", "A2", "A3"} <= set(indexees), indexees


@pytest.mark.asyncio
async def test_un_arret_annule_reprend_les_fiches_abandonnees(db_session, monkeypatch):
    """Deux imports en vol : le lot Y rend ses fiches restantes pendant que
    l'arrêt attend encore la fiche lente du lot X ; l'arrêt est annulé."""
    from app.routers import memory as memoire

    indexees: list[str] = []

    def ecrire(nom):
        time.sleep(1.0 if nom == "X" else 0.1)
        indexees.append(nom)

    async def embed_contact(c):
        await asyncio.to_thread(ecrire, c.first_name)

    monkeypatch.setattr(memoire, "_embed_contact", embed_contact)
    lent = await _fiches(db_session, ["X"])
    rapide = await _fiches(db_session, ["Y1", "Y2", "Y3"])
    memoire.indexer_fiches_en_arriere_plan(lent)
    memoire.indexer_fiches_en_arriere_plan(rapide)
    await asyncio.sleep(0.03)
    arret = asyncio.create_task(memoire.arreter_les_indexations_de_fiches())
    await asyncio.sleep(0.4)  # Y1 finie, Y2 et Y3 rendues ; X encore en vol
    assert not arret.done()
    arret.cancel()
    try:
        await arret
    except asyncio.CancelledError:
        pass
    await _tout_attendre()
    assert {"X", "Y1", "Y2", "Y3"} <= set(indexees), indexees


@pytest.mark.asyncio
async def test_un_arret_abouti_rend_les_fiches_sans_les_relancer(db_session, monkeypatch):
    """Arrêt abouti : l'opération va effacer ou remplacer ; les fiches rendues
    reviennent à l'appelant, rien n'est relancé."""
    from app.routers import memory as memoire

    indexees = _vecteurs_lents(monkeypatch, 0.3, 0.1)
    fiches = await _fiches(db_session, ["C1", "C2", "C3"])
    memoire.indexer_fiches_en_arriere_plan(fiches)
    await asyncio.sleep(0.05)
    rendues = await memoire.arreter_les_indexations_de_fiches()
    await _tout_attendre()
    assert indexees == ["C1"], indexees
    assert set(rendues) == {f.id for f in fiches[1:]}, rendues
