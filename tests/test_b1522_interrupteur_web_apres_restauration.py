"""B-1522 (jumeau de B-1505) : après une restauration, l'interrupteur de
recherche web gardait le choix d'avant.

La restauration remplace toute la table des préférences, mais le cache de
l'interrupteur n'était ni vidé ni relu : une sauvegarde faite avec la
recherche coupée rouvrait le web jusqu'au redémarrage.
"""

import pytest

PASSE = "Passphrase-Test-123"


@pytest.mark.asyncio
async def test_la_restauration_remet_l_interrupteur_de_la_sauvegarde(client):
    from app.services.web_search import poser_autorisation_recherche, recherche_web_autorisee

    try:
        assert (await client.post("/api/config/web-search?enabled=false")).status_code == 200
        sauvegarde = await client.post("/api/data/backup", json={"password": PASSE})
        assert sauvegarde.status_code == 200, sauvegarde.text

        assert (await client.post("/api/config/web-search?enabled=true")).status_code == 200
        assert recherche_web_autorisee() is True

        reponse = await client.post(
            f"/api/data/restore/{sauvegarde.json()['backup_name']}?confirm=true", json={"password": PASSE},
        )
        assert reponse.status_code == 200, reponse.text
        assert recherche_web_autorisee() is False
    finally:
        poser_autorisation_recherche(None)
