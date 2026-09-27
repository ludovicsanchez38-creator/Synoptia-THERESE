"""Régressions de sécurité des préférences génériques, cycle 14."""

from __future__ import annotations

import pytest


class TestB1563LeDossierDeTravailPasseParSaRouteGardee:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("methode", ["post", "put"])
    async def test_la_porte_generique_ne_change_pas_le_dossier(self, client, tmp_path, methode):
        dossier = tmp_path / "travail"
        dossier.mkdir()
        choix = await client.post(
            "/api/config/working-directory", json={"path": str(dossier)}
        )
        assert choix.status_code == 200, choix.text

        if methode == "post":
            tentative = await client.post(
                "/api/config/preferences",
                json={"key": "working_directory", "value": "/", "category": "files"},
            )
        else:
            tentative = await client.put(
                "/api/config/preferences/working_directory", json={"value": "/"}
            )

        assert tentative.status_code == 400, tentative.text
        relecture = await client.get("/api/config/working-directory")
        assert relecture.json()["path"] == str(dossier.resolve())

    @pytest.mark.asyncio
    async def test_effacer_la_preference_ne_retire_pas_le_dossier_valide(self, client, tmp_path):
        dossier = tmp_path / "travail"
        dossier.mkdir()
        choix = await client.post(
            "/api/config/working-directory", json={"path": str(dossier)}
        )
        assert choix.status_code == 200, choix.text

        suppression = await client.delete("/api/config/preferences/working_directory")

        assert suppression.status_code == 400, suppression.text
        relecture = await client.get("/api/config/working-directory")
        assert relecture.json()["path"] == str(dossier.resolve())


class TestB1564LesSecretsNeSortentPasParLaListeGenerique:
    @pytest.mark.asyncio
    async def test_les_jetons_et_secrets_crm_sont_absents(self, client):
        from app.models import database as db_module
        from app.models.entities import Preference

        async with db_module.AsyncSessionLocal() as session:
            for cle in (
                "crm_sheets_access_token",
                "crm_sheets_refresh_token",
                "crm_sheets_client_secret",
                "google_client_secret",
                "anthropic_api_key",
            ):
                session.add(Preference(key=cle, value="jeton-chiffre-factice", category="crm"))
            session.add(Preference(key="theme", value="sombre", category="crm"))
            await session.commit()

        for url in ("/api/config/preferences", "/api/config/preferences?category=crm"):
            reponse = await client.get(url)
            assert reponse.status_code == 200, reponse.text
            donnees = reponse.json()
            assert donnees["theme"]["value"] == "sombre"
            assert not any(
                cle in donnees
                for cle in (
                    "crm_sheets_access_token",
                    "crm_sheets_refresh_token",
                    "crm_sheets_client_secret",
                    "google_client_secret",
                    "anthropic_api_key",
                )
            ), donnees

    @pytest.mark.asyncio
    async def test_les_plafonds_de_jetons_restent_une_preference_ordinaire(self, client):
        from app.models import database as db_module
        from app.models.entities import Preference

        async with db_module.AsyncSessionLocal() as session:
            session.add(Preference(
                key="token_limits",
                value='{"monthly_budget_eur": 42}',
                category="llm",
            ))
            await session.commit()

        reponse = await client.get("/api/config/preferences")
        assert reponse.status_code == 200, reponse.text
        assert reponse.json()["token_limits"]["value"] == {"monthly_budget_eur": 42}


class TestB1711UneCleAPISupprimeePasseParSaRouteDediee:
    @pytest.mark.asyncio
    async def test_la_suppression_generique_ne_laisse_pas_une_cle_dans_le_cache(
        self, client
    ):
        from app.models import database as db_module
        from app.models.entities import Preference
        from app.services import llm
        from sqlmodel import select

        cle_factice = "sk-ant-test-b1711"
        pose = await client.post(
            "/api/config/api-key",
            json={"provider": "anthropic", "api_key": cle_factice},
        )
        assert pose.status_code == 200, pose.text
        assert llm._get_api_key_from_db("anthropic") == cle_factice

        post = await client.post(
            "/api/config/preferences",
            json={"key": "anthropic_api_key", "value": cle_factice},
        )
        put = await client.put(
            "/api/config/preferences/anthropic_api_key", json={"value": cle_factice}
        )
        assert post.status_code == put.status_code == 400

        suppression = await client.delete("/api/config/preferences/anthropic_api_key")
        async with db_module.AsyncSessionLocal() as session:
            pref = (
                await session.execute(
                    select(Preference).where(Preference.key == "anthropic_api_key")
                )
            ).scalar_one_or_none()
        encore_en_cache = llm._get_api_key_from_db("anthropic") == cle_factice

        assert suppression.status_code == 400, (
            f"DELETE générique {suppression.status_code}, "
            f"préférence conservée={pref is not None}, cache conservé={encore_en_cache}"
        )
        assert pref is not None
        assert encore_en_cache

        retiree = await client.delete("/api/config/api-key/anthropic")
        assert retiree.status_code == 200, retiree.text
        assert llm._get_api_key_from_db("anthropic") is None
