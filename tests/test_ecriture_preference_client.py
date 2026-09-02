"""
La seule fonction d'écriture de préférence du client a une route en face.

RB2-004 (persona « robustesse API », deuxième passage). `POST
/api/config/preferences` est la requête que fabrique `setPreference`
(`services/api/config.ts`), et son unique appelant est le réglage « extraction
automatique » des Paramètres. Le serveur, lui, ne montait que `GET` sur ce
chemin : la requête rendait 405 « Method Not Allowed », le `catch` du composant
remettait l'interrupteur à sa position d'origine et affichait « La préférence
n'a pas pu être enregistrée ». Ce réglage ne pouvait pas être changé.

La route PUT `/preferences/{key}`, elle, existe mais n'accepte aucune forme
(RB2-005, hors de ce lot) : aucune porte ne prenait le relais.

Le POST délègue à `set_preference`, donc les trois refus posés là (clés d'API,
mode cabinet, adresse de fournisseur invalide) valent aussi pour lui - c'est
ce que vérifie la seconde classe.
"""

import pytest


class TestLaPreferenceSEcrit:
    @pytest.mark.asyncio
    async def test_la_route_existe_en_post(self, client):
        reponse = await client.post(
            "/api/config/preferences",
            json={"key": "rb2_test", "value": "x", "category": "general"},
        )

        assert reponse.status_code == 200, (
            "la seule fonction d'écriture exposée au client n'a pas de route : "
            f"{reponse.status_code} {reponse.text[:200]}"
        )

    @pytest.mark.asyncio
    async def test_la_valeur_est_relue(self, client):
        await client.post(
            "/api/config/preferences",
            json={"key": "rb2_test", "value": "x", "category": "general"},
        )

        relecture = await client.get("/api/config/preferences")
        assert relecture.status_code == 200, relecture.text
        assert "rb2_test" in relecture.json(), (
            f"la préférence n'a pas été enregistrée : {relecture.text[:200]}"
        )

    @pytest.mark.asyncio
    async def test_le_reglage_de_l_ecran_passe(self, client):
        """La charge utile exacte du composant Paramètres."""
        reponse = await client.post(
            "/api/config/preferences",
            json={
                "key": "auto_extract_entities",
                "value": True,
                "category": "memory",
            },
        )

        assert reponse.status_code == 200, reponse.text[:200]
        relecture = await client.get("/api/config/preferences")
        assert "auto_extract_entities" in relecture.json(), relecture.text[:200]

    @pytest.mark.asyncio
    async def test_une_categorie_absente_prend_le_defaut(self, client):
        reponse = await client.post(
            "/api/config/preferences", json={"key": "rb2_sans_categorie", "value": "x"}
        )

        assert reponse.status_code == 200, reponse.text[:200]
        assert (
            (await client.get("/api/config/preferences")).json()["rb2_sans_categorie"][
                "category"
            ]
            == "general"
        )


class TestLaNouvellePorteNeContournePasLesRefus:
    @pytest.mark.asyncio
    async def test_le_mode_cabinet_reste_refuse(self, client):
        reponse = await client.post(
            "/api/config/preferences",
            json={"key": "mode_cabinet", "value": "true", "category": "general"},
        )

        assert reponse.status_code == 400, (
            "le mode cabinet s'active sans le comptage des fiches qu'il va "
            f"rendre invisibles : {reponse.status_code} {reponse.text[:200]}"
        )
        assert "mode-cabinet" in reponse.json().get("message", ""), (
            "le refus doit dire par où passer, sinon il ressemble à une panne"
        )

    @pytest.mark.asyncio
    async def test_une_cle_vide_ou_demesuree_est_refusee(self, client):
        """La porte PUT ne pouvait pas produire ces deux formes : une clé est
        un segment de chemin. La nouvelle ne doit pas être plus lâche."""
        vide = await client.post(
            "/api/config/preferences", json={"key": "", "value": "x"}
        )
        assert vide.status_code == 422, (
            f"une préférence sans nom est enregistrée : {vide.status_code}"
        )

        enorme = await client.post(
            "/api/config/preferences", json={"key": "k" * 100_000, "value": "x"}
        )
        assert enorme.status_code == 422, (
            f"une clé de 100 000 caractères est enregistrée : {enorme.status_code}"
        )

    @pytest.mark.asyncio
    async def test_une_cle_d_api_reste_refusee(self, client):
        reponse = await client.post(
            "/api/config/preferences",
            json={"key": "anthropic_api_key", "value": "sk-test", "category": "llm"},
        )

        assert reponse.status_code == 400, (
            f"une clé d'API entre par la porte des préférences : {reponse.text[:200]}"
        )

    @pytest.mark.asyncio
    async def test_une_adresse_de_fournisseur_invalide_reste_refusee(self, client):
        reponse = await client.post(
            "/api/config/preferences",
            json={"key": "ollama_base_url", "value": "pas une url", "category": "llm"},
        )

        assert reponse.status_code == 400, (
            f"une adresse invalide est enregistrée : {reponse.text[:200]}"
        )
