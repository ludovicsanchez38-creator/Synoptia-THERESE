"""
Tests pour les memory tools (create_contact / create_project).

Regression #bugs-21052026 : les commandes / passaient par le LLM qui creait
des projets EN MASSE (32 puis 49 doublons) faute de deduplication, et 0 contact
(last_name obligatoire). Ces tests verrouillent la deduplication et le nom simple.
"""

import json

import pytest
from app.models.entities import Contact, Project
from app.services.memory_tools import (
    execute_create_contact,
    execute_create_project,
    execute_read_contact,
)
from sqlmodel import select


async def _count(session, model) -> int:
    rows = (await session.execute(select(model))).scalars().all()
    return len(rows)


@pytest.mark.asyncio
async def test_create_project_dedup_same_name(db_session):
    """Deux create_project avec le meme nom -> une seule ligne (anti-masse)."""
    r1 = json.loads(await execute_create_project({"name": "Site Web"}, db_session))
    r2 = json.loads(await execute_create_project({"name": "Site Web"}, db_session))

    assert r1["success"] is True
    assert r2["success"] is True
    assert r2.get("already_existed") is True
    assert r1["project_id"] == r2["project_id"]
    assert await _count(db_session, Project) == 1


@pytest.mark.asyncio
async def test_create_project_dedup_case_and_space_insensitive(db_session):
    """Le nom est compare insensible a la casse et aux espaces."""
    await execute_create_project({"name": "Projet Alpha"}, db_session)
    await execute_create_project({"name": "  projet alpha "}, db_session)
    assert await _count(db_session, Project) == 1


@pytest.mark.asyncio
async def test_create_project_different_names(db_session):
    """Deux noms differents -> deux projets."""
    await execute_create_project({"name": "Alpha"}, db_session)
    await execute_create_project({"name": "Beta"}, db_session)
    assert await _count(db_session, Project) == 2


@pytest.mark.asyncio
async def test_create_contact_single_name(db_session):
    """Un prenom seul suffit (last_name optionnel) -> 1 contact cree."""
    r = json.loads(await execute_create_contact({"first_name": "Jean"}, db_session))
    assert r["success"] is True
    assert await _count(db_session, Contact) == 1


@pytest.mark.asyncio
async def test_create_contact_dedup_by_email(db_session):
    """Meme email -> pas de doublon."""
    await execute_create_contact(
        {"first_name": "Jean", "last_name": "Dupont", "email": "jean@x.fr"}, db_session
    )
    r2 = json.loads(
        await execute_create_contact(
            {"first_name": "Jean", "last_name": "Dupont", "email": "jean@x.fr"}, db_session
        )
    )
    assert r2.get("already_existed") is True
    assert await _count(db_session, Contact) == 1


@pytest.mark.asyncio
async def test_create_contact_dedup_by_name_case_insensitive(db_session):
    """Meme nom complet (insensible a la casse) -> pas de doublon."""
    await execute_create_contact({"first_name": "Marie", "last_name": "Curie"}, db_session)
    await execute_create_contact({"first_name": "marie", "last_name": "curie"}, db_session)
    assert await _count(db_session, Contact) == 1


@pytest.mark.asyncio
async def test_create_contact_requires_at_least_a_name(db_session):
    """Sans aucun nom -> erreur, rien cree."""
    r = json.loads(await execute_create_contact({}, db_session))
    assert "error" in r
    assert await _count(db_session, Contact) == 0


# ============================================================
# BUG-146 : recherche de contact approchée (retours Dr_logic 19/07)
# « Baudin » ne trouvait pas BODIN et le modèle partait en vrille sur un
# résultat vide. La recherche exacte ignore désormais les accents, et un
# zéro-résultat propose des rapprochements (« Voulais-tu dire BODIN ? »).
# ============================================================


@pytest.mark.asyncio
async def test_read_contact_exact_insensible_aux_accents(db_session):
    db_session.add(Contact(first_name="Jérôme", last_name="Delaunay"))
    await db_session.commit()

    r = json.loads(await execute_read_contact({"query": "jerome"}, db_session))

    assert r["found"] is True
    assert r["contacts"][0]["display_name"] == "Jérôme Delaunay"


@pytest.mark.asyncio
async def test_read_contact_suggestions_orthographe_proche(db_session):
    db_session.add(Contact(first_name="Marc", last_name="BODIN", company="Forge SA"))
    db_session.add(Contact(first_name="Julie", last_name="Dupont"))
    await db_session.commit()

    r = json.loads(await execute_read_contact({"query": "Baudin"}, db_session))

    assert r["found"] is False
    assert any("BODIN" in s for s in r.get("suggestions", []))
    assert "Dupont" not in json.dumps(r.get("suggestions", []), ensure_ascii=False)
    # Le message doit guider le modèle vers une question de clarification
    assert "Voulais-tu dire" in r["message"] or "voulais-tu dire" in r["message"].lower()


@pytest.mark.asyncio
async def test_read_contact_zero_resultat_sans_proche_reste_propre(db_session):
    db_session.add(Contact(first_name="Julie", last_name="Dupont"))
    await db_session.commit()

    r = json.loads(await execute_read_contact({"query": "Xylophone"}, db_session))

    assert r["found"] is False
    assert r.get("suggestions", []) == []
    assert "Aucun contact" in r["message"]
