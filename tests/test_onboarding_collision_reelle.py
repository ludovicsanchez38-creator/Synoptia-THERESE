"""La mise en route marquee deux fois EN MEME TEMPS, avec une vraie collision.

02/09/2026, campagne de robustesse du cycle 2 (RB-004, B-161). Dix POST
simultanes sur `/api/config/onboarding-complete` : quatre 500. La garde
d'idempotence posee le 01/09 attrape pourtant bien `IntegrityError`.

Elle n'attrapait rien. Sur une base chiffree, l'erreur ne vient pas de
`sqlite3` mais de `sqlcipher3`, dont la hierarchie d'exceptions est SEPAREE :
SQLAlchemy ne la reconnaissait pas comme une erreur de base, ne la traduisait
pas en `sqlalchemy.exc.IntegrityError`, et l'exception BRUTE du pilote passait
a travers le `except`. Le test existant (`test_onboarding_concurrent.py`)
FABRIQUAIT un `sqlalchemy.exc.IntegrityError` : il verifiait une garde que la
production n'atteignait jamais.

Ici, la collision est REELLE : un concurrent ecrit le marqueur pour de vrai
entre la lecture et le commit, et c'est SQLite qui leve.
"""

from __future__ import annotations

import pytest


class TestUneCollisionReelleSurLesPreferences:

    @pytest.mark.asyncio
    async def test_le_marquage_survit_a_une_collision_du_pilote(self, client, monkeypatch):
        from app.models import database as db_module
        from app.models.entities import Preference
        from app.routers import config as module

        commit_original = module.AsyncSession.commit
        course = {"doublee": False}

        async def commit_apres_le_concurrent(self, *args, **kwargs):
            if not course["doublee"]:
                course["doublee"] = True
                # Le concurrent GAGNE la course et pose le marqueur avant nous.
                async with db_module.AsyncSessionLocal() as autre:
                    autre.add(
                        Preference(
                            key="onboarding_completed",
                            value="true",
                            category="system",
                        )
                    )
                    await commit_original(autre)
            return await commit_original(self, *args, **kwargs)

        monkeypatch.setattr(module.AsyncSession, "commit", commit_apres_le_concurrent)

        reponse = await client.post("/api/config/onboarding-complete")

        assert course["doublee"], "la collision n'a pas ete provoquee"
        assert reponse.status_code == 200, (
            f"marquer la mise en route deux fois ne doit rien casser : "
            f"{reponse.status_code} {reponse.text[:200]}"
        )
        assert reponse.json()["completed"] is True

    @pytest.mark.asyncio
    async def test_les_erreurs_du_pilote_chiffre_sont_classees(self, client):
        """La cause racine, prise a la source : ce que le dialecte async
        annonce comme famille d'exceptions doit etre celle du pilote qui leve.
        """
        from app.models import database as db_module

        if not db_module._db_cipher_active:
            pytest.skip("base non chiffree : le dialecte annonce deja le bon pilote")

        import sqlcipher3

        pilote = db_module.async_engine.dialect.loaded_dbapi
        assert pilote.IntegrityError is sqlcipher3.dbapi2.IntegrityError
        assert issubclass(sqlcipher3.dbapi2.IntegrityError, pilote.Error)
