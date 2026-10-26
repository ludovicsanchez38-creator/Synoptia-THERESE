"""Exerce init_db et le lifespan de production sur une ancienne table enrichie."""
from contextlib import closing

import pytest
from app import main
from app.models import database
from app.models.entities import Contact

from tests.test_activity_migration import COLONNES, MINIMALES


@pytest.mark.parametrize('pilote', ['sqlite', 'sqlcipher'])
@pytest.mark.parametrize('schema', ['ancien', 'minimal'])
@pytest.mark.parametrize('impossible', ['', 'declencheur', 'collation'], ids=['colonne-preservee', 'declencheur-preserve', 'collation-indisponible'])
async def test_refus_reconstruction_ne_bloque_pas_le_demarrage(tmp_path, monkeypatch, caplog, pilote, schema, impossible):
    await database.close_db()
    monkeypatch.setattr(database.settings, 'data_dir', tmp_path)
    monkeypatch.setattr(database.settings, 'db_path', tmp_path / 'therese.db')
    monkeypatch.setattr(database, 'db_encryption_enabled', lambda: pilote == 'sqlcipher')
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
