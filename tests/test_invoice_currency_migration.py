import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
from app.models.database import ensure_invoice_currency_column, ensure_invoice_legacy_columns


@pytest.mark.parametrize("with_invoices_table", [True, False])
def test_ensure_invoice_currency_column_handles_legacy_sqlite_db(tmp_path: Path, with_invoices_table: bool):
    db_path = tmp_path / "legacy-therese.db"

    with closing(sqlite3.connect(db_path)) as conn:
        if with_invoices_table:
            conn.execute(
                """
                CREATE TABLE invoices (
                    id TEXT PRIMARY KEY,
                    invoice_number TEXT NOT NULL,
                    contact_id TEXT NOT NULL,
                    issue_date TEXT NOT NULL,
                    due_date TEXT NOT NULL,
                    status TEXT NOT NULL,
                    subtotal_ht REAL NOT NULL DEFAULT 0,
                    total_tax REAL NOT NULL DEFAULT 0,
                    total_ttc REAL NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "INSERT INTO invoices VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    "inv-1",
                    "FACT-2026-001",
                    "contact-1",
                    "2026-03-14T00:00:00",
                    "2026-03-30T00:00:00",
                    "draft",
                    100.0,
                    20.0,
                    120.0,
                    "2026-03-14T00:00:00",
                    "2026-03-14T00:00:00",
                ),
            )
        conn.commit()

    changed = ensure_invoice_currency_column(db_path)

    with closing(sqlite3.connect(db_path)) as conn:
        columns = [row[1] for row in conn.execute("PRAGMA table_info(invoices)").fetchall()]
        if with_invoices_table:
            assert changed is True
            assert "currency" in columns
            row = conn.execute("SELECT currency FROM invoices WHERE id = 'inv-1'").fetchone()
            assert row is not None
            assert row[0] == "EUR"
        else:
            assert changed is False
            assert columns == []


def test_ensure_invoice_currency_column_is_idempotent(tmp_path: Path):
    db_path = tmp_path / "legacy-therese.db"

    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute(
            "CREATE TABLE invoices (id TEXT PRIMARY KEY, currency TEXT NOT NULL DEFAULT 'EUR')"
        )
        conn.commit()

    first = ensure_invoice_currency_column(db_path)
    second = ensure_invoice_currency_column(db_path)

    assert first is False
    assert second is False


def test_ensure_invoice_legacy_columns_adds_missing_invoice_fields(tmp_path: Path):
    db_path = tmp_path / "legacy-therese.db"

    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute(
            """
            CREATE TABLE invoices (
                id TEXT PRIMARY KEY,
                invoice_number TEXT NOT NULL,
                contact_id TEXT NOT NULL,
                issue_date TEXT NOT NULL,
                due_date TEXT NOT NULL,
                status TEXT NOT NULL,
                subtotal_ht REAL NOT NULL DEFAULT 0,
                total_tax REAL NOT NULL DEFAULT 0,
                total_ttc REAL NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                currency TEXT DEFAULT 'EUR'
            )
            """
        )
        conn.execute(
            "INSERT INTO invoices VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "inv-1",
                "FACT-2026-001",
                "contact-1",
                "2026-03-14T00:00:00",
                "2026-03-30T00:00:00",
                "draft",
                100.0,
                20.0,
                120.0,
                "2026-03-14T00:00:00",
                "2026-03-14T00:00:00",
                "EUR",
            ),
        )
        conn.commit()

    added_columns = ensure_invoice_legacy_columns(db_path)

    with closing(sqlite3.connect(db_path)) as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(invoices)").fetchall()}
        for expected in {
            "payment_terms",
            "payment_method",
            "late_penalty_rate",
            "legal_mentions",
            "converted_from_id",
            "validite_jours",
            "payment_date",
        }:
            assert expected in columns

        row = conn.execute(
            "SELECT payment_terms, payment_method, late_penalty_rate, validite_jours FROM invoices WHERE id = 'inv-1'"
        ).fetchone()
        assert row == (None, None, None, None)

    assert set(added_columns) >= {
        "payment_terms",
        "payment_method",
        "late_penalty_rate",
        "legal_mentions",
        "converted_from_id",
        "validite_jours",
        "payment_date",
    }


def test_ensure_invoice_legacy_columns_is_idempotent(tmp_path: Path):
    db_path = tmp_path / "legacy-therese.db"

    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute(
            """
            CREATE TABLE invoices (
                id TEXT PRIMARY KEY,
                currency TEXT DEFAULT 'EUR',
                payment_terms TEXT,
                payment_method TEXT,
                late_penalty_rate REAL,
                legal_mentions TEXT,
                converted_from_id TEXT,
                validite_jours INTEGER,
                payment_date TIMESTAMP
            )
            """
        )
        conn.commit()

    first = ensure_invoice_legacy_columns(db_path)
    second = ensure_invoice_legacy_columns(db_path)

    assert first == []
    assert second == []


def test_apply_adhoc_migrations_backfill_le_snapshot_des_factures(tmp_path: Path):
    """Une mise à jour reprend le contact actuel au lieu de poser du vide."""
    from app.models.database import apply_adhoc_migrations

    db_path = tmp_path / "legacy-snapshot.db"
    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute(
            """
            CREATE TABLE contacts (
                id TEXT PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                company TEXT,
                email TEXT,
                phone TEXT,
                address TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE invoices (
                id TEXT PRIMARY KEY,
                contact_id TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "INSERT INTO contacts VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                "contact-1",
                "Aline",
                "Avant",
                "Société Ancienne",
                "aline@example.test",
                "+33492000000",
                "1 rue de la Mémoire",
            ),
        )
        conn.execute("INSERT INTO invoices VALUES (?, ?)", ("invoice-1", "contact-1"))
        conn.commit()

    apply_adhoc_migrations(db_path)

    with closing(sqlite3.connect(db_path)) as conn:
        snapshot = conn.execute(
            "SELECT client_name, client_company, client_email, client_phone, "
            "client_address FROM invoices WHERE id = 'invoice-1'"
        ).fetchone()
    assert snapshot == (
        "Aline Avant",
        "Société Ancienne",
        "aline@example.test",
        "+33492000000",
        "1 rue de la Mémoire",
    )


def test_snapshot_facture_refuse_d_inventer_un_destinataire(tmp_path: Path, caplog):
    """Une pièce dont le contact n'a ni nom ni société ne doit pas mentir.

    B-266 : la promesse nommée par ce test - ne pas inventer un destinataire -
    est intacte. Ce qui change, c'est le prix qu'on y met : la migration va au
    bout et l'application démarre, la pièce reste sans destinataire figé (et
    donc refusée à la génération de document), et elle est nommée dans les
    journaux. Le contact existe ici mais n'apprend rien sur le client : le
    résultat est le même que pour une fiche disparue.
    """
    from app.models.database import apply_adhoc_migrations

    db_path = tmp_path / "legacy-snapshot-sans-identite.db"
    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute(
            "CREATE TABLE contacts (id TEXT PRIMARY KEY, first_name TEXT, "
            "last_name TEXT, company TEXT, email TEXT, phone TEXT, address TEXT)"
        )
        conn.execute(
            "CREATE TABLE invoices (id TEXT PRIMARY KEY, contact_id TEXT NOT NULL)"
        )
        conn.execute(
            "INSERT INTO contacts VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("contact-vide", "", "", "", None, None, None),
        )
        conn.execute(
            "INSERT INTO invoices VALUES (?, ?)",
            ("invoice-sans-destinataire", "contact-vide"),
        )
        conn.commit()

    with caplog.at_level("WARNING", logger="app.models.database"):
        apply_adhoc_migrations(db_path)

    with closing(sqlite3.connect(db_path)) as conn:
        nom = conn.execute(
            "SELECT client_name FROM invoices WHERE id = ?",
            ("invoice-sans-destinataire",),
        ).fetchone()[0]

    assert not nom, f"un destinataire a été inventé : {nom!r}"
    assert "invoice-sans-destinataire" in caplog.text, caplog.text[-500:]


def test_base_legacy_facture_orpheline_ne_bloque_plus_le_demarrage(
    tmp_path: Path, caplog
):
    """B-266 (suite de B-154) : une seule pièce orpheline arrêtait TOUT.

    Le refus global était voulu par le docstring - mieux vaut échouer que
    consacrer un destinataire vide sur une pièce comptable - mais il rendait
    l'application entière indémarrable, sans aucun geste de réparation, alors
    que le commentaire de la fonction annonçait un traitement PAR LIGNE.

    Le nouveau contrat garde la promesse qui compte (aucun destinataire
    inventé) et abandonne celle qui coûtait trop cher (l'arrêt) : la migration
    va au bout, les pièces réparables sont migrées, l'orpheline reste sans
    destinataire figé et est NOMMÉE dans les journaux. Sa pièce reste refusée à
    la génération par `_snapshot_de_la_piece` (409), qui n'a pas bougé.
    """
    from app.models.database import apply_adhoc_migrations

    db_path = tmp_path / "legacy-facture-orpheline.db"
    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute(
            "CREATE TABLE contacts (id TEXT PRIMARY KEY, first_name TEXT, "
            "last_name TEXT, company TEXT, email TEXT, phone TEXT, address TEXT)"
        )
        conn.execute(
            "INSERT INTO contacts VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("contact-vivant", "Marc", "Durand", "ACME", "marc@acme.test", "", ""),
        )
        conn.execute(
            "CREATE TABLE invoices (id TEXT PRIMARY KEY, invoice_number TEXT, "
            "contact_id TEXT NOT NULL)"
        )
        conn.execute(
            "INSERT INTO invoices VALUES (?, ?, ?)",
            ("piece-saine", "FACT-2026-001", "contact-vivant"),
        )
        conn.execute(
            "INSERT INTO invoices VALUES (?, ?, ?)",
            ("facture-orpheline", "FACT-2026-002", "contact-efface"),
        )
        conn.commit()

    with caplog.at_level("WARNING", logger="app.models.database"):
        apply_adhoc_migrations(db_path)

    with closing(sqlite3.connect(db_path)) as conn:
        colonnes = {
            row[1] for row in conn.execute("PRAGMA table_info(invoices)").fetchall()
        }
        lignes = dict(
            conn.execute("SELECT id, client_name FROM invoices").fetchall()
        )

    assert {
        "client_name",
        "client_company",
        "client_email",
        "client_phone",
        "client_address",
    } <= colonnes, f"la migration ne s'est pas faite : {sorted(colonnes)}"

    assert lignes["piece-saine"] == "Marc Durand", (
        "la pièce réparable n'a pas été migrée : une seule orpheline emportait "
        f"toutes les autres ({lignes})"
    )
    assert not lignes["facture-orpheline"], (
        "un destinataire a été inventé pour la pièce orpheline : "
        f"{lignes['facture-orpheline']!r}"
    )

    # La pièce doit être NOMMÉE : c'est la seule prise de l'utilisateur pour
    # réparer sa base, maintenant que le démarrage ne s'arrête plus.
    assert "FACT-2026-002" in caplog.text, caplog.text[-500:]
    assert "FACT-2026-001" not in caplog.text, (
        "une pièce saine est signalée comme à réparer : " + caplog.text[-500:]
    )


def test_migration_orpheline_relancee_ne_reclame_rien_de_plus(tmp_path: Path):
    """Le second démarrage doit être aussi calme que le premier.

    Idempotence : les colonnes existent déjà, l'orpheline est toujours là, et
    rien ne doit lever pour autant.
    """
    from app.models.database import apply_adhoc_migrations

    db_path = tmp_path / "legacy-orpheline-deux-fois.db"
    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute(
            "CREATE TABLE contacts (id TEXT PRIMARY KEY, first_name TEXT, "
            "last_name TEXT, company TEXT, email TEXT, phone TEXT, address TEXT)"
        )
        conn.execute(
            "CREATE TABLE invoices (id TEXT PRIMARY KEY, invoice_number TEXT, "
            "contact_id TEXT NOT NULL)"
        )
        conn.execute(
            "INSERT INTO invoices VALUES (?, ?, ?)",
            ("facture-orpheline", "FACT-2026-002", "contact-efface"),
        )
        conn.commit()

    apply_adhoc_migrations(db_path)
    apply_adhoc_migrations(db_path)


def test_base_legacy_sans_table_contacts_bloque_le_demarrage(tmp_path: Path):
    """Jumeau du précédent : des factures sans la table contacts du tout.

    Même famille (impossible de reconstruire un destinataire), autre branche,
    autre message - et elle non plus n'avait aucun test.
    """
    from app.models.database import apply_adhoc_migrations

    db_path = tmp_path / "legacy-sans-contacts.db"
    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute(
            "CREATE TABLE invoices (id TEXT PRIMARY KEY, contact_id TEXT NOT NULL)"
        )
        conn.execute(
            "INSERT INTO invoices VALUES (?, ?)", ("facture-sans-crm", "contact-1")
        )
        conn.commit()

    with pytest.raises(RuntimeError, match="table contacts est absente"):
        apply_adhoc_migrations(db_path)
