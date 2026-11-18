"""La réparation des liens ne valide pas la transaction appelante."""

import sqlite3
from contextlib import closing

from app.models.activity_migration import migrer_activites

from tests.test_activity_migration import activite, preparer


def test_reparation_preserve_la_transaction_appelante():
    with closing(sqlite3.connect(':memory:')) as conn:
        preparer(conn, 'migre', [activite(project_id='projet-absent')], 1)
        titre_initial = conn.execute('SELECT title FROM activities').fetchone()[0]
        conn.execute("UPDATE activities SET title='Modification en attente'")

        migrer_activites(conn)

        assert conn.in_transaction, 'La réparation a validé la transaction de l’appelant.'
        conn.rollback()
        assert conn.execute('SELECT title, project_id FROM activities').fetchone() == (
            titre_initial, 'projet-absent',
        )
        assert conn.execute('PRAGMA foreign_keys').fetchone()[0] == 1
