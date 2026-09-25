"""B-1299 : l'import de THERESE.md (Paramètres) construisait un profil neuf avec
six champs et écrasait le profil entier : adresse, SIREN, TVA, SIRET, APE et
NDA de la facturation disparaissaient, et l'écran confirmait l'import. Même
règle que la synchro (B-1108, B-1125) : le fichier fait foi pour ce qu'il dit,
pas pour ce qu'il tait. Lecteur X, passe 5."""

import pytest


@pytest.mark.asyncio
async def test_l_import_garde_ce_que_le_fichier_tait(db_session, tmp_path):
    from app.services import user_profile as up

    await up.set_user_profile(
        db_session,
        up.UserProfile(
            name="Marie Exemple", company="Ancienne SARL", address="12 rue de l'Exemple",
            siren="123456789", tva_intra="FR00123456789", siret="12345678900010",
            code_ape="6202A", nda="93000000000",
        ),
        embed_in_qdrant=False,
    )
    fichier = tmp_path / "THERESE.md"
    fichier.write_text("**Owner** : Marie Exemple\n**Marque** : Nouvelle SARL\n", encoding="utf-8")

    profil = await up.import_from_claude_md(db_session, str(fichier))

    assert profil.company == "Nouvelle SARL"
    assert (profil.address, profil.siren, profil.tva_intra, profil.siret, profil.code_ape, profil.nda) == (
        "12 rue de l'Exemple", "123456789", "FR00123456789", "12345678900010", "6202A", "93000000000",
    ), profil
    relu = await up.get_user_profile(db_session)
    assert relu is not None and relu.siret == "12345678900010", relu
