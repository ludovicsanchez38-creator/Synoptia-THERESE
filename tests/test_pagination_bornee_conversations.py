"""La pagination des conversations doit se borner comme les autres.

02/09/2026, campagne de robustesse du cycle 2 (RB-009, B-166).
`GET /api/chat/conversations?limit=-1` rendait 200 avec la table ENTIERE :
SQLite lit `LIMIT -1` comme « sans limite ». Mesure du jour : `?limit=2` ->
2 elements, `?limit=0` -> 0, `?limit=-1` -> les 5 sur 5, `?limit=1000000000`
accepte, `?offset=-1` traite comme 0.

Temoins pris le meme jour sur les routes bornees : `GET
/api/memory/contacts?limit=-1` -> 422 « Input should be greater than or equal
to 1 ». La borne existait partout ailleurs ; cette route ne l'avait pas.
"""

from __future__ import annotations

import pytest


class TestLaPaginationDesConversationsEstBornee:

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "requete",
        [
            "limit=-1",
            "limit=0",
            "limit=1000000000",
            "offset=-1",
        ],
    )
    async def test_une_borne_hors_limites_est_refusee(self, client, requete):
        reponse = await client.get(f"/api/chat/conversations?{requete}")

        assert reponse.status_code == 422, (
            f"« {requete} » doit etre refuse comme sur /api/memory/contacts : "
            f"{reponse.status_code} {reponse.text[:200]}"
        )

    @pytest.mark.asyncio
    async def test_limit_moins_un_ne_rend_pas_la_table_entiere(self, client):
        for titre in ("une", "deux", "trois"):
            creation = await client.post(
                "/api/chat/conversations", json={"title": titre}
            )
            assert creation.status_code == 200, creation.text

        reponse = await client.get("/api/chat/conversations?limit=-1")

        assert reponse.status_code != 200 or len(reponse.json()) <= 1, (
            "LIMIT -1 vaut « sans limite » pour SQLite : la pagination "
            "devient contournable par un simple signe moins"
        )

    @pytest.mark.asyncio
    async def test_une_pagination_normale_marche_toujours(self, client):
        for titre in ("une", "deux", "trois"):
            await client.post("/api/chat/conversations", json={"title": titre})

        page = await client.get("/api/chat/conversations?limit=2&offset=0")
        assert page.status_code == 200, page.text
        assert len(page.json()) == 2

        suite = await client.get("/api/chat/conversations?limit=2&offset=2")
        assert suite.status_code == 200, suite.text
        assert len(suite.json()) == 1
