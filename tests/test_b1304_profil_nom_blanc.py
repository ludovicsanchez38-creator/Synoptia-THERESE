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
