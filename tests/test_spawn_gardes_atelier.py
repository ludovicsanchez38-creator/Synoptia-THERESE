"""B-422 (cycle 4) : /spawn ne portait que la garde du dépôt autorisé. Contrairement
à /request, il ne vérifiait ni la branche main, ni la propreté de l'arbre, ni
l'absence d'une mission déjà en cours : un agent pouvait tourner pendant une
mission Atelier, sur un travail non enregistré. Mêmes gardes que /request."""

from __future__ import annotations

import subprocess

import pytest


def _depot(tmp_path, branche: str = "main", propre: bool = True):
    depot = tmp_path / "depot"
    depot.mkdir()
    subprocess.run(["git", "init", "-q", "-b", branche, str(depot)], check=True)
    subprocess.run(["git", "-C", str(depot), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(depot), "config", "user.name", "t"], check=True)
    (depot / "README.md").write_text("x", encoding="utf-8")
    subprocess.run(["git", "-C", str(depot), "add", "."], check=True)
    subprocess.run(["git", "-C", str(depot), "commit", "-q", "-m", "init"], check=True)
    if not propre:
        (depot / "README.md").write_text("modifié", encoding="utf-8")
    return depot


def _armer(monkeypatch, depot):
    from app.routers import agents

    monkeypatch.setattr(agents, "_get_source_path", lambda: str(depot))
    monkeypatch.setattr(agents, "_resoudre_depot_autorise", lambda chemin, configure: depot)


@pytest.mark.asyncio
async def test_spawn_refuse_hors_de_main(client, monkeypatch, tmp_path):
    _armer(monkeypatch, _depot(tmp_path, branche="feature"))
    reponse = await client.post("/api/agents/spawn", json={"profile_id": "researcher", "instruction": "x"})
    assert reponse.status_code == 409, reponse.text
    assert "main" in (reponse.json().get("detail") or reponse.json().get("message") or "")


@pytest.mark.asyncio
async def test_spawn_refuse_un_arbre_sale(client, monkeypatch, tmp_path):
    _armer(monkeypatch, _depot(tmp_path, propre=False))
    reponse = await client.post("/api/agents/spawn", json={"profile_id": "researcher", "instruction": "x"})
    assert reponse.status_code == 409, reponse.text
    assert "non enregistrés" in (reponse.json().get("detail") or reponse.json().get("message") or "")


@pytest.mark.asyncio
async def test_spawn_refuse_pendant_une_mission_atelier(client, monkeypatch, tmp_path, db_session):
    from app.models.entities_agents import AgentTask

    _armer(monkeypatch, _depot(tmp_path))
    db_session.add(AgentTask(id="mission-en-cours", title="Mission en cours", status="in_progress"))
    await db_session.commit()
    reponse = await client.post("/api/agents/spawn", json={"profile_id": "researcher", "instruction": "x"})
    assert reponse.status_code == 409, reponse.text
    assert "déjà en cours" in (reponse.json().get("detail") or reponse.json().get("message") or "")
