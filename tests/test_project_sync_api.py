"""L'API de project.sync (0.45, phase 7) - le parcours HTTP réel.

Leçon du 24/08 : tester le parcours, pas la classe. Ces tests passent par les
routes, avec les mêmes doublures que le service (surface de patch unique :
le module indexation).
"""

from pathlib import Path
from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def qdrant_factice(monkeypatch):
    from app.services import indexation

    faux = AsyncMock()
    monkeypatch.setattr(indexation, "get_qdrant_service", lambda: faux)
    monkeypatch.setattr(indexation, "extract_text", lambda _p: "texte")
    return faux


@pytest.fixture
def racine(tmp_path: Path) -> Path:
    d = tmp_path / "dossier-api"
    d.mkdir()
    (d / "doc.txt").write_text("contenu", encoding="utf-8")
    return d


async def _projet(client) -> str:
    resp = await client.post("/api/memory/projects", json={"name": "Par la route"})
    return resp.json()["id"]


class TestLeParcoursComplet:
    @pytest.mark.asyncio
    async def test_racine_plan_apply_journal(self, client, racine, qdrant_factice):
        projet = await _projet(client)

        resp = await client.put(
            f"/api/projects/{projet}/sync/racine", json={"chemin": str(racine)}
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["generation"] == 1

        resp = await client.post(f"/api/projects/{projet}/sync/plan")
        assert resp.status_code == 200, resp.text
        plan = resp.json()
        assert plan["nb_indexer"] == 1
        assert len(plan["operations"]) == 1

        resp = await client.post(
            f"/api/projects/{projet}/sync/apply", json={"plan_id": plan["id"]}
        )
        assert resp.status_code == 202, resp.text

        # l'apply tourne en tâche de fond : attendre sa fin par l'état
        import asyncio

        for _ in range(100):
            resp = await client.get(f"/api/projects/{projet}/sync")
            etat = resp.json()
            if etat["dernier_plan"] and etat["dernier_plan"]["etat"] == "applique":
                break
            await asyncio.sleep(0.05)
        assert etat["dernier_plan"]["etat"] == "applique", etat

        resp = await client.get(f"/api/projects/{projet}/sync/journal")
        assert resp.status_code == 200
        journal = resp.json()["operations"]
        assert len(journal) == 1
        assert journal[0]["etat"] == "fait"

    @pytest.mark.asyncio
    async def test_racine_invalide_400(self, client, tmp_path):
        projet = await _projet(client)

        resp = await client.put(
            f"/api/projects/{projet}/sync/racine",
            json={"chemin": str(tmp_path / "inexistant")},
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_plan_sans_racine_404(self, client):
        projet = await _projet(client)

        resp = await client.post(f"/api/projects/{projet}/sync/plan")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_racine_debranchee_422_cause_lisible(
        self, client, racine, qdrant_factice
    ):
        import shutil

        projet = await _projet(client)
        await client.put(
            f"/api/projects/{projet}/sync/racine", json={"chemin": str(racine)}
        )
        shutil.rmtree(racine)

        resp = await client.post(f"/api/projects/{projet}/sync/plan")

        assert resp.status_code == 422
        corps = resp.json()
        message = (corps.get("detail") or corps.get("message") or "").lower()
        assert "plan" in message, corps

    @pytest.mark.asyncio
    async def test_apply_d_un_plan_caduc_409(self, client, racine, qdrant_factice):
        projet = await _projet(client)
        await client.put(
            f"/api/projects/{projet}/sync/racine", json={"chemin": str(racine)}
        )
        premier = (await client.post(f"/api/projects/{projet}/sync/plan")).json()
        await client.post(f"/api/projects/{projet}/sync/plan")

        resp = await client.post(
            f"/api/projects/{projet}/sync/apply", json={"plan_id": premier["id"]}
        )
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_supprimer_le_projet_delie_la_racine(
        self, client, racine, qdrant_factice
    ):
        """Ménage explicite : les FK SQLite ne sont pas activées."""
        projet = await _projet(client)
        await client.put(
            f"/api/projets/{projet}/sync/racine".replace("projets", "projects"),
            json={"chemin": str(racine)},
        )

        resp = await client.delete(f"/api/memory/projects/{projet}")
        assert resp.status_code in (200, 204), resp.text

        # la racine est libre pour un autre projet
        autre = await _projet(client)
        resp = await client.put(
            f"/api/projects/{autre}/sync/racine", json={"chemin": str(racine)}
        )
        assert resp.status_code == 200, resp.text
