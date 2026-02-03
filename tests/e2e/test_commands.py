"""
Tests E2E - Commandes utilisateur (via API).

Tests CRUD pour les commandes personnalisees via l'API REST.
Utilise le fixture api_client (httpx) sans navigateur.
"""

import pytest


def test_commands_list_empty(api_client):
    """
    GET /api/commands/user retourne une liste vide au demarrage.
    """
    resp = api_client.get("/api/commands/user")
    assert resp.status_code == 200

    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_commands_create(api_client):
    """
    POST /api/commands/user cree une commande avec nom et contenu,
    puis GET verifie qu'elle existe.
    """
    # Creer une commande
    payload = {
        "name": "test-resume",
        "description": "Resume un texte en 3 points",
        "category": "productivite",
        "icon": "📝",
        "show_on_home": True,
        "content": "Resume le texte suivant en 3 points cles : {{input}}",
    }

    resp = api_client.post("/api/commands/user", json=payload)
    assert resp.status_code == 201

    created = resp.json()
    assert created["name"] == "test-resume"
    assert created["description"] == "Resume un texte en 3 points"
    assert created["category"] == "productivite"
    assert created["icon"] == "📝"
    assert created["show_on_home"] is True
    assert created["content"] == "Resume le texte suivant en 3 points cles : {{input}}"

    # Verifier via GET que la commande existe
    resp_get = api_client.get("/api/commands/user/test-resume")
    assert resp_get.status_code == 200

    fetched = resp_get.json()
    assert fetched["name"] == "test-resume"
    assert fetched["description"] == "Resume un texte en 3 points"

    # Verifier aussi via la liste
    resp_list = api_client.get("/api/commands/user")
    assert resp_list.status_code == 200

    commands = resp_list.json()
    assert len(commands) >= 1
    names = [c["name"] for c in commands]
    assert "test-resume" in names


def test_commands_update(api_client):
    """
    PUT /api/commands/user/{name} met a jour une commande existante.
    """
    # D'abord creer une commande
    create_payload = {
        "name": "test-update-cmd",
        "description": "Description initiale",
        "category": "general",
        "content": "Contenu initial",
    }
    resp_create = api_client.post("/api/commands/user", json=create_payload)
    assert resp_create.status_code == 201

    # Mettre a jour la description et le contenu
    update_payload = {
        "description": "Description mise a jour",
        "content": "Nouveau contenu ameliore",
        "show_on_home": True,
    }

    resp_update = api_client.put("/api/commands/user/test-update-cmd", json=update_payload)
    assert resp_update.status_code == 200

    updated = resp_update.json()
    assert updated["name"] == "test-update-cmd"
    assert updated["description"] == "Description mise a jour"
    assert updated["content"] == "Nouveau contenu ameliore"
    assert updated["show_on_home"] is True

    # Verifier la persistence via GET
    resp_get = api_client.get("/api/commands/user/test-update-cmd")
    assert resp_get.status_code == 200
    assert resp_get.json()["description"] == "Description mise a jour"


def test_commands_delete(api_client):
    """
    DELETE /api/commands/user/{name} supprime une commande.
    Un GET subsequent retourne 404.
    """
    # Creer une commande a supprimer
    create_payload = {
        "name": "test-delete-cmd",
        "description": "A supprimer",
        "content": "Contenu temporaire",
    }
    resp_create = api_client.post("/api/commands/user", json=create_payload)
    assert resp_create.status_code == 201

    # Verifier qu'elle existe
    resp_get = api_client.get("/api/commands/user/test-delete-cmd")
    assert resp_get.status_code == 200

    # Supprimer la commande
    resp_delete = api_client.delete("/api/commands/user/test-delete-cmd")
    assert resp_delete.status_code == 200

    body = resp_delete.json()
    assert "supprimee" in body.get("message", "").lower() or "message" in body

    # Verifier que la commande n'existe plus
    resp_gone = api_client.get("/api/commands/user/test-delete-cmd")
    assert resp_gone.status_code == 404
