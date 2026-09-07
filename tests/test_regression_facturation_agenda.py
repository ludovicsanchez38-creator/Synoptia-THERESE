"""Non-régression facturation, agenda et e-mail, vérifiée par le COMPORTEMENT (B-039, B-332).

Remplace les gardes textuelles de `test_regression.py` : BUG-092 (PDF en panne),
BUG-094 (répertoire des PDF), BUG-073 et la robustesse CRUD des factures,
BUG-059 (délai du test SMTP), Gmail 403 (aide à l'écran), rotation du jeton
de rafraîchissement, robustesse de l'agenda (statut de synchronisation,
fournisseur inconnu, suppression). Ce qui était déjà couvert par
`test_routers_invoices.py`, `test_routers_calendar.py` et
`test_services_imap_smtp_provider.py` n'est pas dupliqué ici.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest

# ---------------------------------------------------------------- aides


async def _contact(client) -> str:
    reponse = await client.post(
        "/api/memory/contacts",
        json={"first_name": "Marie", "last_name": "Martin", "company": "Atelier", "email": "marie@test.fr"},
    )
    assert reponse.status_code == 200, reponse.text
    return reponse.json()["id"]


async def _facture(client, contact_id: str, **extra) -> dict:
    corps = {
        "contact_id": contact_id,
        "lines": [{"description": "Conseil", "quantity": 1.0, "unit_price_ht": 100.0, "tva_rate": 20.0}],
    }
    corps.update(extra)
    reponse = await client.post("/api/invoices/", json=corps)
    assert reponse.status_code == 200, reponse.text
    return reponse.json()


# ---------------------------------------------------------------- facturation


class TestPdfDeFacture:
    @pytest.mark.asyncio
    async def test_un_generateur_en_panne_repond_500_avec_un_message_qui_parle_de_pdf(self, client, monkeypatch):
        from app.routers import invoices as module

        class GenerateurEnPanne:
            def __init__(self, *args, **kwargs):
                pass

            def __getattr__(self, nom):
                def _explose(*args, **kwargs):
                    raise RuntimeError("police introuvable")

                return _explose

        from app.services.user_profile import UserProfile

        monkeypatch.setattr(module, "InvoicePDFGenerator", GenerateurEnPanne)
        monkeypatch.setattr(
            module, "get_cached_profile",
            lambda: UserProfile(name="Marie Exemple", company="Atelier Exemple", siret="123 456 789 00010", address="1 rue de l'Exemple"),
        )
        facture = await _facture(client, await _contact(client))

        reponse = await client.get(f"/api/invoices/{facture['id']}/pdf")

        assert reponse.status_code == 500, reponse.text
        message = (reponse.json().get("message") or reponse.json().get("detail") or "")
        assert "PDF" in message and "rreur" in message, message
        assert "police introuvable" not in message, "la trace interne ne doit pas sortir à l'écran"

    @pytest.mark.asyncio
    async def test_le_repertoire_des_pdf_suit_le_dossier_de_travail(self, client, db_session, tmp_path):
        from app.models.entities import Preference
        from app.services.invoice_pdf import InvoicePDFGenerator, resolve_invoice_output_dir

        db_session.add(Preference(key="working_directory", value=str(tmp_path)))
        await db_session.commit()

        resolu = resolve_invoice_output_dir()
        assert resolu == str(tmp_path / "factures"), resolu
        generateur = InvoicePDFGenerator(output_dir=None)
        assert str(generateur.output_dir) == resolu, "sans répertoire explicite, le générateur suit le dossier de travail"

    def test_sans_dossier_de_travail_le_repli_n_est_pas_un_chemin_en_dur(self, monkeypatch):
        from app.services import invoice_pdf as module

        monkeypatch.setattr(module, "get_sync_session", lambda: (_ for _ in ()).throw(RuntimeError("pas de base")), raising=False)
        resolu = module.resolve_invoice_output_dir()
        from app.config import settings

        assert str(settings.data_dir) in resolu or "invoices" in resolu, resolu


class TestRobustesseDesFactures:
    @pytest.mark.asyncio
    async def test_les_numeros_ne_se_reutilisent_pas_apres_une_suppression(self, client):
        contact = await _contact(client)
        premiere = await _facture(client, contact)
        seconde = await _facture(client, contact)
        assert premiere["invoice_number"] != seconde["invoice_number"]
        suppression = await client.delete(f"/api/invoices/{premiere['id']}")
        assert suppression.status_code in (200, 204), suppression.text

        troisieme = await _facture(client, contact)

        assert troisieme["invoice_number"] not in (premiere["invoice_number"], seconde["invoice_number"]), (
            "un numéro déjà émis ne doit jamais être réattribué (BUG-073, séquence par MAX et non par COUNT)"
        )

    @pytest.mark.asyncio
    async def test_le_prefixe_suit_le_type_de_document(self, client):
        contact = await _contact(client)
        assert (await _facture(client, contact, document_type="facture"))["invoice_number"].startswith("FACT-")
        assert (await _facture(client, contact, document_type="devis"))["invoice_number"].startswith("DEV-")
        assert (await _facture(client, contact, document_type="avoir"))["invoice_number"].startswith("AV-")

    @pytest.mark.asyncio
    async def test_un_contact_inconnu_ou_un_type_inconnu_sont_refuses(self, client):
        contact = await _contact(client)
        lignes = [{"description": "x", "quantity": 1.0, "unit_price_ht": 1.0, "tva_rate": 20.0}]
        assert (await client.post("/api/invoices/", json={"contact_id": "inexistant", "lines": lignes})).status_code == 404
        assert (
            await client.post("/api/invoices/", json={"contact_id": contact, "document_type": "note", "lines": lignes})
        ).status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_modifier_ou_supprimer_une_facture_inconnue_repond_404(self, client):
        assert (await client.put("/api/invoices/inexistante", json={"notes": "x"})).status_code == 404
        assert (await client.delete("/api/invoices/inexistante")).status_code == 404


# ---------------------------------------------------------------- e-mail


class TestTestDeConnexionImapSmtp:
    @pytest.mark.imap_reel
    @pytest.mark.asyncio
    async def test_un_serveur_smtp_muet_ne_bloque_pas_et_le_verdict_est_structure(self, monkeypatch):
        from app.services.email import imap_smtp_provider as module

        monkeypatch.setattr(module, "IMAP_CONNECT_TIMEOUT", 0.2)

        class SmtpMuet:
            def __init__(self, *args, **kwargs):
                pass

            async def connect(self):
                await asyncio.sleep(30)

        monkeypatch.setattr(module.aiosmtplib, "SMTP", SmtpMuet)
        provider = module.ImapSmtpProvider.__new__(module.ImapSmtpProvider)
        provider._smtp_host, provider._smtp_port, provider._smtp_use_tls = "smtp.exemple.fr", 587, True
        provider._email, provider._password = "a@exemple.fr", "secret"
        provider._connect_mailbox = lambda **kw: (_ for _ in ()).throw(ConnectionRefusedError("IMAP refusé"))

        top = asyncio.get_running_loop().time()
        verdict = await asyncio.wait_for(provider.test_connection(), timeout=8)
        duree = asyncio.get_running_loop().time() - top

        assert "success" in verdict, verdict
        assert verdict["success"] is False
        assert verdict["imap_ok"] is False and verdict["smtp_ok"] is False
        assert duree < 6, f"le test de connexion doit être borné par un délai (BUG-059), il a duré {duree:.1f} s"
        assert "délai" in verdict["message"].lower() or "delai" in verdict["message"].lower()


class TestAideGmail403:
    @pytest.mark.asyncio
    async def test_un_refus_google_explique_les_utilisateurs_de_test_et_les_api(self, client):
        reponse = await client.get("/api/email/auth/callback-redirect", params={"error": "access_denied"})
        assert reponse.status_code == 400, reponse.text
        page = reponse.text
        assert "Utilisateurs de test" in page, page[page.find("Causes") : page.find("Causes") + 600]
        assert "Gmail API" in page, page[page.find("Causes") : page.find("Causes") + 600]


class TestRotationDuJetonDeRafraichissement:
    @pytest.mark.asyncio
    async def test_un_nouveau_refresh_token_est_conserve_chiffre(self, client, db_session, monkeypatch):
        from app.models.entities import EmailAccount
        from app.routers import email as module
        from app.services.encryption import decrypt_value, encrypt_value, is_value_encrypted

        compte = EmailAccount(
            email="jerome@gmail.com", provider="gmail",
            access_token=encrypt_value("ancien-acces"), refresh_token=encrypt_value("ancien-refresh"),
            client_id=encrypt_value("cid"), client_secret=encrypt_value("secret"),
            token_expiry=datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=5),
        )
        db_session.add(compte)
        await db_session.commit()

        class FauxOAuth:
            async def refresh_access_token(self, refresh_token, config):
                assert refresh_token == "ancien-refresh"
                return {"access_token": "nouvel-acces", "expires_in": 3600, "refresh_token": "refresh-tourne"}

        monkeypatch.setattr(module, "get_oauth_service", lambda: FauxOAuth())
        monkeypatch.setattr(module, "get_gmail_oauth_config", lambda cid, secret: {"cid": cid})

        acces = await module.ensure_valid_access_token(compte, db_session)

        assert acces == "nouvel-acces"
        await db_session.refresh(compte)
        assert is_value_encrypted(compte.refresh_token), "le jeton renouvelé doit être chiffré"
        assert decrypt_value(compte.refresh_token) == "refresh-tourne", "la rotation Google doit être enregistrée"


# ---------------------------------------------------------------- agenda


class TestRobustesseDeLAgenda:
    @pytest.mark.asyncio
    async def test_le_statut_de_synchronisation_liste_les_fournisseurs(self, client):
        reponse = await client.get("/api/calendar/sync/status")
        assert reponse.status_code == 200, reponse.text
        assert isinstance(reponse.json().get("providers"), list)

    @pytest.mark.asyncio
    async def test_un_fournisseur_inconnu_est_refuse_proprement(self, client, db_session):
        from app.models.entities import Calendar

        martien = Calendar(summary="Agenda martien", provider="martien")
        db_session.add(martien)
        await db_session.commit()
        debut = datetime.now(UTC) + timedelta(days=1)
        reponse = await client.post(
            "/api/calendar/events",
            json={
                "calendar_id": martien.id, "summary": "Test",
                "start_datetime": debut.strftime("%Y-%m-%dT%H:%M:%S"),
                "end_datetime": (debut + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S"),
            },
        )
        # Refusé sans plantage : 400 et un message. (Observation B-039 : le
        # message parle de Google faute de branche dédiée aux fournisseurs
        # inconnus dans la création d'événement ; le routeur des calendriers
        # dit « Provider inconnu ».)
        assert reponse.status_code == 400, reponse.text
        assert reponse.json().get("message")

    @pytest.mark.asyncio
    async def test_supprimer_un_evenement_inconnu_est_une_erreur_expliquee_pas_une_route_absente(self, client):
        reponse = await client.delete("/api/calendar/events/inexistant")
        assert reponse.status_code in (400, 404), reponse.text
        assert reponse.status_code != 405
