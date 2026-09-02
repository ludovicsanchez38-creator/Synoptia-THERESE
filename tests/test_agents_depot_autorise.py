"""B-099 : une route accepte un chemin de dépôt que sa voisine refuse par 403.

`POST /api/agents/request` résout `source_path` et refuse par un 403 tout
écart avec le dépôt autorisé dans les réglages (agents.py:181-187).
`POST /api/agents/spawn` prenait `request.source_path` sans aucune comparaison
(agents.py:499) : la même garde manquait d'un côté. La portée est bornée,
l'exécuteur d'outils confinant ensuite les chemins, mais la porte d'entrée
n'était pas la même selon la route empruntée.

Le profil demandé ici est volontairement inexistant : la garde de chemin doit
passer AVANT la recherche du profil, sinon le contrôle dépend de l'ordre des
arguments et un profil valide lancerait un vrai agent pendant les tests.
"""
import pytest
from app.routers import agents as routeur_agents


@pytest.fixture
def depot_autorise(tmp_path, monkeypatch):
    autorise = tmp_path / "depot-autorise"
    autorise.mkdir()
    monkeypatch.setattr(routeur_agents, "_get_source_path", lambda: str(autorise))
    return autorise


@pytest.mark.asyncio
async def test_spawn_refuse_un_depot_hors_du_perimetre_autorise(
    client, depot_autorise, tmp_path
):
    ailleurs = tmp_path / "ailleurs"
    ailleurs.mkdir()

    resp = await client.post(
        "/api/agents/spawn",
        json={
            "profile_id": "profil-inexistant",
            "instruction": "lis tout",
            "source_path": str(ailleurs),
        },
    )

    assert resp.status_code == 403, resp.text
    assert "dépôt autorisé" in resp.json()["message"]


@pytest.mark.asyncio
async def test_spawn_laisse_passer_le_depot_autorise(client, depot_autorise):
    """Contrôle : la garde refuse l'écart, pas tout chemin."""
    resp = await client.post(
        "/api/agents/spawn",
        json={
            "profile_id": "profil-inexistant",
            "instruction": "lis tout",
            "source_path": str(depot_autorise),
        },
    )

    assert resp.status_code == 404, resp.text
    assert "Profil" in resp.json()["message"]


@pytest.mark.asyncio
async def test_request_refuse_le_meme_depot_hors_perimetre(
    client, depot_autorise, tmp_path
):
    """Témoin de parité : la route voisine refusait déjà, elle doit continuer."""
    ailleurs = tmp_path / "ailleurs"
    ailleurs.mkdir()

    resp = await client.post(
        "/api/agents/request",
        json={"message": "lis tout", "source_path": str(ailleurs)},
    )

    assert resp.status_code == 403, resp.text
    assert "dépôt autorisé" in resp.json()["message"]
