"""B-1089 : réparer les seuls liens orphelins, sans perdre le journal CRM."""

import logging
import sqlite3
from contextlib import closing

import pytest
from app.models.activity_migration import migrer_activites
from app.models.database import _db_key_pragma

COLONNES = {
    'id': 'VARCHAR PRIMARY KEY NOT NULL',
    'contact_id': 'VARCHAR NOT NULL REFERENCES contacts(id)',
    'project_id': 'VARCHAR REFERENCES projects(id)',
    'conversation_id': 'VARCHAR REFERENCES conversations(id) ON DELETE SET NULL',
    'execution_id': 'VARCHAR',
    'type': 'VARCHAR NOT NULL',
    'title': 'VARCHAR NOT NULL',
    'description': 'VARCHAR',
    'statut': "VARCHAR NOT NULL DEFAULT 'en_vigueur'",
    'remplace_id': 'VARCHAR REFERENCES activities(id)',
    'extra_data': 'VARCHAR',
    'created_at': 'DATETIME NOT NULL',
}
LIENS = {
    'contact_id': {'contact-valide'},
    'project_id': {'projet-valide'},
    'conversation_id': {'conversation-valide'},
}
MINIMALES = {'id', 'contact_id', 'type', 'title', 'description', 'extra_data', 'created_at'}


def activite(identifiant='a1', **changements):
    return {
        'id': identifiant,
        'contact_id': 'contact-valide',
        'project_id': 'projet-valide',
        'conversation_id': 'conversation-valide',
        'execution_id': f'execution-{identifiant}',
        'type': 'note',
        'title': f'SENTINELLE_B1089_TITRE_{identifiant}',
        'description': f'SENTINELLE_B1089_NOTE_{identifiant}',
        'statut': 'en_vigueur',
        'remplace_id': None,
        'extra_data': '{"notes":["SENTINELLE_B1089_JSON"]}',
        'created_at': '2026-01-02 03:04:05',
        **changements,
    }


# Chaque cas est une base distincte, rejouée avec SQLite/SQLCipher et FK OFF/ON.
CAS = [
    pytest.param('ancien', [activite(contact_id='contact-absent')], id='contact-orphelin'),
    pytest.param('ancien', [activite(project_id='projet-absent')], id='projet-orphelin'),
    pytest.param('ancien', [activite(conversation_id='conversation-absente')], id='conversation-orpheline'),
    pytest.param('ancien', [activite(remplace_id='activite-absente')], id='remplacement-orphelin'),
    pytest.param('ancien', [
        activite('a1', statut='annulee'),
        activite('a2', contact_id='contact-absent', conversation_id='conversation-absente', remplace_id='a1'),
        activite('a3', project_id='projet-absent', remplace_id='activite-absente'),
    ], id='orphelins-meles'),
    pytest.param('ancien', [], id='zero-activite'),
    pytest.param('ancien', [
        activite(f'a{i}', contact_id='contact-absent', project_id='projet-absent',
                 conversation_id='conversation-absente', remplace_id='activite-absente')
        for i in range(3)
    ], id='toutes-orphelines'),
    pytest.param('migre', [activite(), activite('a2', contact_id=None, project_id=None,
                 conversation_id=None, remplace_id='a1')], id='deja-migre-sain'),
    pytest.param('migre', [activite(contact_id='contact-absent', remplace_id='activite-absente')],
                 id='deja-migre-orphelin'),
    pytest.param('minimal', [activite(), activite('a2', contact_id='contact-absent')],
                 id='colonnes-optionnelles-absentes'),
    pytest.param('partiel', [activite(contact_id=None, project_id='projet-absent')],
                 id='contact-nullable-execution-absente'),
    pytest.param('ancien', [activite('a1', statut='annulee', remplace_id='a2'),
                 activite('a2', remplace_id='a1'), activite('a3', remplace_id='a3')],
                 id='remplacements-valides-avant-cycle-soi'),
]


def connecter(chemin, pilote):
    if pilote == 'sqlcipher':
        import sqlcipher3

        conn = sqlcipher3.connect(str(chemin))
        conn.execute(_db_key_pragma())
        return conn
    return sqlite3.connect(chemin)


def preparer(conn, schema, lignes, foreign_keys, *, sans=None, autre_fk=False):
    for table, identifiant in (
        ('contacts', 'contact-valide'), ('projects', 'projet-valide'),
        ('conversations', 'conversation-valide'),
    ):
        conn.execute(f'CREATE TABLE {table} (id VARCHAR PRIMARY KEY)')
        conn.execute(f'INSERT INTO {table} VALUES (?)', (identifiant,))
    colonnes = dict(COLONNES)
    if schema in {'migre', 'partiel'}:
        colonnes['contact_id'] = colonnes['contact_id'].replace(' NOT NULL', '')
    if schema == 'minimal':
        colonnes = {n: d for n, d in colonnes.items() if n in MINIMALES}
    if schema == 'partiel':
        colonnes.pop('execution_id')
    if sans:
        colonnes.pop(sans)
    if autre_fk:
        colonnes['title'] += ' REFERENCES contacts(id)'
    definition = ', '.join(f'{n} {d}' for n, d in colonnes.items())
    conn.execute(f'CREATE TABLE activities ({definition})')
    for ligne in lignes:
        conn.execute(
            f'INSERT INTO activities ({",".join(colonnes)}) VALUES ({",".join("?" for _ in colonnes)})',
            tuple(ligne[n] for n in colonnes),
        )
    conn.commit()
    conn.execute(f'PRAGMA foreign_keys={foreign_keys}')
    return colonnes


def lire(conn):
    resultat = conn.execute('SELECT * FROM activities ORDER BY id')
    return [dict(zip((c[0] for c in resultat.description), ligne, strict=True)) for ligne in resultat]


def etat(conn):
    return (
        conn.execute("SELECT type, name, sql FROM sqlite_master ORDER BY type, name").fetchall(),
        lire(conn),
    )


@pytest.mark.parametrize('pilote', ['sqlite', 'sqlcipher'])
@pytest.mark.parametrize('foreign_keys', [0, 1], ids=['fk-off', 'fk-on'])
@pytest.mark.parametrize(('schema', 'lignes'), CAS)
def test_migration_repare_sans_perte_et_reste_idempotente(
    tmp_path, caplog, record_property, pilote, foreign_keys, schema, lignes,
):
    chemin = tmp_path / 'activites.db'
    with closing(connecter(chemin, pilote)) as conn:
        preparer(conn, schema, lignes, foreign_keys)
        avant = lire(conn)
        attendues = []
        reparations = 0
        for ligne in avant:
            attendue = dict.fromkeys(COLONNES) | {'statut': 'en_vigueur'} | ligne
            for nom, valides in (LIENS | {'remplace_id': {r['id'] for r in avant}}).items():
                if attendue[nom] is not None and attendue[nom] not in valides:
                    attendue[nom] = None
                    reparations += 1
            attendues.append(attendue)
        with caplog.at_level(logging.WARNING, logger='app.models.activity_migration'):
            migrer_activites(conn)
        assert lire(conn) == attendues
        nombre_apres = conn.execute('SELECT COUNT(*) FROM activities').fetchone()[0]
        assert nombre_apres == len(avant)
        record_property('activites_avant', len(avant))
        record_property('activites_apres', nombre_apres)
        record_property('liens_nullifies', reparations)
        assert not conn.execute('PRAGMA foreign_key_check(activities)').fetchall()
        assert conn.execute('PRAGMA foreign_keys').fetchone()[0] == foreign_keys
        assert set(r[1] for r in conn.execute('PRAGMA table_info(activities)')) == set(COLONNES)
        assert not next(r[3] for r in conn.execute('PRAGMA table_info(activities)') if r[1] == 'contact_id')
        if schema != 'migre':
            assert {r[1] for r in conn.execute('PRAGMA index_list(activities)')} >= {
                'ix_activities_contact_id', 'ix_activities_project_id',
                'ix_activities_conversation_id', 'ix_activities_statut', 'ix_activities_execution_id',
            }
        messages = [r.getMessage() for r in caplog.records if r.name == 'app.models.activity_migration']
        assert messages == ([f'Migration des activités : {reparations} lien(s) orphelin(s) remis à NULL.']
                            if reparations else [])
        instantane, changements = etat(conn), conn.total_changes
        caplog.clear()
        migrer_activites(conn)
        assert etat(conn) == instantane
        assert conn.total_changes == changements
        assert conn.execute('PRAGMA foreign_keys').fetchone()[0] == foreign_keys
        assert not [r for r in caplog.records if r.name == 'app.models.activity_migration']
        if foreign_keys:
            with pytest.raises(Exception, match='FOREIGN KEY constraint failed'):
                conn.execute("INSERT INTO activities (id, contact_id, type, title, created_at) "
                             "VALUES ('interdit', 'contact-absent', 'note', 'Test FK', '2026-01-01')")
            conn.rollback()
    with closing(connecter(chemin, pilote)) as conn:
        assert lire(conn) == attendues
    if pilote == 'sqlcipher':
        assert b'SENTINELLE_B1089' not in chemin.read_bytes()
        with closing(sqlite3.connect(chemin)) as sans_cle, pytest.raises(sqlite3.DatabaseError):
            sans_cle.execute('SELECT * FROM activities').fetchall()


class ConnexionDefaillante:
    """Injecter une panne après copie, ou simuler une copie tronquée."""

    def __init__(self, conn, panne):
        self.conn, self.panne = conn, panne

    def __getattr__(self, nom):
        return getattr(self.conn, nom)

    def execute(self, sql):
        if self.panne == 'copie-incomplete' and sql.startswith('INSERT INTO activities_r5'):
            sql += ' LIMIT 1'
        if self.panne == 'erreur-sql' and sql.startswith('CREATE UNIQUE INDEX'):
            return self.conn.execute('SQL INVALIDE POUR TEST')
        return self.conn.execute(sql)


@pytest.mark.parametrize('pilote', ['sqlite', 'sqlcipher'])
@pytest.mark.parametrize('foreign_keys', [0, 1], ids=['fk-off', 'fk-on'])
@pytest.mark.parametrize('panne', [
    'erreur-sql', 'copie-incomplete', 'colonne-obligatoire-absente', 'autre-fk', 'execution-dupliquee',
])
def test_migration_annule_toute_autre_incoherence(tmp_path, caplog, pilote, foreign_keys, panne):
    with closing(connecter(tmp_path / 'rollback.db', pilote)) as conn:
        preparer(
            conn, 'migre' if panne == 'autre-fk' else 'ancien',
            [activite(contact_id='contact-valide' if panne == 'copie-incomplete' else 'contact-absent'),
             activite('a2', execution_id='execution-a1' if panne == 'execution-dupliquee' else 'execution-a2')],
            foreign_keys,
            sans='title' if panne == 'colonne-obligatoire-absente' else None,
            autre_fk=panne == 'autre-fk',
        )
        avant = etat(conn)
        erreur = ValueError if panne in {'copie-incomplete', 'autre-fk'} else Exception
        message = {
            'erreur-sql': 'syntax error', 'copie-incomplete': 'copie incomplète',
            'colonne-obligatoire-absente': 'NOT NULL constraint failed.*title',
            'autre-fk': 'liens incohérents', 'execution-dupliquee': 'UNIQUE constraint failed.*execution_id',
        }[panne]
        with pytest.raises(erreur, match=message):
            migrer_activites(ConnexionDefaillante(conn, panne))
        assert etat(conn) == avant
        assert conn.execute('PRAGMA foreign_keys').fetchone()[0] == foreign_keys
        assert not conn.in_transaction
        assert not [r for r in caplog.records if r.name == 'app.models.activity_migration']


def test_absence_table_ne_modifie_rien():
    with closing(sqlite3.connect(':memory:')) as conn:
        conn.execute('PRAGMA foreign_keys=ON')
        migrer_activites(conn)
        assert conn.execute('SELECT name FROM sqlite_master').fetchall() == []
        assert conn.execute('PRAGMA foreign_keys').fetchone()[0] == 1


@pytest.mark.asyncio
@pytest.mark.parametrize('pilote', ['sqlite', 'sqlcipher'])
async def test_init_db_redemarre_avec_des_activites_orphelines(tmp_path, monkeypatch, caplog, pilote):
    from app.models import database

    monkeypatch.setattr(database.settings, 'data_dir', tmp_path)
    monkeypatch.setattr(database.settings, 'db_path', tmp_path / 'therese.db')
    monkeypatch.setattr(database, 'db_encryption_enabled', lambda: pilote == 'sqlcipher')
    try:
        await database.init_db()
        await database.close_db()
        with closing(database.db_connect(database.settings.db_path)) as conn:
            conn.execute('DROP TABLE activities')
            definition = ', '.join(f'{n} {d}' for n, d in COLONNES.items())
            conn.execute(f'CREATE TABLE activities ({definition})')
            lignes = [activite('a1', statut='annulee', remplace_id='activite-absente'),
                      activite('a2', remplace_id='a1')]
            for ligne in lignes:
                conn.execute(
                    f'INSERT INTO activities ({",".join(COLONNES)}) '
                    f'VALUES ({",".join("?" for _ in COLONNES)})', tuple(ligne.values()),
                )
            conn.commit()
        caplog.clear()
        with caplog.at_level(logging.WARNING, logger='app.models.activity_migration'):
            await database.init_db()
        assert database._db_cipher_active == (pilote == 'sqlcipher')
        with closing(database.db_connect(database.settings.db_path)) as conn:
            attendues = [ligne | dict.fromkeys(LIENS) for ligne in lignes]
            attendues[0]['remplace_id'] = None
            assert lire(conn) == attendues
            assert not conn.execute('PRAGMA foreign_key_check(activities)').fetchall()
        assert [r.getMessage() for r in caplog.records if r.name == 'app.models.activity_migration'] == [
            'Migration des activités : 7 lien(s) orphelin(s) remis à NULL.',
        ]
    finally:
        await database.close_db()
