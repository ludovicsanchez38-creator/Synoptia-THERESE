"""Régression bug image #3 (11/06/2026).

La génération d'images lisait la clé API via une connexion SQLite STANDARD
(`create_engine("sqlite:///...")`), incapable de lire la base chiffrée
SQLCipher (US-014). Résultat : « Clé API ... (Image) non configurée » alors
que le test de la clé dans les Réglages (connecteur applicatif) passait.
`_get_api_key_from_db` doit passer par `db_connect` (qui pose la clé SQLCipher
si la base est chiffrée).
"""

import sqlcipher3
from app.config import settings
from app.models.database import db_is_encrypted
from app.services.encryption import get_db_key_hex, get_encryption_service
from app.services.image_generator import _get_api_key_from_db


def _make_encrypted_db_with_pref(db_path, key_name: str, plaintext: str) -> None:
    """Crée une base SQLCipher chiffrée avec une préférence chiffrée Fernet."""
    conn = sqlcipher3.connect(str(db_path))
    conn.execute(f"PRAGMA key = \"x'{get_db_key_hex()}'\"")
    conn.execute("CREATE TABLE preferences (key TEXT PRIMARY KEY, value TEXT)")
    encrypted = get_encryption_service().encrypt(plaintext)
    conn.execute(
        "INSERT INTO preferences (key, value) VALUES (?, ?)",
        (f"{key_name}_api_key", encrypted),
    )
    conn.commit()
    conn.close()


def test_lecture_cle_image_sur_base_chiffree(tmp_path, monkeypatch):
    """La clé image se lit sur une base chiffrée (le cas réel de production)."""
    db_path = tmp_path / "therese.db"
    _make_encrypted_db_with_pref(db_path, "gemini_image", "AIzaTESTKEY123")

    # Garde-fou : sans ça le test ne prouverait rien (base claire = pas de bug).
    assert db_is_encrypted(db_path), "la base de test doit être chiffrée"

    monkeypatch.setattr(settings, "db_path", db_path)
    # Empêcher une variable d'env de court-circuiter la lecture en base.
    monkeypatch.delenv("GEMINI_IMAGE_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    assert _get_api_key_from_db("gemini_image") == "AIzaTESTKEY123"
