"""
THERESE v2 - Data Router Tests

Tests pour les endpoints d'export, import, backup et logs (US-SEC-02, US-BAK-01 a US-BAK-05).
"""

from datetime import UTC, datetime

import pytest
from app.models.entities import Conversation, Message, Project
from httpx import AsyncClient

# ============================================================
# Helpers
# ============================================================


async def _create_contact(client: AsyncClient, first_name: str = "Jean") -> str:
    """Cree un contact de test et retourne son ID."""
    response = await client.post("/api/memory/contacts", json={
        "first_name": first_name,
        "last_name": "Dupont",
        "company": "Synoptia",
        "email": f"{first_name.lower()}@synoptia.fr",
    })
    assert response.status_code == 200
    return response.json()["id"]


async def _create_prestation(client: AsyncClient, contact_id: str) -> dict:
    """Crée une prestation contenant les données sensibles visées par le lot D."""
    response = await client.post(
        "/api/prestations",
        json={
            "contact_id": contact_id,
            "intitule": "Formation confidentielle",
            "montant_ht": 2490.0,
            "phase": "gagne",
            "financeur": "Atlas",
            "statut_financement": "valide",
            "fin_le": "2026-10-15",
            "suivi_apres_jours": 120,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


async def _create_document_with_section_and_piste(client: AsyncClient) -> dict:
    """Cree un document de l'atelier documentaire avec une section redigee
    et une piste, pour verrouiller sa presence dans export/delete RGPD."""
    doc_response = await client.post(
        "/api/documents", json={"title": "Doc RGPD", "brief": "Brief du besoin"}
    )
    assert doc_response.status_code == 200, doc_response.text
    document = doc_response.json()

    section_response = await client.post(
        f"/api/documents/{document['id']}/sections",
        json={"title": "Section RGPD", "brief": "", "order": 0.0, "depth": 0},
    )
    assert section_response.status_code == 200, section_response.text
    section = section_response.json()

    await client.patch(
        f"/api/documents/sections/{section['id']}",
        json={"content": "Contenu redige a exporter/supprimer."},
    )

    piste_response = await client.post(
        f"/api/documents/{document['id']}/pistes",
        json={"texte": "Piste RGPD a retrouver dans l'export"},
    )
    assert piste_response.status_code == 200, piste_response.text
    piste = piste_response.json()

    return {"document": document, "section": section, "piste": piste}


# ============================================================
# Export Tests
# ============================================================


class TestDataExport:
    """Tests pour les endpoints d'export RGPD."""

    @pytest.mark.asyncio
    async def test_export_all_data_empty(self, client: AsyncClient):
        """GET /api/data/export retourne une structure avec des tableaux vides."""
        response = await client.get("/api/data/export")

        assert response.status_code == 200
        data = response.json()

        # Verifier la structure de base
        assert "exported_at" in data
        assert "contacts" in data
        assert "projects" in data
        assert "conversations" in data
        assert "files" in data
        assert "preferences" in data
        assert "board_decisions" in data
        assert "activity_logs" in data

        assert isinstance(data["contacts"], list)
        assert isinstance(data["projects"], list)
        assert isinstance(data["conversations"], list)

    @pytest.mark.asyncio
    async def test_export_all_data_with_contacts(self, client: AsyncClient):
        """GET /api/data/export contient les contacts crees."""
        # Creer des contacts
        await _create_contact(client, "Alice")
        await _create_contact(client, "Bob")

        response = await client.get("/api/data/export")

        assert response.status_code == 200
        data = response.json()

        assert len(data["contacts"]) >= 2
        first_names = [c["first_name"] for c in data["contacts"]]
        assert "Alice" in first_names
        assert "Bob" in first_names

    @pytest.mark.asyncio
    async def test_export_all_data_contains_prestations(self, client: AsyncClient):
        """Art. 20 : l'engagement, son montant et son financeur sont portables."""
        contact_id = await _create_contact(client, "AlicePrestation")
        prestation = await _create_prestation(client, contact_id)

        response = await client.get("/api/data/export")

        assert response.status_code == 200
        exported = response.json()
        assert exported["prestations"] == [
            {
                "id": prestation["id"],
                "contact_id": contact_id,
                "intitule": "Formation confidentielle",
                "montant_ht": 2490.0,
                "phase": "gagne",
                "financeur": "Atlas",
                "statut_financement": "valide",
                "fin_le": "2026-10-15",
                "suivi_apres_jours": 120,
                "created_at": prestation["created_at"],
                "updated_at": prestation["updated_at"],
            }
        ]
        assert exported["data_format_version"] == "1.3"

    @pytest.mark.asyncio
    async def test_export_all_data_contains_documents_sections_pistes(self, client: AsyncClient):
        """GET /api/data/export (RGPD Art. 20) restitue l'atelier documentaire :
        un « supprimer toutes mes donnees » sans ces 3 tables laisserait un
        trou dans le droit a la portabilite."""
        created = await _create_document_with_section_and_piste(client)

        response = await client.get("/api/data/export")

        assert response.status_code == 200
        data = response.json()

        assert "documents" in data
        assert "document_sections" in data
        assert "document_pistes" in data
        assert isinstance(data["documents"], list)
        assert isinstance(data["document_sections"], list)
        assert isinstance(data["document_pistes"], list)

        doc_ids = [d["id"] for d in data["documents"]]
        assert created["document"]["id"] in doc_ids

        section_ids = [s["id"] for s in data["document_sections"]]
        assert created["section"]["id"] in section_ids
        exported_section = next(
            s for s in data["document_sections"] if s["id"] == created["section"]["id"]
        )
        assert exported_section["content"] == "Contenu redige a exporter/supprimer."
        assert exported_section["document_id"] == created["document"]["id"]

        piste_ids = [p["id"] for p in data["document_pistes"]]
        assert created["piste"]["id"] in piste_ids
        exported_piste = next(
            p for p in data["document_pistes"] if p["id"] == created["piste"]["id"]
        )
        assert exported_piste["texte"] == "Piste RGPD a retrouver dans l'export"

    @pytest.mark.asyncio
    async def test_export_conversations_json(self, client: AsyncClient):
        """GET /api/data/export/conversations retourne le format JSON."""
        response = await client.get("/api/data/export/conversations")

        assert response.status_code == 200
        data = response.json()

        assert "exported_at" in data
        assert "conversations" in data
        assert isinstance(data["conversations"], list)

    @pytest.mark.asyncio
    async def test_export_conversations_preserve_tout_etat_reimportable(
        self, client: AsyncClient, db_session
    ):
        """L'export dédié ne doit pas jeter les champs que l'import sait restaurer."""
        created_at = datetime(2026, 8, 20, 9, 15, tzinfo=UTC)
        updated_at = datetime(2026, 8, 21, 10, 30, tzinfo=UTC)
        project = Project(id="project-export-conv", name="Projet export")
        conversation = Conversation(
            id="conversation-export-complete",
            title="Historique complet",
            summary="Résumé conservé",
            project_id=project.id,
            memory_scope="project",
            created_at=created_at,
            updated_at=updated_at,
        )
        message = Message(
            id="message-export-complet",
            conversation_id=conversation.id,
            role="assistant",
            content="Document généré",
            tokens_in=12,
            tokens_out=34,
            model="modele-test",
            provider="mistral",
            extra_data='{"skill_files":[{"name":"preuve.docx"}]}',
            created_at=datetime(2026, 8, 20, 9, 16, tzinfo=UTC),
        )
        db_session.add_all([project, conversation, message])
        await db_session.commit()

        response = await client.get("/api/data/export/conversations")

        assert response.status_code == 200
        exported = next(
            item
            for item in response.json()["conversations"]
            if item["id"] == conversation.id
        )
        assert exported["summary"] == "Résumé conservé"
        assert exported["project_id"] == project.id
        assert exported["memory_scope"] == "project"
        assert exported["created_at"].startswith("2026-08-20T09:15:00")
        assert exported["updated_at"].startswith("2026-08-21T10:30:00")
        assert exported["messages"] == [
            {
                "id": message.id,
                "role": "assistant",
                "content": "Document généré",
                "tokens_in": 12,
                "tokens_out": 34,
                "model": "modele-test",
                "provider": "mistral",
                "extra_data": '{"skill_files":[{"name":"preuve.docx"}]}',
                "created_at": "2026-08-20T09:16:00",
            }
        ]

    @pytest.mark.asyncio
    async def test_export_conversations_markdown(self, client: AsyncClient):
        """GET /api/data/export/conversations?format=markdown retourne du Markdown."""
        response = await client.get("/api/data/export/conversations?format=markdown")

        assert response.status_code == 200
        data = response.json()

        assert data["format"] == "markdown"
        assert "content" in data
        assert "# Export Conversations THERESE" in data["content"]


# ============================================================
# Delete All Data Tests
# ============================================================


class TestDataDeletion:
    """Tests pour la suppression de toutes les donnees (RGPD Art. 17)."""

    @pytest.mark.asyncio
    async def test_delete_all_data_requires_confirm(self, client: AsyncClient):
        """DELETE /api/data/all sans confirm=true retourne 400."""
        response = await client.delete("/api/data/all")

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_all_data(self, client: AsyncClient):
        """DELETE /api/data/all?confirm=true supprime toutes les donnees."""
        # Creer des donnees d'abord
        await _create_contact(client, "ContactASupprimer")

        # Confirmer la suppression
        response = await client.delete("/api/data/all?confirm=true")

        assert response.status_code == 200
        result = response.json()
        assert result["deleted"] is True

        # Verifier que les contacts sont supprimes
        list_response = await client.get("/api/memory/contacts")
        assert list_response.status_code == 200
        assert len(list_response.json()) == 0

    @pytest.mark.asyncio
    async def test_delete_all_data_purges_prestations(self, client: AsyncClient):
        """Art. 17 : aucun montant ni financeur ne survit à l'effacement global."""
        contact_id = await _create_contact(client, "ContactPrestation")
        await _create_prestation(client, contact_id)

        response = await client.delete("/api/data/all?confirm=true")

        assert response.status_code == 200
        prestations = await client.get("/api/prestations")
        assert prestations.status_code == 200
        assert prestations.json() == []

    @pytest.mark.asyncio
    async def test_delete_all_purge_fichiers_disque_et_annonce_backups(self, client: AsyncClient):
        """Revue 0.40 : la route vidait les tables et Qdrant mais laissait
        images/ et outputs/ sur disque, et le message affirmait que TOUT était
        supprimé. Attendu : purge des fichiers utilisateur + annonce honnête
        des sauvegardes conservées."""
        from pathlib import Path

        from app.config import settings

        data_dir = Path(settings.data_dir)
        (data_dir / "images").mkdir(parents=True, exist_ok=True)
        (data_dir / "images" / "photo.png").write_bytes(b"pixels")
        (data_dir / "outputs").mkdir(parents=True, exist_ok=True)
        (data_dir / "outputs" / "doc.docx").write_bytes(b"docx")
        # F3 revue 0.40.1 : les fichiers de projets sur disque aussi
        (data_dir / "projects" / "proj-1" / "files").mkdir(parents=True, exist_ok=True)
        (data_dir / "projects" / "proj-1" / "files" / "contrat.pdf").write_bytes(b"pdf")

        backup = await client.post("/api/data/backup", json={"password": "pw-solide-123"})
        assert backup.status_code == 200

        response = await client.delete("/api/data/all?confirm=true")
        assert response.status_code == 200
        result = response.json()

        assert not (data_dir / "images" / "photo.png").exists()
        assert not (data_dir / "outputs" / "doc.docx").exists()
        assert not (data_dir / "projects" / "proj-1" / "files" / "contrat.pdf").exists()
        # Les sauvegardes sont volontairement conservées, et on le DIT.
        assert result["backups_kept"] >= 1
        assert "sauvegarde" in result["note"].lower()

    @pytest.mark.asyncio
    async def test_delete_all_purge_les_commandes_utilisateur(self, client: AsyncClient):
        """B-193 (RB2-023) : la route annonce « toutes tes données » et nomme
        ses deux exceptions (logs d'audit, sauvegardes). Les commandes
        utilisateur, du texte écrit par l'utilisateur, vivaient hors des tables
        balayées - sur le disque, dans commands/user/ - et survivaient sans
        que rien ne l'annonce."""
        from app.services.command_registry import get_command_registry
        from app.services.user_commands import UserCommandsService

        service = UserCommandsService.get_instance()
        service.create_command(name="rb2cmd", description="ma recette", content="Bonjour Marc")
        service.create_command(name="rb2v3", description="autre", content="Relance Sophie")
        assert len(service.list_commands()) == 2
        dossier = service._commands_dir

        # Le registre est chargé une fois au démarrage : sans cette copie en
        # mémoire, effacer les fichiers laisserait les commandes s'afficher
        # dans le menu et la palette jusqu'au prochain lancement.
        registre = get_command_registry()
        await registre._load_user_commands()
        assert registre.get("user-rb2cmd") is not None
        assert registre.get("user-rb2v3") is not None

        response = await client.delete("/api/data/all?confirm=true")
        assert response.status_code == 200

        assert service.list_commands() == []
        assert list(dossier.glob("*.md")) == []
        liste = await client.get("/api/commands/user")
        assert liste.status_code == 200
        assert liste.json() == []
        assert registre.get("user-rb2cmd") is None
        assert registre.get("user-rb2v3") is None

    @pytest.mark.asyncio
    async def test_delete_all_data_purges_documents_sections_pistes(self, client: AsyncClient):
        """DELETE /api/data/all?confirm=true (RGPD Art. 17) purge aussi
        l'atelier documentaire - sinon le droit a l'oubli laisse des
        documents en base apres un 'supprimer toutes mes donnees'."""
        created = await _create_document_with_section_and_piste(client)

        response = await client.delete("/api/data/all?confirm=true")

        assert response.status_code == 200
        assert response.json()["deleted"] is True

        list_response = await client.get("/api/documents")
        assert list_response.status_code == 200
        assert list_response.json() == []

        get_response = await client.get(f"/api/documents/{created['document']['id']}")
        assert get_response.status_code == 404


# ============================================================
# Activity Logs Tests
# ============================================================


class TestActivityLogs:
    """Tests pour les logs d'activite."""

    @pytest.mark.asyncio
    async def test_get_activity_logs(self, client: AsyncClient):
        """GET /api/data/logs retourne une structure paginee de logs."""
        response = await client.get("/api/data/logs")

        assert response.status_code == 200
        data = response.json()

        assert "logs" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert isinstance(data["logs"], list)

    @pytest.mark.asyncio
    async def test_get_activity_logs_after_export(self, client: AsyncClient):
        """Un export genere un log d'activite."""
        # Lancer un export (cela cree un log)
        await client.get("/api/data/export")

        # Verifier que le log existe
        response = await client.get("/api/data/logs")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1


# ============================================================
# Backup Status Tests
# ============================================================


class TestBackupStatus:
    """Tests pour le statut des backups."""

    @pytest.mark.asyncio
    async def test_backup_status(self, client: AsyncClient):
        """GET /api/data/backup/status retourne le statut des sauvegardes."""
        response = await client.get("/api/data/backup/status")

        assert response.status_code == 200
        data = response.json()

        assert "has_backups" in data
        assert "last_backup" in data


# ============================================================
# Import Tests
# ============================================================


class TestDataImport:
    """Tests pour l'import de donnees."""

    @pytest.mark.asyncio
    async def test_import_conversations(self, client: AsyncClient):
        """POST /api/data/import/conversations importe des conversations JSON."""
        import_data = {
            "conversations": [
                {
                    "title": "Conversation importee",
                    "messages": [
                        {
                            "role": "user",
                            "content": "Bonjour THERESE",
                            "created_at": "2026-01-15T10:00:00",
                        },
                        {
                            "role": "assistant",
                            "content": "Bonjour ! Comment puis-je vous aider ?",
                            "created_at": "2026-01-15T10:00:05",
                        },
                    ],
                }
            ]
        }

        response = await client.post("/api/data/import/conversations", json=import_data)

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["imported"]["conversations"] == 1
        assert result["imported"]["messages"] == 2

    @pytest.mark.asyncio
    async def test_import_conversations_invalid_format(self, client: AsyncClient):
        """POST /api/data/import/conversations echoue si le format est invalide."""
        response = await client.post("/api/data/import/conversations", json={
            "invalid_key": "pas de conversations",
        })

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_import_conversations_retablit_identifiants_et_metadonnees(
        self, client: AsyncClient
    ):
        """L'import dédié restaure l'état exporté, pas une conversation ressemblante."""
        payload = {
            "conversations": [
                {
                    "id": "conversation-import-complete",
                    "title": "Conversation restaurée",
                    "summary": "Résumé restauré",
                    "project_id": "project-historique",
                    "memory_scope": "project",
                    "created_at": "2026-08-10T08:00:00+00:00",
                    "updated_at": "2026-08-11T09:00:00+00:00",
                    "messages": [
                        {
                            "id": "message-import-complet",
                            "role": "assistant",
                            "content": "Pièce restaurée",
                            "tokens_in": 7,
                            "tokens_out": 19,
                            "model": "modele-restaure",
                            "provider": "ollama",
                            "extra_data": '{"skill_files":[{"name":"archive.xlsx"}]}',
                            "created_at": "2026-08-10T08:01:00+00:00",
                        }
                    ],
                }
            ]
        }

        response = await client.post("/api/data/import/conversations", json=payload)

        assert response.status_code == 200, response.text
        conversation = await client.get(
            "/api/chat/conversations/conversation-import-complete"
        )
        messages = await client.get(
            "/api/chat/conversations/conversation-import-complete/messages"
        )
        assert conversation.status_code == 200
        assert conversation.json()["summary"] == "Résumé restauré"
        assert conversation.json()["project_id"] == "project-historique"
        assert conversation.json()["memory_scope"] == "project"
        assert conversation.json()["created_at"].startswith("2026-08-10T08:00:00")
        assert conversation.json()["updated_at"].startswith("2026-08-11T09:00:00")
        assert messages.json() == [
            {
                "id": "message-import-complet",
                "conversation_id": "conversation-import-complete",
                "role": "assistant",
                "content": "Pièce restaurée",
                "tokens_in": 7,
                "tokens_out": 19,
                "model": "modele-restaure",
                "provider": "ollama",
                "extra_data": '{"skill_files":[{"name":"archive.xlsx"}]}',
                "created_at": "2026-08-10T08:01:00",
            }
        ]

    @pytest.mark.asyncio
    async def test_import_contacts(self, client: AsyncClient):
        """POST /api/data/import/contacts importe des contacts JSON."""
        import_data = {
            "contacts": [
                {
                    "first_name": "ImporteAlice",
                    "last_name": "Durand",
                    "company": "Import Co",
                    "email": "alice.import@test.fr",
                },
                {
                    "first_name": "ImporteBob",
                    "last_name": "Leroy",
                    "email": "bob.import@test.fr",
                },
            ]
        }

        response = await client.post("/api/data/import/contacts", json=import_data)

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["imported"] == 2

    @pytest.mark.asyncio
    async def test_import_contacts_invalid_format(self, client: AsyncClient):
        """POST /api/data/import/contacts echoue si le format est invalide."""
        response = await client.post("/api/data/import/contacts", json={
            "invalid_key": "pas de contacts",
        })

        assert response.status_code == 400
