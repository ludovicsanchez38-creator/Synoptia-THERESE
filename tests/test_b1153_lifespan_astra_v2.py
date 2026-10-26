"""Exerce init_db et le lifespan de production sur une ancienne table enrichie."""
import sqlite3
import tempfile
from contextlib import AsyncExitStack, closing

import aiosqlite.core
import pytest
from app import main
from app.models import database
from app.models.entities import Contact
from app.services import http_client, project_sync_service, qdrant
from starlette.datastructures import State

from tests.test_activity_migration import COLONNES, MINIMALES


@pytest.fixture
async def lifespan_isole(tmp_path, monkeypatch, pilote):
    """Rendre les globals d'entrée, même si le vrai démarrage ou le test échoue."""
    with monkeypatch.context() as patch:
        patch.setenv('THERESE_SKIP_SERVICES', '1')
        patch.setenv('THERESE_DATA_DIR', str(tmp_path))
        patch.setattr(database.settings, 'data_dir', tmp_path)
        patch.setattr(database.settings, 'db_path', tmp_path / 'therese.db')
        # Le ménage des audios du vrai lifespan doit lui aussi rester local.
        patch.setattr(tempfile, 'tempdir', str(tmp_path))
        patch.setattr(database, 'db_encryption_enabled', lambda: pilote == 'sqlcipher')

        # Détacher les ressources précédentes AVANT init_db/close_db : les
        # restaurer après les avoir fermées ou annulées ne les préserverait pas.
        for nom in ('sync_engine', 'async_engine', 'AsyncSessionLocal'):
            patch.setattr(database, nom, None)
        patch.setattr(database, '_db_cipher_active', False)
        # init_db substitue ce pilote global en SQLCipher ; close_db ne le rend
        # pas. Chaque cas SQLite doit aussi repartir avec le vrai pilote SQLite.
        patch.setattr(aiosqlite.core, 'sqlite3', sqlite3)
        patch.setattr(http_client, '_http_client', None)
        patch.setattr(qdrant, '_qdrant_service', None)
        patch.setattr(project_sync_service, '_applies_en_cours', set())

        # Le shutdown efface le fichier du jeton, mais laisse session_token
        # dans app.state : les clients suivants recevaient alors tous un 401.
        patch.setattr(main.app, 'state', State(dict(main.app.state._state)))
        patch.setattr(main.app, 'dependency_overrides', dict(main.app.dependency_overrides))

        async with AsyncExitStack() as nettoyage:
            nettoyage.push_async_callback(database.close_db)
            nettoyage.push_async_callback(qdrant.close_qdrant)
            nettoyage.push_async_callback(http_client.close_http_client)
            yield
        # Les pools du cas sont fermés avant que monkeypatch rende les globals.


@pytest.mark.parametrize('pilote', ['sqlite', 'sqlcipher'])
@pytest.mark.parametrize('schema', ['ancien', 'minimal'])
@pytest.mark.parametrize('impossible', ['', 'declencheur', 'collation'], ids=['colonne-preservee', 'declencheur-preserve', 'collation-indisponible'])
async def test_refus_reconstruction_ne_bloque_pas_le_demarrage(lifespan_isole, caplog, pilote, schema, impossible):
    try:
        await database.init_db()
        async with database.get_session_context() as session:
            session.add(Contact(id='contact-source', first_name='Camille'))
        await database.close_db()
        with closing(database.db_connect(database.settings.db_path)) as conn:
            conn.execute('DROP TABLE activities')
            colonnes = {n:d for n,d in COLONNES.items() if schema == 'ancien' or n in MINIMALES}
            definition = ', '.join(f'{n} {d}' for n,d in colonnes.items())
            if impossible == 'collation':
                conn.create_collation('tri_archive', lambda a, b: (a > b) - (a < b))
            extra = ' COLLATE tri_archive' if impossible == 'collation' else ''
            conn.execute(f'CREATE TABLE activities ({definition}, origine_archive TEXT{extra})')
            conn.execute("INSERT INTO activities (id, contact_id, type, title, created_at, origine_archive) VALUES ('activite-source', 'contact-source', 'note', 'Entretien', '2026-01-02', 'archive conservée')")
            if impossible == 'declencheur':
                conn.execute("CREATE TRIGGER garder_archive AFTER UPDATE ON activities BEGIN SELECT 1; END")
            conn.commit()
        # Le vrai lifespan appelle init_db avant son bloc try/except des migrations.
        async with main.lifespan(main.app):
            assert database.AsyncSessionLocal is not None
            assert database._db_cipher_active == (pilote == 'sqlcipher')
            with closing(database.db_connect(database.settings.db_path)) as conn:
                assert conn.execute('SELECT origine_archive FROM activities').fetchall() == [('archive conservée',)]
                infos = {r[1]: r for r in conn.execute('PRAGMA table_info(activities)')}
                if impossible:
                    assert infos['contact_id'][3] == 1
                    assert ('déclencheur présent' if impossible == 'declencheur' else 'Migration sautée') in caplog.text
                else:
                    assert infos['contact_id'][3] == 0
                    assert set(COLONNES) <= infos.keys()
        # Deuxième vrai démarrage : conservation et absence de reconstruction inutile.
        async with main.lifespan(main.app):
            with closing(database.db_connect(database.settings.db_path)) as conn:
                assert conn.execute('SELECT origine_archive FROM activities').fetchall() == [('archive conservée',)]
    finally:
        await database.close_db()
