"""B-1276 : la purge n'attendait qu'un instantané des créations du chat en vol
(B-1260). Une création lancée pendant ses autres attentes (fiche en vol,
profil) écrivait après elle, ou retrouvait le verrou d'écriture de SQLite.
Pendant « Effacer toutes mes données », le chat ne crée plus rien et le dit.
Revue du diff, passe 5 (cas B2)."""

import json

import pytest
from app.models.entities import Contact
from sqlmodel import select


@pytest.mark.asyncio
async def test_une_creation_pendant_la_suspension_est_refusee_et_dite(db_session):
    from app.services import memory_tools as mt

    async with mt.creations_du_chat_suspendues():
        resultat = json.loads(await mt.execute_create_contact({"first_name": "Marie"}, db_session))
    assert resultat.get("success") is False, resultat
    assert "effacement" in json.dumps(resultat, ensure_ascii=False).lower(), resultat
    assert not (await db_session.execute(select(Contact))).scalars().all()

    apres = json.loads(await mt.execute_create_contact({"first_name": "Marie"}, db_session))
    assert apres.get("success") is True, apres


@pytest.mark.asyncio
async def test_la_purge_refuse_une_creation_lancee_pendant_ses_attentes(client, monkeypatch):
    from app.routers import memory as memoire
    from app.services import memory_tools as mt

    issues: list[dict] = []
    arret_reel = memoire.arreter_les_indexations_de_fiches

    async def arret_pendant_lequel_le_chat_cree():
        from app.models.database import get_session_context

        async with get_session_context() as session:
            issues.append(json.loads(await mt.execute_create_contact({"first_name": "Tardif"}, session)))
        await arret_reel()

    monkeypatch.setattr(memoire, "arreter_les_indexations_de_fiches", arret_pendant_lequel_le_chat_cree)
    r = await client.delete("/api/data/all?confirm=true")
    assert r.status_code == 200, r.text
    assert issues and issues[0].get("success") is False, issues
    assert (await client.get("/api/memory/contacts")).json() == []
