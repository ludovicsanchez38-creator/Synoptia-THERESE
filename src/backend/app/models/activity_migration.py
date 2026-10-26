"""Migration desktop idempotente, sans commande Alembic au démarrage."""
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

_COLONNES_RECONSTRUITES = {
    'id': 'VARCHAR PRIMARY KEY NOT NULL', 'contact_id': 'VARCHAR REFERENCES contacts(id)',
    'project_id': 'VARCHAR REFERENCES projects(id)',
    'conversation_id': 'VARCHAR REFERENCES conversations(id) ON DELETE SET NULL',
    'execution_id': 'VARCHAR', 'type': 'VARCHAR NOT NULL', 'title': 'VARCHAR NOT NULL',
    'description': 'VARCHAR', 'statut': "VARCHAR NOT NULL DEFAULT 'en_vigueur'",
    'remplace_id': 'VARCHAR REFERENCES activities(id)', 'extra_data': 'VARCHAR',
    'created_at': 'DATETIME NOT NULL',
}

# Les chaînes, identifiants cités et commentaires restent des jetons indivisibles.
_JETONS_SQL = re.compile(r"' (?:''|[^'])* ' | \" (?:\"\"|[^\"])* \" | ` (?:``|[^`])* ` "
                         r"| \[ [^\]]* \] | --[^\n]* | /\*.*?\*/ | \w+ | [^\s]", re.X | re.S)


def _schema_enrichi(conn: Any, colonnes: dict[str, Any]) -> str | None:
    """Reprendre le DDL exact, en ne retirant que NOT NULL de contact_id.

    Ainsi CHECK, DEFAULT, COLLATE, contraintes et colonnes calculées ne sont
    pas réinventés à partir de table_info, qui ne sait pas les restituer.
    """
    sql: str = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='activities'").fetchone()[0]
    jetons = list(_JETONS_SQL.finditer(sql))
    profondeur = 0
    debut = fin = None
    contact = False
    retraits = []
    for i, jeton in enumerate(jetons):
        mot = jeton.group()
        if mot == '(':
            profondeur += 1
            if profondeur == 1:
                debut = jeton.end()
        elif mot == ')':
            profondeur -= 1
            if profondeur == 0:
                fin = jeton.start()
        elif profondeur == 1:
            if jetons[i - 1].group() in ('(', ','):
                contact = mot.strip('"`[]').lower() == 'contact_id'
            if contact and mot.upper() == 'NOT' and jetons[i + 1].group().upper() == 'NULL':
                # Une contrainte nommée exige aussi de retirer son nom.
                start = jetons[i - 2].start() if jetons[i - 2].group().upper() == 'CONSTRAINT' else jeton.start()
                end = jetons[i + 1].end()
                if [j.group().upper() for j in jetons[i + 2:i + 4]] == ['ON', 'CONFLICT']:
                    end = jetons[i + 4].end()
                retraits.append((start, end))
    if (debut is None or fin is None or 'VIRTUAL TABLE' in sql[:debut].upper()
            or (colonnes['contact_id'][3] and len(retraits) != 1)):
        return None
    corps = sql[debut:fin]
    for start, end in reversed(retraits):
        corps = corps[:start - debut] + corps[end - debut:]
    ajouts = [f'{nom} {definition}' for nom, definition in _COLONNES_RECONSTRUITES.items()
              if nom not in colonnes]
    # Les colonnes doivent précéder les contraintes de table déjà présentes.
    return 'CREATE TABLE activities_r5 (' + ', '.join([*ajouts, corps]) + ')' + sql[fin + 1:]


def _verifier_liens(conn: Any, tables: set[str], liens: dict[str, str]) -> None:
    contraintes: dict[int, set[tuple[str, str]]] = {}
    for r in conn.execute('PRAGMA foreign_key_list(activities)'):
        contraintes.setdefault(r[0], set()).add((r[3], r[2]))
    if any(
        r[2] in tables or any(lien not in liens.items() for lien in contraintes[r[3]])
        for r in conn.execute('PRAGMA foreign_key_check(activities)')
    ):
        raise ValueError('Migration des activités : liens incohérents.')


def migrer_activites(conn: Any) -> None:
    # table_xinfo inclut les colonnes générées, également perdues par un DROP.
    colonnes = {r[1]: r for r in conn.execute('PRAGMA table_xinfo(activities)')}
    if not colonnes:
        return
    # Aucun déclencheur n'appartient au schéma standard. Préserver aussi ceux
    # d'une ancienne table, qu'une reconstruction ferait disparaître.
    if conn.execute("SELECT 1 FROM sqlite_master WHERE type='trigger' AND tbl_name='activities'").fetchone():
        logger.warning('Migration des activités : réparations des liens non effectuées (déclencheur présent).')
        return
    reconstruire = colonnes['contact_id'][3] or not {
        'project_id', 'conversation_id', 'execution_id', 'statut', 'remplace_id',
    } <= colonnes.keys()
    definition = 'CREATE TABLE activities_r5 (' + ', '.join(
        f'{nom} {ddl}' for nom, ddl in _COLONNES_RECONSTRUITES.items()) + ')'
    schema_enrichi = bool(colonnes.keys() - _COLONNES_RECONSTRUITES.keys())
    if reconstruire and schema_enrichi:
        enrichie = _schema_enrichi(conn, colonnes)
        if enrichie is None or conn.in_transaction:
            logger.warning('Migration des activités refusée : schéma enrichi non reconstructible '
                           'ou transaction en cours. Migration sautée, table conservée.')
            return
        definition = enrichie
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    liens = {
        'contact_id': 'contacts', 'project_id': 'projects',
        'conversation_id': 'conversations', 'remplace_id': 'activities',
    }
    # B-1140 : la base déjà migrée et sans réparation reste en lecture seule.
    # Les contraintes inhabituelles doivent toujours être vérifiées.
    if not reconstruire and not any(
        conn.execute(
            f'SELECT 1 FROM activities WHERE {colonne} IS NOT NULL '
            f'AND NOT EXISTS (SELECT 1 FROM {table} AS cible WHERE cible.id=activities.{colonne}) LIMIT 1'
        ).fetchone()
        for colonne, table in liens.items() if table in tables
    ):
        _verifier_liens(conn, tables, liens)
        return
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
            indexes = conn.execute("SELECT sql FROM sqlite_master WHERE type='index' "
                                   "AND tbl_name='activities' AND sql IS NOT NULL").fetchall()
            conn.execute(definition)
            communs = ','.join('"' + r[1].replace('"', '""') + '"'
                               for r in conn.execute('PRAGMA table_xinfo(activities_r5)')
                               if r[1] in colonnes and r[6] == 0)
            conn.execute(f'INSERT INTO activities_r5 ({communs}) SELECT {communs} FROM activities')
            if conn.execute('SELECT COUNT(*) FROM activities_r5').fetchone()[0] != nombre:
                raise ValueError('Migration des activités : copie incomplète.')
            conn.execute('DROP TABLE activities')
            conn.execute('ALTER TABLE activities_r5 RENAME TO activities')
            for (sql,) in indexes:
                conn.execute(sql)
            for nom in ('contact_id', 'project_id', 'conversation_id', 'statut', 'execution_id'):
                unique = 'UNIQUE ' if nom == 'execution_id' else ''
                conn.execute(f'CREATE {unique}INDEX IF NOT EXISTS ix_activities_{nom} ON activities ({nom})')
        # Une ancienne suppression peut avoir laissé ces liens sans cible.
        # Les annulations valides, y compris vers une ligne copiée plus tard,
        # restent intactes : toutes les activités sont déjà dans la table finale.
        for colonne, table in liens.items():
            # Une base partielle ne permet pas de conclure à un lien orphelin.
            if table not in tables:
                continue
            reparations += conn.execute(
                f'UPDATE activities SET {colonne}=NULL WHERE {colonne} IS NOT NULL '
                f'AND NOT EXISTS (SELECT 1 FROM {table} AS cible WHERE cible.id=activities.{colonne})'
            ).rowcount
        _verifier_liens(conn, tables, liens)
        conn.commit()
    except Exception as erreur:
        conn.rollback()
        # Une extension locale absente empêche de recréer son DDL, mais la
        # table d'origine reste lisible. Ne pas masquer les autres erreurs
        # (disque, intégrité, copie incomplète, etc.).
        if schema_enrichi and str(erreur).lower().startswith((
            'no such collation sequence:', 'no such function:', 'unknown datatype for ',
        )):
            logger.warning('Migration des activités refusée : définition enrichie indisponible. '
                           'Migration sautée, table conservée après annulation.')
            return
        raise
    finally:
        conn.execute(f'PRAGMA foreign_keys={int(foreign_keys)}')
    if reparations:
        logger.warning('Migration des activités : %d lien(s) orphelin(s) remis à NULL.', reparations)
