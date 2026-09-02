"""Un filtre que le serveur ne connaît pas ne doit pas passer pour appliqué.

RB2-007 (B-178). `POST /api/memory/search` recevait
`{"query": "Zorglub", "types": ["contacts"]}` et rendait 200 avec des fiches ET
des dossiers : `MemorySearchRequest` déclare `entity_types`, Pydantic ignorait
en silence le champ `types`, et l'appelant croyait sa recherche restreinte
alors qu'elle ne l'était pas.

Le client, lui, a été corrigé (commit `e8389ed7`, table `TYPES_SERVEUR` de
`services/api/memory.ts`) : il envoie `entity_types` au singulier. Ce qui
restait ouvert est côté serveur, et c'est le silence.
"""

import pytest


class TestUnFiltreInconnuEstRefuse:
    @pytest.mark.asyncio
    async def test_le_champ_types_du_client_est_refuse(self, client):
        reponse = await client.post(
            "/api/memory/search",
            json={"query": "Zorglub", "limit": 20, "types": ["contacts"]},
        )

        assert reponse.status_code == 422, (
            "un filtre inconnu est absorbé en silence et la recherche répond "
            f"comme si elle avait obéi : {reponse.status_code} {reponse.text[:300]}"
        )
        assert "types" in reponse.text, (
            f"le refus ne nomme pas le champ en cause : {reponse.text[:300]}"
        )

    @pytest.mark.asyncio
    async def test_un_filtre_declare_passe_toujours(self, client, sample_contact_data):
        """La garde vise le champ inconnu, pas la route."""
        await client.post("/api/memory/contacts", json=sample_contact_data)

        reponse = await client.post(
            "/api/memory/search",
            json={
                "query": "Jean",
                "limit": 20,
                "entity_types": ["contact"],
                "include_semantic": False,
            },
        )

        assert reponse.status_code == 200, reponse.text[:300]
        types_rendus = {r["entity_type"] for r in reponse.json()["results"]}
        assert types_rendus <= {"contact"}, (
            f"une recherche restreinte aux fiches rend autre chose : {types_rendus}"
        )
