"""Migration desktop idempotente, sans commande Alembic au démarrage."""
from typing import Any


def migrer_activites(conn: Any) -> None:
    colonnes = {r[1]: r for r in conn.execute('PRAGMA table_info(activities)')}
    if not colonnes:
        return
    if not colonnes['contact_id'][3] and {'project_id', 'conversation_id', 'execution_id'} <= colonnes.keys():
        return
    # SQLite exige une reconstruction pour retirer NOT NULL. Aucune copie
    # hors SQLCipher ; les ids, annulations et notes CRM restent identiques.
    conn.commit()
    foreign_keys = conn.execute('PRAGMA foreign_keys').fetchone()[0]
    conn.execute('PRAGMA foreign_keys=OFF')
    try:
        conn.execute('BEGIN IMMEDIATE')
        conn.execute('''CREATE TABLE activities_r5 (
            id VARCHAR PRIMARY KEY NOT NULL, contact_id VARCHAR REFERENCES contacts(id),
            project_id VARCHAR REFERENCES projects(id),
            conversation_id VARCHAR REFERENCES conversations(id) ON DELETE SET NULL,
            execution_id VARCHAR, type VARCHAR NOT NULL, title VARCHAR NOT NULL,
            description VARCHAR, statut VARCHAR NOT NULL DEFAULT 'en_vigueur',
            remplace_id VARCHAR REFERENCES activities(id), extra_data VARCHAR, created_at DATETIME NOT NULL)''')
        communs = ','.join(n for n in ('id', 'contact_id', 'project_id', 'conversation_id', 'execution_id',
            'type', 'title', 'description', 'statut', 'remplace_id', 'extra_data', 'created_at') if n in colonnes)
        conn.execute(f'INSERT INTO activities_r5 ({communs}) SELECT {communs} FROM activities')
        conn.execute('DROP TABLE activities')
        conn.execute('ALTER TABLE activities_r5 RENAME TO activities')
        for nom in ('contact_id', 'project_id', 'conversation_id', 'statut', 'execution_id'):
            unique = 'UNIQUE ' if nom == 'execution_id' else ''
            conn.execute(f'CREATE {unique}INDEX ix_activities_{nom} ON activities ({nom})')
        if conn.execute('PRAGMA foreign_key_check(activities)').fetchall():
            raise ValueError('Migration des activités : liens incohérents.')
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.execute(f'PRAGMA foreign_keys={int(foreign_keys)}')
