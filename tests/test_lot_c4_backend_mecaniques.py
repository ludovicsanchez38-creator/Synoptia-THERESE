"""Cycle 4, lot 2 backend : cinq défauts tranchés au portail humain du 05/09/2026.

B-469 : deux relations redéclarées après les classes perdaient leurs options.
B-476 : le cloisonnement de l'agenda reposait sur le NOM de la classe du fournisseur.
B-434 : deux ajouts de colonne conditionnés à l'absence d'une seule.
B-439 : « déplacer » un message Gmail n'en retirait jamais le libellé d'origine.
B-460 : purger le journal d'audit validait tout ce que l'appelant avait en attente.
"""

from __future__ import annotations

import sqlite3

import pytest
from sqlalchemy import inspect, select


class TestB469LesRelationsGardentLeursOptions:
    def test_contact_invoices_garde_passive_deletes(self):
        from app.models.entities import Contact

        rel = inspect(Contact).relationships["invoices"]
        assert rel.passive_deletes == "all", (
            "Contact.invoices a perdu passive_deletes='all' : la suppression CRM "
            "tenterait de passer contact_id à NULL sur une pièce comptable"
        )

    def test_project_deliverables_garde_sa_cascade(self):
        from app.models.entities import Project

        rel = inspect(Project).relationships["deliverables"]
        assert "delete" in rel.cascade, rel.cascade


class TestB476LaCloisonAgendaNeDependPasDuNomDeClasse:
    @pytest.mark.asyncio
    async def test_une_sous_classe_du_fournisseur_local_recoit_le_perimetre(self, db_session, monkeypatch):
        from app.services import workspace_tools
        from app.services.calendar.local_provider import LocalCalendarProvider

        recu: dict = {}

        class FournisseurLocalDerive(LocalCalendarProvider):
            def __init__(self):  # pas de session : on ne touche pas la base
                pass

            async def list_events(self, calendar_id, time_min=None, time_max=None, max_results=50, **kwargs):
                recu.update(kwargs)
                recu["calendar_id"] = calendar_id
                return [], None

        async def faux_fournisseur(session, calendar_id=None):
            return FournisseurLocalDerive(), "cal-local", None

        monkeypatch.setattr(workspace_tools, "_get_calendar_provider", faux_fournisseur)

        await workspace_tools._list_calendar_events({"days": 7}, db_session, project_id="projet-marie")

        assert recu.get("project_id") == "projet-marie", (
            "un fournisseur local dérivé (renommé ou sous-classé) retombait en silence "
            f"dans le régime sans périmètre : {recu}"
        )


class TestB434ChaqueColonneASaGarde:
    def test_statut_financement_est_posee_meme_si_financeur_existe_deja(self, tmp_path, monkeypatch):
        from app.models import database as db_module

        monkeypatch.setattr(db_module, "db_encryption_enabled", lambda: False)
        from sqlalchemy import create_engine
        from sqlmodel import SQLModel

        chemin = tmp_path / "therese.db"
        moteur = create_engine(f"sqlite:///{chemin}")
        SQLModel.metadata.create_all(moteur)
        moteur.dispose()
        with sqlite3.connect(chemin) as conn:
            # Un démarrage interrompu entre les deux ALTER : `financeur` posée, pas `statut_financement`.
            conn.execute("DROP INDEX IF EXISTS ix_prestations_statut_financement")
            conn.execute("ALTER TABLE prestations DROP COLUMN statut_financement")
            conn.commit()

        db_module.apply_adhoc_migrations(chemin)

        with sqlite3.connect(chemin) as conn:
            colonnes = {row[1] for row in conn.execute("PRAGMA table_info(prestations)").fetchall()}
        assert "statut_financement" in colonnes, (
            "la colonne manquante ne sera plus jamais posée : la garde testait `financeur`, "
            "pas `statut_financement`"
        )


class TestB439DeplacerUnMessageGmailRetireLeLibelleDOrigine:
    @pytest.mark.asyncio
    async def test_le_libelle_de_depart_et_la_boite_de_reception_sont_retires(self, monkeypatch):
        from app.services.email.gmail_provider import GmailProvider

        appels: list[dict] = []

        class FauxService:
            async def get_message(self, message_id, format="full"):
                return {"id": message_id, "labelIds": ["INBOX", "UNREAD", "Label_7", "IMPORTANT"]}

            async def modify_message(self, message_id, add_label_ids=None, remove_label_ids=None):
                appels.append({"add": add_label_ids or [], "remove": remove_label_ids or []})
                return {"id": message_id, "labelIds": add_label_ids or []}

        provider = GmailProvider("jeton")
        provider._service = FauxService()

        async def faux_get_message(message_id):
            return {"id": message_id}

        monkeypatch.setattr(provider, "get_message", faux_get_message)

        await provider.move_message("msg-1", "Label_9")

        assert len(appels) == 1, appels
        assert appels[0]["add"] == ["Label_9"]
        assert set(appels[0]["remove"]) == {"INBOX", "Label_7"}, (
            "le message doit quitter la boîte de réception et son libellé d'origine ; "
            f"retirés : {appels[0]['remove']}"
        )
        assert "UNREAD" not in appels[0]["remove"] and "IMPORTANT" not in appels[0]["remove"]


class TestB460LaPurgeDuJournalNeValidePasLeTravailEnAttente:
    @pytest.mark.asyncio
    async def test_un_brouillon_non_commite_ne_survit_pas_a_la_purge(self, db_session):
        from app.models import database as db_module
        from app.models.entities import Contact
        from app.services.audit import AuditService

        brouillon = Contact(display_name="BROUILLON B-460 jamais validé")
        db_session.add(brouillon)
        cle = brouillon.id

        await AuditService(db_session).cleanup_old_logs(days=90)

        await db_session.rollback()

        async with db_module.AsyncSessionLocal() as verif:
            trouve = (await verif.execute(select(Contact).where(Contact.id == cle))).scalar_one_or_none()
        assert trouve is None, "la purge du journal a rendu durable un brouillon que l'appelant n'avait pas validé"
