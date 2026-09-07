"""Cycle 4 : candidats COCO (B-581 à B-588) et lecteurs (B-589 à B-593) reproduits, puis corrigés.

B-581 : un début qui tombe sur une borne de pause s'affiche 12 h au lieu de 14 h.
B-582 : les plafonds de jetons enregistrés ne sont lus qu'à l'ouverture de l'onglet Limites.
B-583 : generate_content() contourne le disjoncteur quand il relève max_tokens.
B-586 : la garde « fin après début » compare des heures locales, pas des instants.
B-587 : renommer une commande utilisateur laisse son ancienne clé dans le registre.
B-588 : l'export de portabilité ignore les cinq tables de planning.
B-589 : le nom du fichier de référence téléversé est concaténé dans un chemin.
B-590 : l'export d'un contact n'exporte ni ses prestations ni ses e-mails, que l'anonymisation efface.
B-591 : la rotation de clé par le trousseau ne réécrit pas le fichier de secours.
B-592 : le guide Gmail dicte une URI de redirection que le code refuse.
B-593 : le score fabrique un JSON par interpolation : un guillemet le casse.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

PARIS = ZoneInfo("Europe/Paris")


class TestB581DebutSurUneBorneDePause:
    def test_le_successeur_commence_a_14h_pas_a_12h(self):
        from app.services.planning import (
            PlanningDependencyInput,
            PlanningTaskInput,
            calculate_schedule,
        )

        taches = [
            PlanningTaskInput(id="a", title="Dépose", duration_optimistic_minutes=180, duration_likely_minutes=180, duration_pessimistic_minutes=180),
            PlanningTaskInput(id="b", title="Pose", duration_optimistic_minutes=60, duration_likely_minutes=60, duration_pessimistic_minutes=60),
        ]
        deps = [PlanningDependencyInput(predecessor_task_id="a", successor_task_id="b")]
        resultat = calculate_schedule(taches, deps, starts_at=datetime(2026, 3, 2, 9, 0, tzinfo=PARIS), timezone="Europe/Paris")
        assert resultat.state == "complete", resultat.errors
        par_id = {t.task_id: t for t in resultat.tasks}
        assert par_id["a"].earliest_finish_at.astimezone(PARIS).strftime("%H:%M") == "12:00"
        assert par_id["b"].earliest_start_at.astimezone(PARIS).strftime("%H:%M") == "14:00", (
            "un début ne peut pas tomber pendant la pause : la date d'un début se normalise"
        )
        assert par_id["b"].earliest_finish_at.astimezone(PARIS).strftime("%H:%M") == "15:00"


class TestB582PlafondsLusSansOuvrirLOnglet:
    @pytest.mark.asyncio
    async def test_le_budget_enregistre_s_applique_au_premier_controle(self, client, db_session):
        from app.models.entities import Preference
        from app.services.token_tracker import TokenTracker

        db_session.add(Preference(key="token_limits", value=json.dumps({"monthly_budget_eur": 500.0, "warn_at_percentage": 80}), category="llm"))
        await db_session.commit()

        suivi = TokenTracker()
        suivi.check_limits(10, None, model="claude-sonnet-4-6")
        assert suivi.get_limits().monthly_budget_eur == 500.0, (
            "avant l'ouverture de Paramètres > Limites, le chat appliquait le budget par défaut"
        )


class TestB583GenerateContentRespecteLeDisjoncteur:
    @pytest.mark.asyncio
    async def test_le_repli_du_disjoncteur_garde_le_plafond_releve(self, monkeypatch):
        from app.services.llm import LLMConfig, LLMProvider, LLMService
        from app.services.providers.base import StreamEvent

        service = LLMService(LLMConfig(LLMProvider.ANTHROPIC, "claude-sonnet-4-6", api_key="k", max_tokens=4096))
        repli = LLMConfig(LLMProvider.OLLAMA, "repli-local", max_tokens=4096)
        monkeypatch.setattr(service, "_resolve_with_circuit_breaker", lambda: repli)
        recu: dict = {}

        async def faux_flux(context, tools=None, enable_grounding=True, config=None):
            recu["config"] = config
            yield StreamEvent(type="text", content="ok")
            yield StreamEvent(type="done")

        monkeypatch.setattr(service, "stream_response_with_tools", faux_flux)
        await service.generate_content("Rédige", max_tokens=16384)

        assert recu["config"] is not None
        assert recu["config"].provider == LLMProvider.OLLAMA, "le fournisseur déclaré indisponible était rappelé"
        assert recu["config"].max_tokens == 16384


class TestB586FinApresDebutEnInstants:
    @pytest.mark.asyncio
    async def test_une_fin_posterieure_dans_un_autre_fuseau_est_acceptee(self, client):
        cal = await client.post(
            "/api/calendar/calendars",
            params={"summary": "Local", "description": "x", "timezone": "Europe/Paris", "provider_type": "local"},
        )
        assert cal.status_code == 200, cal.text
        debut = datetime.now(UTC) + timedelta(days=2)
        creation = await client.post(
            "/api/calendar/events",
            json={
                "calendar_id": cal.json()["id"], "summary": "Point",
                "start_datetime": debut.strftime("%Y-%m-%dT%H:%M:%S"),
                "end_datetime": (debut + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S"),
            },
        )
        assert creation.status_code == 200, creation.text
        jour = (debut + timedelta(days=1)).strftime("%Y-%m-%d")
        modification = await client.put(
            f"/api/calendar/events/{creation.json()['id']}",
            params={"calendar_id": cal.json()["id"]},
            json={"start_datetime": f"{jour}T10:30:00+02:00", "end_datetime": f"{jour}T09:00:00+00:00"},
        )
        assert modification.status_code == 200, (
            "10:30+02:00 -> 09:00+00:00 dure trente minutes réelles ; la garde comparait les heures affichées : " + modification.text
        )


class TestB587RenommerUneCommandeChangeSaCle:
    @pytest.mark.asyncio
    async def test_l_ancien_nom_redevient_libre_sans_ecraser_le_nouveau(self, client):
        creation = await client.post("/api/v3/commands/user", json={"name": "ancien", "prompt_template": "Premier"})
        assert creation.status_code == 201, creation.text
        assert creation.json()["id"] == "user-ancien"

        renommage = await client.put("/api/v3/commands/user/user-ancien", json={"name": "nouveau"})
        assert renommage.status_code == 200, renommage.text
        assert renommage.json()["id"] == "user-nouveau", "l'identifiant doit suivre le nom"

        recreation = await client.post("/api/v3/commands/user", json={"name": "ancien", "prompt_template": "Second"})
        assert recreation.status_code == 201, recreation.text

        nouveau = await client.get("/api/v3/commands/user-nouveau")
        assert nouveau.status_code == 200, nouveau.text
        assert nouveau.json()["prompt_template"] == "Premier", "la commande renommée a été écrasée par la recréation de l'ancien nom"
        ancien = await client.get("/api/v3/commands/user-ancien")
        assert ancien.status_code == 200 and ancien.json()["prompt_template"] == "Second"

class TestB588ExportDePortabiliteAvecLePlanning:
    @pytest.mark.asyncio
    async def test_les_cinq_tables_de_planning_sont_exportees(self, client, db_session):
        from app.models.entities import Project, Task, TaskDependency, TaskSchedule
        from app.routers.data import _assembler_export_rgpd

        projet = Project(name="Chantier")
        db_session.add(projet)
        await db_session.flush()
        t1, t2 = Task(title="a", project_id=projet.id), Task(title="b", project_id=projet.id)
        db_session.add_all([t1, t2])
        await db_session.flush()
        db_session.add_all([
            TaskSchedule(task_id=t1.id, duration_optimistic_minutes=30, duration_likely_minutes=30, duration_pessimistic_minutes=30),
            TaskDependency(predecessor_task_id=t1.id, successor_task_id=t2.id),
        ])
        await db_session.commit()

        export = _assembler_export_rgpd()
        for cle in ("task_schedules", "task_dependencies", "planning_resources", "task_allocations", "planning_snapshots"):
            assert cle in export, f"{cle} manque à la portabilité alors que l'effacement total la détruit"
        assert any(s["task_id"] == t1.id for s in export["task_schedules"])
        assert any(d["successor_task_id"] == t2.id for d in export["task_dependencies"])


class TestB589NomDeFichierDeReferenceSur:
    @pytest.mark.parametrize(
        ("fourni", "attendu"),
        [("../../etc/x.png", "x.png"), ("/tmp/../a/b.png", "b.png"), ("", "reference"), ("photo de réf.png", "photo de réf.png")],
    )
    def test_le_nom_est_reduit_a_sa_base(self, fourni, attendu):
        from app.routers.images import nom_de_fichier_de_reference

        assert nom_de_fichier_de_reference(fourni) == attendu


class TestB590ExportDUnContactAvecCeQueLAnonymisationEfface:
    @pytest.mark.asyncio
    async def test_prestations_et_emails_sont_dans_l_export(self, client, db_session):
        from app.models.entities import Contact, EmailAccount, EmailMessage, Prestation

        contact = Contact(first_name="Paul", last_name="Martin", email="paul@exemple.fr")
        db_session.add(contact)
        await db_session.flush()
        compte = EmailAccount(email="moi@exemple.fr", provider="imap")
        db_session.add(compte)
        await db_session.flush()
        maintenant = datetime.now(UTC).replace(tzinfo=None)
        db_session.add_all([
            Prestation(contact_id=contact.id, intitule="Formation IA", phase="devis", montant_ht=490.0),
            EmailMessage(
                id="m-1", thread_id="t-1", account_id=compte.id, contact_id=contact.id, subject="Devis",
                from_email="paul@exemple.fr", to_emails="[]", date=maintenant, internal_date=maintenant, labels="[]",
            ),
        ])
        await db_session.commit()

        reponse = await client.get(f"/api/rgpd/export/{contact.id}")
        assert reponse.status_code == 200, reponse.text
        corps = reponse.json()
        assert any(p.get("intitule") == "Formation IA" for p in corps.get("prestations", [])), corps.keys()
        assert any(m.get("subject") == "Devis" for m in corps.get("email_messages", [])), corps.keys()


class FauxTrousseau:
    def __init__(self, secret=None):
        self.secret = secret

    def get_password(self, service, compte):
        return self.secret

    def set_password(self, service, compte, valeur):
        self.secret = valeur


class TestB591RotationEtFichierDeSecours:
    def test_la_rotation_par_le_trousseau_reecrit_le_fichier_de_secours(self, monkeypatch, tmp_path):
        from app.services import encryption as module

        module.EncryptionService._instance = None
        module.EncryptionService._fernet = None
        module.EncryptionService._using_keychain = False
        monkeypatch.setattr(module, "KEY_FILE", tmp_path / ".encryption_key")
        monkeypatch.setattr(module, "_try_keyring_available", lambda: True)
        trousseau = FauxTrousseau("cle-initiale-ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789ab=")
        monkeypatch.setitem(sys.modules, "keyring", trousseau)
        try:
            service = module.EncryptionService()
            service._get_or_create_key()
            service._using_keychain = True

            ancienne = service.rotate_key()

            assert ancienne == b"cle-initiale-ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789ab="
            assert module.KEY_FILE.read_bytes().decode() == trousseau.secret, (
                "au démarrage suivant, la garde BUG-050 aurait restauré l'ANCIENNE clé du fichier et rendu les données illisibles"
            )
        finally:
            module.EncryptionService._instance = None
            module.EncryptionService._fernet = None
            module.EncryptionService._using_keychain = False


class TestB592LeGuideGmailDitLaVraieUri:
    @pytest.mark.asyncio
    async def test_le_guide_annonce_l_uri_que_le_code_utilise(self):
        from app.services.email_setup_assistant import EmailSetupAssistant
        from app.services.oauth import RUNTIME_PORT

        for has_project in (True, False):
            guide = await EmailSetupAssistant.generate_guide_message("gmail", has_project)
            assert "8080/oauth/callback" not in guide, "Google refuse l'URI dictée par le guide"
            assert f"http://localhost:{RUNTIME_PORT}/api/email/auth/callback-redirect" in guide


class TestB593LeScoreEcritDuJsonValide:
    @pytest.mark.asyncio
    async def test_une_raison_avec_guillemets_reste_lisible(self, db_session):
        from app.models.entities import Activity, Contact
        from app.services.scoring import update_contact_score
        from sqlalchemy import select

        contact = Contact(first_name="Ana", last_name="Ruiz", email="ana@exemple.fr")
        db_session.add(contact)
        await db_session.commit()
        raison = 'Devis "urgent" signé, relance {test}'

        await update_contact_score(db_session, contact, reason=raison)

        activite = (await db_session.execute(select(Activity).where(Activity.contact_id == contact.id, Activity.type == "score_change"))).scalars().first()
        assert activite is not None
        assert json.loads(activite.extra_data)["reason"] == raison, activite.extra_data
