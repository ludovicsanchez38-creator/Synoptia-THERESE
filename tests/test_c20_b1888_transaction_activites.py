"""La migration ne doit pas valider la transaction de son appelant."""

import sqlite3
from contextlib import closing

from app.models.activity_migration import migrer_activites

from tests.test_activity_migration import activite, preparer


def test_reconstruction_preserve_la_transaction_appelante():
    with closing(sqlite3.connect(':memory:')) as conn:
        preparer(conn, 'ancien', [activite()], 1)
        titre_initial = conn.execute('SELECT title FROM activities').fetchone()[0]
        conn.execute("UPDATE activities SET title='Modification en attente'")

        migrer_activites(conn)

        assert conn.in_transaction, 'La transaction de l’appelant a été validée.'
        conn.rollback()
        assert conn.execute('SELECT title FROM activities').fetchone()[0] == titre_initial
        assert next(r[3] for r in conn.execute('PRAGMA table_info(activities)') if r[1] == 'contact_id')
        assert conn.execute('PRAGMA foreign_keys').fetchone()[0] == 1
