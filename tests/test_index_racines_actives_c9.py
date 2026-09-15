"""B-831 (cycle 9) : l'index unique « une racine active = un projet » était créé
hors de tout try au démarrage ; deux racines actives identiques héritées d'une
base ancienne faisaient échouer init_db, donc l'application."""
from __future__ import annotations

import sqlite3

from app.models.database import poser_index_racine_active
from sqlalchemy import create_engine


def _base_avec_doublons(tmp_path):
    chemin = tmp_path / "doublons.db"
    con = sqlite3.connect(chemin)
    con.execute("CREATE TABLE project_sync_roots (id TEXT PRIMARY KEY, racine TEXT NOT NULL, detachee INTEGER NOT NULL DEFAULT 0)")
    con.executemany("INSERT INTO project_sync_roots VALUES (?, ?, 0)", [("a", "/Users/ludo/Projets"), ("b", "/Users/ludo/Projets")])
    con.commit()
    con.close()
    return chemin


def test_des_doublons_herites_ne_bloquent_pas_le_demarrage(tmp_path, caplog) -> None:
    engine = create_engine(f"sqlite:///{_base_avec_doublons(tmp_path)}")
    with engine.connect() as conn, caplog.at_level("WARNING", logger="app.models.database"):
        assert poser_index_racine_active(conn) is False
    assert "racine" in caplog.text.lower()


def test_sans_doublon_l_index_est_pose(tmp_path) -> None:
    chemin = tmp_path / "saine.db"
    con = sqlite3.connect(chemin)
    con.execute("CREATE TABLE project_sync_roots (id TEXT PRIMARY KEY, racine TEXT NOT NULL, detachee INTEGER NOT NULL DEFAULT 0)")
    con.commit()
    con.close()
    engine = create_engine(f"sqlite:///{chemin}")
    with engine.connect() as conn:
        assert poser_index_racine_active(conn) is True
        conn.commit()
    con = sqlite3.connect(chemin)
    assert con.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name='uq_sync_root_racine_active'").fetchone()[0] == 1
