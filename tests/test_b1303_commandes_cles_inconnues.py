"""B-1303 : `/contact adresse=…`, `/projet montant=…` : une clé que la
commande ne lit pas était jetée sans le dire ; la réponse annonçait la
création comme si tout avait été pris. Lecteurs X et W, passe 5."""

import pytest


@pytest.mark.asyncio
async def test_contact_dit_la_cle_qu_il_ne_lit_pas(db_session):
    from app.services.slash_commands import execute_slash_command

    reponse = await execute_slash_command("contact", "Marie Exemple adresse=12 rue de l'Exemple", db_session)
    assert "créé" in reponse, reponse
    assert "adresse" in reponse and "ignor" in reponse.lower(), reponse


@pytest.mark.asyncio
async def test_projet_dit_la_cle_qu_il_ne_lit_pas(db_session):
    from app.services.slash_commands import execute_slash_command

    reponse = await execute_slash_command("projet", "Chantier montant=1200 date=lundi", db_session)
    assert "créé" in reponse, reponse
    assert "montant" in reponse and "date" in reponse, reponse


@pytest.mark.asyncio
async def test_les_cles_lues_ne_sont_pas_signalees(db_session):
    from app.services.slash_commands import execute_slash_command

    reponse = await execute_slash_command("contact", "Marie Exemple email=marie@exemple.fr tel=0600000000", db_session)
    assert "ignor" not in reponse.lower(), reponse
