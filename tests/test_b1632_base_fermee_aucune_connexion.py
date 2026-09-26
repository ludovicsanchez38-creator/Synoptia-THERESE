"""B-1632 : pendant une restauration, close_db() laissait la fabrique de
sessions branchée sur le moteur fermé. La sonde /health, que le mode
maintenance laisse passer, pouvait donc rouvrir une connexion au fichier en
cours de remplacement (sous Windows, un fichier ouvert ne se remplace pas).
Base fermée : toute demande de session échoue tout de suite, et la sonde
dit la base indisponible.
"""

import pytest


@pytest.mark.asyncio
async def test_base_fermee_la_sonde_n_ouvre_aucune_connexion(client):
    from app import main
    from app.models import database

    await database.close_db()
    try:
        assert database.AsyncSessionLocal is None
        assert await main._check_database_available() is False
    finally:
        await database.init_db()
