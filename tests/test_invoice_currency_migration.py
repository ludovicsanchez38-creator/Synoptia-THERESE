import sqlite3
from pathlib import Path

import pytest
from app.models.database import ensure_invoice_currency_column


@pytest.mark.parametrize("with_invoices_table", [True, False])
def test_ensure_invoice_currency_column_handles_legacy_sqlite_db(tmp_path: Path, with_invoices_table: bool):
    db_path = tmp_path / "legacy-therese.db"

    with sqlite3.connect(db_path) as conn:
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

    with sqlite3.connect(db_path) as conn:
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

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "CREATE TABLE invoices (id TEXT PRIMARY KEY, currency TEXT NOT NULL DEFAULT 'EUR')"
        )
        conn.commit()

    first = ensure_invoice_currency_column(db_path)
    second = ensure_invoice_currency_column(db_path)

    assert first is False
    assert second is False
