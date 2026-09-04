"""
THÉRÈSE v2 - Database Connection

SQLite database setup with SQLModel.
"""

import logging
import sqlite3
from pathlib import Path
from typing import Any, AsyncGenerator

from app.config import settings
from sqlalchemy import event
from sqlalchemy import text as sqlalchemy_text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel, create_engine

logger = logging.getLogger(__name__)

# Sync engine for SQLModel compatibility
sync_engine = None

# Async engine for FastAPI
async_engine = None

# Session factory
AsyncSessionLocal = None


INVOICE_LEGACY_COLUMN_DEFINITIONS: dict[str, str] = {
    "currency": "TEXT DEFAULT 'EUR'",
    "payment_terms": "TEXT",
    "payment_method": "TEXT",
    "late_penalty_rate": "REAL",
    "legal_mentions": "TEXT",
    "converted_from_id": "TEXT",
    "validite_jours": "INTEGER",
    "payment_date": "TIMESTAMP",
}

BOARD_HISTORY_COLUMN_DEFINITIONS: dict[str, str] = {
    "web_sources": "TEXT NOT NULL DEFAULT '[]'",
    "synthesis_usage": "TEXT NOT NULL DEFAULT '{}'",
}

ATELIER_HISTORY_COLUMN_DEFINITIONS: dict[str, str] = {
    "run_phase": "TEXT",
    "plan": "TEXT",
    "test_results": "TEXT",
    "explanation": "TEXT",
    "events": "TEXT",
    "agent_outputs": "TEXT",
    "base_branch": "TEXT",
    "commit_hash": "TEXT",
}


def ensure_invoice_currency_column(db_path: Path | None) -> bool:
    """Ajoute la colonne invoices.currency si elle manque sur une DB legacy."""
    return "currency" in ensure_invoice_legacy_columns(db_path, columns=("currency",))


def ensure_invoice_legacy_columns(
    db_path: Path | None,
    columns: tuple[str, ...] | None = None,
) -> list[str]:
    """Ajoute les colonnes invoices manquantes sur une DB legacy."""
    if db_path is None or not db_path.exists():
        return []

    target_columns = columns or tuple(INVOICE_LEGACY_COLUMN_DEFINITIONS.keys())
    added_columns: list[str] = []

    # US-014 : db_connect pose la clé SQLCipher si la base est chiffrée
    with db_connect(db_path) as conn:
        cursor = conn.execute("PRAGMA table_info(invoices)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        if not existing_columns:
            return []

        for column_name in target_columns:
            if column_name in existing_columns:
                continue

            column_definition = INVOICE_LEGACY_COLUMN_DEFINITIONS[column_name]
            conn.execute(f"ALTER TABLE invoices ADD COLUMN {column_name} {column_definition}")
            added_columns.append(column_name)

        if added_columns:
            conn.commit()
            logger.info(
                "Migration auto : colonnes invoices ajoutées (%s)",
                ", ".join(added_columns),
            )

    return added_columns


def _ensure_invoice_client_snapshot(conn: sqlite3.Connection) -> list[str]:
    """Ajoute et remplit le destinataire figé des pièces existantes.

    Une facture orpheline ne permet plus de reconstruire une identité fiable.
    B-154 refusait alors GLOBALEMENT : une seule pièce arrêtait le démarrage de
    toute l'application, sans aucun geste de réparation, là où le commentaire du
    remplissage annonçait déjà un traitement PAR LIGNE.

    B-266 garde la promesse qui compte - aucun destinataire n'est inventé - et
    abandonne celle qui coûtait trop cher : les pièces réparables sont migrées,
    l'orpheline reste sans destinataire figé, et elle est NOMMÉE dans les
    journaux avec le geste qui la répare. Elle n'est pas pour autant utilisable
    en silence : `_snapshot_de_la_piece` (routers/invoices.py) refuse déjà de
    produire un document dont le destinataire n'est pas figé.
    """
    invoice_columns = {
        row[1] for row in conn.execute("PRAGMA table_info(invoices)").fetchall()
    }
    if not invoice_columns:
        return []

    invoice_count = conn.execute("SELECT COUNT(*) FROM invoices").fetchone()[0]
    contact_table = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='contacts'"
    ).fetchone()
    if invoice_count and contact_table is None:
        raise RuntimeError(
            "Migration des factures impossible : la table contacts est absente"
        )
    definitions = {
        "client_name": "TEXT",
        "client_company": "TEXT",
        "client_email": "TEXT",
        "client_phone": "TEXT",
        "client_address": "TEXT",
    }
    missing_columns = set(definitions) - invoice_columns
    # Une pièce déjà migrée peut légitimement avoir perdu sa fiche CRM : son
    # snapshot est justement là pour cela. L'absence du contact ne bloque que
    # les lignes qu'il reste réellement à reconstruire.
    needs_backfill = bool(missing_columns)
    if not needs_backfill and invoice_count:
        needs_backfill = conn.execute(
            "SELECT 1 FROM invoices WHERE client_name IS NULL "
            "OR TRIM(client_name) = '' LIMIT 1"
        ).fetchone() is not None

    added: list[str] = []
    for column_name, definition in definitions.items():
        if column_name not in invoice_columns:
            conn.execute(
                f"ALTER TABLE invoices ADD COLUMN {column_name} {definition}"
            )
            added.append(column_name)

    if invoice_count and needs_backfill:
        where_clause = "1 = 1" if missing_columns else (
            "client_name IS NULL OR TRIM(client_name) = ''"
        )
        conn.execute(
            f"""
            UPDATE invoices
            SET client_name = (
                    SELECT CASE
                        WHEN TRIM(COALESCE(c.first_name, '') || ' ' || COALESCE(c.last_name, '')) != ''
                        THEN TRIM(COALESCE(c.first_name, '') || ' ' || COALESCE(c.last_name, ''))
                        WHEN COALESCE(c.company, '') != '' THEN c.company
                        ELSE NULL
                    END
                    FROM contacts c WHERE c.id = invoices.contact_id
                ),
                client_company = (SELECT c.company FROM contacts c WHERE c.id = invoices.contact_id),
                client_email = (SELECT c.email FROM contacts c WHERE c.id = invoices.contact_id),
                client_phone = (SELECT c.phone FROM contacts c WHERE c.id = invoices.contact_id),
                client_address = (SELECT c.address FROM contacts c WHERE c.id = invoices.contact_id)
            WHERE {where_clause}
            """
        )
        # B-266 : par ligne. Les pièces restées sans destinataire figé sont
        # celles dont la fiche CRM a disparu (ou n'a jamais porté de nom) ;
        # elles sont nommées, avec le geste qui les répare, et n'empêchent pas
        # les autres d'être migrées ni l'application de démarrer.
        colonne_numero = (
            "invoice_number" if "invoice_number" in invoice_columns else "id"
        )
        sans_destinataire = conn.execute(
            f"SELECT {colonne_numero} FROM invoices "
            "WHERE client_name IS NULL OR TRIM(client_name) = ''"
        ).fetchall()
        if sans_destinataire:
            pieces = ", ".join(str(ligne[0]) for ligne in sans_destinataire)
            logger.warning(
                "Destinataire historique introuvable pour %d pièce(s) : %s. "
                "Leur fiche client a disparu de la base. Rattache un client à "
                "chacune depuis Facturation, ou supprime-la : tant qu'elle n'a "
                "pas de destinataire figé, sa génération de document est "
                "refusée (aucun destinataire n'est inventé à sa place).",
                len(sans_destinataire),
                pieces,
            )
    conn.commit()
    return added


def apply_adhoc_migrations(db_path) -> None:
    """Migrations ad-hoc idempotentes (desktop : pas d'alembic auto historique).

    Factorisées depuis main.py (revue adversariale US-015) : elles DOIVENT
    tourner avant ensure_alembic_stamp, sinon une DB legacy serait estampillée
    head sans avoir le schéma de head. Appelées par init_db, le lifespan
    (filet) et le pré-vol alembic/env.py.
    """
    from contextlib import closing
    from pathlib import Path as _Path

    if not db_path or not _Path(str(db_path)).exists():
        return
    with closing(db_connect(db_path)) as conn:
        cursor = conn.execute("PRAGMA table_info(invoices)")
        columns = [row[1] for row in cursor.fetchall()]
        if columns and "currency" not in columns:
            conn.execute("ALTER TABLE invoices ADD COLUMN currency TEXT DEFAULT 'EUR'")
            conn.commit()
            logger.info("Migration auto : colonne 'currency' ajoutée à la table invoices")
        snapshot_columns = _ensure_invoice_client_snapshot(conn)
        if snapshot_columns:
            logger.info(
                "Migration auto : snapshot destinataire ajouté aux factures (%s)",
                ", ".join(snapshot_columns),
            )
        # 0.56 : cloison de l'agenda par dossier. NULLABLE et SANS backfill -
        # les evenements d'avant la 0.56 n'appartiennent a aucun dossier et
        # restent visibles partout. Les coller au premier dossier venu ferait
        # disparaitre l'agenda de tout le monde.
        cursor = conn.execute("PRAGMA table_info(calendar_events)")
        cal_columns = [row[1] for row in cursor.fetchall()]
        if cal_columns and "project_id" not in cal_columns:
            conn.execute("ALTER TABLE calendar_events ADD COLUMN project_id TEXT")
            conn.commit()
            logger.info(
                "Migration auto : colonne 'project_id' ajoutee a calendar_events"
            )
        # B-026 : rappels de l'evenement (JSON array de minutes). NULLABLE et
        # SANS backfill - un evenement d'avant cette colonne n'a jamais porte
        # de rappel, lui en inventer un ferait sonner tout l'agenda.
        if cal_columns and "reminders" not in cal_columns:
            conn.execute("ALTER TABLE calendar_events ADD COLUMN reminders TEXT")
            conn.commit()
            logger.info(
                "Migration auto : colonne 'reminders' ajoutee a calendar_events"
            )

        # P0-IA-3 : provider LLM par message (badge local/cloud)
        cursor = conn.execute("PRAGMA table_info(messages)")
        msg_columns = [row[1] for row in cursor.fetchall()]
        if msg_columns and "provider" not in msg_columns:
            conn.execute("ALTER TABLE messages ADD COLUMN provider TEXT")
            conn.commit()
            logger.info("Migration auto : colonne 'provider' ajoutée à la table messages")
        # BUG-130 : extra_data JSON par message (fichier de skill généré, à restaurer)
        if msg_columns and "extra_data" not in msg_columns:
            conn.execute("ALTER TABLE messages ADD COLUMN extra_data TEXT")
            conn.commit()
            logger.info("Migration auto : colonne 'extra_data' ajoutée à la table messages")
        # 0.43 : rattachement d'une conversation à un projet, qui commande le
        # cloisonnement du contexte documentaire. Les testeurs ont déjà une base
        # 0.42 : `create_all()` crée les tables manquantes mais n'ajoute AUCUNE
        # colonne, et aucun `alembic upgrade head` ne tourne au démarrage
        # packagé. Sans cette migration, toute lecture de conversation
        # échouerait après mise à jour.
        # Plan du 29/08 : la prochaine relance est une DATE DÉCIDÉE. Sans cette
        # colonne, l'accueil continuerait de déduire un devoir d'une absence
        # d'interaction, et de l'affirmer.
        # Tranche C du 29/08 : la prestation. `create_all` ne cree la table
        # que sur une base neuve ; une installation existante ne l'aurait pas.
        conn.execute(
            "CREATE TABLE IF NOT EXISTS prestations ("
            "id TEXT PRIMARY KEY, contact_id TEXT NOT NULL, intitule TEXT NOT NULL, "
            "montant_ht REAL, phase TEXT NOT NULL DEFAULT 'piste', "
            "created_at TIMESTAMP NOT NULL, updated_at TIMESTAMP NOT NULL, "
            "FOREIGN KEY(contact_id) REFERENCES contacts(id))"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_prestations_contact_id ON prestations(contact_id)"
        )
        conn.execute("CREATE INDEX IF NOT EXISTS ix_prestations_phase ON prestations(phase)")
        # Tranche E1 : le dossier de financement est un ETAT de la prestation,
        # pas une entite. Un dossier sans prestation ne veut rien dire.
        colonnes_prestations = {
            row[1] for row in conn.execute("PRAGMA table_info(prestations)").fetchall()
        }
        if colonnes_prestations and "suivi_apres_jours" not in colonnes_prestations:
            conn.execute(
                "ALTER TABLE prestations ADD COLUMN suivi_apres_jours INTEGER NOT NULL DEFAULT 90"
            )
            conn.commit()
        if colonnes_prestations and "fin_le" not in colonnes_prestations:
            conn.execute("ALTER TABLE prestations ADD COLUMN fin_le DATE")
            conn.commit()
        # E2 : un evenement peut etre bloque sans etre annule.
        colonnes_events = {
            row[1] for row in conn.execute("PRAGMA table_info(calendar_events)").fetchall()
        }
        if colonnes_events and "blocage" not in colonnes_events:
            conn.execute("ALTER TABLE calendar_events ADD COLUMN blocage TEXT")
            conn.commit()
        if colonnes_prestations and "financeur" not in colonnes_prestations:
            conn.execute("ALTER TABLE prestations ADD COLUMN financeur TEXT")
            conn.execute("ALTER TABLE prestations ADD COLUMN statut_financement TEXT")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS ix_prestations_statut_financement "
                "ON prestations(statut_financement)"
            )
        conn.commit()

        # Tranche B du 29/08 : une trace peut en annuler une autre.
        colonnes_activites = {
            row[1] for row in conn.execute("PRAGMA table_info(activities)").fetchall()
        }
        if colonnes_activites and "statut" not in colonnes_activites:
            conn.execute(
                "ALTER TABLE activities ADD COLUMN statut TEXT NOT NULL DEFAULT 'en_vigueur'"
            )
            conn.execute("ALTER TABLE activities ADD COLUMN remplace_id TEXT")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS ix_activities_statut ON activities(statut)"
            )
            conn.commit()
            logger.info("Migration auto : 'statut' et 'remplace_id' ajoutés à activities")

        # Lot 3 du 29/08 : une tache doit pouvoir nommer la personne qu'elle
        # concerne, sinon « Relancer Dupont » n'est qu'une chaine de caracteres.
        colonnes_taches = {
            row[1] for row in conn.execute("PRAGMA table_info(tasks)").fetchall()
        }
        if colonnes_taches and "contact_id" not in colonnes_taches:
            conn.execute("ALTER TABLE tasks ADD COLUMN contact_id TEXT")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS ix_tasks_contact_id ON tasks(contact_id)"
            )
            conn.commit()
            logger.info("Migration auto : colonne 'contact_id' ajoutée à la table tasks")

        colonnes_contacts = {
            row[1] for row in conn.execute("PRAGMA table_info(contacts)").fetchall()
        }
        if colonnes_contacts and "next_follow_up" not in colonnes_contacts:
            conn.execute("ALTER TABLE contacts ADD COLUMN next_follow_up TIMESTAMP")
            # `Field(index=True)` ne vaut que pour une base neuve (`create_all`).
            # Sur une base packagée déjà installée, la colonne arriverait nue et
            # le balayage se ferait par rowid.
            conn.execute(
                "CREATE INDEX IF NOT EXISTS ix_contacts_next_follow_up "
                "ON contacts(next_follow_up)"
            )
            conn.commit()
            logger.info(
                "Migration auto : colonne 'next_follow_up' ajoutée à la table contacts"
            )

        cursor = conn.execute("PRAGMA table_info(conversations)")
        conv_columns = {row[1] for row in cursor.fetchall()}
        if conv_columns and "project_id" not in conv_columns:
            conn.execute("ALTER TABLE conversations ADD COLUMN project_id TEXT")
            conn.commit()
            logger.info(
                "Migration auto : colonne 'project_id' ajoutée à la table conversations"
            )
        if conv_columns and "memory_scope" not in conv_columns:
            # Politique documentaire (0.43). Les conversations EXISTANTES
            # basculent au moindre privilège : c'est un changement de
            # comportement assumé, annoncé dans les notes de version.
            conn.execute(
                "ALTER TABLE conversations ADD COLUMN memory_scope TEXT "
                "NOT NULL DEFAULT 'global'"
            )
            conn.commit()
            logger.info(
                "Migration auto : colonne 'memory_scope' ajoutée à conversations"
            )
        if conv_columns:
            # `Field(index=True)` ne pose l'index que via `create_all()`, donc
            # jamais sur une base existante (relevé en revue : la colonne était
            # bien ajoutée, l'index non). Sans lui, le filtrage par projet fait
            # un balayage complet de la table.
            conn.execute(
                "CREATE INDEX IF NOT EXISTS ix_conversations_project_id "
                "ON conversations (project_id)"
            )
            conn.commit()
        # BUG-165 : provenance du périmètre d'un document. Les bases existantes
        # n'ont que des périmètres VOULUS (posés par l'explorateur ou par la
        # 0.43) : le défaut 0 est donc le bon, et aucun document déjà indexé ne
        # pourra être rectifié par un simple attachement.
        cursor = conn.execute("PRAGMA table_info(files)")
        file_columns = {row[1] for row in cursor.fetchall()}
        if file_columns and "scope_provisoire" not in file_columns:
            conn.execute(
                "ALTER TABLE files ADD COLUMN scope_provisoire BOOLEAN "
                "NOT NULL DEFAULT 0"
            )
            conn.commit()
            logger.info(
                "Migration auto : colonne 'scope_provisoire' ajoutée à la table files"
            )
        # 0.40 : historique Board reconstructible (sources + usage de synthèse)
        cursor = conn.execute("PRAGMA table_info(board_decisions)")
        board_columns = {row[1] for row in cursor.fetchall()}
        for column_name, definition in BOARD_HISTORY_COLUMN_DEFINITIONS.items():
            if board_columns and column_name not in board_columns:
                conn.execute(
                    f"ALTER TABLE board_decisions ADD COLUMN {column_name} {definition}"
                )
                conn.commit()
                logger.info(
                    "Migration auto : colonne '%s' ajoutée à board_decisions",
                    column_name,
                )
        # 0.40 : journal Atelier reconstructible après redémarrage.
        cursor = conn.execute("PRAGMA table_info(agent_tasks)")
        agent_task_columns = {row[1] for row in cursor.fetchall()}
        for column_name, definition in ATELIER_HISTORY_COLUMN_DEFINITIONS.items():
            if agent_task_columns and column_name not in agent_task_columns:
                conn.execute(
                    f"ALTER TABLE agent_tasks ADD COLUMN {column_name} {definition}"
                )
                conn.commit()
                logger.info(
                    "Migration auto : colonne '%s' ajoutée à agent_tasks",
                    column_name,
                )
        # US-017 : purge_excluded sur contacts
        cursor = conn.execute("PRAGMA table_info(contacts)")
        contact_columns = [row[1] for row in cursor.fetchall()]
        if contact_columns and "purge_excluded" not in contact_columns:
            conn.execute("ALTER TABLE contacts ADD COLUMN purge_excluded BOOLEAN DEFAULT 0")
            conn.commit()
            logger.info("Migration auto : colonne 'purge_excluded' ajoutée à la table contacts")
        # Email Backlog : signature_html sur email_accounts
        cursor = conn.execute("PRAGMA table_info(email_accounts)")
        ea_columns = [row[1] for row in cursor.fetchall()]
        if ea_columns and "signature_html" not in ea_columns:
            conn.execute("ALTER TABLE email_accounts ADD COLUMN signature_html TEXT")
            conn.commit()
            logger.info("Migration auto : colonne 'signature_html' ajoutée à email_accounts")
        # Email Backlog : contact_id sur email_messages
        cursor = conn.execute("PRAGMA table_info(email_messages)")
        em_columns = [row[1] for row in cursor.fetchall()]
        if em_columns and "contact_id" not in em_columns:
            conn.execute("ALTER TABLE email_messages ADD COLUMN contact_id TEXT REFERENCES contacts(id)")
            conn.execute("CREATE INDEX IF NOT EXISTS ix_email_messages_contact_id ON email_messages(contact_id)")
            conn.commit()
            logger.info("Migration auto : colonne 'contact_id' ajoutée à email_messages")
        # Email Backlog : table email_follow_ups
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='email_follow_ups'"
        )
        if not cursor.fetchone():
            conn.execute("""
                CREATE TABLE email_follow_ups (
                    id VARCHAR NOT NULL PRIMARY KEY,
                    email_message_id VARCHAR NOT NULL REFERENCES email_messages(id),
                    contact_id VARCHAR REFERENCES contacts(id),
                    due_date VARCHAR NOT NULL,
                    note VARCHAR,
                    status VARCHAR NOT NULL DEFAULT 'pending',
                    created_at VARCHAR NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS ix_email_follow_ups_email_message_id ON email_follow_ups(email_message_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS ix_email_follow_ups_contact_id ON email_follow_ups(contact_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS ix_email_follow_ups_status ON email_follow_ups(status)")
            conn.commit()
            logger.info("Migration auto : table 'email_follow_ups' créée")
        # Chantier 4 Variables V1 (design V4 11/07/2026) : table variables
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='variables'"
        )
        if not cursor.fetchone():
            conn.execute("""
                CREATE TABLE variables (
                    id VARCHAR NOT NULL PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    kind VARCHAR NOT NULL DEFAULT 'text',
                    value VARCHAR NOT NULL DEFAULT '""',
                    description VARCHAR,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
            """)
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_variables_name ON variables(name)"
            )
            conn.commit()
            logger.info("Migration auto : table 'variables' créée")
        # BUG-144 (0.41.1) : avant cette version, la fin « toute la journée »
        # des événements Google/CalDAV en cache était stockée EXCLUSIVE
        # (convention de ces protocoles) alors que l'app est INCLUSIVE.
        # Conversion -1 jour clampée, UNE seule fois (marqueur preferences) -
        # les calendriers locaux étaient déjà inclusifs et ne bougent pas.
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name IN"
                " ('calendars', 'calendar_events', 'preferences')"
            ).fetchall()
        }
        if {"calendars", "calendar_events", "preferences"} <= tables:
            marker = conn.execute(
                "SELECT value FROM preferences WHERE key = 'allday_end_semantics'"
            ).fetchone()
            if marker is None:
                from datetime import UTC as _UTC
                from datetime import date as _date
                from datetime import datetime as _datetime
                from datetime import timedelta as _timedelta
                from uuid import uuid4 as _uuid4

                rows = conn.execute(
                    "SELECT e.id, e.start_date, e.end_date FROM calendar_events e"
                    " JOIN calendars c ON c.id = e.calendar_id"
                    " WHERE c.provider IN ('google', 'caldav') AND e.all_day = 1"
                    " AND e.start_date IS NOT NULL AND e.end_date IS NOT NULL"
                    " AND e.end_date > e.start_date"
                ).fetchall()
                converted = 0
                for event_id, start_raw, end_raw in rows:
                    try:
                        new_end = max(
                            _date.fromisoformat(start_raw),
                            _date.fromisoformat(end_raw) - _timedelta(days=1),
                        ).isoformat()
                    except ValueError:
                        continue
                    conn.execute(
                        "UPDATE calendar_events SET end_date = ? WHERE id = ?",
                        (new_end, event_id),
                    )
                    converted += 1
                now_iso = _datetime.now(_UTC).isoformat()
                conn.execute(
                    "INSERT INTO preferences (id, key, value, category, created_at, updated_at)"
                    " VALUES (?, 'allday_end_semantics', '\"inclusive-0.41.1\"', 'general', ?, ?)",
                    (str(_uuid4()), now_iso, now_iso),
                )
                conn.commit()
                logger.info(
                    "Migration auto : %d fin(s) all-day Google/CalDAV converties en sémantique inclusive",
                    converted,
                )


# US-015 : tête Alembic épinglée. Une DB bootstrapée par create_all + les
# migrations ad-hoc d'init_db/main.py EST au schéma de cette révision : on
# l'estampille pour qu'Alembic devienne l'unique voie d'évolution du schéma.
# Le test tests/test_alembic_stamp.py vérifie que cette constante suit la
# vraie tête de src/backend/alembic/versions (épinglée en dur pour que
# l'app PACKAGÉE puisse estampiller sans embarquer le dossier alembic/).
ALEMBIC_HEAD_REVISION = "a7b8c9d0e1f2"


def ensure_alembic_stamp(db_path) -> None:
    """Estampille la DB à la tête Alembic si elle n'a pas d'alembic_version.

    Idempotent. Une DB déjà suivie reste à son ancienne révision tant que son
    schéma n'est pas réellement au niveau de la tête.
    Ne stamp JAMAIS une DB vide (sans tables métier) : elle doit être créée
    par les migrations ou par create_all d'abord.
    """
    from contextlib import closing
    from pathlib import Path as _Path

    if not db_path or not _Path(str(db_path)).exists():
        return
    try:
        # US-014 : db_connect pose la clé SQLCipher si la base est chiffrée
        with closing(db_connect(db_path)) as conn:
            has_tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='contacts'"
            ).fetchone()
            if not has_tables:
                return
            has_stamp = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'"
            ).fetchone()
            if has_stamp:
                # Revue adversariale US-015 : une DB trackée à une révision
                # ANCIENNE dont le schéma a déjà été patché par les migrations
                # ad-hoc (elles tournent à chaque boot) ferait planter
                # `upgrade head` en duplicate column. Preuve de schéma au
                # niveau de la tête épinglée : invoices.validite_jours (la
                # colonne ajoutée PAR cette révision). Si présente ->
                # ré-estampiller à la tête.
                current = conn.execute(
                    "SELECT version_num FROM alembic_version"
                ).fetchone()
                if current and current[0] != ALEMBIC_HEAD_REVISION:
                    # Incident du 31/08 : les anciens appelants directs du
                    # filet n'exécutaient pas tous apply_adhoc_migrations.
                    # Compléter ce snapshot ici empêche de laisser une base à
                    # l'ancienne tête ; une identité irrécupérable interrompt
                    # le ré-estampillage, conformément au contrat fail-closed.
                    _ensure_invoice_client_snapshot(conn)
                    inv_cols = {
                        row[1]
                        for row in conn.execute("PRAGMA table_info(invoices)")
                    }
                    # La preuve de schéma doit couvrir CHAQUE élément apporté
                    # depuis, sinon une base trackée serait ré-estampillée à la
                    # nouvelle tête et `upgrade head` sauterait les migrations.
                    # Toute future révision doit étendre cette preuve et les
                    # migrations ad-hoc ci-dessus.
                    has_variables = conn.execute(
                        "SELECT name FROM sqlite_master "
                        "WHERE type='table' AND name='variables'"
                    ).fetchone()
                    board_cols = {
                        row[1]
                        for row in conn.execute("PRAGMA table_info(board_decisions)")
                    }
                    atelier_cols = {
                        row[1]
                        for row in conn.execute("PRAGMA table_info(agent_tasks)")
                    }
                    has_board_history = (
                        BOARD_HISTORY_COLUMN_DEFINITIONS.keys() <= board_cols
                    )
                    has_atelier_history = (
                        ATELIER_HISTORY_COLUMN_DEFINITIONS.keys() <= atelier_cols
                    )
                    # 0.45 : la preuve couvre les tables project.sync - sans
                    # elles, ré-estampiller ferait sauter la migration
                    # e5f6a7b8c9d0 sur une vraie base 0.44 (revue jalon, B4).
                    # Passes 2-3 de revue : la preuve dérive du MODÈLE -
                    # toutes les colonnes, sans liste manuelle qui prend du
                    # retard. Une table au bon nom mais au schéma incomplet
                    # ne sera jamais estampillée head.
                    def _colonnes(table: str) -> set[str]:
                        return {
                            row[1]
                            for row in conn.execute(f"PRAGMA table_info({table})")
                        }

                    from app.models import entities_sync as _sync  # noqa: F401
                    from sqlmodel import SQLModel as _SQLModel

                    has_sync_tables = all(
                        set(_SQLModel.metadata.tables[table].columns.keys())
                        <= _colonnes(table)
                        for table in (
                            "project_sync_roots", "project_sync_entries",
                            "sync_plans", "sync_operations",
                        )
                    )
                    # P-039 : les cinq tables de planning sont créées par
                    # create_all au boot desktop avant cette preuve. Exiger
                    # toutes leurs colonnes empêche de sauter la migration sur
                    # une base Alembic ancienne partiellement patchée.
                    planning_tables = (
                        "task_schedules",
                        "task_dependencies",
                        "planning_resources",
                        "task_allocations",
                        "planning_snapshots",
                    )
                    has_planning_tables = all(
                        table in _SQLModel.metadata.tables
                        and set(_SQLModel.metadata.tables[table].columns.keys())
                        <= _colonnes(table)
                        for table in planning_tables
                    )
                    if (
                        "validite_jours" in inv_cols
                        and {
                            "client_name",
                            "client_company",
                            "client_email",
                            "client_phone",
                            "client_address",
                        } <= inv_cols
                        and has_variables
                        and has_board_history
                        and has_atelier_history
                        and has_sync_tables
                        and has_planning_tables
                    ):
                        conn.execute(
                            "UPDATE alembic_version SET version_num = ?",
                            (ALEMBIC_HEAD_REVISION,),
                        )
                        conn.commit()
                        logger.info(
                            f"US-015 : alembic_version réaligné {current[0]} -> "
                            f"{ALEMBIC_HEAD_REVISION} (schéma déjà patché par "
                            "les migrations ad-hoc)"
                        )
                return
            conn.execute(
                "CREATE TABLE alembic_version ("
                "version_num VARCHAR(32) NOT NULL, "
                "CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num))"
            )
            conn.execute(
                "INSERT INTO alembic_version (version_num) VALUES (?)",
                (ALEMBIC_HEAD_REVISION,),
            )
            conn.commit()
            logger.info(f"US-015 : DB estampillée Alembic {ALEMBIC_HEAD_REVISION}")
    except Exception as e:
        logger.warning(f"Estampillage Alembic échoué : {e}")


# ============================================================
# US-014 : chiffrement de la base au repos (SQLCipher)
# ============================================================
# therese.db est chiffrée avec SQLCipher (AES-256), clé dérivée de la clé
# maîtresse du trousseau (HKDF, cf. encryption.get_db_key_hex). Une DB claire
# existante est migrée au démarrage (sqlcipher_export + vérification).
# Échappatoire : THERESE_DB_PLAINTEXT=1 (debug / trousseau indisponible).

_db_cipher_active = False  # positionné par init_db, lu par les listeners


def db_encryption_enabled() -> bool:
    """Chiffrement au repos actif ? (US-014)"""
    import os

    return os.environ.get("THERESE_DB_PLAINTEXT") != "1"


def db_is_encrypted(db_path) -> bool:
    """Une DB SQLite claire commence par l'en-tête 'SQLite format 3'."""
    from pathlib import Path as _Path

    p = _Path(str(db_path))
    if not p.exists() or p.stat().st_size == 0:
        return False
    with open(p, "rb") as f:
        return f.read(16) != b"SQLite format 3\x00"


def _db_key_pragma() -> str:
    from app.services.encryption import get_db_key_hex

    return f"PRAGMA key = \"x'{get_db_key_hex()}'\""


def db_connect(db_path):
    """Connexion directe à therese.db (remplace les sqlite3.connect épars).

    Adaptatif : DB chiffrée -> sqlcipher3 + clé ; DB claire (échappatoire ou
    pré-migration) -> sqlite3 standard. Tous les accès hors engine DOIVENT
    passer par ici (data.py, agents.py, swarm.py, main.py, env.py).
    """

    if db_is_encrypted(db_path):
        import sqlcipher3

        conn = sqlcipher3.connect(str(db_path))
        conn.execute(_db_key_pragma())
        return conn
    return sqlite3.connect(str(db_path))


def ensure_db_encrypted(db_path) -> None:
    """Migre une DB claire existante vers SQLCipher (idempotent).

    Étapes : checkpoint WAL -> sqlcipher_export vers un fichier temporaire ->
    vérification (mêmes tables + integrity_check) -> remplacement atomique.
    La copie claire n'est PAS conservée (la garder annulerait le chiffrement
    au repos) : la vérification précède toujours le remplacement.
    """
    import os
    from contextlib import closing
    from pathlib import Path as _Path

    p = _Path(str(db_path))
    if not p.exists() or p.stat().st_size == 0 or db_is_encrypted(p):
        return

    import sqlcipher3
    from app.services.encryption import get_db_key_hex

    key_hex = get_db_key_hex()
    tmp = _Path(str(p) + ".encrypting")
    tmp.unlink(missing_ok=True)

    # Rapatrier le WAL avant export (sinon transactions récentes perdues)
    with closing(sqlite3.connect(str(p))) as conn:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        expected_tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }

    with closing(sqlcipher3.connect(str(p))) as conn:
        conn.execute(
            f"ATTACH DATABASE ? AS encrypted KEY \"x'{key_hex}'\"", (str(tmp),)
        )
        conn.execute("SELECT sqlcipher_export('encrypted')")
        conn.execute("DETACH DATABASE encrypted")

    # Vérifier le chiffré AVANT de remplacer la claire
    with closing(sqlcipher3.connect(str(tmp))) as conn:
        conn.execute(f"PRAGMA key = \"x'{key_hex}'\"")
        got_tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    if got_tables != expected_tables or integrity != "ok":
        tmp.unlink(missing_ok=True)
        raise RuntimeError(
            "Migration SQLCipher : vérification échouée "
            f"(tables {len(got_tables)}/{len(expected_tables)}, integrity={integrity}). "
            "La base claire est intacte."
        )

    os.replace(tmp, p)
    for suffix in ("-wal", "-shm"):
        _Path(str(p) + suffix).unlink(missing_ok=True)
    logger.info("US-014 : base migrée vers SQLCipher (chiffrement au repos actif)")


# Noms de la PEP 249. SQLAlchemy interroge ces attributs du pilote pour
# décider si une exception vient de la base, et de quelle famille elle est.
_EXCEPTIONS_DBAPI = (
    "Error",
    "Warning",
    "InterfaceError",
    "DatabaseError",
    "DataError",
    "OperationalError",
    "IntegrityError",
    "InternalError",
    "ProgrammingError",
    "NotSupportedError",
)


def _aligner_erreurs_du_pilote(engine: Any, module: Any) -> list[str]:
    """Fait pointer les classes d'exception du dialecte sur celles du pilote réel.

    Le dialecte aiosqlite annonce les exceptions de `sqlite3`. Quand la base
    est chiffrée, elles viennent en réalité de `sqlcipher3`, dont la hiérarchie
    est SÉPARÉE (`sqlcipher3.dbapi2.Error` n'hérite pas de `sqlite3.Error`).
    Sans cet alignement, `_handle_dbapi_exception` ne reconnaît pas l'erreur,
    ne la traduit pas en `sqlalchemy.exc.*`, et l'exception brute du pilote
    remonte jusqu'au gestionnaire d'erreurs générique.

    Retourne les noms effectivement alignés (pour les tests).
    """
    pilote = getattr(engine, "dialect", None)
    pilote = getattr(pilote, "loaded_dbapi", None)
    if pilote is None:
        return []
    alignes = []
    for nom in _EXCEPTIONS_DBAPI:
        remplacement = getattr(module, nom, None)
        if remplacement is None:
            continue
        setattr(pilote, nom, remplacement)
        alignes.append(nom)
    return alignes


def get_database_url(async_mode: bool = True) -> str:
    """Get database URL for SQLite."""
    db_path = settings.db_path
    if async_mode:
        return f"sqlite+aiosqlite:///{db_path}"
    return f"sqlite:///{db_path}"


async def init_db() -> None:
    """Initialize database connection and create tables."""
    global sync_engine, async_engine, AsyncSessionLocal

    logger.info(f"Initializing database at {settings.db_path}")

    # Ensure parent directory exists
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)

    # US-014 : chiffrement au repos. Migrer une DB claire existante, puis
    # brancher les deux engines sur sqlcipher3 (clé posée en PREMIER pragma
    # de chaque connexion). Échec de clé/migration = fatal et explicite
    # (démarrer en clair en silence trahirait la promesse de souveraineté ;
    # échappatoire documentée : THERESE_DB_PLAINTEXT=1).
    global _db_cipher_active
    _db_cipher_active = False
    engine_kwargs: dict = {}
    # Revue adversariale US-014 : si la base est DÉJÀ chiffrée, l'échappatoire
    # THERESE_DB_PLAINTEXT=1 est inopérante (les engines doivent poser la clé,
    # sinon « file is not a database »). Le flag n'empêche que la migration
    # initiale vers le chiffré.
    if not db_encryption_enabled() and db_is_encrypted(settings.db_path):
        logger.warning(
            "US-014 : THERESE_DB_PLAINTEXT=1 ignoré - la base est déjà chiffrée "
            "(le flag n'agit qu'avant la migration initiale)."
        )
    if db_encryption_enabled() or db_is_encrypted(settings.db_path):
        try:
            ensure_db_encrypted(settings.db_path)
            # Revue adversariale US-014 : sur une DB DÉJÀ chiffrée, une
            # mauvaise clé (Keychain réinitialisé, DB d'une autre machine)
            # explosait plus loin en « file is not a database » brut, hors de
            # ce try. Probe explicite ici -> diagnostic pédagogique ci-dessous.
            if db_is_encrypted(settings.db_path):
                from contextlib import closing as _closing

                with _closing(db_connect(settings.db_path)) as _probe:
                    _probe.execute("SELECT count(*) FROM sqlite_master").fetchone()
            import aiosqlite.core as _aiosqlite_core
            import sqlcipher3

            # aiosqlite importe sqlite3 en dur : on substitue le module DBAPI
            # SQLCipher (même API) pour le moteur async. Substitution
            # PROCESS-GLOBALE non restaurée par close_db : tout autre
            # consommateur d'aiosqlite de ce process passerait par sqlcipher3
            # (sans clé il lit les DB claires comme sqlite3 - inoffensif
            # aujourd'hui, à garder en tête si un second engine async apparaît).
            _aiosqlite_core.sqlite3 = sqlcipher3.dbapi2
            engine_kwargs["module"] = sqlcipher3.dbapi2
            _db_cipher_active = True
        except Exception:
            logger.error(
                "US-014 : clé de chiffrement indisponible ou différente de celle "
                "de la base (Keychain réinitialisé ? base d'une autre machine ?). "
                "La base est INTACTE mais verrouillée : restaure le fichier "
                "~/.therese/.encryption_key d'origine (présent dans tes backups). "
                "Démarrage refusé pour ne pas écrire en clair en silence. "
                "THERESE_DB_PLAINTEXT=1 n'agit que sur une base encore en clair."
            )
            raise

    # Create sync engine for table creation
    sync_engine = create_engine(
        get_database_url(async_mode=False),
        echo=settings.debug,
        connect_args={"check_same_thread": False},
        **engine_kwargs,
    )

    # PERF-005 + Phase 3: SQLite PRAGMAs optimises
    @event.listens_for(sync_engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        if _db_cipher_active:
            cursor.execute(_db_key_pragma())  # DOIT précéder tout autre accès
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-10000")  # 10 MB
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.execute("PRAGMA mmap_size=268435456")  # 256 MB
        cursor.close()

    # Create async engine for operations (Phase 3: pool configuration)
    async_engine = create_async_engine(
        get_database_url(async_mode=True),
        echo=settings.debug,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=1800,
    )

    # B-160/B-161 (02/09/2026) : les erreurs SQLCipher doivent être CLASSÉES.
    # Le moteur sync reçoit `module=sqlcipher3.dbapi2` (engine_kwargs), le
    # moteur async non : son dialecte est celui d'aiosqlite, dont les classes
    # d'exception sont celles de `sqlite3`. Or `sqlcipher3.dbapi2.Error`
    # n'hérite PAS de `sqlite3.Error` : SQLAlchemy ne reconnaissait donc aucune
    # erreur de la base, ne les traduisait pas, et l'exception BRUTE du pilote
    # traversait tout `except IntegrityError` de l'application pour finir en
    # 500 « erreur inattendue ». La garde d'idempotence de la mise en route en
    # était la première victime : elle était juste, elle n'attrapait rien.
    if _db_cipher_active:
        import sqlcipher3 as _sqlcipher3

        _aligner_erreurs_du_pilote(async_engine, _sqlcipher3.dbapi2)

    # Appliquer les memes PRAGMAs sur le moteur async
    @event.listens_for(async_engine.sync_engine, "connect")
    def _set_async_sqlite_pragmas(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        if _db_cipher_active:
            cursor.execute(_db_key_pragma())  # DOIT précéder tout autre accès
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-10000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.execute("PRAGMA mmap_size=268435456")
        cursor.close()

    # Create session factory
    AsyncSessionLocal = sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Create tables using sync engine
    # Import models to register them with SQLModel
    from app.models import (
        entities,  # noqa: F401
        entities_agents,  # noqa: F401 - Agent system tables
        entities_sync,  # noqa: F401 - project.sync (0.45)
        processing,  # noqa: F401 - Traitements longs (J1a)
    )
    from app.services import audit  # noqa: F401 - ActivityLog model

    SQLModel.metadata.create_all(sync_engine)

    # Auto-migration : ajouter les colonnes manquantes aux tables existantes
    ensure_invoice_legacy_columns(settings.db_path)

    # 0.45 (passe 3 de revue) : create_all n'ajoute pas d'index à une table
    # existante, et une base déjà estampillée ne rejouera jamais la révision.
    # L'invariant « une racine active = un projet » se pose donc ICI,
    # idempotent, à chaque démarrage.
    with sync_engine.connect() as conn:
        conn.exec_driver_sql(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_sync_root_racine_active "
            "ON project_sync_roots(racine) WHERE detachee = 0"
        )
        # 0.46 : le panneau trie et la retention filtre par created_at.
        conn.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_processing_tasks_created_at "
            "ON processing_tasks(created_at)"
        )
        conn.commit()

    with sync_engine.connect() as conn:
        alter_statements = [
            # BUG-068 : colonne mode ajoutée dans BoardDecisionDB mais absente des DB existantes
            "ALTER TABLE board_decisions ADD COLUMN mode VARCHAR DEFAULT 'cloud'",
        ]
        for stmt in alter_statements:
            try:
                conn.execute(sqlalchemy_text(stmt))
            except Exception as e:
                logger.debug("Migration colonne deja existante: %s", e)  # déjà existante
        conn.commit()

    # Phase 3 + PERF audit: Creer les index manquants pour les DB existantes
    with sync_engine.connect() as conn:
        index_statements = [
            "CREATE INDEX IF NOT EXISTS ix_contacts_email ON contacts (email)",
            "CREATE INDEX IF NOT EXISTS ix_contacts_last_interaction ON contacts (last_interaction)",
            "CREATE INDEX IF NOT EXISTS ix_conversations_created_at ON conversations (created_at)",
            "CREATE INDEX IF NOT EXISTS ix_board_decisions_created_at ON board_decisions (created_at)",
            # PERF audit - index sur les FK frequemment filtrees
            "CREATE INDEX IF NOT EXISTS ix_tasks_project_id ON tasks (project_id)",
            "CREATE INDEX IF NOT EXISTS ix_invoice_lines_invoice_id ON invoice_lines (invoice_id)",
            "CREATE INDEX IF NOT EXISTS ix_invoices_converted_from_id ON invoices (converted_from_id)",
            "CREATE INDEX IF NOT EXISTS ix_activities_contact_id ON activities (contact_id)",
            "CREATE INDEX IF NOT EXISTS ix_deliverables_project_id ON deliverables (project_id)",
            "CREATE INDEX IF NOT EXISTS ix_calendar_events_calendar_id ON calendar_events (calendar_id)",
        ]
        for stmt in index_statements:
            try:
                conn.execute(sqlalchemy_text(stmt))
            except Exception as e:
                logger.debug(f"Index creation skipped: {e}")
        conn.commit()

    # Revue adversariale US-015 : les migrations ad-hoc DOIVENT précéder
    # l'estampille, sinon la DB serait marquée head sans le schéma de head.
    apply_adhoc_migrations(settings.db_path)

    # US-015 : estampiller la DB à la tête Alembic. Le bootstrap ci-dessus
    # (create_all + colonnes/index ad-hoc) amène la DB AU schéma courant ;
    # l'estampille fait d'Alembic l'unique voie d'évolution future
    # (`make db-migrate` fonctionne désormais aussi sur une DB legacy).
    ensure_alembic_stamp(settings.db_path)

    logger.info("Database initialized successfully")


async def close_db() -> None:
    """Close database connections."""
    global async_engine, sync_engine

    if async_engine:
        await async_engine.dispose()
        async_engine = None

    if sync_engine:
        sync_engine.dispose()
        sync_engine = None

    logger.info("Database connections closed")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session for dependency injection."""
    if AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_sync_session() -> Session:
    """Get sync database session for migrations and setup."""
    if sync_engine is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    return Session(sync_engine)


def get_sync_connection():
    """Get a sync connection from the singleton engine (reuses WAL/cache PRAGMAs)."""
    if sync_engine is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return sync_engine.connect()


from contextlib import asynccontextmanager  # noqa: E402


@asynccontextmanager
async def get_session_context():
    """
    Get async database session as context manager.

    Use this for non-dependency injection scenarios (e.g., startup code).

    Usage:
        async with get_session_context() as session:
            # use session
    """
    if AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
