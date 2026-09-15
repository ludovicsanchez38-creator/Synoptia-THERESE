"""B-840 (cycle 9) : `with db_connect(...) as conn` gère la transaction sqlite3,
pas la fermeture ; les deux autres appelants passent par `closing()`."""
from __future__ import annotations

from unittest.mock import MagicMock

from app.models import database


def test_la_connexion_est_fermee_apres_la_verification_des_colonnes(tmp_path, monkeypatch) -> None:
    chemin = tmp_path / "factures.db"
    chemin.write_bytes(b"")
    conn = MagicMock()
    conn.execute.return_value.fetchall.return_value = []
    conn.__enter__.return_value = conn
    monkeypatch.setattr(database, "db_connect", lambda _p: conn)

    assert database.ensure_invoice_legacy_columns(chemin) == []
    conn.close.assert_called_once()
