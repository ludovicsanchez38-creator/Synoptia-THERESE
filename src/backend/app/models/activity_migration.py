"""Migration desktop idempotente, sans commande Alembic au démarrage."""
import logging
from typing import Any

logger = logging.getLogger(__name__)


def migrer_activites(conn: Any) -> None:
    colonnes = {r[1]: r for r in conn.execute('PRAGMA table_info(activities)')}
    if not colonnes:
        return
    reconstruire = colonnes['contact_id'][3] or not {
        'project_id', 'conversation_id', 'execution_id', 'statut', 'remplace_id',
    } <= colonnes.keys()
    # SQLite exige une reconstruction pour retirer NOT NULL. Aucune copie
    # hors SQLCipher ; les ids, annulations et notes CRM restent identiques.
    conn.commit()
    foreign_keys = conn.execute('PRAGMA foreign_keys').fetchone()[0]
    conn.execute('PRAGMA foreign_keys=OFF')
    reparations = 0
    try:
        conn.execute('BEGIN IMMEDIATE')
        if reconstruire:
            nombre = conn.execute('SELECT COUNT(*) FROM activities').fetchone()[0]
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
            if conn.execute('SELECT COUNT(*) FROM activities_r5').fetchone()[0] != nombre:
                raise ValueError('Migration des activités : copie incomplète.')
            conn.execute('DROP TABLE activities')
            conn.execute('ALTER TABLE activities_r5 RENAME TO activities')
            for nom in ('contact_id', 'project_id', 'conversation_id', 'statut', 'execution_id'):
                unique = 'UNIQUE ' if nom == 'execution_id' else ''
                conn.execute(f'CREATE {unique}INDEX ix_activities_{nom} ON activities ({nom})')
        # Une ancienne suppression peut avoir laissé ces liens sans cible.
        # Les annulations valides, y compris vers une ligne copiée plus tard,
        # restent intactes : toutes les activités sont déjà dans la table finale.
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for colonne, table in (
            ('contact_id', 'contacts'), ('project_id', 'projects'),
            ('conversation_id', 'conversations'), ('remplace_id', 'activities'),
        ):
            # Une base partielle ne permet pas de conclure à un lien orphelin.
            if table not in tables:
                continue
            reparations += conn.execute(
                f'UPDATE activities SET {colonne}=NULL WHERE {colonne} IS NOT NULL '
                f'AND NOT EXISTS (SELECT 1 FROM {table} AS cible WHERE cible.id=activities.{colonne})'
            ).rowcount
        if any(r[2] in tables for r in conn.execute('PRAGMA foreign_key_check(activities)')):
            raise ValueError('Migration des activités : liens incohérents.')
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.execute(f'PRAGMA foreign_keys={int(foreign_keys)}')
    if reparations:
        logger.warning('Migration des activités : %d lien(s) orphelin(s) remis à NULL.', reparations)
