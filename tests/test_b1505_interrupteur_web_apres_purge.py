"""B-1505 : l'interrupteur de recherche web gardait son ancienne valeur
après « Effacer toutes mes données ».

La purge efface la préférence et vide les caches du profil et des clés,
pas celui de l'interrupteur : jusqu'au redémarrage, la recherche restait
coupée alors que plus rien ne le disait en base.
"""

import pytest


@pytest.mark.asyncio
async def test_la_purge_remet_l_interrupteur_a_son_etat_par_defaut(client):
    from app.services.web_search import poser_autorisation_recherche, recherche_web_autorisee

    try:
        coupure = await client.post("/api/config/web-search?enabled=false")
        assert coupure.status_code == 200, coupure.text
        assert recherche_web_autorisee() is False

        purge = await client.delete("/api/data/all?confirm=true")
        assert purge.status_code == 200, purge.text

        etat = await client.get("/api/config/web-search")
        attendu = etat.json().get("enabled", True) if etat.status_code == 200 else True
        assert recherche_web_autorisee() is attendu is True
    finally:
        poser_autorisation_recherche(None)
