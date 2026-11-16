"""Les bases antérieures à contact_id doivent rester migrables."""

import sqlite3
from contextlib import closing

import pytest
from app.models.activity_migration import migrer_activites

from tests.test_activity_migration import activite, preparer


@pytest.mark.parametrize('enrichi', [False, True], ids=['standard', 'enrichi'])
def test_migration_ajoute_contact_absent_sans_perte(enrichi):
    with closing(sqlite3.connect(':memory:')) as conn:
        preparer(conn, 'minimal', [activite()], 1, sans='contact_id')
        if enrichi:
            conn.execute("ALTER TABLE activities ADD COLUMN archive TEXT DEFAULT 'conservée'")
        migrer_activites(conn)
        colonnes = {r[1]: r for r in conn.execute('PRAGMA table_info(activities)')}
        assert colonnes['contact_id'][3] == 0
        assert conn.execute('SELECT id, contact_id FROM activities').fetchone() == ('a1', None)
        if enrichi:
            assert conn.execute('SELECT archive FROM activities').fetchone()[0] == 'conservée'
        assert conn.execute('PRAGMA foreign_keys').fetchone()[0] == 1
