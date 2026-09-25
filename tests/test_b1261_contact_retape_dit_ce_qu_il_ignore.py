"""B-1261 : `/contact` sur un contact existant répondait « je le réutilise »
sans dire que le téléphone ou le courriel saisis n'avaient pas été
enregistrés (l'outil le signale dans champs_ignores). Lecteur U, passe 4."""

import pytest


@pytest.mark.asyncio
async def test_contact_retape_avec_un_telephone(db_session):
    from app.services.slash_commands import execute_slash_command

    await execute_slash_command("contact", "Marie Exemple", db_session)
    reponse = await execute_slash_command("contact", "Marie Exemple phone=0600000000", db_session)
    assert "déjà en mémoire" in reponse, reponse
    assert "Non appliqué" in reponse and "telephone" in reponse.replace("é", "e"), reponse


@pytest.mark.asyncio
async def test_contact_retape_sans_option(db_session):
    from app.services.slash_commands import execute_slash_command

    await execute_slash_command("contact", "Marie Exemple", db_session)
    reponse = await execute_slash_command("contact", "Marie Exemple", db_session)
    assert "Non appliqué" not in reponse, reponse


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "options",
    ["email=marie@exemple.fr", "email=MARIE@exemple.fr", "phone=0612345678", "phone=06 12 34 56 78"],
)
async def test_contact_retape_a_l_identique(db_session, options):
    """B-1271 : les champs ignorés comptaient la PRÉSENCE d'une valeur, pas sa
    différence ; retaper le courriel qui a retrouvé la fiche répondait
    « Non appliqué : email ». Revue du diff, passe 5 (cas C)."""
    from app.services.slash_commands import execute_slash_command

    await execute_slash_command(
        "contact", "Marie Exemple email=marie@exemple.fr phone=0612345678", db_session
    )
    reponse = await execute_slash_command("contact", f"Marie Exemple {options}", db_session)
    assert "déjà en mémoire" in reponse, reponse
    assert "Non appliqué" not in reponse, reponse


@pytest.mark.asyncio
async def test_un_autre_telephone_reste_signale(db_session):
    from app.services.slash_commands import execute_slash_command

    await execute_slash_command("contact", "Marie Exemple phone=0612345678", db_session)
    reponse = await execute_slash_command("contact", "Marie Exemple phone=0799999999", db_session)
    assert "Non appliqué" in reponse and "téléphone" in reponse, reponse


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("champ", "valeur", "libelle"),
    [("phone", 612345678, "téléphone"), ("notes", ["Rappeler lundi"], "notes"), ("address", {"rue": "1 rue X"}, "adresse")],
)
async def test_une_valeur_non_textuelle_reste_signalee(db_session, champ, valeur, libelle):
    """B-1285 : régression de B-1271, `_texte` rendait "" pour une valeur non
    textuelle et le champ n'était plus signalé ; un modèle local ne respecte
    pas toujours le schéma. Revue du diff, passe 6 (cas E)."""
    import json

    from app.services.memory_tools import execute_create_contact

    await execute_create_contact({"first_name": "Marie", "last_name": "Exemple"}, db_session)
    resultat = json.loads(await execute_create_contact(
        {"first_name": "Marie", "last_name": "Exemple", champ: valeur}, db_session,
    ))
    assert resultat.get("already_existed") is True, resultat
    assert libelle in resultat.get("champs_ignores", []), resultat
    assert resultat.get("success") is False, resultat


@pytest.mark.asyncio
async def test_un_autre_nom_retrouve_par_le_courriel_est_signale(db_session):
    """B-1298 : régression de B-1271. Retrouvée par son courriel sous un autre
    nom, la fiche était réutilisée en silence : succès, aucun champ ignoré,
    alors que le nom saisi n'était pas enregistré. Lecteur X, passe 5."""
    import json

    from app.services.memory_tools import execute_create_contact

    await execute_create_contact(
        {"first_name": "Marie", "last_name": "Exemple", "email": "marie@exemple.fr"}, db_session,
    )
    resultat = json.loads(await execute_create_contact(
        {"first_name": "Marie", "last_name": "Durand", "email": "marie@exemple.fr"}, db_session,
    ))
    assert resultat.get("already_existed") is True, resultat
    assert "nom" in resultat.get("champs_ignores", []), resultat
    assert resultat.get("success") is False, resultat


@pytest.mark.asyncio
async def test_le_meme_nom_en_autre_casse_n_est_pas_signale(db_session):
    import json

    from app.services.memory_tools import execute_create_contact

    await execute_create_contact(
        {"first_name": "Marie", "last_name": "Exemple", "email": "marie@exemple.fr"}, db_session,
    )
    resultat = json.loads(await execute_create_contact(
        {"first_name": "marie", "last_name": "EXEMPLE", "email": "marie@exemple.fr"}, db_session,
    ))
    assert "nom" not in resultat.get("champs_ignores", []), resultat


@pytest.mark.asyncio
async def test_un_prenom_seul_avec_le_courriel_n_est_pas_un_autre_nom(db_session):
    import json

    from app.services.memory_tools import execute_create_contact

    await execute_create_contact(
        {"first_name": "Marie", "last_name": "Exemple", "email": "marie@exemple.fr"}, db_session,
    )
    resultat = json.loads(await execute_create_contact(
        {"first_name": "Marie", "email": "marie@exemple.fr"}, db_session,
    ))
    assert "nom" not in resultat.get("champs_ignores", []), resultat


@pytest.mark.asyncio
async def test_une_difference_d_accent_n_est_pas_un_autre_nom(db_session):
    """B-1311 : Hélène et Helene étaient annoncés comme deux noms (casefold ne
    replie pas les accents). Lecteur α, passe 6."""
    import json

    from app.services.memory_tools import execute_create_contact

    await execute_create_contact(
        {"first_name": "Hélène", "last_name": "Exemple", "email": "helene@exemple.fr"}, db_session,
    )
    resultat = json.loads(await execute_create_contact(
        {"first_name": "Helene", "last_name": "Exemple", "email": "helene@exemple.fr"}, db_session,
    ))
    assert "nom" not in resultat.get("champs_ignores", []), resultat
