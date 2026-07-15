"""US-015 : voie de migration unique (Alembic branché).

Avant : deux mécanismes concurrents (create_all + ALTER ad-hoc au boot, et
Alembic jamais appliqué). Une DB legacy n'avait pas d'alembic_version :
`make db-migrate` y échouait en tentant de recréer des tables existantes.
Désormais : init_db estampille la DB à la tête (le bootstrap l'amène AU
schéma courant), et env.py fait le même pré-vol pour les DB legacy.
"""
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
from app.models.database import (
    ALEMBIC_HEAD_REVISION,
    ensure_alembic_stamp,
)

BACKEND = Path(__file__).parent.parent / "src" / "backend"
BOARD_HISTORY_COLUMNS = ("web_sources", "synthesis_usage")
ATELIER_HISTORY_COLUMNS = (
    "run_phase",
    "plan",
    "test_results",
    "explanation",
    "events",
    "agent_outputs",
    "base_branch",
    "commit_hash",
)


def _read_stamp(db_path: Path) -> str | None:
    # db_connect : la DB peut être CHIFFRÉE (depuis la revue adversariale,
    # make db-migrate sur dossier vierge crée une DB chiffrée d'office)
    from app.models.database import db_connect

    with db_connect(db_path) as conn:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'"
        ).fetchone()
        if row is None:
            return None
        return conn.execute("SELECT version_num FROM alembic_version").fetchone()[0]


def _make_legacy_db(db_path: Path) -> None:
    """DB « legacy » minimale : tables métier présentes, pas d'alembic_version."""
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("CREATE TABLE contacts (id VARCHAR PRIMARY KEY, first_name VARCHAR)")
        conn.commit()


def _make_patched_tracked_db(db_path: Path, missing_column: str | None = None) -> None:
    """Construit une DB ancienne dont les patches ad-hoc simulent le schéma head."""
    board_columns = [
        column
        for column in BOARD_HISTORY_COLUMNS
        if column != missing_column
    ]
    atelier_columns = [
        column
        for column in ATELIER_HISTORY_COLUMNS
        if column != missing_column
    ]
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("CREATE TABLE contacts (id VARCHAR PRIMARY KEY)")
        conn.execute(
            "CREATE TABLE invoices "
            "(id VARCHAR PRIMARY KEY, currency TEXT, validite_jours INTEGER)"
        )
        conn.execute("CREATE TABLE variables (id VARCHAR PRIMARY KEY)")
        conn.execute(
            "CREATE TABLE board_decisions (id VARCHAR PRIMARY KEY, "
            + ", ".join(f"{column} TEXT" for column in board_columns)
            + ")"
        )
        conn.execute(
            "CREATE TABLE agent_tasks (id VARCHAR PRIMARY KEY, "
            + ", ".join(f"{column} TEXT" for column in atelier_columns)
            + ")"
        )
        conn.execute("CREATE TABLE alembic_version (version_num VARCHAR(32) PRIMARY KEY)")
        conn.execute("INSERT INTO alembic_version VALUES ('c3d4e5f6a7b8')")
        conn.commit()


def test_constante_epinglee_suit_la_vraie_tete():
    """ALEMBIC_HEAD_REVISION (épinglée pour l'app packagée) doit suivre la
    tête réelle de alembic/versions - sinon une nouvelle migration serait
    silencieusement ignorée par le stamp."""
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND / "alembic"))
    head = ScriptDirectory.from_config(cfg).get_current_head()
    assert head == ALEMBIC_HEAD_REVISION, (
        f"Tête Alembic réelle {head} != constante épinglée {ALEMBIC_HEAD_REVISION}. "
        "Mettre à jour ALEMBIC_HEAD_REVISION dans database.py après toute "
        "nouvelle migration."
    )


def test_stamp_db_legacy(tmp_path):
    db = tmp_path / "legacy.db"
    _make_legacy_db(db)
    ensure_alembic_stamp(db)
    assert _read_stamp(db) == ALEMBIC_HEAD_REVISION


def test_stamp_idempotent_et_ne_regresse_pas(tmp_path):
    db = tmp_path / "tracked.db"
    _make_legacy_db(db)
    # DB déjà suivie par Alembic à une révision plus ancienne
    with sqlite3.connect(str(db)) as conn:
        conn.execute("CREATE TABLE alembic_version (version_num VARCHAR(32) PRIMARY KEY)")
        conn.execute("INSERT INTO alembic_version VALUES ('21b429e036ef')")
        conn.commit()
    ensure_alembic_stamp(db)
    # Pas d'écrasement : upgrade head fera avancer cette DB normalement
    assert _read_stamp(db) == "21b429e036ef"


def test_stamp_ignore_db_vide(tmp_path):
    """Une DB sans tables métier ne doit PAS être estampillée (elle doit être
    créée par les migrations ou par create_all d'abord)."""
    db = tmp_path / "empty.db"
    sqlite3.connect(str(db)).close()
    ensure_alembic_stamp(db)
    assert _read_stamp(db) is None


def _run_upgrade_head(data_dir: Path) -> subprocess.CompletedProcess:
    env = {**os.environ, "THERESE_DATA_DIR": str(data_dir)}
    return subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        capture_output=True, text=True, cwd=str(BACKEND), env=env, timeout=120,
    )


@pytest.mark.slow
def test_make_db_migrate_sur_db_legacy(tmp_path):
    """Scénario du plan : `make db-migrate` sur une DB legacy (create_all,
    sans alembic_version) doit réussir - le pré-vol d'env.py l'estampille
    au lieu de laisser Alembic recréer des tables existantes."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _make_legacy_db(data_dir / "therese.db")

    result = _run_upgrade_head(data_dir)
    assert result.returncode == 0, result.stderr[-800:]
    assert _read_stamp(data_dir / "therese.db") == ALEMBIC_HEAD_REVISION


@pytest.mark.slow
def test_make_db_migrate_sur_db_neuve(tmp_path):
    """`make db-migrate` sur une DB neuve (aucun fichier) doit dérouler les
    migrations depuis la racine sans erreur."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    result = _run_upgrade_head(data_dir)
    assert result.returncode == 0, result.stderr[-800:]
    assert _read_stamp(data_dir / "therese.db") == ALEMBIC_HEAD_REVISION

def test_stamp_sur_db_chiffree(tmp_path):
    """Revue adversariale : ensure_alembic_stamp passe par db_connect, donc
    doit fonctionner sur une DB SQLCipher (et pas avaler une erreur de clé
    en silence)."""
    from app.models.database import db_connect, ensure_db_encrypted

    db = tmp_path / "therese.db"
    _make_legacy_db(db)
    ensure_db_encrypted(db)

    ensure_alembic_stamp(db)
    assert _read_stamp(db) == ALEMBIC_HEAD_REVISION
    with db_connect(db) as conn:
        assert conn.execute("SELECT COUNT(*) FROM contacts").fetchone() is not None


def test_realignement_db_trackee_ancienne_schema_patche(tmp_path):
    """Revue adversariale US-015 : une DB trackée à une révision ancienne dont
    le schéma a déjà été patché par les migrations ad-hoc doit être
    ré-estampillée à la tête - sinon upgrade head replante en duplicate
    column. Variables V4 finding Codex 8 : la preuve de schéma exige DÉSORMAIS
    chaque élément apporté depuis (table variables comprise) - dans le flux
    desktop réel, apply_adhoc_migrations tourne AVANT et la crée. La preuve
    couvre également toutes les colonnes Board et Atelier de la 0.40."""
    db = tmp_path / "therese.db"
    _make_patched_tracked_db(db)

    ensure_alembic_stamp(db)
    assert _read_stamp(db) == ALEMBIC_HEAD_REVISION


@pytest.mark.parametrize(
    "missing_column",
    [
        *BOARD_HISTORY_COLUMNS,
        *ATELIER_HISTORY_COLUMNS,
    ],
)
def test_realignement_refuse_si_une_colonne_v040_manque(tmp_path, missing_column):
    """Aucune migration Board/Atelier ne doit être sautée par un stamp abusif."""
    db = tmp_path / "therese.db"
    _make_patched_tracked_db(db, missing_column=missing_column)

    ensure_alembic_stamp(db)

    assert _read_stamp(db) == "c3d4e5f6a7b8"


@pytest.mark.slow
def test_make_db_migrate_sur_db_chiffree(tmp_path):
    """`make db-migrate` doit fonctionner sur une DB CHIFFRÉE (env.py
    _make_engine pose la clé SQLCipher)."""
    from app.models.database import ensure_db_encrypted

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    db = data_dir / "therese.db"
    _make_legacy_db(db)
    ensure_db_encrypted(db)

    result = _run_upgrade_head(data_dir)
    assert result.returncode == 0, result.stderr[-800:]
    assert _read_stamp(db) == ALEMBIC_HEAD_REVISION
