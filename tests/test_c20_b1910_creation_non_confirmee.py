"""La bulle ne doit pas annoncer une création sans succès explicite."""

import json
from unittest.mock import AsyncMock

import pytest
from app.services.tool_confirmations import register_pending


@pytest.mark.asyncio
@pytest.mark.parametrize("nom", ["create_contact", "create_project", "create_task", "create_invoice"])
@pytest.mark.parametrize("donnees", [{}, {"id": "fictif"}, {"success": None}, {"success": 1}, []])
async def test_confirmation_ne_pretend_pas_creer_sans_succes(client, monkeypatch, nom, donnees):
    from app.routers import chat

    brut = json.dumps(donnees)
    monkeypatch.setattr(chat, "execute_memory_tool", AsyncMock(return_value=brut))
    monkeypatch.setattr(chat, "execute_workspace_tool", AsyncMock(return_value=brut))
    identifiant = register_pending(nom, {"_provenance_documents": "sans_document"})
    reponse = await client.post("/api/chat/confirm-tool", json={
        "confirmation_id": identifiant, "approved": True,
    })
    assert reponse.status_code == 200
    texte = reponse.json()["result"].lower()
    assert "créé" not in texte and "créée" not in texte
    assert "confirm" in texte


@pytest.mark.asyncio
async def test_message_de_succes_contredit_par_le_json_n_est_pas_annonce(client, monkeypatch):
    from app.routers import chat

    brut = json.dumps({"success": False, "message": "Contact créé."})
    monkeypatch.setattr(chat, "execute_memory_tool", AsyncMock(return_value=brut))
    identifiant = register_pending("create_contact", {"_provenance_documents": "sans_document"})
    reponse = await client.post("/api/chat/confirm-tool", json={
        "confirmation_id": identifiant, "approved": True,
    })
    assert reponse.status_code == 200
    assert "Contact créé" not in reponse.json()["result"]


@pytest.mark.asyncio
async def test_contact_existant_n_est_pas_presente_comme_une_creation(client, monkeypatch):
    from app.routers import chat

    brut = json.dumps({"success": True, "already_existed": True})
    monkeypatch.setattr(chat, "execute_memory_tool", AsyncMock(return_value=brut))
    identifiant = register_pending("create_contact", {"_provenance_documents": "sans_document"})
    reponse = await client.post("/api/chat/confirm-tool", json={
        "confirmation_id": identifiant, "approved": True,
    })
    assert "existe déjà" in reponse.json()["result"]
    assert "Contact créé" not in reponse.json()["result"]


@pytest.mark.asyncio
async def test_contact_existant_signale_les_champs_non_enregistres(client, monkeypatch):
    from app.routers import chat

    brut = json.dumps({"success": False, "already_existed": True, "champs_ignores": ["notes"]})
    monkeypatch.setattr(chat, "execute_memory_tool", AsyncMock(return_value=brut))
    identifiant = register_pending("create_contact", {"_provenance_documents": "sans_document"})
    reponse = await client.post("/api/chat/confirm-tool", json={
        "confirmation_id": identifiant, "approved": True,
    })
    assert "notes" in reponse.json()["result"]
    assert "pas été enregistrées" in reponse.json()["result"]


@pytest.mark.asyncio
async def test_erreur_de_validation_du_contact_est_affichee(client):
    identifiant = register_pending("create_contact", {
        "first_name": "Test", "email": "adresse-invalide",
        "_provenance_documents": "sans_document",
    })

    reponse = await client.post("/api/chat/confirm-tool", json={
        "confirmation_id": identifiant, "approved": True,
    })

    assert reponse.status_code == 200
    assert "L'adresse e-mail n'a pas la forme attendue" in reponse.json()["result"]
    assert "Rien n'a été enregistré" in reponse.json()["result"]


@pytest.mark.asyncio
async def test_brouillon_sans_ligne_affiche_l_instruction_reelle(client):
    identifiant = register_pending("create_invoice", {
        "document_type": "facture", "lines": [], "_provenance_documents": "sans_document",
    })

    reponse = await client.post("/api/chat/confirm-tool", json={
        "confirmation_id": identifiant, "approved": True,
    })

    assert reponse.status_code == 200
    assert reponse.json()["result"] == "Ajoute au moins une ligne au brouillon."


@pytest.mark.parametrize("message", [
    "Ajouter une ligne au brouillon.",
    "Ajoute au moins une ligne au brouillon.",
    "Enregistre le brouillon après validation.",
    "Crée un brouillon avant de continuer.",
    "La ligne doit être ajoutée.",
    "La ligne peut être enregistrée.",
    "Le brouillon sera créé après validation.",
])
def test_instruction_de_creation_n_est_pas_une_affirmation(message):
    from app.services.tool_confirmations import resultat_pour_l_ecran

    assert resultat_pour_l_ecran("create_invoice", json.dumps({
        "success": False, "message": message,
    })) == message


@pytest.mark.asyncio
async def test_motif_d_interruption_de_creation_est_affiche(client, monkeypatch):
    from app.routers import chat

    motif = "Création du contact interrompue avant écriture : l'utilisateur a arrêté la génération."
    brut = json.dumps({"success": False, "message": motif})
    monkeypatch.setattr(chat, "execute_memory_tool", AsyncMock(return_value=brut))
    identifiant = register_pending("create_contact", {"_provenance_documents": "sans_document"})

    reponse = await client.post("/api/chat/confirm-tool", json={
        "confirmation_id": identifiant, "approved": True,
    })

    assert reponse.status_code == 200
    assert reponse.json()["result"] == motif


@pytest.mark.asyncio
async def test_erreur_qui_affirme_une_creation_reste_masquee(client, monkeypatch):
    from app.routers import chat

    brut = json.dumps({"success": False, "error": "Contact créé."})
    monkeypatch.setattr(chat, "execute_memory_tool", AsyncMock(return_value=brut))
    identifiant = register_pending("create_contact", {"_provenance_documents": "sans_document"})

    reponse = await client.post("/api/chat/confirm-tool", json={
        "confirmation_id": identifiant, "approved": True,
    })

    assert reponse.status_code == 200
    assert "Contact créé" not in reponse.json()["result"]
    assert "n'est pas confirmée" in reponse.json()["result"]


@pytest.mark.asyncio
async def test_negation_puis_affirmation_de_creation_reste_masquee(client, monkeypatch):
    from app.routers import chat

    brut = json.dumps({"success": False, "message": (
        "La création n'a pas été confirmée mais le contact a été créé."
    )})
    monkeypatch.setattr(chat, "execute_memory_tool", AsyncMock(return_value=brut))
    identifiant = register_pending("create_contact", {"_provenance_documents": "sans_document"})

    reponse = await client.post("/api/chat/confirm-tool", json={
        "confirmation_id": identifiant, "approved": True,
    })

    assert reponse.status_code == 200
    assert "le contact a été créé" not in reponse.json()["result"]


@pytest.mark.asyncio
async def test_cause_evoquant_une_adresse_deja_enregistree_est_preservee(client, monkeypatch):
    from app.routers import chat

    cause = "Cet e-mail est déjà enregistré pour un contact."
    monkeypatch.setattr(chat, "execute_memory_tool", AsyncMock(return_value=json.dumps({"error": cause})))
    identifiant = register_pending("create_contact", {"_provenance_documents": "sans_document"})

    reponse = await client.post("/api/chat/confirm-tool", json={
        "confirmation_id": identifiant, "approved": True,
    })

    assert reponse.status_code == 200
    assert reponse.json()["result"] == cause


@pytest.mark.asyncio
async def test_creation_dite_effectuee_malgre_l_echec_reste_masquee(client, monkeypatch):
    from app.routers import chat

    brut = json.dumps({"success": False, "message": "La création du contact a été effectuée."})
    monkeypatch.setattr(chat, "execute_memory_tool", AsyncMock(return_value=brut))
    identifiant = register_pending("create_contact", {"_provenance_documents": "sans_document"})

    reponse = await client.post("/api/chat/confirm-tool", json={
        "confirmation_id": identifiant, "approved": True,
    })

    assert reponse.status_code == 200
    assert "a été effectuée" not in reponse.json()["result"]


@pytest.mark.asyncio
async def test_affirmation_sans_accents_malgre_l_echec_reste_masquee(client, monkeypatch):
    from app.routers import chat

    brut = json.dumps({"success": False, "error": "Contact cree avec succes."})
    monkeypatch.setattr(chat, "execute_memory_tool", AsyncMock(return_value=brut))
    identifiant = register_pending("create_contact", {"_provenance_documents": "sans_document"})

    reponse = await client.post("/api/chat/confirm-tool", json={
        "confirmation_id": identifiant, "approved": True,
    })

    assert reponse.status_code == 200
    assert "Contact cree" not in reponse.json()["result"]
