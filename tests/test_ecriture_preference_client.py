"""
La seule fonction d'écriture de préférence du client a une route en face.

RB2-004 (persona « robustesse API », deuxième passage). `POST
/api/config/preferences` est la requête que fabrique `setPreference`
(`services/api/config.ts`), et son unique appelant est le réglage « extraction
automatique » des Paramètres. Le serveur, lui, ne montait que `GET` sur ce
chemin : la requête rendait 405 « Method Not Allowed », le `catch` du composant
remettait l'interrupteur à sa position d'origine et affichait « La préférence
n'a pas pu être enregistrée ». Ce réglage ne pouvait pas être changé.

La route PUT `/preferences/{key}`, elle, existait mais n'acceptait aucune forme
(RB2-005 / B-176, dernière classe de ce fichier) : aucune porte ne prenait le
relais.

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


class TestLaPortePutEstAppelable:
    """RB2-005 (B-176) : `PUT /preferences/{key}` n'acceptait AUCUNE forme.

    `value: str | int | float | bool | list | dict` déclaré en paramètre simple
    est classé `params.File` par FastAPI (son `list` nu passe pour une séquence
    de fichiers). L'OpenAPI annonçait donc `multipart/form-data`, et cette
    forme partait dans `_extract_form_body`, qui appelait `.read()` sur une
    chaîne : HTTP 500 « Une erreur inattendue s'est produite ». Toutes les
    autres formes (sept corps JSON, le paramètre d'URL) rendaient 422
    « value : Field required ».
    """

    @pytest.mark.asyncio
    async def test_la_valeur_s_ecrit_par_un_corps_json(self, client):
        reponse = await client.put(
            "/api/config/preferences/rb2_put", json={"value": "coucou"}
        )

        assert reponse.status_code == 200, (
            "la porte PUT annoncée par l'OpenAPI n'accepte aucune forme : "
            f"{reponse.status_code} {reponse.text[:200]}"
        )
        relecture = await client.get("/api/config/preferences")
        assert relecture.json().get("rb2_put", {}).get("value") == "coucou", (
            f"la préférence n'a pas été écrite : {relecture.text[:300]}"
        )

    @pytest.mark.asyncio
    async def test_le_contrat_openapi_du_corps_est_du_json(self, client):
        schema = (await client.get("/openapi.json")).json()
        corps = schema["paths"]["/api/config/preferences/{key}"]["put"]["requestBody"]

        assert list(corps["content"]) == ["application/json"], (
            "l'OpenAPI annonce un corps qu'aucun client ne peut produire : "
            f"{list(corps['content'])}"
        )

    @pytest.mark.asyncio
    async def test_un_formulaire_multipart_est_refuse_sans_rien_ecrire(self, client):
        """La forme de la reproduction. Elle ne doit plus rendre 500, et elle
        ne doit surtout pas écrire le corps multipart brut comme valeur."""
        reponse = await client.put(
            "/api/config/preferences/rb2_put_form", data={"value": "coucou"}
        )

        assert 400 <= reponse.status_code < 500, (
            f"un formulaire multipart rend {reponse.status_code} : {reponse.text[:200]}"
        )
        relecture = await client.get("/api/config/preferences")
        assert "rb2_put_form" not in relecture.json(), (
            f"le corps du formulaire a été stocké tel quel : {relecture.text[:300]}"
        )

    @pytest.mark.asyncio
    async def test_les_refus_de_la_porte_restent_poses(self, client):
        cle_api = await client.put(
            "/api/config/preferences/anthropic_api_key", json={"value": "sk-test"}
        )
        assert cle_api.status_code == 400, cle_api.text[:200]

        adresse = await client.put(
            "/api/config/preferences/ollama_base_url", json={"value": "pas une url"}
        )
        assert adresse.status_code == 400, adresse.text[:200]
