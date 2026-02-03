"""
THERESE v2 - Tests E2E Export/Backup donnees

Test des fonctionnalites d'export, backup et restauration de donnees.
Principalement des tests API (pas d'UI).
"""

import json
import pytest


# ============================================================
# Export donnees (RGPD Art. 20 - Portabilite)
# ============================================================


def test_data_export_all(api_client):
    """
    P0 - Export complet de toutes les donnees utilisateur.

    GET /api/data/export et verifie la structure JSON
    contenant contacts, conversations, files, preferences, etc.
    """
    resp = api_client.get("/api/data/export")
    assert resp.status_code == 200, f"Erreur export: {resp.status_code} - {resp.text}"

    data = resp.json()

    # Verifier la structure principale
    assert "exported_at" in data
    assert "data_format_version" in data

    # Verifier les arrays de donnees
    expected_keys = [
        "contacts",
        "projects",
        "conversations",
        "files",
        "preferences",
        "board_decisions",
        "activity_logs",
    ]

    for key in expected_keys:
        assert key in data, f"Cle manquante dans l'export: {key}"
        assert isinstance(data[key], list), f"{key} n'est pas une liste"

    # Verifier que les cles API sont masquees dans les preferences
    for pref in data["preferences"]:
        if "api_key" in pref.get("key", "").lower():
            assert pref["value"] == "[REDACTED]", (
                f"Cle API non masquee: {pref['key']}"
            )


def test_data_export_conversations_markdown(api_client):
    """
    P1 - Export des conversations au format Markdown.

    GET /api/data/export/conversations?format=markdown
    et verifie que le contenu est bien du Markdown.
    """
    resp = api_client.get("/api/data/export/conversations?format=markdown")
    assert resp.status_code == 200, f"Erreur export MD: {resp.status_code} - {resp.text}"

    data = resp.json()

    # Verifier la structure
    assert "format" in data
    assert data["format"] == "markdown"
    assert "content" in data

    # Le contenu doit commencer par un titre Markdown
    content = data["content"]
    assert isinstance(content, str)
    assert content.startswith("# Export Conversations THERESE")


# ============================================================
# Backup & Restore
# ============================================================


def test_data_backup_create(api_client):
    """
    P1 - Creation d'un backup de la base de donnees.

    POST /api/data/backup et verifie que le backup
    est cree avec un nom et un chemin valides.
    """
    resp = api_client.post("/api/data/backup")
    assert resp.status_code == 200, f"Erreur backup: {resp.status_code} - {resp.text}"

    data = resp.json()

    # Verifier la structure de la reponse
    assert data["success"] is True
    assert "backup_name" in data
    assert "path" in data
    assert "created_at" in data

    # Le nom du backup doit suivre le pattern therese_backup_YYYYMMDD_HHMMSS
    backup_name = data["backup_name"]
    assert backup_name.startswith("therese_backup_")

    # Le chemin doit contenir le dossier backups
    assert "backups" in data["path"]


def test_data_backup_list(api_client):
    """
    P1 - Liste des backups disponibles.

    Cree d'abord un backup, puis GET /api/data/backups
    et verifie que la liste contient au moins un backup.
    """
    # S'assurer qu'il y a au moins un backup
    api_client.post("/api/data/backup")

    resp = api_client.get("/api/data/backups")
    assert resp.status_code == 200, f"Erreur liste backups: {resp.status_code} - {resp.text}"

    data = resp.json()

    # Verifier la structure
    assert "backups" in data
    assert isinstance(data["backups"], list)

    # Au moins un backup doit exister
    assert len(data["backups"]) >= 1

    # Verifier la structure d'un backup
    backup = data["backups"][0]
    assert "backup_name" in backup
    assert "created_at" in backup
    assert "db_path" in backup


def test_data_backup_status(api_client):
    """
    P2 - Status et recommandation de backup.

    GET /api/data/backup/status et verifie la structure
    de la reponse avec recommandation.
    """
    resp = api_client.get("/api/data/backup/status")
    assert resp.status_code == 200, f"Erreur status backup: {resp.status_code} - {resp.text}"

    data = resp.json()

    # Verifier la structure
    assert "has_backups" in data
    assert isinstance(data["has_backups"], bool)

    # Si pas de backups, la recommendation doit etre presente
    if not data["has_backups"]:
        assert "recommendation" in data
        assert data["recommendation"] is not None
    else:
        # Si backups existent, last_backup doit etre present
        assert "last_backup" in data
