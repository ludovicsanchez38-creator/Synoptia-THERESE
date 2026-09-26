"""P-132, seconde moitié, lot 1 : l'étape « Perdu » au moteur.

RFC du 26/09 (`docs/plans/2026-09-26-rfc-p132-vocabulaire-unique-perdu.md`,
§4 et §7). Le pipeline mélangeait deux issues opposées dans une seule
colonne : le commentaire du score d'Archive disait « Perdu ou terminé ».
« Perdu » devient une étape à part, identifiant `lost`, huitième colonne,
exclue des prospects en cours, relançable si une date est posée, rangée en
intérêt légitime au titre du RGPD.
"""

from __future__ import annotations

import csv
import io
import json
from datetime import UTC, date, datetime, time, timedelta
from typing import Any

import pytest
from app.models.entities import Activity, Contact
from httpx import AsyncClient
from sqlmodel import select

JOUR = date(2026, 9, 24)


async def _fiche(client: AsyncClient, **champs: Any) -> dict[str, Any]:
    corps = {"first_name": "Karim", "last_name": "Benali", **champs}
    cree = await client.post("/api/memory/contacts", json=corps)
    assert cree.status_code == 200, cree.text
    return cree.json()


# ---------------------------------------------------------------------------
# Le domaine
# ---------------------------------------------------------------------------


def test_perdu_est_une_etape_du_pipeline_entre_actif_et_archive():
    from typing import get_args

    from app.models.schemas import EtapePipeline
    from app.services.crm_utils import LIBELLES_ETAPES

    assert get_args(EtapePipeline) == (
        "contact", "discovery", "proposition", "signature", "delivery", "active", "lost", "archive",
    )
    # Les libellés suivent le même ordre : l'écran et le moteur lisent la même grille.
    assert list(LIBELLES_ETAPES) == list(get_args(EtapePipeline))
    assert LIBELLES_ETAPES["lost"] == "Perdu"


# ---------------------------------------------------------------------------
# Changement d'étape : activité et score
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_passer_une_fiche_en_perdu_ecrit_l_activite_et_le_score(client: AsyncClient, db_session):
    fiche = await _fiche(
        client, company="Benali SARL", email="karim@benali.test", phone="06 00 00 00 00",
        source="referral", stage="proposition",
    )

    reponse = await client.patch(f"/api/crm/contacts/{fiche['id']}/stage", json={"stage": "lost"})

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["stage"] == "lost"
    # Base 50 + courriel 20 + téléphone 15 + entreprise 10 + recommandation 25
    # = 120, puis -100 pour Perdu : 20. Le même poids qu'Archive, pour que qui
    # rangeait ses ventes perdues en Archive garde son score.
    assert reponse.json()["score"] == 20
    activites = (await db_session.execute(
        select(Activity).where(Activity.contact_id == fiche["id"], Activity.type == "stage_change")
    )).scalars().all()
    assert [json.loads(a.extra_data or "{}") for a in activites] == [
        {"old_stage": "proposition", "new_stage": "lost"}
    ]


def test_perdu_pese_comme_archive_et_le_plancher_tient():
    from app.services.scoring import STAGE_SCORES, calculate_base_score

    assert STAGE_SCORES["lost"] == STAGE_SCORES["archive"] == -100
    assert calculate_base_score(Contact(first_name="Nu", stage="lost")) == 0


# ---------------------------------------------------------------------------
# Prospects en cours (Accueil) : Signature compte, Perdu non
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_une_fiche_perdue_ne_compte_pas_parmi_les_prospects(client: AsyncClient, db_session, monkeypatch):
    monkeypatch.setattr("app.routers.dashboard.date_civile_paris", lambda *_a, **_k: JOUR)
    db_session.add_all([
        Contact(id="c-decouverte", first_name="Dé", last_name="Couverte", stage="discovery"),
        Contact(id="c-signature", first_name="Si", last_name="Gnature", stage="signature"),
        Contact(id="c-livraison", first_name="Li", last_name="Vraison", stage="delivery"),
        Contact(id="c-actif", first_name="Ac", last_name="Tif", stage="active"),
        Contact(id="c-perdu", first_name="Per", last_name="Du", stage="lost"),
        Contact(id="c-archive", first_name="Ar", last_name="Chive", stage="archive"),
    ])
    await db_session.commit()

    corps = (await client.get("/api/dashboard/semaine")).json()

    # Constat 6 de la revue : une fiche en Signature reste un prospect en cours
    # tant que la livraison n'a pas commencé.
    assert corps["prospects_par_etape"] == {"discovery": 1, "signature": 1}


@pytest.mark.asyncio
async def test_signature_est_un_prospect_en_cours_et_deja_un_contrat(client: AsyncClient, db_session, monkeypatch):
    """Les deux lectures ne se contredisent pas : « prospect en cours » veut
    dire « avant la livraison » (Accueil), « contrat » veut dire « accord
    donné » (base légale RGPD). Signature = accord donné ou en cours de
    formalisation, livraison pas commencée : elle est les deux à la fois."""
    monkeypatch.setattr("app.routers.dashboard.date_civile_paris", lambda *_a, **_k: JOUR)
    fiche = await _fiche(client, stage="signature")

    semaine = (await client.get("/api/dashboard/semaine")).json()
    rgpd = await client.post(f"/api/rgpd/infer/{fiche['id']}")

    assert semaine["prospects_par_etape"].get("signature") == 1
    assert rgpd.status_code == 200, rgpd.text
    assert rgpd.json()["base_legale"] == "contrat"


# ---------------------------------------------------------------------------
# Relances : Perdu se relance si une date est posée, Archive jamais
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_une_fiche_perdue_datee_se_relance_une_archivee_jamais(db_session):
    from app.services.relances import contacts_a_relancer

    hier = datetime.now(UTC) - timedelta(days=1)
    db_session.add_all([
        Contact(id="c-perdu", first_name="Rappel", last_name="Dans6mois", stage="lost", next_follow_up=hier),
        Contact(id="c-archive", first_name="Anonyme", last_name="Rgpd", stage="archive", next_follow_up=hier),
    ])
    await db_session.commit()

    trouves = (await db_session.execute(contacts_a_relancer())).scalars().all()

    assert [c.id for c in trouves] == ["c-perdu"]


# ---------------------------------------------------------------------------
# Base légale RGPD
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_une_fiche_perdue_est_en_interet_legitime(client: AsyncClient):
    """Un prospect perdu n'a jamais signé."""
    fiche = await _fiche(client, stage="lost")

    reponse = await client.post(f"/api/rgpd/infer/{fiche['id']}")

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["base_legale"] == "interet_legitime"


# ---------------------------------------------------------------------------
# Tableur : export, import, filtre
# ---------------------------------------------------------------------------


async def _exporter(client: AsyncClient, filtre: str = "") -> list[dict[str, str]]:
    reponse = await client.post(f"/api/crm/export/contacts?format=csv{filtre}")
    assert reponse.status_code == 200, reponse.text
    return list(csv.DictReader(io.StringIO(reponse.content.decode("utf-8-sig"))))


@pytest.mark.asyncio
async def test_l_export_tableur_ecrit_perdu_et_filtre_sur_lost(client: AsyncClient):
    await _fiche(client, last_name="Perdue", stage="lost")
    await _fiche(client, last_name="Encours", stage="discovery")

    lignes = await _exporter(client)
    assert next(ligne for ligne in lignes if ligne["Nom"] == "Perdue")["Étape"] == "Perdu"

    filtrees = await _exporter(client, "&stage=lost")
    assert [ligne["Nom"] for ligne in filtrees] == ["Perdue"]


@pytest.mark.parametrize("cellule", ["Perdu", "perdu", "PERDU", "lost"])
@pytest.mark.asyncio
async def test_l_import_tableur_relit_perdu(client: AsyncClient, cellule: str):
    tampon = io.StringIO()
    graveur = csv.DictWriter(tampon, fieldnames=["Prénom", "Nom", "Étape"])
    graveur.writeheader()
    graveur.writerow({"Prénom": "Import", "Nom": f"Perdu-{cellule}", "Étape": cellule})

    apercu = await client.post(
        "/api/crm/import/contacts/preview",
        files={"file": ("contacts.csv", tampon.getvalue().encode("utf-8"), "text/csv")},
    )
    importe = await client.post(
        "/api/crm/import/contacts",
        files={"file": ("contacts.csv", tampon.getvalue().encode("utf-8"), "text/csv")},
    )

    assert apercu.status_code == 200, apercu.text
    # P-130 : l'aperçu ne signale plus « Perdu » comme une étape inconnue.
    assert not [e for e in apercu.json()["validation_errors"] if e.get("column") == "stage"], apercu.json()
    assert importe.status_code == 200, importe.text
    assert importe.json()["created"] == 1, importe.json()
    relue = next(ligne for ligne in await _exporter(client) if ligne["Nom"] == f"Perdu-{cellule}")
    assert relue["Étape"] == "Perdu"


@pytest.mark.asyncio
async def test_l_import_json_de_contacts_garde_lost(client: AsyncClient):
    reponse = await client.post("/api/data/import/contacts", json={
        "contacts": [{"id": "c-json-perdu", "first_name": "Json", "last_name": "Perdu", "stage": "lost"}],
    })

    assert reponse.status_code == 200, reponse.text
    fiche = (await client.get("/api/memory/contacts/c-json-perdu")).json()
    assert fiche["stage"] == "lost"


# ---------------------------------------------------------------------------
# Synchro Google Sheets
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("cellule", "attendue"), [
    ("lost", "lost"),
    ("Perdu", "lost"),
    # B-1416 a décidé que l'import accepte identifiant et libellé ; la synchro
    # ne lisait que l'identifiant.
    ("Découverte", "discovery"),
])
@pytest.mark.asyncio
async def test_la_synchro_lit_l_identifiant_et_le_libelle(client: AsyncClient, cellule: str, attendue: str):
    fiche = await _fiche(client, stage="proposition")

    reponse = await client.post("/api/crm/sync/import", json={
        "clients": [{"ID": fiche["id"], "Nom": "Karim Benali", "Stage": cellule}],
    })

    assert reponse.status_code == 200, reponse.text
    assert (await client.get(f"/api/memory/contacts/{fiche['id']}")).json()["stage"] == attendue


@pytest.mark.asyncio
async def test_la_synchro_laisse_l_etape_sur_une_cellule_inconnue(client: AsyncClient):
    fiche = await _fiche(client, stage="proposition")

    await client.post("/api/crm/sync/import", json={
        "clients": [{"ID": fiche["id"], "Nom": "Karim Benali", "Stage": "Abandonné"}],
    })

    assert (await client.get(f"/api/memory/contacts/{fiche['id']}")).json()["stage"] == "proposition"


@pytest.mark.asyncio
async def test_la_ligne_poussee_au_tableur_se_relit_en_perdu(client: AsyncClient, db_session, monkeypatch):
    """Constat 1 de la revue : la synchro n'est pas à sens unique. La création
    d'une fiche CRM pousse une ligne dans la feuille « Clients ». Elle y écrit
    le libellé de l'écran, et la synchro la relit sans perdre l'étape."""
    from app.models.entities import Preference

    db_session.add_all([
        Preference(key="crm_spreadsheet_id", value="feuille-test", category="crm"),
        Preference(key="crm_sheets_access_token", value="jeton-chiffre", category="crm"),
    ])
    await db_session.commit()

    poussees: list[list[str]] = []

    class FeuilleFactice:
        def __init__(self, access_token: str | None = None, api_key: str | None = None) -> None:
            assert access_token == "jeton-clair"

        async def append_row(self, spreadsheet_id: str, onglet: str, valeurs: list[str]) -> None:
            assert (spreadsheet_id, onglet) == ("feuille-test", "Clients")
            poussees.append(valeurs)

    monkeypatch.setattr("app.services.encryption.decrypt_value", lambda _valeur: "jeton-clair")
    monkeypatch.setattr("app.services.sheets_service.GoogleSheetsService", FeuilleFactice)

    cree = await client.post("/api/crm/contacts", json={
        "first_name": "Karim", "last_name": "Benali", "company": "Benali SARL", "stage": "lost",
    })

    assert cree.status_code == 200, cree.text
    assert len(poussees) == 1, "sans les deux préférences, le test ne pousse rien et ne prouve rien"
    ligne = dict(zip(["ID", "Nom", "Entreprise", "Email", "Tel", "Source", "Stage", "Score", "Tags"],
                     poussees[0], strict=True))
    assert ligne["Stage"] == "Perdu", "la feuille reçoit le mot de l'écran, pas l'identifiant"

    relue = await client.post("/api/crm/sync/import", json={"clients": [{**ligne, "ID": "c-relue"}]})
    assert relue.status_code == 200, relue.text
    assert (await client.get("/api/memory/contacts/c-relue")).json()["stage"] == "lost"


# ---------------------------------------------------------------------------
# Ce que reçoivent les modèles : le libellé, pas l'identifiant
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_l_agent_relance_clients_recoit_le_libelle(db_session):
    from app.services.action_agents import _gather_local_context

    db_session.add(Contact(
        id="c-agent", first_name="Sophie", last_name="Garcia", stage="lost",
        next_follow_up=datetime.combine(JOUR, time(9, 0)),
    ))
    await db_session.commit()

    contexte = await _gather_local_context(["crm"])

    assert "étape : Perdu" in contexte
    assert "étape : lost" not in contexte


@pytest.mark.asyncio
async def test_la_fiche_lue_par_le_modele_porte_le_libelle(db_session):
    from app.services.memory_tools import execute_memory_tool

    db_session.add(Contact(first_name="Karim", last_name="Benali", stage="lost"))
    await db_session.commit()

    charge = json.loads(await execute_memory_tool("read_contact", {"query": "Benali"}, db_session))

    # Revue du diff, constat 2 : `stage` reste l'identifiant, comme dans la
    # liste des contacts ; le mot et sa définition voyagent à côté.
    fiche = charge["contacts"][0]
    assert fiche["stage"] == "lost"
    assert fiche["etape"] == "Perdu"
    assert fiche["definition_de_l_etape"] == "la vente n'a pas abouti"


@pytest.mark.asyncio
async def test_list_contacts_puis_get_contact_rendent_la_meme_forme(client: AsyncClient):
    """Revue du diff, constat 2 : le même modèle lisait l'identifiant par
    `list_contacts` et le libellé par `get_contact`, sous la même clé. Les deux
    portes MCP rendent désormais l'identifiant sous `stage` ; la fiche ajoute
    le mot et sa définition, là où « signature » seul se lisait « en attente
    de signature »."""
    from app.services.mcp_therese_server import TOOL_ROUTES

    fiche = await _fiche(client, stage="signature")
    _, route_liste = TOOL_ROUTES["list_contacts"]
    _, route_fiche = TOOL_ROUTES["get_contact"]

    liste = await client.get(route_liste)
    lue = await client.get(route_fiche.format(contact_id=fiche["id"]))

    assert liste.status_code == 200, liste.text
    assert lue.status_code == 200, lue.text
    [dans_la_liste] = [c for c in liste.json() if c["id"] == fiche["id"]]
    assert dans_la_liste["stage"] == lue.json()["stage"] == "signature"
    assert lue.json()["etape"] == "Signature"
    assert "accord est donné" in lue.json()["definition_de_l_etape"]


def test_le_skill_proposition_donne_l_etape_en_toutes_lettres(tmp_path):
    from app.services.skills.text_skills import ProposalSkill

    skill = ProposalSkill(tmp_path)
    enrichissement = skill.get_enrichment_context({}, {
        "inputs": {"client_name": "Benali"},
        "contacts": [{"name": "Karim Benali", "company": "Benali SARL", "stage": "lost"}],
    })

    assert "Étape : Perdu" in enrichissement["client_context"]
    assert "lost" not in enrichissement["client_context"]


def test_le_contexte_des_skills_porte_l_etape_de_la_fiche():
    """Le dictionnaire donné aux skills n'avait pas de clé `stage` : la ligne
    du skill de proposition affichait toujours « Non renseigné »."""
    from app.routers.skills import contact_pour_un_skill

    vue = contact_pour_un_skill(Contact(first_name="Karim", last_name="Benali", stage="lost"))

    assert vue["stage"] == "lost"
    assert vue["name"] == "Karim Benali"
