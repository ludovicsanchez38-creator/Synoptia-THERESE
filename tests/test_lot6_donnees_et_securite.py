"""Lot 6 du cycle 3 (05/09/2026) : données, secrets et cohérence, confirmés
par les reproductions RP04, RP06 et RP07. Une classe par bug.
"""

from __future__ import annotations

import inspect
import json
from datetime import UTC, datetime, timedelta

import pytest


class TestB538LesSecretsOAuthNeSortentPasDeLExport:
    @pytest.mark.parametrize(
        "cle",
        ["google_client_secret", "crm_sheets_access_token", "crm_sheets_refresh_token", "brave_api_key",
         "smtp_password", "caldav_password"],
    )
    def test_une_preference_secrete_est_masquee(self, cle: str):
        from app.models.entities import Preference
        from app.routers.data import _valeur_de_preference_exportable

        pref = Preference(key=cle, value="ya29.secret-valeur", category="oauth")
        assert _valeur_de_preference_exportable(pref) == "[REDACTED]", cle

    def test_une_preference_ordinaire_sort_telle_quelle(self):
        from app.models.entities import Preference
        from app.routers.data import _valeur_de_preference_exportable

        pref = Preference(key="theme", value="dark", category="general")
        assert _valeur_de_preference_exportable(pref) == "dark"


class TestB545LaConversionRecalculeLEcheance:
    @pytest.mark.asyncio
    async def test_la_facture_convertie_n_est_pas_echue_avant_d_etre_emise(self, client):
        contact = await client.post(
            "/api/memory/contacts",
            json={"first_name": "Paul", "last_name": "Durand", "email": "paul@durand.test"},
        )
        devis = await client.post(
            "/api/invoices/",
            json={
                "contact_id": contact.json()["id"],
                "document_type": "devis",
                "issue_date": "2026-01-01T00:00:00",
                "due_date": "2026-01-31T00:00:00",
                "lines": [{"description": "Conseil", "quantity": 1, "unit_price_ht": 100, "tva_rate": 20}],
            },
        )
        assert devis.status_code == 200, devis.text

        facture = await client.post(f"/api/invoices/{devis.json()['id']}/convert", json={"target_type": "facture"})
        assert facture.status_code == 200, facture.text
        emission = datetime.fromisoformat(facture.json()["issue_date"].replace("Z", "")).replace(tzinfo=None)
        echeance = datetime.fromisoformat(facture.json()["due_date"].replace("Z", "")).replace(tzinfo=None)
        assert echeance >= emission, f"échéance {echeance} avant émission {emission}"
        assert (echeance - emission).days >= 29


class TestB542LImportDeContactsVerifieLaForme:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("charge", [{"contacts": "x"}, {"contacts": [1]}, {"contacts": {"a": 1}}])
    async def test_une_forme_invalide_est_un_400(self, client, charge):
        reponse = await client.post("/api/data/import/contacts", json=charge)
        assert reponse.status_code == 400, reponse.text[:200]


class TestB519LeDepotResoluEstCeluiQuiEstUtilise:
    @pytest.mark.asyncio
    async def test_spawn_transmet_le_chemin_resolu_aux_outils(self, client, monkeypatch, tmp_path):
        from app.routers import agents as module

        depot = tmp_path / "depot"
        depot.mkdir()
        (depot / "README.md").write_text("# lisible")
        monkeypatch.setattr(module, "_get_source_path", lambda: str(depot))
        captures: dict[str, str] = {}

        class FauxExecuteur:
            def __init__(self, source_path=None, **kwargs):
                captures["source_path"] = source_path

        class FauxGit:
            def __init__(self, path):
                captures["git"] = path

        monkeypatch.setattr(module, "GitService", FauxGit)
        monkeypatch.setattr("app.services.agents.tools.AgentToolExecutor", FauxExecuteur)

        profils = await client.get("/api/agents/profiles")
        assert profils.status_code == 200, profils.text
        premier = profils.json()[0]["id"] if isinstance(profils.json(), list) else profils.json()["profiles"][0]["id"]

        variante = str(tmp_path) + "/./depot/../depot"
        reponse = await client.post(
            "/api/agents/spawn",
            json={"profile_id": premier, "instruction": "lis tout", "source_path": variante},
        )
        assert reponse.status_code != 403, reponse.text
        # La garde est passée (le chemin est le dépôt autorisé) ; ce qui doit
        # atteindre les outils est le chemin RÉSOLU, jamais la chaîne brute.
        assert captures, "l'exécuteur d'outils n'a pas été construit"
        for valeur in captures.values():
            assert "/./" not in valeur and "/../" not in valeur, captures


class TestB508LesVariablesDEnvironnementMCPSontChiffreesAuChargement:
    @pytest.mark.asyncio
    async def test_un_fichier_ancien_en_clair_est_rechiffre_et_masque(self, tmp_path):
        from app.services.encryption import is_value_encrypted
        from app.services.mcp_service import MCPService

        fichier = tmp_path / "mcp_servers.json"
        fichier.write_text(json.dumps({"servers": [{
            "id": "abcd1234", "name": "Notion", "command": "npx", "args": [],
            "env": {"NOTION_API_KEY": "secret_en_clair"}, "enabled": True,
            "created_at": "2026-08-01T00:00:00+00:00",
        }]}))

        service = MCPService(config_path=fichier)
        await service._load_config()

        serveur = service.servers["abcd1234"]
        assert is_value_encrypted(serveur.env["NOTION_API_KEY"]), "la clé est encore en clair en mémoire"
        assert "secret_en_clair" not in fichier.read_text(), "la clé est encore en clair sur le disque"
        expose = service.list_servers()[0]["env"]
        assert "secret_en_clair" not in json.dumps(expose)
        assert "NOTION_API_KEY" in expose, "le nom de la variable doit rester visible pour l'édition"


class TestB510LaCleDAPIEstNettoyeeAvantChiffrement:
    @pytest.mark.asyncio
    async def test_les_blancs_autour_de_la_cle_ne_sont_pas_stockes(self, client):
        from sqlalchemy import select

        from app.models import database as db_module
        from app.models.entities import Preference
        from app.services.encryption import decrypt_value

        reponse = await client.post(
            "/api/config/api-key",
            json={"provider": "anthropic", "api_key": " sk-ant-api03-test-cle-propre-1234567890abcdefghij \n"},
        )
        assert reponse.status_code == 200, reponse.text[:200]

        async with db_module.AsyncSessionLocal() as session:
            pref = (await session.execute(select(Preference).where(Preference.key == "anthropic_api_key"))).scalar_one()
        assert decrypt_value(pref.value) == "sk-ant-api03-test-cle-propre-1234567890abcdefghij"


class TestB455LaMiseAJourDUnEvenementEstCoherente:
    async def _evenement(self, client) -> tuple[str, str]:
        cal = await client.post(
            "/api/calendar/calendars",
            params={"summary": "Local", "description": "", "timezone": "Europe/Paris", "provider_type": "local"},
        )
        assert cal.status_code == 200, cal.text
        debut = datetime.now(UTC) + timedelta(days=1, hours=1)
        evt = await client.post(
            "/api/calendar/events",
            json={
                "calendar_id": cal.json()["id"],
                "summary": "Point",
                "start_datetime": debut.strftime("%Y-%m-%dT%H:%M:%S"),
                "end_datetime": (debut + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S"),
            },
        )
        assert evt.status_code == 200, evt.text
        return cal.json()["id"], evt.json()["id"]

    @pytest.mark.asyncio
    async def test_une_fin_avant_le_debut_stocke_est_refusee(self, client):
        cal_id, evt_id = await self._evenement(client)
        avant = (datetime.now(UTC) + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
        reponse = await client.put(
            f"/api/calendar/events/{evt_id}?calendar_id={cal_id}", json={"end_datetime": avant}
        )
        assert reponse.status_code == 400, reponse.text[:200]

    @pytest.mark.asyncio
    async def test_un_participant_sans_adresse_est_refuse(self, client):
        cal_id, evt_id = await self._evenement(client)
        reponse = await client.put(
            f"/api/calendar/events/{evt_id}?calendar_id={cal_id}", json={"attendees": ["pas-une-adresse"]}
        )
        assert reponse.status_code in (400, 422), reponse.text[:200]


class TestB465LaPurgeRGPDRetrouveLesCommandesArchivees:
    def test_une_commande_supprimee_puis_purgee_ne_survit_pas_dans_la_corbeille(self, tmp_path, monkeypatch):
        from app.services.user_commands import UserCommandsService

        monkeypatch.setenv("HOME", str(tmp_path))
        (tmp_path / ".Trash").mkdir()
        service = UserCommandsService()
        commande = service.create_command(name="purge_b465", description="test", content="Texte rédigé par Marie")
        assert commande is not None
        assert service.delete_command("purge_b465") is True
        assert list((tmp_path / ".Trash").glob("purge_b465*.md")), "le témoin devait être dans la Corbeille"

        service.purger_tout()

        assert not list((tmp_path / ".Trash").glob("purge_b465*.md")), "le texte de l'utilisatrice survit dans la Corbeille"


class TestB536LaResolutionDuDepotNeBloquePasLaBoucle:
    def test_les_quatre_routes_passent_par_un_thread(self):
        from app.routers import agents as module

        source = inspect.getsource(module)
        assert source.count("await asyncio.to_thread(_get_source_path)") == 4, source.count("await asyncio.to_thread(_get_source_path)")
        assert source.count("= _get_source_path()") == 0


class TestB500LesCompteursDeJetonsSurviventAuRedemarrage:
    def test_le_mois_est_relu_au_demarrage(self, tmp_path, monkeypatch):
        from app.config import settings
        from app.services import token_tracker as module

        monkeypatch.setattr(settings, "data_dir", str(tmp_path))
        module.TokenTracker._instance = None
        module._token_tracker = None
        premier = module.get_token_tracker()
        premier.record_usage(conversation_id="c1", model="claude-sonnet-4-6", provider="anthropic", input_tokens=1000, output_tokens=200)
        assert premier.get_monthly_usage()["input_tokens"] == 1000

        module.TokenTracker._instance = None
        module._token_tracker = None
        second = module.get_token_tracker()
        assert second.get_monthly_usage()["input_tokens"] == 1000, "le plafond mensuel s'applique à un compteur remis à zéro"
        module.TokenTracker._instance = None
        module._token_tracker = None


class TestB525LEnvoiSMTPDeposeUneCopieDansEnvoyes:
    @pytest.mark.asyncio
    async def test_le_message_envoye_est_appose_dans_le_dossier_envoyes(self, monkeypatch):
        from contextlib import contextmanager

        from app.services.email import imap_smtp_provider as module
        from app.services.email.base_provider import SendEmailRequest

        provider = module.ImapSmtpProvider(email_address="marie@atelier.test", password="x", imap_host="imap.test", smtp_host="smtp.test")
        appends: list[tuple] = []

        class Boite:
            def append(self, contenu, dossier, dt=None, flag_set=None, **k):
                appends.append((dossier, contenu))
                return ("OK", [b"[APPENDUID 1 42] Append completed."])

        @contextmanager
        def connexion(**k):
            yield Boite()

        monkeypatch.setattr(provider, "_connect_mailbox", connexion)

        async def resolution(label):
            return "Sent"

        monkeypatch.setattr(provider, "resolve_folder_for_label", resolution)

        async def faux_send(*a, **k):
            return None

        monkeypatch.setattr(module.aiosmtplib, "send", faux_send)

        identifiant = await provider.send_message(
            SendEmailRequest(to=["paul@durand.test"], subject="Devis", body="Bonjour")
        )

        assert appends, "aucune copie apposée dans Envoyés"
        assert appends[0][0] == "Sent"
        assert b"Devis" in appends[0][1]
        assert identifiant == "42"
