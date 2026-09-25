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
