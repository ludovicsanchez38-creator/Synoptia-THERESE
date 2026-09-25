"""B-1304 : un nom de profil fait seulement d'espaces faisait lever IndexError
à `display_name()` (`"   ".split()[0]`), soit une erreur 500 à
l'enregistrement du profil. Lecteur X, passe 5."""

import pytest


def test_le_nom_affiche_d_un_nom_blanc():
    from app.services.user_profile import UserProfile

    assert UserProfile(name="   ").display_name() == "Utilisateur"


@pytest.mark.asyncio
async def test_l_api_ne_tombe_pas_sur_un_nom_blanc(client):
    r = await client.post("/api/config/profile", json={"name": "   "})
    assert r.status_code != 500, r.text


@pytest.mark.asyncio
async def test_un_nom_blanc_est_refuse_et_ne_compte_pas_comme_raison_sociale(client):
    """B-1310 : B-1304 à moitié. Le nom blanc était enregistré et comptait
    comme raison sociale de facturation (billing_missing). L'interface exige
    déjà un nom (ProfileStep, ProfileTab) ; le moteur aussi. Lecteur α."""
    r = await client.post("/api/config/profile", json={"name": "   ", "siret": "12345678900010"})
    assert r.status_code == 422, r.text
    ok = await client.post("/api/config/profile", json={"name": "  Marie Exemple  "})
    assert ok.status_code == 200, ok.text
    assert ok.json()["name"] == "Marie Exemple", ok.json()
