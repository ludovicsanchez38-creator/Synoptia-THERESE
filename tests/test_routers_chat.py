"""
THERESE v2 - Chat Router Tests

Tests for US-CHAT-01 to US-CHAT-10.
"""

import pytest
from httpx import AsyncClient


class TestChatBasics:
    """Tests for basic chat functionality."""

    @pytest.mark.asyncio
    async def test_send_message_streaming(self, client: AsyncClient, sample_chat_message):
        """US-CHAT-02: Streaming response via SSE."""
        # Enable streaming
        sample_chat_message["stream"] = True

        response = await client.post("/api/chat/send", json=sample_chat_message)

        # Streaming endpoint returns text/event-stream
        assert response.status_code in [200, 401, 503]

        if response.status_code == 200:
            assert "text/event-stream" in response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_send_message_non_streaming(self, client: AsyncClient, sample_chat_message):
        """Test non-streaming response."""
        sample_chat_message["stream"] = False

        response = await client.post("/api/chat/send", json=sample_chat_message)

        # May fail without LLM key
        assert response.status_code in [200, 401, 503]

    @pytest.mark.asyncio
    async def test_send_empty_message(self, client: AsyncClient):
        """Test sending empty message."""
        response = await client.post("/api/chat/send", json={
            "message": "",
            "stream": False,
        })

        # Empty string passes Pydantic validation (it's a valid str),
        # but may fail at LLM level (no API key, etc.)
        assert response.status_code in [200, 400, 422, 503]


class TestConversations:
    """Tests for US-CHAT-03: Conversation persistence."""

    @pytest.mark.asyncio
    async def test_list_conversations_empty(self, client: AsyncClient):
        """US-CHAT-03: List conversations when empty."""
        response = await client.get("/api/chat/conversations")

        assert response.status_code == 200
        conversations = response.json()

        assert isinstance(conversations, list)

    @pytest.mark.asyncio
    async def test_get_conversation_nonexistent(self, client: AsyncClient):
        """Test getting a non-existent conversation."""
        response = await client.get("/api/chat/conversations/nonexistent-id")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_conversation_nonexistent(self, client: AsyncClient):
        """Test deleting a non-existent conversation."""
        response = await client.delete("/api/chat/conversations/nonexistent-id")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_rename_conversation_is_persisted(self, client: AsyncClient):
        created = await client.post("/api/chat/conversations", json={"title": "Titre initial"})
        assert created.status_code == 200
        conversation_id = created.json()["id"]

        renamed = await client.patch(
            f"/api/chat/conversations/{conversation_id}",
            json={"title": "  Titre durable  "},
        )
        assert renamed.status_code == 200
        assert renamed.json()["title"] == "Titre durable"

        reloaded = await client.get(f"/api/chat/conversations/{conversation_id}")
        assert reloaded.status_code == 200
        assert reloaded.json()["title"] == "Titre durable"

    @pytest.mark.asyncio
    async def test_rename_conversation_rejects_empty_title(self, client: AsyncClient):
        created = await client.post("/api/chat/conversations", json={})
        conversation_id = created.json()["id"]
        response = await client.patch(
            f"/api/chat/conversations/{conversation_id}",
            json={"title": "   "},
        )
        assert response.status_code == 400


class TestEphemeralConversations:
    """Tests for US-CHAT-04: Ephemeral conversations."""

    @pytest.mark.asyncio
    async def test_create_conversation(self, client: AsyncClient):
        """US-CHAT-04: Create conversation (ephemeral is frontend-only concept)."""
        response = await client.post("/api/chat/conversations", json={})

        assert response.status_code == 200
        conversation = response.json()
        assert "id" in conversation


class TestMemoryIntegration:
    """Tests for US-CHAT-08: User identity recognition."""

    @pytest.mark.asyncio
    async def test_message_includes_memory_context(self, client: AsyncClient, sample_chat_message):
        """Test that messages can include memory context."""
        sample_chat_message["include_memory"] = True

        response = await client.post("/api/chat/send", json=sample_chat_message)

        # Request should be accepted
        assert response.status_code in [200, 401, 503]

    @pytest.mark.asyncio
    async def test_message_excludes_memory_context(self, client: AsyncClient, sample_chat_message):
        """Test that memory context can be disabled."""
        sample_chat_message["include_memory"] = False

        response = await client.post("/api/chat/send", json=sample_chat_message)

        assert response.status_code in [200, 401, 503]


class TestSlashCommands:
    """Tests for US-CHAT-07: Slash commands."""

    @pytest.mark.asyncio
    async def test_fichier_command(self, client: AsyncClient):
        """US-CHAT-07: Test /fichier command."""
        response = await client.post("/api/chat/send", json={
            "message": "/fichier /tmp/test.txt",
            "stream": False,
        })

        # Command should be processed (may fail for other reasons)
        assert response.status_code in [200, 400, 401, 404, 503]

    @pytest.mark.asyncio
    async def test_analyse_command(self, client: AsyncClient):
        """US-CHAT-07: Test /analyse command."""
        response = await client.post("/api/chat/send", json={
            "message": "/analyse /tmp/test.txt",
            "stream": False,
        })

        assert response.status_code in [200, 400, 401, 404, 503]

    @pytest.mark.asyncio
    async def test_directive_inline_pure_sans_llm(self, client: AsyncClient):
        """Directives inline [action: ...] seules : réponse déterministe, zéro appel LLM."""
        response = await client.post("/api/chat/send", json={
            "message": "[contact: Ines Testinline email=ines@test.fr]",
            "stream": False,
        })

        assert response.status_code == 200
        data = response.json()
        assert "Ines" in data["content"]
        assert "créé" in data["content"] or "déjà en mémoire" in data["content"]

    @pytest.mark.asyncio
    async def test_directives_inline_multiples_cumulees(self, client: AsyncClient):
        """Plusieurs directives dans un même message : toutes exécutées, confirmations listées."""
        response = await client.post("/api/chat/send", json={
            "message": "[contact: Paul Testinline]\n[projet: Chantier Testinline budget=1500]",
            "stream": False,
        })

        assert response.status_code == 200
        content = response.json()["content"]
        assert "Paul" in content
        assert "Chantier Testinline" in content


class TestConversationExport:
    """Export d'une conversation en fichier téléchargeable (md/docx)."""

    @pytest.mark.asyncio
    async def test_export_markdown_et_telechargement(self, client: AsyncClient):
        # Créer une conversation avec un échange déterministe (sans LLM)
        response = await client.post("/api/chat/send", json={
            "message": "[contact: Zoe Testexport]",
            "stream": False,
        })
        assert response.status_code == 200
        conv_id = response.json()["conversation_id"]

        # Export markdown
        response = await client.get(f"/api/chat/conversations/{conv_id}/export?format=md")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["file_name"].endswith(".md")

        # Le fichier est servi par le circuit des documents générés
        response = await client.get(data["download_url"])
        assert response.status_code == 200
        assert "Zoe" in response.text

    @pytest.mark.asyncio
    async def test_export_format_inconnu_400(self, client: AsyncClient):
        response = await client.get("/api/chat/conversations/nimporte/export?format=pdf")
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_export_conversation_inconnue_404(self, client: AsyncClient):
        response = await client.get("/api/chat/conversations/inexistante/export?format=md")
        assert response.status_code == 404


class TestLLMProviders:
    """Tests for US-CHAT-01: Multiple LLM providers."""

    @pytest.mark.asyncio
    async def test_available_providers(self, client: AsyncClient):
        """US-CHAT-01: Check available providers."""
        response = await client.get("/api/config/llm")

        assert response.status_code == 200
        config = response.json()

        # Should list available providers
        assert "provider" in config

    @pytest.mark.asyncio
    async def test_chat_with_specific_provider(self, client: AsyncClient, sample_chat_message):
        """Test chat with specific provider selected."""
        # First set provider
        await client.post("/api/config/llm", json={
            "provider": "anthropic",
            "model": "claude-sonnet-4-5-20250929",
        })

        response = await client.post("/api/chat/send", json=sample_chat_message)

        # Should use selected provider
        assert response.status_code in [200, 401, 503]


class TestWebSearchIntegration:
    """Tests for US-CHAT-06: Web search integration."""

    @pytest.mark.asyncio
    async def test_chat_with_web_search_enabled(self, client: AsyncClient, sample_chat_message):
        """US-CHAT-06: Chat with web search enabled."""
        # Enable web search
        await client.post("/api/config/web-search?enabled=true")

        sample_chat_message["message"] = "Quelle est la meteo aujourd'hui ?"
        response = await client.post("/api/chat/send", json=sample_chat_message)

        assert response.status_code in [200, 401, 503]


class TestMCPToolCalling:
    """Tests for US-CHAT-05: MCP tool calling."""

    @pytest.mark.asyncio
    async def test_chat_with_tools(
        self, client: AsyncClient, sample_chat_message, monkeypatch
    ):
        """US-CHAT-05 : le chat accepte une demande qui mobilise des outils.

        Ce test appelait un VRAI fournisseur. Sur une machine où un Ollama local
        écoute (le cas de plusieurs postes de développement), il partait vers le
        modèle réel : durée imprévisible, et un 500 selon l'état du serveur. Il
        signalait alors une panne qui n'existait pas, et pouvait en masquer une
        vraie en acceptant trois codes de statut différents.

        Il est désormais hermétique — aucun appel sortant — et n'accepte plus
        qu'une seule issue.
        """
        from app.routers import chat as chat_router

        async def faux_flux(*args, **kwargs):
            for morceau in ("Voici ", "les fichiers."):
                yield morceau

        class FauxService:
            # `provider` est un enum côté production : le chat lit `.value`.
            # Une simple chaîne ici produisait un 500 par AttributeError, et
            # c'était exactement le faux signal que ce test envoyait.
            config = type(
                "C", (),
                {"provider": type("P", (), {"value": "ollama"})(), "model": "test"},
            )()

            def prepare_context(self, messages, system_prompt=None, memory_context=None):
                return type("Ctx", (), {"messages": messages, "system_prompt": system_prompt})()

            async def stream_response(self, *args, **kwargs):
                async for morceau in faux_flux():
                    yield morceau

        monkeypatch.setattr(chat_router, "get_llm_service", lambda: FauxService())

        sample_chat_message["message"] = "Liste les fichiers dans /tmp"
        response = await client.post("/api/chat/send", json=sample_chat_message)

        assert response.status_code == 200, (
            f"la demande a echoue ({response.status_code}) alors qu'aucun "
            "fournisseur reel n'est sollicite : la panne est dans le chat"
        )


class TestEntityExtraction:
    """Tests for US-CHAT-09: Automatic entity extraction."""

    @pytest.mark.asyncio
    async def test_message_with_contact_mention(self, client: AsyncClient):
        """US-CHAT-09: Message mentioning a person."""
        response = await client.post("/api/chat/send", json={
            "message": "J'ai rencontre Pierre Dupont de Microsoft aujourd'hui",
            "stream": True,
        })

        # Request should be accepted
        assert response.status_code in [200, 401, 503]


class TestConversationHistory:
    """Tests for conversation message history."""

    @pytest.mark.asyncio
    async def test_get_conversation_messages(self, client: AsyncClient):
        """Test getting messages from a non-existent conversation."""
        response = await client.get("/api/chat/conversations/test-id/messages")

        # Endpoint returns empty list for non-existent conversation (no 404 check)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_conversation_pagination(self, client: AsyncClient):
        """Test conversation list pagination."""
        response = await client.get("/api/chat/conversations?limit=10&offset=0")

        assert response.status_code == 200


class TestChatErrors:
    """Tests for chat error handling."""

    @pytest.mark.asyncio
    async def test_missing_message_field(self, client: AsyncClient):
        """Test request without message field."""
        response = await client.post("/api/chat/send", json={
            "stream": True,
        })

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_conversation_id(self, client: AsyncClient):
        """Test with invalid conversation ID format."""
        response = await client.post("/api/chat/send", json={
            "message": "Test",
            "conversation_id": "invalid-format-!!!",
        })

        # Should either accept or reject gracefully
        assert response.status_code in [200, 400, 401, 404, 422, 503]


# B-055 — une conversation supprimée ne doit pas survivre dans l'index
class TestSuppressionEtIndexDeRecherche:
    """`POST /conversations` inscrit le titre dans l'index de recherche ; la
    suppression doit l'en retirer.

    Sans ce retrait, `GET /api/perf/conversations/search` continue de rendre la
    conversation avec `source: "index"` : un fantôme que la base ne connaît
    plus, dont le titre reste lisible en clair.
    """

    @pytest.mark.asyncio
    async def test_supprimer_une_conversation_la_retire_de_l_index(self, client: AsyncClient):
        import uuid

        # Titre unique : l'index est un singleton de process, un voisin ne doit
        # ni peupler ni vider ce mot à notre place.
        titre = f"zorglub-{uuid.uuid4().hex[:12]}"

        creation = await client.post("/api/chat/conversations", json={"title": titre})
        assert creation.status_code == 200, creation.text[:200]
        conversation_id = creation.json()["id"]

        avant = await client.get(f"/api/perf/conversations/search?q={titre}")
        assert avant.status_code == 200, avant.text[:200]
        corps_avant = avant.json()
        assert corps_avant["source"] == "index", corps_avant
        assert conversation_id in [r["id"] for r in corps_avant["results"]]

        suppression = await client.delete(f"/api/chat/conversations/{conversation_id}")
        assert suppression.status_code == 200, suppression.text[:200]
        assert suppression.json()["deleted"] is True

        apres = await client.get(f"/api/perf/conversations/search?q={titre}")
        assert apres.status_code == 200, apres.text[:200]
        corps_apres = apres.json()
        assert conversation_id not in [r["id"] for r in corps_apres["results"]], (
            "la conversation supprimée sort encore de la recherche "
            f"(source={corps_apres['source']}) : {corps_apres}"
        )
        # Le titre lui-même ne doit plus être consultable via l'index.
        assert titre not in [r["title"] for r in corps_apres["results"]], corps_apres


# ---------------------------------------------------------------------------
# B-224 : le modèle ignore qu'un outil sensible n'est que MIS EN FILE.
#
# Le portillon de confirmation fonctionne (`requires_confirmation`) : l'action
# est enregistrée, une carte s'affiche, rien ne s'exécute. Mais RIEN, dans le
# prompt système, n'apprend cela au modèle : il appelle `generate_document`,
# croit avoir agi, et écrit au passé composé en fabriquant un lien de
# téléchargement mort. Le bloc « capacités » (chat.py) ne mentionne la
# confirmation nulle part.
#
# La garde ci-dessous ne cherche pas une phrase : elle exige que le prompt
# réellement transmis au fournisseur porte l'annonce DÉRIVÉE de la
# classification des outils du tour. Un texte constant appendu sans condition
# échoue au second test.
# ---------------------------------------------------------------------------


class TestPromptOutilsSousConfirmation:
    """B-224 — le prompt annonce les outils qui attendent une validation."""

    @staticmethod
    async def _prompt_transmis(db_session):
        """Le system prompt VU par le fournisseur, et les outils du tour."""
        from types import SimpleNamespace
        from unittest.mock import AsyncMock, patch

        from app.models.entities import Conversation
        from app.routers.chat import _do_stream_response
        from app.services.providers.base import StreamEvent

        capture: dict = {}

        class _FauxLLM:
            config = SimpleNamespace(
                provider=SimpleNamespace(value="anthropic"), model="faux"
            )

            def prepare_context(self, messages, memory_context=None):
                return SimpleNamespace(messages=[], system_prompt="")

            async def stream_response_with_tools(self, context, tools=None):
                capture["system_prompt"] = context.system_prompt
                capture["tool_names"] = [
                    t.get("function", {}).get("name", "")
                    for t in (tools or [])
                    if t.get("type") == "function"
                ]
                yield StreamEvent(type="text", content="D'accord.")
                yield StreamEvent(type="done", stop_reason="end_turn")

        conv = Conversation(id="conv-b224", title="B-224")
        db_session.add(conv)
        await db_session.commit()

        with patch("app.routers.chat.get_llm_service", return_value=_FauxLLM()), patch(
            "app.routers.chat._get_memory_context", AsyncMock(return_value="")
        ):
            async for _ in _do_stream_response(
                conv.id, "Génère un document Word listant mes tâches.", db_session
            ):
                pass

        assert "system_prompt" in capture, (
            "le fournisseur n'a jamais été appelé : la capture ne prouve rien"
        )
        assert capture["tool_names"], (
            "aucun outil n'a été proposé au modèle : le bloc de capacités n'a "
            "même pas été construit, ce test ne surveille rien"
        )
        return capture["system_prompt"], capture["tool_names"]

    @pytest.mark.asyncio
    async def test_prompt_annonce_les_outils_en_attente_de_confirmation(
        self, client, db_session
    ):
        """Le prompt transmis porte l'annonce, dérivée des outils du tour.

        Sabotage de référence : retirer la ligne qui ajoute le bloc au
        system_prompt dans chat.py doit rougir ce test.
        """
        from app.services.tool_confirmations import (
            bloc_outils_sous_confirmation,
            requires_confirmation,
        )

        prompt, noms = await self._prompt_transmis(db_session)

        attendus = sorted(n for n in noms if requires_confirmation(n))
        assert attendus, (
            "aucun outil sensible dans ce tour : le cas testé n'existe pas"
        )
        bloc = bloc_outils_sous_confirmation(noms)
        assert bloc, "le bloc dérivé des outils du tour est vide"
        assert bloc in prompt, (
            "le prompt transmis au fournisseur n'annonce pas les outils mis en "
            f"attente de validation ({attendus}) : le modèle croit avoir agi"
        )

    @pytest.mark.asyncio
    async def test_le_bloc_ne_nomme_que_les_outils_soumis_a_validation(self):
        """Le contenu suit la classification, il n'est pas un texte figé."""
        from app.services.contexte_execution import LECTURE_SEULE, classe_de
        from app.services.tool_confirmations import bloc_outils_sous_confirmation

        outils = ["read_contact", "search_files", "generate_document", "send_email"]
        bloc = bloc_outils_sous_confirmation(outils)
        nommes = {o for o in outils if o in bloc}
        assert nommes == {"generate_document", "send_email"}, (
            f"le bloc nomme {sorted(nommes)} au lieu des seuls outils sensibles"
        )
        lectures = [o for o in outils if classe_de(o) == LECTURE_SEULE]
        assert bloc_outils_sous_confirmation(lectures) == "", (
            "un tour sans aucun outil sensible ne doit rien annoncer : sinon "
            "le bloc est un texte constant, pas une conséquence du classement"
        )

    @pytest.mark.asyncio
    async def test_le_bloc_interdit_de_promettre_le_resultat_sans_interdire_l_appel(
        self,
    ):
        """Deux erreurs symétriques à éviter, la seconde a déjà coûté BUG-130.

        Dire « ce n'est pas exécuté » sans dire « appelle quand même » pousse
        le modèle à rédiger le document en clair dans le chat au lieu
        d'appeler l'outil.
        """
        from app.services.tool_confirmations import bloc_outils_sous_confirmation

        bloc = bloc_outils_sous_confirmation(["generate_document"]).lower()
        assert "appelle" in bloc, "le bloc doit maintenir l'ordre d'appeler l'outil"
        assert "lien" in bloc, "le bloc doit interdire de fabriquer un lien"
        assert "valid" in bloc or "confirm" in bloc, (
            "le bloc doit dire que l'action attend une validation de l'utilisateur"
        )
