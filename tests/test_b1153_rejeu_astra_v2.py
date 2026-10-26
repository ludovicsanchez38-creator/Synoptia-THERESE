"""Dix schémas inventés après le premier vert, sur les deux moteurs."""
from contextlib import closing

import pytest
from app.models.activity_migration import migrer_activites

from tests.test_activity_migration import activite, connecter, etat, lire, preparer


@pytest.mark.parametrize('pilote', ['sqlite', 'sqlcipher'])
@pytest.mark.parametrize('nom,definition,valeur,index', [
    ('annotation', "TEXT DEFAULT 'NOT NULL, (archive)'", 'été, automne (Lyon)', ''),
    ('rang', 'INTEGER NOT NULL DEFAULT 9 CHECK (rang BETWEEN 1 AND 20)', 12, ''),
    ('signature', 'BLOB', b'\x00\x81\xff', ''),
    ('taux', 'REAL CHECK (taux >= 0)', 18.125, ''),
    ('commentaire', 'TEXT', None, ''),
    ('note "source", (locale)', 'TEXT', 'citation « reçue »', ''),
    ('titre_minuscule', 'TEXT GENERATED ALWAYS AS (lower(title)) VIRTUAL', None, ''),
    ('longueur', 'INTEGER GENERATED ALWAYS AS (length(title)) STORED', None, ''),
    ('code', 'TEXT COLLATE NOCASE UNIQUE', 'ARCHIVE-A', ''),
    ('origine', 'TEXT REFERENCES contacts(id)', 'contact-valide',
     'CREATE INDEX archive_origine ON activities (origine) WHERE origine IS NOT NULL'),
])
def test_dix_schemas_enrichis(tmp_path, pilote, nom, definition, valeur, index):
    with closing(connecter(tmp_path / 'archive.db', pilote)) as conn:
        preparer(conn, 'minimal', [], 1)
        identifiant = '"' + nom.replace('"', '""') + '"'
        schema = conn.execute("SELECT sql FROM sqlite_master WHERE name='activities'").fetchone()[0]
        conn.execute('DROP TABLE activities')
        conn.execute(schema[:-1] + f', {identifiant} {definition})')
        ligne = activite()
        conn.execute('INSERT INTO activities (id, contact_id, type, title, created_at) VALUES (?, ?, ?, ?, ?)',
                     tuple(ligne[k] for k in ('id', 'contact_id', 'type', 'title', 'created_at')))
        if 'GENERATED' not in definition:
            conn.execute(f'UPDATE activities SET {identifiant}=?', (valeur,))
        if index:
            conn.execute(index)
        conn.commit()
        avant = lire(conn)
        migrer_activites(conn)
        assert [{k: ligne[k] for k in avant[0]} for ligne in lire(conn)] == avant
        ddl = conn.execute("SELECT sql FROM sqlite_master WHERE name='activities'").fetchone()[0]
        assert definition in ddl
        if index:
            assert conn.execute("SELECT sql FROM sqlite_master WHERE name='archive_origine'").fetchone()[0] == index
        assert not conn.execute('PRAGMA foreign_key_check(activities)').fetchall()
        assert conn.execute('PRAGMA foreign_keys').fetchone()[0] == 1
        apres = etat(conn)
        migrer_activites(conn)
        assert etat(conn) == apres
        if 'GENERATED' in definition:
            conn.execute("UPDATE activities SET title='Nouveau titre'")
            attendu = len('Nouveau titre') if nom == 'longueur' else 'nouveau titre'
            assert conn.execute(f'SELECT {identifiant} FROM activities').fetchone()[0] == attendu


@pytest.mark.parametrize('pilote', ['sqlite', 'sqlcipher'])
@pytest.mark.parametrize('forme', ['contrainte-table', 'not-null-nomme'])
def test_contraintes_enrichies_conservees(tmp_path, pilote, forme):
    with closing(connecter(tmp_path / 'contraintes.db', pilote)) as conn:
        preparer(conn, 'minimal', [], 1)
        ddl = conn.execute("SELECT sql FROM sqlite_master WHERE name='activities'").fetchone()[0]
        if forme == 'not-null-nomme':
            ddl = ddl.replace('contact_id VARCHAR NOT NULL',
                              '"contact_id" VARCHAR CONSTRAINT lien_requis NOT NULL ON CONFLICT ABORT')
        conn.execute('DROP TABLE activities')
        conn.execute(ddl[:-1] + ', archive TEXT, CONSTRAINT archive_non_vide CHECK (length(archive) > 0))')
        conn.execute("INSERT INTO activities (id, contact_id, type, title, created_at, archive) "
                     "VALUES ('a1', 'contact-valide', 'note', 'Titre', '2026-02-01', 'source')")
        conn.commit()
        migrer_activites(conn)
        assert conn.execute('SELECT archive FROM activities').fetchone()[0] == 'source'
        assert 'project_id' in {r[1] for r in conn.execute('PRAGMA table_info(activities)')}
        conn.execute('UPDATE activities SET contact_id=NULL')
        conn.commit()
        with pytest.raises(Exception, match='CHECK constraint failed'):
            conn.execute("UPDATE activities SET archive=''")
        conn.rollback()
