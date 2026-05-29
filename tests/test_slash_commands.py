"""
Tests des commandes slash deterministes (sans LLM).

Verrouille la regression #bugs-21052026 : /contact, /projet, /rdv doivent
s'executer en CRUD direct, sans LLM, sans creation en masse.
"""


import pytest
from app.models.entities import Contact, Project
from app.services.slash_commands import (
    _split_positional_and_kwargs,
    execute_slash_command,
    parse_slash_command,
)
from sqlmodel import select

# -------- Detection --------

def test_parse_detects_known_commands():
    assert parse_slash_command("/contact Jean Dupont") == ("contact", "Jean Dupont")
    assert parse_slash_command("/projet Refonte site") == ("projet", "Refonte site")
    assert parse_slash_command("/rdv Point date=2026-06-03T14:00") == (
        "rdv",
        "Point date=2026-06-03T14:00",
    )


def test_parse_ignores_non_commands():
    assert parse_slash_command("Bonjour Therese") is None
    assert parse_slash_command("/resume") is None  # commande non deterministe
    assert parse_slash_command("/inconnue truc") is None
    assert parse_slash_command("") is None


# -------- Parsing arguments --------

def test_split_positional_and_kwargs():
    pos, kw = _split_positional_and_kwargs("Jean Dupont email=jean@x.fr tel=0601 societe=Acme")
    assert pos == "Jean Dupont"
    assert kw == {"email": "jean@x.fr", "phone": "0601", "company": "Acme"}


def test_split_value_with_spaces():
    pos, kw = _split_positional_and_kwargs("Refonte site budget=5000 desc=Site vitrine moderne")
    assert pos == "Refonte site"
    assert kw["budget"] == "5000"
    assert kw["description"] == "Site vitrine moderne"


def test_split_no_kwargs():
    pos, kw = _split_positional_and_kwargs("Juste du texte")
    assert pos == "Juste du texte"
    assert kw == {}


# -------- Execution deterministe --------

@pytest.mark.asyncio
async def test_contact_command_creates_one(db_session):
    msg = await execute_slash_command("contact", "Jean Dupont email=jean@x.fr", db_session)
    assert "Jean Dupont" in msg
    contacts = (await db_session.execute(select(Contact))).scalars().all()
    assert len(contacts) == 1
    assert contacts[0].email == "jean@x.fr"


@pytest.mark.asyncio
async def test_contact_command_no_duplicate(db_session):
    await execute_slash_command("contact", "Jean Dupont", db_session)
    msg2 = await execute_slash_command("contact", "Jean Dupont", db_session)
    assert "déjà" in msg2.lower() or "réutilise" in msg2.lower()
    contacts = (await db_session.execute(select(Contact))).scalars().all()
    assert len(contacts) == 1


@pytest.mark.asyncio
async def test_projet_command_creates_one_with_budget(db_session):
    msg = await execute_slash_command("projet", "Refonte site budget=5000 statut=active", db_session)
    assert "Refonte site" in msg
    projects = (await db_session.execute(select(Project))).scalars().all()
    assert len(projects) == 1
    assert projects[0].budget == 5000.0


@pytest.mark.asyncio
async def test_projet_command_no_mass_creation(db_session):
    """Le coeur de la regression : N appels du meme projet -> 1 seule ligne."""
    for _ in range(5):
        await execute_slash_command("projet", "Site Web", db_session)
    projects = (await db_session.execute(select(Project))).scalars().all()
    assert len(projects) == 1


@pytest.mark.asyncio
async def test_rdv_without_date_asks_for_date(db_session):
    msg = await execute_slash_command("rdv", "Point hebdo", db_session)
    assert "date" in msg.lower()


@pytest.mark.asyncio
async def test_rdv_invalid_date(db_session):
    msg = await execute_slash_command("rdv", "Point date=pas-une-date", db_session)
    assert "invalide" in msg.lower() or "iso" in msg.lower()
