"""Deux marquages simultanés de la mise en route ne doivent pas se percuter.

01/09/2026. Les parcours de bout en bout tournent en parallèle et marquent
tous la mise en route au démarrage. Le journal du backend crachait alors
`UNIQUE constraint failed: preferences.key`, et l'un des appels récoltait un
500 : deux requêtes lisent « marqueur absent » en même temps, les deux
insèrent, la seconde viole la contrainte.

La docstring de `_mark_onboarding_completed` dit « de façon idempotente ». Elle
l'est pour deux appels successifs, pas pour deux appels simultanés — et c'est
le second cas qui se produit en vrai.
"""

from __future__ import annotations

import pytest


class TestLaMiseEnRouteSeMarqueSansSePercuter:
    """Le premier jet de ces tests lancait deux POST par `asyncio.gather` et
    passait deja : le client de test serialise les requetes, la course ne se
    produit pas. Un test vert qui ne peut pas rougir ne prouve rien — on
    provoque donc la collision au point exact ou elle a lieu, le commit."""

    @pytest.mark.asyncio
    async def test_une_collision_au_commit_ne_fait_pas_echouer_le_marquage(
        self, client, monkeypatch
    ):
        from app.routers import config as module
        from sqlalchemy.exc import IntegrityError

        original = module.AsyncSession.commit
        collisions = {"restantes": 1}

        async def commit_qui_percute(self, *a, **k):
            if collisions["restantes"]:
                collisions["restantes"] -= 1
                # Le concurrent a GAGNÉ la course : il a écrit avant nous.
                # Simuler la collision sans poser le marqueur donnerait une
                # situation qui n'existe pas — et le code doit alors lever,
                # ce qu'il fait.
                await original(self, *a, **k)
                raise IntegrityError(
                    "INSERT INTO preferences", {},
                    Exception("UNIQUE constraint failed: preferences.key"),
                )
            return await original(self, *a, **k)

        monkeypatch.setattr(module.AsyncSession, "commit", commit_qui_percute)

        reponse = await client.post("/api/config/onboarding-complete")

        assert collisions["restantes"] == 0, "la collision n'a pas ete provoquee"
        assert reponse.status_code == 200, (
            f"une collision au commit ne doit pas remonter en erreur : "
            f"{reponse.status_code} {reponse.text[:200]}"
        )

    @pytest.mark.asyncio
    async def test_l_etat_final_est_bien_termine_apres_une_collision(self, client):
        await client.post("/api/config/onboarding-complete")
        etat = await client.get("/api/config/onboarding-complete")
        assert etat.json()["completed"] is True
