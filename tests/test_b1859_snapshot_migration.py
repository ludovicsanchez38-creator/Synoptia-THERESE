"""Les destinataires déjà figés ne changent pas pendant une migration partielle."""

import sqlite3
from contextlib import closing

import pytest
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


@pytest.mark.parametrize("absente", [
    "client_name", "client_company", "client_email", "client_phone", "client_address",
])
def test_chaque_colonne_absente_preserve_toutes_les_valeurs_existantes(tmp_path, absente):
    colonnes = ("client_name", "client_company", "client_email", "client_phone", "client_address")
    existantes = [colonne for colonne in colonnes if colonne != absente]
    anciennes = {
        "client_name": None, "client_company": None, "client_email": None,
        "client_phone": "", "client_address": "Adresse historique",
    }
    nouvelles = {
        "client_name": "Nouveau Nom", "client_company": "Société actuelle",
        "client_email": "nouveau@example.test", "client_phone": "0123456789",
        "client_address": "Adresse actuelle",
    }
    with closing(sqlite3.connect(tmp_path / "partielle.db")) as connexion:
        connexion.execute(
            "CREATE TABLE contacts (id TEXT PRIMARY KEY, first_name TEXT, last_name TEXT, "
            "company TEXT, email TEXT, phone TEXT, address TEXT)"
        )
        connexion.execute(
            "CREATE TABLE invoices (id TEXT PRIMARY KEY, contact_id TEXT, "
            + ", ".join(f"{colonne} TEXT" for colonne in existantes) + ")"
        )
        connexion.execute(
            "INSERT INTO contacts VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("c", "Nouveau", "Nom", nouvelles["client_company"], nouvelles["client_email"],
             nouvelles["client_phone"], nouvelles["client_address"]),
        )
        connexion.execute(
            "INSERT INTO invoices VALUES (" + ", ".join("?" for _ in range(2 + len(existantes))) + ")",
            ("i", "c", *(anciennes[colonne] for colonne in existantes)),
        )
        assert _ensure_invoice_client_snapshot(connexion) == [absente]
        attendu = tuple(nouvelles[c] if c == absente else anciennes[c] for c in colonnes)
        assert connexion.execute("SELECT " + ", ".join(colonnes) + " FROM invoices").fetchone() == attendu
        _ensure_invoice_client_snapshot(connexion)
        assert connexion.execute("SELECT " + ", ".join(colonnes) + " FROM invoices").fetchone() == attendu
