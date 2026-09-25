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
