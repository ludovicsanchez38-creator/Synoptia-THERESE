"""B-212 : l'export RGPD doit restituer le profil, pas un jeton Fernet.

« Exporter toutes mes données » rendait le profil sous la seule forme de la
préférence `user_profile`, dont la valeur est chiffrée : ni le nom, ni la
société, ni l'e-mail, ni la ville n'étaient lisibles, et aucune section de
l'export ne portait le profil. Un droit à la portabilité qui rend un blob
illisible ne restitue rien.
"""

import pytest
from app.services.encryption import is_value_encrypted
from httpx import AsyncClient

PROFIL = {
    "name": "Sophie Martin",
    "nickname": "Sophie",
    "company": "Studio Martin",
    "role": "graphiste freelance",
    "email": "sophie.martin@example.com",
    "location": "Lyon",
}


@pytest.mark.asyncio
async def test_export_restitue_le_profil_en_clair(client: AsyncClient):
    """Le profil saisi ressort en clair et structuré dans l'export."""
    reponse = await client.post("/api/config/profile", json=PROFIL)
    assert reponse.status_code == 200, reponse.text

    reponse = await client.get("/api/data/export")
    assert reponse.status_code == 200, reponse.text
    export = reponse.json()

    assert "profil" in export, (
        "aucune section profil : l'export ne restitue pas l'identité de "
        "l'utilisatrice"
    )
    profil = export["profil"]
    assert profil is not None
    for champ, attendu in PROFIL.items():
        assert profil.get(champ) == attendu, f"{champ} absent ou altéré de l'export"


@pytest.mark.asyncio
async def test_export_ne_livre_pas_le_profil_sous_forme_chiffree(client: AsyncClient):
    """La préférence `user_profile` ne doit plus expédier son jeton Fernet.

    Assertion bornée au profil : d'autres préférences chiffrées (secrets de
    connexion) relèvent d'un autre constat et ne sont pas jugées ici.
    """
    reponse = await client.post("/api/config/profile", json=PROFIL)
    assert reponse.status_code == 200, reponse.text

    export = (await client.get("/api/data/export")).json()

    valeurs_profil = [
        p["value"]
        for p in export["preferences"]
        if p["key"] == "user_profile"
    ]
    assert valeurs_profil, "la préférence user_profile a disparu de l'export"
    for valeur in valeurs_profil:
        assert not is_value_encrypted(str(valeur)), (
            "la préférence user_profile expédie encore son jeton chiffré : "
            f"{str(valeur)[:24]}…"
        )

    for valeur in (export.get("profil") or {}).values():
        assert not is_value_encrypted(str(valeur))
