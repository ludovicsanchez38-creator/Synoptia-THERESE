"""B-1284 : la restauration ne suspendait pas les créations du chat (B-1276 ne
couvrait que la purge). Elle comptait sur begin(), qui ne suit plus une
réponse en flux une fois ses en-têtes partis : le chat en flux exécute ses
outils dans le corps de la réponse, donc une création pouvait écrire pendant
la fermeture des moteurs ou l'extraction. Revue du diff, passe 6 (cas D)."""

import json
from pathlib import Path

import pytest

PASSE = "Passphrase-Test-123"


@pytest.mark.asyncio
async def test_la_restauration_refuse_une_creation_du_chat(client, monkeypatch):
    from app.config import settings
    from app.routers import memory as memoire
    from app.services import memory_tools as mt

    data_dir = Path(settings.data_dir)
    (data_dir / "THERESE.md").write_text("consignes", encoding="utf-8")
    resp = await client.post("/api/data/backup", json={"password": PASSE})
    assert resp.status_code == 200, resp.text
    nom = resp.json()["backup_name"]

    issues: list[dict] = []
    arret_reel = memoire.arreter_les_indexations_de_fiches

    async def arret_pendant_lequel_le_chat_cree():
        from app.models.database import get_session_context

        async with get_session_context() as session:
            issues.append(json.loads(await mt.execute_create_contact({"first_name": "Tardif"}, session)))
        return await arret_reel()

    monkeypatch.setattr(memoire, "arreter_les_indexations_de_fiches", arret_pendant_lequel_le_chat_cree)
    r = await client.post(f"/api/data/restore/{nom}?confirm=true", json={"password": PASSE})
    assert r.status_code == 200, r.text
    assert issues and issues[0].get("success") is False, issues
    assert mt._CREATIONS_SUSPENDUES == 0, "suspension non levée après la restauration"
