"""B-1127 : le réimport garde un couple périmètre/identifiant cohérent."""
import json

import pytest
from app.models.entities import Contact
from app.services.cloisonnement import cloison_contacts
from app.services.crm_import import CRMImportService
from sqlmodel import select


@pytest.mark.parametrize("perimetre", ["project", "", "partout"])
async def test_identifiant_vide_ne_detache_pas_le_contact(db_session, perimetre):
    db_session.add(Contact(id="client", first_name="Lucie", scope="project", scope_id="atelier"))
    await db_session.commit()
    csv = f"id,Prénom,Périmètre,ID perimetre,Notes\nclient,Lucie,{perimetre},,Note importée\n"
    resultat = await CRMImportService(db_session).import_contacts(csv.encode(), "contacts.csv")
    assert resultat.updated == 1
    db_session.expire_all()
    contact = await db_session.get(Contact, "client")
    assert (contact.scope, contact.scope_id) == ("project", "atelier")
    assert contact.notes == "Note importée"
    visibles = (await db_session.execute(cloison_contacts(select(Contact), "project", "atelier"))).scalars().all()
    assert contact.id in {c.id for c in visibles}


async def test_creation_globale_ne_garde_pas_un_identifiant_etranger(db_session):
    contenu = json.dumps([{"id": "neuf", "first_name": "Émile", "scope": "partout", "scope_id": "atelier"}]).encode()
    resultat = await CRMImportService(db_session).import_contacts(contenu, "contacts.json")
    assert resultat.created == 1
    contact = await db_session.get(Contact, "neuf")
    assert (contact.scope, contact.scope_id) == ("global", None)


@pytest.mark.parametrize("ancien,nouveau", [("project", "conversation"), ("conversation", "project")])
async def test_changement_perimetre_sans_identifiant_garde_le_couple(db_session, ancien, nouveau):
    db_session.add(Contact(id="prive", first_name="Lucie", scope=ancien, scope_id="dossier-42"))
    await db_session.commit()
    csv = f"id,Prénom,Périmètre,ID perimetre,Notes\nprive,Lucie,{nouveau},,Note actualisée\n"
    resultat = await CRMImportService(db_session).import_contacts(csv.encode(), "contacts.csv")
    assert resultat.updated == 1
    db_session.expire_all()
    contact = await db_session.get(Contact, "prive")
    assert (contact.scope, contact.scope_id) == (ancien, "dossier-42")
    assert contact.notes == "Note actualisée"
    for perimetre in (ancien, nouveau):
        requete = cloison_contacts(
            select(Contact), "project" if perimetre == "project" else "global",
            "dossier-42" if perimetre == "project" else None,
            "dossier-42" if perimetre == "conversation" else None,
        )
        visibles = (await db_session.execute(requete)).scalars().all()
        assert (contact.id in {c.id for c in visibles}) == (perimetre == ancien)


# Entrées inventées après le correctif. None pour « ancien » signifie création.
@pytest.mark.parametrize("nom,ancien,cellules,attendu", [
    ("Agathe", ("project", "ambre"), {"scope": "PROJECT", "scope_id": " "}, ("project", "ambre")),
    ("Benoît", ("project", "brique"), {"scope_id": None}, ("project", "brique")),
    ("Clara", ("project", "chêne"), {"scope": "ailleurs", "scope_id": ""}, ("project", "chêne")),
    ("Dorian", ("conversation", "dialogue"), {"scope": "", "scope_id": ""}, ("conversation", "dialogue")),
    ("Éva", ("project", "école"), {"scope": "Global", "scope_id": "école"}, ("global", None)),
    ("Flora", ("project", "four"), {"scope": "project", "scope_id": "fresque"}, ("project", "fresque")),
    ("Gaspard", None, {"scope": "inconnu", "scope_id": "garage"}, ("global", None)),
    ("Hana", None, {"scope": "", "scope_id": "halle"}, ("global", None)),
    ("Ilan", None, {"scope": "Global", "scope_id": "îlot"}, ("global", None)),
    ("Jade", None, {"scope": "project", "scope_id": "jardin"}, ("project", "jardin")),
])
async def test_rejeu_apres_correctif(db_session, nom, ancien, cellules, attendu):
    if ancien:
        db_session.add(Contact(id=nom, first_name=nom, scope=ancien[0], scope_id=ancien[1]))
        await db_session.commit()
    contenu = json.dumps([{"id": nom, "first_name": nom, "notes": "Notes réimportées", **cellules}]).encode()
    resultat = await CRMImportService(db_session).import_contacts(contenu, "contacts.json")
    assert resultat.updated == int(ancien is not None)
    assert resultat.created == int(ancien is None)
    db_session.expire_all()
    contact = await db_session.get(Contact, nom)
    assert (contact.scope, contact.scope_id) == attendu
    assert contact.notes == "Notes réimportées"


# Dix entrées nouvelles après la reprise Astra v1.
@pytest.mark.parametrize("nom,ancien,cellules,attendu", [
    ("Katia", ("project", "kayak"), {"scope": "conversation", "scope_id": ""}, ("project", "kayak")),
    ("Loris", ("conversation", "lac"), {"scope": "project", "scope_id": None}, ("conversation", "lac")),
    ("Mina", ("project", "miel"), {"scope": "Conversation", "scope_id": "  "}, ("project", "miel")),
    ("Nils", ("conversation", "neige"), {"scope": "PROJECT"}, ("conversation", "neige")),
    ("Olga", ("global", None), {"scope": "project", "scope_id": ""}, ("global", None)),
    ("Paco", ("global", None), {"scope": "conversation", "scope_id": None}, ("global", None)),
    ("Quentin", ("project", "quai"), {"scope": "conversation", "scope_id": "question"}, ("conversation", "question")),
    ("Rita", ("conversation", "rive"), {"scope": "project", "scope_id": "roche"}, ("project", "roche")),
    ("Samia", ("conversation", "sable"), {"scope": "global", "scope_id": ""}, ("global", None)),
    ("Tao", ("project", "terre"), {"scope_id": "tulipe"}, ("project", "tulipe")),
])
async def test_rejeu_astra_apres_correctif(db_session, nom, ancien, cellules, attendu):
    await test_rejeu_apres_correctif(db_session, nom, ancien, cellules, attendu)
