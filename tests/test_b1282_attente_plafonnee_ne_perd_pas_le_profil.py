"""B-1282 : régression de B-1277. `arreter_l_indexation_du_profil` avançait la
génération AVANT de prendre le verrou ; quand le plafond expirait (ou que la
purge était annulée) pendant l'attente du verrou, la purge répondait 503
« rien n'a été modifié », mais l'indexation du dernier profil enregistré, qui
attendait derrière, renonçait : l'index gardait l'ancien nom. Revue du diff,
passe 6 (cas A)."""

import asyncio
import time

import pytest


def _profil_lent(monkeypatch, duree):
    from app.services import user_profile as up

    indexes: list[str] = []

    def ecrire(nom):
        time.sleep(duree)
        indexes.append(nom)

    async def embed(profile):
        await asyncio.to_thread(ecrire, profile.name)

    monkeypatch.setattr(up, "_embed_profile", embed)
    monkeypatch.setattr(up, "_VERROU_INDEXATION", asyncio.Lock())
    return indexes


@pytest.mark.asyncio
async def test_un_503_laisse_le_dernier_profil_s_indexer(db_session, monkeypatch):
    from app.routers import data as data_router
    from app.services import user_profile as up
    from fastapi import HTTPException

    indexes = _profil_lent(monkeypatch, 0.8)
    await up.set_user_profile(db_session, up.UserProfile(name="Ancien Nom"))
    await asyncio.sleep(0.05)
    await up.set_user_profile(db_session, up.UserProfile(name="Nouveau Nom"))
    monkeypatch.setattr(data_router, "DELAI_MAX_TRAVAUX_DE_FOND_S", 0.3)
    with pytest.raises(HTTPException) as refus:
        await data_router._arreter_les_travaux_de_fond()
    assert refus.value.status_code == 503
    await asyncio.wait(list(up._INDEXATIONS_EN_COURS))
    assert indexes and indexes[-1] == "Nouveau Nom", indexes


@pytest.mark.asyncio
async def test_un_arret_abouti_fait_renoncer_ce_qui_suit(db_session, monkeypatch):
    """L'arrêt reste un arrêt : une indexation lancée APRÈS lui renonce."""
    from app.services import user_profile as up

    indexes = _profil_lent(monkeypatch, 0.1)
    generation_d_avant = up._GENERATION_PROFIL
    await up.arreter_l_indexation_du_profil()
    await up._indexer_en_arriere_plan(up.UserProfile(name="Périmé"), generation_d_avant)
    assert indexes == [], indexes
