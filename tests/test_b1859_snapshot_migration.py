"""Les destinataires déjà figés ne changent pas pendant une migration partielle."""

import sqlite3
from contextlib import closing

from app.models.database import _ensure_invoice_client_snapshot


def test_migration_partielle_preserve_les_snapshots_existants(tmp_path):
    chemin = tmp_path / "historique.db"
    with closing(sqlite3.connect(chemin)) as connexion:
        connexion.executescript("""
            CREATE TABLE contacts (
                id TEXT PRIMARY KEY, first_name TEXT, last_name TEXT,
                company TEXT, email TEXT, phone TEXT, address TEXT
            );
            CREATE TABLE invoices (
                id TEXT PRIMARY KEY, contact_id TEXT, client_name TEXT,
                client_company TEXT, client_email TEXT, client_address TEXT
            );
            INSERT INTO contacts VALUES
                ('contact-actuel', 'Nouveau', 'Nom', 'Nouvelle société',
                 'nouveau@example.test', '0102030405', 'Nouvelle adresse');
            INSERT INTO invoices VALUES
                ('existante', 'contact-actuel', 'Ancien Nom', 'Ancienne société',
                 NULL, 'Ancienne adresse'),
                ('orpheline', 'contact-supprime', 'Nom conservé', 'Société conservée',
                 'ancien@example.test', 'Adresse conservée');
        """)

        assert _ensure_invoice_client_snapshot(connexion) == ["client_phone"]
        lignes = dict(
            (ligne[0], ligne[1:])
            for ligne in connexion.execute(
                "SELECT id, client_name, client_company, client_email, client_address "
                "FROM invoices"
            )
        )

    assert lignes["existante"] == (
        "Ancien Nom", "Ancienne société", None, "Ancienne adresse"
    )
    assert lignes["orpheline"] == (
        "Nom conservé", "Société conservée", "ancien@example.test", "Adresse conservée"
    )
