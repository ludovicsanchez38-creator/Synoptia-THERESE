"""Une base incomplète ne doit pas être marquée à la tête Alembic."""

import sqlite3
from contextlib import closing

import pytest
from app.models.database import ALEMBIC_HEAD_REVISION, ensure_alembic_stamp
from app.models.entities import Invoice
from sqlalchemy import create_engine
from sqlmodel import SQLModel

from tests.test_alembic_stamp import _make_patched_tracked_db, _read_stamp


@pytest.mark.parametrize("suivie", [True, False])
@pytest.mark.parametrize("colonne", [
    "tva_applicable", "service_date", "purchase_order", "payment_terms", "issue_date", "due_date", "total_ttc",
])
def test_factures_au_schema_incomplet_ne_peuvent_pas_etre_estampillees(tmp_path, suivie, colonne):
    base = tmp_path / "factures-incompletes.db"
    _make_patched_tracked_db(base)
    with closing(sqlite3.connect(base)) as connexion:
        connexion.execute("DROP TABLE invoices")
        if not suivie:
            connexion.execute("DROP TABLE alembic_version")
        connexion.commit()
    moteur = create_engine(f"sqlite:///{base}")
    try:
        Invoice.__table__.create(moteur)
    finally:
        moteur.dispose()
    with closing(sqlite3.connect(base)) as connexion:
        connexion.execute(f"ALTER TABLE invoices DROP COLUMN {colonne}")
        connexion.commit()

    ensure_alembic_stamp(base)
    assert _read_stamp(base) == ("c3d4e5f6a7b8" if suivie else None)


@pytest.mark.parametrize("suivie", [False, True])
def test_schema_incomplet_ne_saute_pas_les_migrations(tmp_path, suivie):
    base = tmp_path / "incomplete.db"
    with closing(sqlite3.connect(base)) as connexion:
        connexion.execute("CREATE TABLE contacts (id TEXT PRIMARY KEY)")
        if suivie:
            connexion.execute("CREATE TABLE alembic_version (version_num TEXT PRIMARY KEY)")
            connexion.execute("INSERT INTO alembic_version VALUES ('ancienne_revision')")
        connexion.commit()
    ensure_alembic_stamp(base)
    assert _read_stamp(base) == ("ancienne_revision" if suivie else None)


def test_base_complete_sans_stamp_peut_etre_estampillee(tmp_path):
    base = tmp_path / "complete.db"
    moteur = create_engine(f"sqlite:///{base}")
    try:
        SQLModel.metadata.create_all(moteur)
    finally:
        moteur.dispose()
    ensure_alembic_stamp(base)
    assert _read_stamp(base) == ALEMBIC_HEAD_REVISION


def test_colonne_contact_absente_des_activites_bloque_le_reestampillage(tmp_path):
    base = tmp_path / "activites.db"
    _make_patched_tracked_db(base)
    with closing(sqlite3.connect(base)) as connexion:
        colonnes = [
            ligne[1] for ligne in connexion.execute("PRAGMA table_info(activities)")
            if ligne[1] != "contact_id"
        ]
        connexion.execute(f"CREATE TABLE activites_sans_contact AS SELECT {', '.join(colonnes)} FROM activities")
        connexion.execute("DROP TABLE activities")
        connexion.execute("ALTER TABLE activites_sans_contact RENAME TO activities")
        connexion.commit()
    ensure_alembic_stamp(base)
    assert _read_stamp(base) == "c3d4e5f6a7b8"
