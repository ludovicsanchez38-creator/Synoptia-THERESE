"""B-1116 : le client HTTP doit fermer les moteurs laissés par un service."""
from contextlib import AsyncExitStack, ExitStack

import pytest
from app.models import database
from app.models.entities import Contact
from sqlalchemy import text

from tests.conftest import _test_lifespan, app


async def verifier_fermeture(nom="Témoin", nombre_sync=1, nombre_async=1):
    await database.close_db()
    await database.init_db()
    contact = Contact(first_name=nom)
    async with database.get_session_context() as session:
        session.add(contact)
    with ExitStack() as pile:
        for _ in range(nombre_sync):
            pile.enter_context(database.sync_engine.connect()).execute(text("SELECT 1"))
    async with AsyncExitStack() as pile_async:
        for _ in range(nombre_async):
            connexion = await pile_async.enter_async_context(database.async_engine.connect())
            await connexion.execute(text("SELECT 1"))
    # Garder les références permet de vérifier la fermeture sans dépendre du GC.
    moteur_sync, moteur_async = database.sync_engine, database.async_engine
    pool_sync, pool_async = moteur_sync.pool, moteur_async.pool
    assert pool_sync.checkedin() == nombre_sync
    assert pool_async.checkedin() == nombre_async
    try:
        async with _test_lifespan(app):
            assert pool_sync.checkedin() == 0, "L'ancien pool sync reste connecté à la base partagée"
            assert pool_async.checkedin() == 0, "L'ancien pool async reste connecté à la base partagée"
            async with database.get_session_context() as session:
                assert (await session.get(Contact, contact.id)).first_name == nom
    finally:
        await moteur_async.dispose()
        moteur_sync.dispose()


async def test_le_client_ne_perd_pas_les_pools_du_service_precedent():
    await verifier_fermeture()


# Dix états de pools et données inventés après le correctif de la fixture.
@pytest.mark.parametrize("nom,nombre_sync,nombre_async", [
    ("Alix", 1, 2), ("Brune", 2, 1), ("Céleste", 2, 2), ("Denis", 1, 3),
    ("Éloi", 3, 1), ("Faustine", 2, 3), ("Gaël", 3, 2), ("Héloïse", 3, 3),
    ("Ismaël", 1, 4), ("Joséphine", 4, 1),
])
async def test_rejeu_apres_correctif(nom, nombre_sync, nombre_async):
    await verifier_fermeture(nom, nombre_sync, nombre_async)
