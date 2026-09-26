"""P-132, seconde moitié, lot 3 : les prestations parlent la langue du pipeline.

RFC du 26/09 (`docs/plans/2026-09-26-rfc-p132-vocabulaire-unique-perdu.md`,
§3 et §5). Sous la même fiche, le Pipeline disait Contact, Découverte,
Proposition, Signature, Livraison, Actif, Archive, et la prestation Piste,
Proposition envoyée, Signée, Perdue, En cours, Terminée. Deux champs restent
deux champs (une personne peut avoir une vente en cours ET une autre en
proposition), mais ils parlent la même langue : mêmes identifiants, mêmes
libellés, une seule source.

Correspondance (injective, donc réversible) :
piste -> discovery, proposition -> proposition, gagne -> signature,
perdue -> lost, en_cours -> delivery, terminee -> archive.
"""

from __future__ import annotations

import importlib.util
import json
import logging
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from httpx import AsyncClient
from sqlalchemy import create_engine, text

RACINE = Path(__file__).resolve().parent.parent
REVISION = RACINE / "src/backend/alembic/versions/c9d0e1f2a3b4_prestations_parlent_le_pipeline.py"

ANCIENNES = ("piste", "proposition", "gagne", "perdue", "en_cours", "terminee")
NOUVELLES = ("discovery", "proposition", "signature", "lost", "delivery", "archive")
HORODATAGE = "2026-08-01 10:00:00.000000"


# ---------------------------------------------------------------------------
# Le domaine
# ---------------------------------------------------------------------------


def test_une_prestation_prend_six_des_huit_etapes_du_pipeline():
    """Constat 7 de la revue : la liste dérive du domaine des étapes, dans son
    ordre. « Contact » et « Actif » décrivent une personne, pas une vente."""
    from typing import get_args

    from app.models.entities import PHASES_DE_PRESTATION, PHASES_OUVERTES
    from app.models.schemas import EtapePipeline

    assert PHASES_DE_PRESTATION == ("discovery", "proposition", "signature", "delivery", "lost", "archive")
    derivees = tuple(e for e in get_args(EtapePipeline) if e not in {"contact", "active"})
    assert derivees == PHASES_DE_PRESTATION
    assert PHASES_OUVERTES == ("discovery", "proposition", "signature", "delivery")


def test_chaque_etape_a_sa_definition():
    from typing import get_args

    from app.models.schemas import EtapePipeline
    from app.services.crm_utils import DEFINITIONS_ETAPES

    assert list(DEFINITIONS_ETAPES) == list(get_args(EtapePipeline))
    signature = DEFINITIONS_ETAPES["signature"]
    assert "accord est donné" in signature and "livraison n'a pas commencé" in signature
    assert "attente" not in signature


# ---------------------------------------------------------------------------
# L'API
# ---------------------------------------------------------------------------


async def _fiche(client: AsyncClient, nom: str = "Martin") -> str:
    reponse = await client.post("/api/memory/contacts", json={"first_name": "Élodie", "last_name": nom})
    assert reponse.status_code == 200, reponse.text
    return str(reponse.json()["id"])


@pytest.mark.parametrize("etape", ["discovery", "proposition", "signature", "delivery", "lost", "archive"])
@pytest.mark.asyncio
async def test_l_api_accepte_les_six_etapes(client: AsyncClient, etape: str):
    contact_id = await _fiche(client)

    reponse = await client.post("/api/prestations", json={
        "contact_id": contact_id, "intitule": "FORGER", "phase": etape,
    })

    assert reponse.status_code == 201, reponse.text
    assert reponse.json()["phase"] == etape


@pytest.mark.parametrize("valeur", ["piste", "gagne", "en_cours", "terminee", "perdue", "contact", "active"])
@pytest.mark.asyncio
async def test_l_api_refuse_l_ancien_vocabulaire_et_les_etapes_d_une_personne(client: AsyncClient, valeur: str):
    contact_id = await _fiche(client)

    creee = await client.post("/api/prestations", json={
        "contact_id": contact_id, "intitule": "FORGER", "phase": valeur,
    })
    modifiee = await client.post("/api/prestations", json={
        "contact_id": contact_id, "intitule": "FORGER", "phase": "discovery",
    })
    patch = await client.patch(f"/api/prestations/{modifiee.json()['id']}", json={"phase": valeur})

    assert creee.status_code == 400, creee.text
    assert patch.status_code == 400, patch.text


# ---------------------------------------------------------------------------
# La migration ad hoc du démarrage
# ---------------------------------------------------------------------------


def _base_d_avant(chemin: Path, *, valeurs: tuple[str, ...] = ANCIENNES) -> None:
    """Une base d'avant P-132 : la table telle que la créait la 0.59."""
    with closing(sqlite3.connect(str(chemin))) as conn:
        conn.execute("CREATE TABLE contacts (id TEXT PRIMARY KEY, stage TEXT)")
        conn.execute(
            "CREATE TABLE prestations ("
            "id TEXT PRIMARY KEY, contact_id TEXT NOT NULL, intitule TEXT NOT NULL, "
            "montant_ht REAL, phase TEXT NOT NULL DEFAULT 'piste', "
            "created_at TIMESTAMP NOT NULL, updated_at TIMESTAMP NOT NULL)"
        )
        for numero, valeur in enumerate(valeurs):
            conn.execute(
                "INSERT INTO prestations (id, contact_id, intitule, phase, created_at, updated_at)"
                " VALUES (?, 'c1', ?, ?, ?, ?)",
                (f"p{numero}", f"Prestation {numero}", valeur, HORODATAGE, HORODATAGE),
            )
        conn.commit()


def _lignes(chemin: Path) -> list[tuple[Any, ...]]:
    with closing(sqlite3.connect(str(chemin))) as conn:
        return conn.execute("SELECT id, phase, updated_at FROM prestations ORDER BY id").fetchall()


def test_le_demarrage_reecrit_les_six_anciennes_valeurs_sans_toucher_updated_at(tmp_path):
    from app.models.database import apply_adhoc_migrations

    base = tmp_path / "therese.db"
    _base_d_avant(base)

    apply_adhoc_migrations(base)

    assert _lignes(base) == [
        (f"p{numero}", nouvelle, HORODATAGE) for numero, nouvelle in enumerate(NOUVELLES)
    ]


def test_le_second_demarrage_ne_change_rien(tmp_path):
    from app.models.database import apply_adhoc_migrations

    base = tmp_path / "therese.db"
    _base_d_avant(base)
    apply_adhoc_migrations(base)
    apres_le_premier = _lignes(base)

    apply_adhoc_migrations(base)

    assert _lignes(base) == apres_le_premier


def test_une_valeur_inconnue_traverse_intacte_et_se_journalise(tmp_path, caplog):
    from app.models.database import apply_adhoc_migrations

    base = tmp_path / "therese.db"
    _base_d_avant(base, valeurs=("gagne", "peut-etre"))

    with caplog.at_level(logging.WARNING, logger="app.models.database"):
        apply_adhoc_migrations(base)

    assert [phase for _, phase, _ in _lignes(base)] == ["signature", "peut-etre"]
    signalements = [r.getMessage() for r in caplog.records if "peut-etre" in r.getMessage()]
    assert len(signalements) == 1, signalements


def test_la_table_creee_au_demarrage_n_a_plus_de_defaut_piste(tmp_path):
    """Le modèle n'a plus de défaut depuis la 0.59 ; le DDL ad hoc le gardait."""
    from app.models.database import apply_adhoc_migrations

    base = tmp_path / "therese.db"
    with closing(sqlite3.connect(str(base))) as conn:
        conn.execute("CREATE TABLE contacts (id TEXT PRIMARY KEY)")
        conn.commit()

    apply_adhoc_migrations(base)

    with closing(sqlite3.connect(str(base))) as conn:
        colonnes = {ligne[1]: ligne[4] for ligne in conn.execute("PRAGMA table_info(prestations)")}
    assert "phase" in colonnes
    assert colonnes["phase"] is None


# ---------------------------------------------------------------------------
# La révision Alembic
# ---------------------------------------------------------------------------


def _revision():
    spec = importlib.util.spec_from_file_location("revision_p132", REVISION)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_la_revision_se_chaine_sur_la_date_d_envoi():
    revision = _revision()

    assert revision.revision == "c9d0e1f2a3b4"
    assert revision.down_revision == "b8c9d0e1f2a3"


def test_upgrade_puis_downgrade_rendent_les_valeurs_de_depart(tmp_path):
    base = tmp_path / "therese.db"
    _base_d_avant(base)
    with closing(sqlite3.connect(str(base))) as conn:
        conn.execute("INSERT INTO contacts VALUES ('c-perdu', 'lost'), ('c-archive', 'archive')")
        conn.commit()
    revision = _revision()
    moteur = create_engine(f"sqlite:///{base}")

    with moteur.begin() as connexion:
        revision.op = Operations(MigrationContext.configure(connexion))
        revision.upgrade()
        apres_upgrade = connexion.execute(text("SELECT phase FROM prestations ORDER BY id")).scalars().all()
        revision.upgrade()  # idempotente
        deux_fois = connexion.execute(text("SELECT phase FROM prestations ORDER BY id")).scalars().all()
        revision.downgrade()
        apres_downgrade = connexion.execute(text("SELECT phase FROM prestations ORDER BY id")).scalars().all()
        etapes = connexion.execute(text("SELECT id, stage FROM contacts ORDER BY id")).all()
    moteur.dispose()

    assert apres_upgrade == list(NOUVELLES)
    assert deux_fois == list(NOUVELLES)
    assert apres_downgrade == list(ANCIENNES)
    # Perdu n'existait pas avant P-132 : une fiche perdue retrouve son ancien sens.
    assert [tuple(ligne) for ligne in etapes] == [("c-archive", "archive"), ("c-perdu", "archive")]


def test_la_revision_tolere_une_base_sans_prestations(tmp_path):
    """Aucune révision ne crée la table : elle naît de create_all ou du démarrage."""
    base = tmp_path / "therese.db"
    with closing(sqlite3.connect(str(base))) as conn:
        conn.execute("CREATE TABLE contacts (id TEXT PRIMARY KEY, stage TEXT)")
        conn.commit()
    revision = _revision()
    moteur = create_engine(f"sqlite:///{base}")

    with moteur.begin() as connexion:
        revision.op = Operations(MigrationContext.configure(connexion))
        revision.upgrade()
        revision.downgrade()
    moteur.dispose()


# ---------------------------------------------------------------------------
# Ce que lit l'assistante
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_une_prestation_migree_depuis_gagne_est_presentee_comme_signee(client: AsyncClient):
    """Constat 2 de la revue : « signature » tout court se lit « en attente de
    signature » (le commentaire du score le disait). Une prestation signée
    avant P-132 doit rester signée pour l'assistante."""
    from app.config import settings
    from app.models.database import apply_adhoc_migrations, get_sync_connection

    contact_id = await _fiche(client, nom="Signee")
    creee = await client.post("/api/prestations", json={
        "contact_id": contact_id, "intitule": "PROPULSER", "phase": "discovery",
    })
    with get_sync_connection() as connexion:
        connexion.execute(
            text("UPDATE prestations SET phase = 'gagne' WHERE id = :id"), {"id": creee.json()["id"]}
        )
        connexion.commit()

    apply_adhoc_migrations(settings.db_path)
    fiche = await client.get(f"/api/memory/contacts/{contact_id}/fiche")

    assert fiche.status_code == 200, fiche.text
    [etat] = fiche.json()["etat_courant"]["prestations_ouvertes"]
    assert etat["etape"] == "Signature"
    assert "accord est donné" in etat["definition_de_l_etape"]
    assert "signature" not in json.dumps(etat, ensure_ascii=False), "l'identifiant ne voyage plus"
    assert "attente" not in json.dumps(etat, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Restauration, export, import
# ---------------------------------------------------------------------------

PASSE = "Passphrase-Test-123"


@pytest.mark.asyncio
async def test_une_sauvegarde_d_avant_p132_se_relit_dans_le_nouveau_vocabulaire(client: AsyncClient):
    from app.models.database import get_sync_connection

    contact_id = await _fiche(client, nom="Restauree")
    creee = await client.post("/api/prestations", json={
        "contact_id": contact_id, "intitule": "FORGER", "phase": "discovery",
    })
    with get_sync_connection() as connexion:
        connexion.execute(
            text("UPDATE prestations SET phase = 'en_cours' WHERE id = :id"), {"id": creee.json()["id"]}
        )
        connexion.commit()
    sauvegarde = await client.post("/api/data/backup", json={"password": PASSE})
    assert sauvegarde.status_code == 200, sauvegarde.text
    # Après la sauvegarde, la base vit sa vie : la restauration doit la remplacer.
    await client.patch(f"/api/prestations/{creee.json()['id']}", json={"phase": "archive"})

    restauree = await client.post(
        f"/api/data/restore/{sauvegarde.json()['backup_name']}?confirm=true", json={"password": PASSE},
    )

    assert restauree.status_code == 200, restauree.text
    lues = (await client.get(f"/api/prestations?contact_id={contact_id}")).json()
    assert [p["phase"] for p in lues] == ["delivery"]


@pytest.mark.asyncio
async def test_l_import_d_un_export_1_4_relit_ses_contacts(client: AsyncClient):
    """Il n'existe pas d'import JSON des prestations : un export complet se
    réimporte par ses contacts (`/api/data/import/contacts`). Un fichier 1.4,
    avec des prestations à l'ancien vocabulaire, doit rester importable."""
    ancien = {
        "data_format_version": "1.4",
        "contacts": [{"id": "c-export-14", "first_name": "Ancien", "last_name": "Export", "stage": "archive"}],
        "prestations": [{
            "id": "p-export-14", "contact_id": "c-export-14", "intitule": "FORGER", "phase": "gagne",
        }],
    }

    reponse = await client.post("/api/data/import/contacts", json=ancien)

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["imported"] == 1
    assert (await client.get("/api/memory/contacts/c-export-14")).json()["stage"] == "archive"
