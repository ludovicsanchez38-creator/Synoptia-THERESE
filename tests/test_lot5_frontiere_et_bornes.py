"""Lot 5 du cycle 3 (05/09/2026) : onze défauts simples confirmés par les
reproductions RP03, RP04 et RP06. Un fichier par lot, une classe par bug.
"""

from __future__ import annotations

import inspect

import pytest


class TestB423NullEtAbsentNeSontPasConfondus:
    """tasks.py testait `is not None` sur des champs `str | None = None` :
    impossible d'effacer une description ou une échéance par PUT."""

    @pytest.mark.asyncio
    async def test_un_null_explicite_efface_la_description(self, client):
        creation = await client.post(
            "/api/tasks/", json={"title": "Avec description", "description": "à effacer"}
        )
        assert creation.status_code == 200, creation.text
        tache = creation.json()

        maj = await client.put(f"/api/tasks/{tache['id']}", json={"description": None})
        assert maj.status_code == 200, maj.text
        assert maj.json()["description"] is None, "le null explicite doit effacer"

        relu = await client.get(f"/api/tasks/{tache['id']}")
        assert relu.json()["description"] is None

    @pytest.mark.asyncio
    async def test_un_champ_absent_ne_touche_a_rien(self, client):
        creation = await client.post(
            "/api/tasks/", json={"title": "Avec description", "description": "à garder"}
        )
        tache = creation.json()
        maj = await client.put(f"/api/tasks/{tache['id']}", json={"title": "Renommée"})
        assert maj.status_code == 200, maj.text
        assert maj.json()["description"] == "à garder"


class TestB504LesMessagesDesTachesSontEnFrancais:
    @pytest.mark.asyncio
    async def test_une_tache_introuvable_est_dite_en_francais(self, client):
        reponse = await client.get("/api/tasks/inexistante")
        assert reponse.status_code == 404
        message = reponse.json().get("message", reponse.text)
        assert "Task not found" not in message
        assert "introuvable" in message.lower() or "tâche" in message.lower(), message

    def test_aucun_detail_anglais_ne_reste_dans_le_routeur(self):
        from app.routers import tasks as module

        source = inspect.getsource(module)
        for anglais in ('"Task not found"', '"Project not found"', '"Contact not found"'):
            assert anglais not in source, anglais


class TestB430UneHTTPExceptionNEstPasAvaleeEn500:
    @pytest.mark.asyncio
    async def test_un_401_google_reste_un_401(self, client, monkeypatch):
        import httpx

        from app.routers import crm as module
        from app.services import crm_sync

        async def jeton_valide(session):
            return "jeton-de-test"

        monkeypatch.setattr(crm_sync, "ensure_valid_crm_token", jeton_valide)

        class Reponse401:
            status_code = 401
            text = "Invalid Credentials"

        class ClientQuiRefuse:
            def __init__(self, *a, **k):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return False

            async def get(self, *a, **k):
                return Reponse401()

        monkeypatch.setattr(httpx, "AsyncClient", ClientQuiRefuse)

        reponse = await client.get("/api/crm/google-sheets/list")
        assert reponse.status_code == 401, reponse.text[:200]
        assert "expiré" in reponse.text.lower()


class TestB436AucunExceptPassMuet:
    def test_le_routeur_des_agents_journalise_ses_rattrapages(self):
        from app.routers import agents as module

        source = inspect.getsource(module)
        assert "except Exception:\n        pass" not in source
        assert "except Exception:\n            pass" not in source


class TestB443LaPaginationDesMessagesEstBornee:
    @pytest.mark.asyncio
    async def test_limit_hors_bornes_est_refuse(self, client):
        creation = await client.post("/api/chat/conversations", json={"title": "Bornes"})
        assert creation.status_code in (200, 201), creation.text
        conv_id = creation.json()["id"]

        assert (await client.get(f"/api/chat/conversations/{conv_id}/messages?limit=0")).status_code == 422
        assert (await client.get(f"/api/chat/conversations/{conv_id}/messages?limit=100000")).status_code == 422
        assert (await client.get(f"/api/chat/conversations/{conv_id}/messages?limit=50")).status_code == 200


class TestB461UnFluxVideNEstPasUnBrouillon:
    @pytest.mark.asyncio
    async def test_une_reponse_vide_leve_generation_impossible(self, monkeypatch):
        from app.services import email_response_generator as module

        class ServiceMuet:
            async def generate_content(self, *args, **kwargs):
                return "   "

        monkeypatch.setattr(module, "get_llm_service", lambda: ServiceMuet(), raising=False)

        with pytest.raises(module.GenerationImpossible):
            await module.EmailResponseGenerator.generate_response(
                subject="Devis",
                from_name="Client",
                from_email="client@exemple.fr",
                body="Bonjour, pouvez-vous me faire un devis ?",
            )


class TestB467LaVoixNeRecopiePasLeTechnique:
    @pytest.mark.asyncio
    async def test_une_panne_locale_ne_fuit_pas_a_l_ecran(self, client, monkeypatch):
        from app.services import voice_local as moteur

        monkeypatch.setattr(moteur, "stt_available", lambda: True, raising=False)
        monkeypatch.setattr(moteur, "active_whisper_model", lambda: "tiny", raising=False)

        def transcription_qui_crash(*a, **k):
            raise ValueError("faster_whisper /Users/ludo/.cache/model sk-secret")

        monkeypatch.setattr(moteur, "transcribe_local", transcription_qui_crash, raising=False)

        reponse = await client.post(
            "/api/voice/local/transcribe",
            files={"audio": ("rec.webm", b"RIFF....", "audio/webm")},
        )
        assert reponse.status_code == 500, reponse.text[:200]
        assert "/Users/ludo" not in reponse.text
        assert "sk-secret" not in reponse.text

    def test_aucune_interpolation_brute_dans_le_routeur_voix(self):
        from app.routers import voice as module

        source = inspect.getsource(module)
        import re

        assert 'detail=f"Erreur transcription: {error_msg}"' not in source
        assert not re.search(r'detail=f"[^"]*\{e\}"', source), (
            "une exception est encore recopiée dans un detail"
        )


class TestB468LePdfPorteLeStatutEffectif:
    @pytest.mark.asyncio
    async def test_une_facture_envoyee_echue_est_en_retard_sur_le_pdf(self, client):
        from datetime import UTC, datetime, timedelta

        from pypdf import PdfReader

        profil = await client.post(
            "/api/config/profile",
            json={"name": "Marie Exemple", "company": "Atelier Exemple", "address": "Manosque",
                  "siret": "12345678900011"},
        )
        assert profil.status_code == 200, profil.text
        contact = await client.post(
            "/api/memory/contacts",
            json={"first_name": "Paul", "last_name": "Durand", "email": "paul@durand.test"},
        )
        hier = (datetime.now(UTC) - timedelta(days=3)).isoformat()
        piece = await client.post(
            "/api/invoices/",
            json={
                "contact_id": contact.json()["id"],
                "document_type": "facture",
                "due_date": hier,
                "lines": [{"description": "Conseil", "quantity": 1, "unit_price_ht": 100, "tva_rate": 20}],
            },
        )
        assert piece.status_code == 200, piece.text
        envoi = await client.put(f"/api/invoices/{piece.json()['id']}", json={"status": "sent"})
        assert envoi.status_code == 200, envoi.text
        assert envoi.json()["status"] == "overdue", "la liste dit déjà « en retard »"

        pdf = await client.get(f"/api/invoices/{piece.json()['id']}/pdf")
        assert pdf.status_code == 200, pdf.text[:200]
        texte = " ".join((p.extract_text() or "") for p in PdfReader(pdf.json()["pdf_path"]).pages)
        assert "En retard" in texte, "le PDF dit encore « Envoyée »"


class TestB498LaFicheCRMEstBornee:
    @pytest.mark.asyncio
    async def test_un_prenom_de_dix_mille_caracteres_est_refuse(self, client):
        reponse = await client.post(
            "/api/crm/contacts",
            json={"first_name": "x" * 10_000, "last_name": "Long"},
        )
        assert reponse.status_code == 422, reponse.text[:200]


class TestB505LesOutilsDeLEspaceNeRecopientPasLException:
    def test_les_cinq_sites_rendent_un_libelle_fixe(self):
        from app.services import workspace_tools as module

        source = inspect.getsource(module)
        for brut in (
            "Erreur lors de la génération du document : {e}",
            "Erreur lors de l'envoi de l'email : {e}",
            "Erreur lors de la recherche : {e}",
            "Erreur lors de la lecture du calendrier : {e}",
            "Erreur lors de la creation de l'evenement : {e}",
        ):
            assert brut not in source, brut


class TestB512ThereseMdEstSchematiseEtRobuste:
    @pytest.mark.asyncio
    async def test_un_contenu_non_textuel_est_refuse(self, client):
        assert (await client.post("/api/config/therese-md", json={"content": 123})).status_code == 422
        assert (await client.post("/api/config/therese-md", json={})).status_code == 422

    @pytest.mark.asyncio
    async def test_un_fichier_mal_encode_se_lit_quand_meme(self, client):
        from pathlib import Path

        from app.config import settings

        chemin = Path(settings.data_dir) / "THERESE.md"
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_bytes(b"# Profil\n\xe9\xff mal encod\xe9\n")

        reponse = await client.get("/api/config/therese-md")
        assert reponse.status_code == 200, reponse.text[:200]
        assert reponse.json()["exists"] is True
        assert "Profil" in reponse.json()["content"]
