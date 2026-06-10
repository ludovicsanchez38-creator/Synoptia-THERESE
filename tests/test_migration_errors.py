"""US-008 (RES5-b) : une migration auto qui échoue pour une raison fatale
(DB en lecture seule, permission, verrou, disque plein) ne doit pas être
avalée en WARNING — l'app démarrerait avec un schéma incomplet sans signal."""
import sqlite3

from app.main import _is_fatal_migration_error


def test_erreurs_fatales_detectees():
    assert _is_fatal_migration_error(
        sqlite3.OperationalError("attempt to write a readonly database")
    )
    assert _is_fatal_migration_error(sqlite3.OperationalError("database is locked"))
    assert _is_fatal_migration_error(OSError("disk I/O error"))


def test_erreurs_benignes_non_fatales():
    # Colonne déjà présente, etc. : on continue (warning), pas de re-raise.
    assert not _is_fatal_migration_error(
        sqlite3.OperationalError("duplicate column name: currency")
    )
    assert not _is_fatal_migration_error(Exception("table already exists"))
