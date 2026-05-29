"""
Tests pour les memory tools (create_contact / create_project).

Regression #bugs-21052026 : les commandes / passaient par le LLM qui creait
des projets EN MASSE (32 puis 49 doublons) faute de deduplication, et 0 contact
(last_name obligatoire). Ces tests verrouillent la deduplication et le nom simple.
"""

import json

import pytest
from app.models.entities import Contact, Project
from app.services.memory_tools import execute_create_contact, execute_create_project
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
