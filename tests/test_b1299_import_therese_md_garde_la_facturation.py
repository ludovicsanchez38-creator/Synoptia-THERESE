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


@pytest.mark.asyncio
async def test_un_fichier_d_une_autre_personne_ne_recupere_rien(db_session, tmp_path):
    """B-1317 : la fusion de B-1299 gardait le surnom et la facturation de
    l'ancien profil même quand le fichier nommait une autre personne.
    Lecteur β, passe 6."""
    from app.services import user_profile as up

    await up.set_user_profile(
        db_session,
        up.UserProfile(name="Marie Exemple", nickname="Mimi", siret="12345678900010"),
        embed_in_qdrant=False,
    )
    fichier = tmp_path / "THERESE.md"
    fichier.write_text("**Owner** : Paul Autre\n", encoding="utf-8")
    profil = await up.import_from_claude_md(db_session, str(fichier))
    # B-1319 : le surnom de l'autre personne n'est pas repris ; la facturation,
    # elle, n'est jamais effacée par un fichier qui ne la porte pas.
    assert (profil.name, profil.nickname, profil.siret) == ("Paul Autre", "", "12345678900010"), profil


@pytest.mark.asyncio
@pytest.mark.parametrize("nom_du_fichier", ["Marie-Claire Exemple", "Marie Claire Exemple Durand", "Marie"])
async def test_une_variante_du_nom_garde_la_facturation(db_session, tmp_path, nom_du_fichier):
    """B-1319 : régression de B-1317, le critère strict de « même personne »
    effaçait la facturation pour un tiret, un second prénom ou un nom d'usage.
    Lecteur γ, passe 7."""
    from app.services import user_profile as up

    await up.set_user_profile(
        db_session,
        up.UserProfile(name="Marie Claire Exemple", address="12 rue de l'Exemple", siret="12345678900010"),
        embed_in_qdrant=False,
    )
    fichier = tmp_path / "THERESE.md"
    fichier.write_text(f"**Owner** : {nom_du_fichier}\n", encoding="utf-8")
    profil = await up.import_from_claude_md(db_session, str(fichier))
    assert (profil.address, profil.siret) == ("12 rue de l'Exemple", "12345678900010"), profil


@pytest.mark.asyncio
async def test_la_meme_personne_autrement_ecrite_garde_tout(db_session, tmp_path):
    from app.services import user_profile as up

    await up.set_user_profile(
        db_session, up.UserProfile(name="Hélène Exemple", siret="12345678900010"), embed_in_qdrant=False,
    )
    fichier = tmp_path / "THERESE.md"
    fichier.write_text("**Owner** : helene EXEMPLE\n", encoding="utf-8")
    profil = await up.import_from_claude_md(db_session, str(fichier))
    assert profil.siret == "12345678900010", profil


@pytest.mark.asyncio
async def test_la_reponse_de_l_import_porte_la_facturation(client, tmp_path):
    """B-1323 : la route d'import ne renvoyait pas la facturation ; l'écran des
    Paramètres l'affichait vide, et « Enregistrer » l'effaçait. Lecteur δ."""
    r = await client.post(
        "/api/config/profile",
        json={"name": "Marie Exemple", "address": "12 rue de l'Exemple", "siret": "12345678900010", "nda": "93000000000"},
    )
    assert r.status_code == 200, r.text
    fichier = tmp_path / "THERESE.md"
    fichier.write_text("**Owner** : Marie Exemple\n**Marque** : Exemple SARL\n", encoding="utf-8")
    reponse = await client.post("/api/config/profile/import-claude-md", json={"file_path": str(fichier)})
    assert reponse.status_code == 200, reponse.text
    corps = reponse.json()
    assert (corps["address"], corps["siret"], corps["nda"]) == ("12 rue de l'Exemple", "12345678900010", "93000000000"), corps


@pytest.mark.asyncio
async def test_une_variante_sans_marque_garde_la_raison_sociale(db_session, tmp_path):
    """B-1328 : la raison sociale n'était pas protégée comme la facturation ;
    une variante du nom sans ligne « Marque » gardait le SIRET mais perdait
    la raison sociale, et la facture sortait au nom de la personne avec le
    SIRET de la société. Lecteur ζ, passe 8."""
    from app.services import user_profile as up

    await up.set_user_profile(
        db_session,
        up.UserProfile(name="Marie Claire Exemple", company="Exemple SARL", siret="12345678900010"),
        embed_in_qdrant=False,
    )
    fichier = tmp_path / "THERESE.md"
    fichier.write_text("**Owner** : Marie-Claire Exemple\n", encoding="utf-8")
    profil = await up.import_from_claude_md(db_session, str(fichier))
    assert (profil.company, profil.siret) == ("Exemple SARL", "12345678900010"), profil


@pytest.mark.asyncio
async def test_la_meme_personne_retrouve_son_surnom_et_son_role(db_session, tmp_path):
    """B-1329 : la reprise des champs pour la même personne n'était testée
    nulle part (un _meme_personne toujours faux passait vert). Lecteur ζ."""
    from app.services import user_profile as up

    await up.set_user_profile(
        db_session, up.UserProfile(name="Hélène Exemple", nickname="Léna", role="Coach"), embed_in_qdrant=False,
    )
    fichier = tmp_path / "THERESE.md"
    fichier.write_text("**Owner** : helene EXEMPLE\n", encoding="utf-8")
    profil = await up.import_from_claude_md(db_session, str(fichier))
    assert (profil.nickname, profil.role) == ("Léna", "Coach"), profil
