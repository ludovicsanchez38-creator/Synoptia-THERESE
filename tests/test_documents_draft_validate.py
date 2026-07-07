"""
THÉRÈSE v2 - Tests rédaction SSE (draft) + validation d'une section (tâche B3)

Deux garanties de design vérifiées ici :
- Zéro perte de contenu : le partiel accumulé pendant le stream est persisté
  en base et y RESTE même si le fournisseur LLM plante en cours de route.
- La validation ne bloque jamais : un résumé LLM en échec retombe sur les
  300 premiers caractères du contenu plutôt que de faire échouer la requête.

Le provider LLM est mocké au niveau de `LLMService.stream_response` /
`LLMService.generate_content` - jamais de vrai appel réseau.
"""

import json
from datetime import datetime
from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


async def _create_document(client: AsyncClient, title: str = "Proposition ISOCUBE", brief: str = "Brief du besoin") -> dict:
    response = await client.post("/api/documents", json={"title": title, "brief": brief})
    assert response.status_code == 200, response.text
    return response.json()


async def _create_section(
    client: AsyncClient, document_id: str, title: str, order: float, depth: int = 0
) -> dict:
    response = await client.post(
        f"/api/documents/{document_id}/sections",
        json={"title": title, "brief": "", "order": order, "depth": depth},
    )
    assert response.status_code == 200, response.text
    return response.json()


async def _document_updated_at(client: AsyncClient, document_id: str) -> datetime:
    response = await client.get(f"/api/documents/{document_id}")
    assert response.status_code == 200, response.text
    return datetime.fromisoformat(response.json()["updated_at"])


def _fake_stream_response(chunks: list[str], then_raise: Exception | None = None):
    """Remplace `LLMService.stream_response` par un générateur async minimal.

    Patché DIRECTEMENT sur la classe (`new=`, pas `new_callable=AsyncMock`) :
    une fonction assignée en attribut de classe reste un descripteur Python,
    donc `self` (l'instance LLMService) est bindé automatiquement à l'appel
    `llm_service.stream_response(context, ...)`.
    """

    async def _stream(self, context, **kwargs) -> AsyncGenerator[str, None]:
        for chunk in chunks:
            yield chunk
        if then_raise is not None:
            raise then_raise

    return _stream


def _parse_sse(text: str) -> list[dict]:
    """Découpe le corps SSE (`data: {...}\\n\\n`) en liste d'événements JSON."""
    events = []
    for block in text.strip().split("\n\n"):
        block = block.strip()
        if not block:
            continue
        assert block.startswith("data: "), f"bloc SSE inattendu : {block!r}"
        events.append(json.loads(block[len("data: ") :]))
    return events


class TestDraftSectionStream:
    """POST /api/documents/sections/{id}/draft - rédaction en streaming SSE."""

    @pytest.mark.asyncio
    async def test_draft_nominal_persiste_le_contenu_sans_pistes_et_cree_les_pistes(
        self, client: AsyncClient
    ):
        """Un stream nominal : le contenu persisté est débarrassé du bloc
        PISTES, les pistes sont créées à part, statut 'brouillon', et le
        flux SSE se termine par un chunk 'done'."""
        doc = await _create_document(client)
        section = await _create_section(client, doc["id"], "Financement bancaire", order=10.0)

        chunks = [
            "Les prêts bancaires classiques restent la voie la plus utilisée",
            " par les TPE.\n\nPISTES:\n- Comparer avec le crédit-bail\n",
        ]

        with patch(
            "app.services.llm.LLMService.stream_response",
            new=_fake_stream_response(chunks),
        ):
            response = await client.post(
                f"/api/documents/sections/{section['id']}/draft",
                json={"instruction": None},
            )

        assert response.status_code == 200, response.text
        assert "text/event-stream" in response.headers.get("content-type", "")

        events = _parse_sse(response.text)
        assert [e["type"] for e in events] == ["text", "text", "done"]
        assert events[0]["content"] == chunks[0]
        assert events[1]["content"] == chunks[1]
        assert events[-1]["section_id"] == section["id"]

        detail = await client.get(f"/api/documents/{doc['id']}")
        saved = detail.json()["sections"][0]
        assert saved["status"] == "brouillon"
        assert "PISTES" not in saved["content"]
        assert saved["content"] == (
            "Les prêts bancaires classiques restent la voie la plus utilisée"
            " par les TPE."
        )

        pistes_resp = await client.get(f"/api/documents/{doc['id']}/pistes")
        pistes = pistes_resp.json()
        assert len(pistes) == 1
        assert pistes[0]["texte"] == "Comparer avec le crédit-bail"
        assert pistes[0]["section_origine_id"] == section["id"]
        assert pistes[0]["status"] == "nouvelle"

    @pytest.mark.asyncio
    async def test_draft_nominal_bumps_document_updated_at(self, client: AsyncClient):
        """La liste des documents est triée par updated_at desc : un document
        en cours de rédaction doit remonter - une rédaction persistée sans
        toucher `Document.updated_at` le laisserait figé en place."""
        doc = await _create_document(client)
        section = await _create_section(client, doc["id"], "Financement bancaire", order=10.0)
        before = await _document_updated_at(client, doc["id"])

        with patch(
            "app.services.llm.LLMService.stream_response",
            new=_fake_stream_response(["Contenu rédigé."]),
        ):
            response = await client.post(
                f"/api/documents/sections/{section['id']}/draft",
                json={"instruction": None},
            )
        assert response.status_code == 200, response.text

        after = await _document_updated_at(client, doc["id"])
        assert after > before

    @pytest.mark.asyncio
    async def test_erreur_provider_a_mi_course_garde_le_partiel_en_base(
        self, client: AsyncClient
    ):
        """Zéro perte : une panne provider en cours de stream laisse le
        texte déjà généré en base (statut 'brouillon'), avec un chunk SSE
        'error' au message causal en français."""
        doc = await _create_document(client)
        section = await _create_section(client, doc["id"], "Aides publiques", order=10.0)

        with patch(
            "app.services.llm.LLMService.stream_response",
            new=_fake_stream_response(
                ["Premier fragment rédigé. ", "Second fragment rédigé."],
                then_raise=RuntimeError("panne du fournisseur"),
            ),
        ):
            response = await client.post(
                f"/api/documents/sections/{section['id']}/draft",
                json={"instruction": None},
            )

        assert response.status_code == 200, response.text
        events = _parse_sse(response.text)
        assert [e["type"] for e in events] == ["text", "text", "error"]
        assert "panne du fournisseur" in events[-1]["content"]

        detail = await client.get(f"/api/documents/{doc['id']}")
        saved = detail.json()["sections"][0]
        assert saved["status"] == "brouillon"
        assert saved["content"] == "Premier fragment rédigé. Second fragment rédigé."

        # Aucune piste créée (le stream n'a jamais fini -> pas de parsing PISTES).
        pistes_resp = await client.get(f"/api/documents/{doc['id']}/pistes")
        assert pistes_resp.json() == []

    @pytest.mark.asyncio
    async def test_instruction_sur_section_deja_redigee_inclut_le_contenu_actuel_au_contexte(
        self, client: AsyncClient
    ):
        """Cas « Retoucher » : le contexte envoyé au LLM doit contenir le
        contenu ACTUEL de la section cible, en plus de l'instruction."""
        doc = await _create_document(client)
        section = await _create_section(client, doc["id"], "Financement bancaire", order=10.0)
        await client.patch(
            f"/api/documents/sections/{section['id']}",
            json={"content": "Paragraphe existant à retoucher."},
        )

        captured: dict[str, str] = {}

        def fake_prepare_context(self, messages, **kwargs):
            captured["prompt"] = messages[0].content
            return object()

        async def fake_stream(self, context, **kwargs) -> AsyncGenerator[str, None]:
            yield "Nouveau contenu retouché."

        with (
            patch("app.services.llm.LLMService.prepare_context", new=fake_prepare_context),
            patch("app.services.llm.LLMService.stream_response", new=fake_stream),
        ):
            response = await client.post(
                f"/api/documents/sections/{section['id']}/draft",
                json={"instruction": "Raccourcis le 2e paragraphe."},
            )

        assert response.status_code == 200, response.text
        assert "CONTENU ACTUEL DE LA SECTION" in captured["prompt"]
        assert "Paragraphe existant à retoucher." in captured["prompt"]
        assert "Raccourcis le 2e paragraphe." in captured["prompt"]

    @pytest.mark.asyncio
    async def test_draft_section_introuvable_404(self, client: AsyncClient):
        response = await client.post(
            "/api/documents/sections/id-inexistant/draft",
            json={"instruction": None},
        )
        assert response.status_code == 404


class TestDraftCompletionVide:
    """Revue adversariale lot B, finding 1 (CRITIQUE) : une complétion vide
    (0 chunk, ou bloc PISTES sans aucun contenu réel) ne doit JAMAIS
    écraser le contenu existant d'une section, ni son statut - seul un
    chunk `error` est émis, sans `done`."""

    @pytest.mark.asyncio
    async def test_completion_vide_sur_section_redigee_garde_le_contenu_intact(
        self, client: AsyncClient
    ):
        """Repro confirmée : un provider mocké qui ne yield aucun chunk sur
        une section déjà rédigée ne doit PAS écraser son contenu par du
        vide."""
        doc = await _create_document(client)
        section = await _create_section(client, doc["id"], "Financement bancaire", order=10.0)
        await client.patch(
            f"/api/documents/sections/{section['id']}",
            json={"content": "Contenu déjà rédigé, à préserver."},
        )

        with patch(
            "app.services.llm.LLMService.stream_response",
            new=_fake_stream_response([]),
        ):
            response = await client.post(
                f"/api/documents/sections/{section['id']}/draft",
                json={"instruction": "Continue la rédaction."},
            )

        assert response.status_code == 200, response.text
        events = _parse_sse(response.text)
        assert [e["type"] for e in events] == ["error"]
        assert "aucun contenu" in events[0]["content"].lower()

        detail = await client.get(f"/api/documents/{doc['id']}")
        saved = detail.json()["sections"][0]
        assert saved["content"] == "Contenu déjà rédigé, à préserver."
        assert saved["status"] == "brouillon"

    @pytest.mark.asyncio
    async def test_completion_vide_sur_section_vide_garde_le_statut_vide(
        self, client: AsyncClient
    ):
        """Même repro sur une section jamais rédigée : elle doit rester
        'vide' (pas de brouillon vide + done)."""
        doc = await _create_document(client)
        section = await _create_section(client, doc["id"], "Section neuve", order=10.0)

        with patch(
            "app.services.llm.LLMService.stream_response",
            new=_fake_stream_response([]),
        ):
            response = await client.post(
                f"/api/documents/sections/{section['id']}/draft",
                json={"instruction": None},
            )

        assert response.status_code == 200, response.text
        events = _parse_sse(response.text)
        assert [e["type"] for e in events] == ["error"]

        detail = await client.get(f"/api/documents/{doc['id']}")
        saved = detail.json()["sections"][0]
        assert saved["status"] == "vide"
        assert saved["content"] == ""

    @pytest.mark.asyncio
    async def test_completion_pistes_only_sur_section_redigee_ne_cree_aucune_piste(
        self, client: AsyncClient
    ):
        """Une réponse qui ne contient QUE le bloc PISTES (aucun contenu
        réel avant) doit être traitée comme une complétion vide : contenu
        intact, error, et AUCUNE piste créée."""
        doc = await _create_document(client)
        section = await _create_section(client, doc["id"], "Financement bancaire", order=10.0)
        await client.patch(
            f"/api/documents/sections/{section['id']}",
            json={"content": "Contenu déjà rédigé, à préserver."},
        )

        chunks = ["PISTES:\n", "- Une idée annexe seulement\n"]
        with patch(
            "app.services.llm.LLMService.stream_response",
            new=_fake_stream_response(chunks),
        ):
            response = await client.post(
                f"/api/documents/sections/{section['id']}/draft",
                json={"instruction": "Continue la rédaction."},
            )

        assert response.status_code == 200, response.text
        events = _parse_sse(response.text)
        assert events[-1]["type"] == "error"

        detail = await client.get(f"/api/documents/{doc['id']}")
        saved = detail.json()["sections"][0]
        assert saved["content"] == "Contenu déjà rédigé, à préserver."

        pistes_resp = await client.get(f"/api/documents/{doc['id']}/pistes")
        assert pistes_resp.json() == []


class TestDraftFlushPeriodiqueEtFermeture:
    """Revue adversariale lot B, finding 3 (CRITIQUE, honnêteté) : la
    branche de flush périodique doit vraiment écrire en base PENDANT le
    stream, et une fermeture réelle (GeneratorExit/CancelledError) doit
    persister le partiel via le filet `finally` - sans chunk error (la
    connexion est déjà morte)."""

    @pytest.mark.asyncio
    async def test_flush_periodique_persiste_pendant_le_stream(
        self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ):
        """Preuve que la persistance a lieu PENDANT le stream (pas
        seulement à la fin) : le fake provider lit la section en base,
        depuis une session fraîche, ENTRE deux chunks - avec l'intervalle
        de flush ramené à 0, cette lecture doit déjà voir le premier
        fragment persisté."""
        import app.models.database as db_module
        from app.models.entities import DocumentSection
        from app.routers import documents as documents_router

        monkeypatch.setattr(documents_router, "DRAFT_FLUSH_INTERVAL_SECONDS", 0.0)

        doc = await _create_document(client)
        section = await _create_section(client, doc["id"], "Financement bancaire", order=10.0)

        captured: dict[str, str | None] = {}

        async def fake_stream(self, context, **kwargs) -> AsyncGenerator[str, None]:
            yield "Premier fragment. "
            async with db_module.AsyncSessionLocal() as fresh_session:
                fresh = await fresh_session.get(DocumentSection, section["id"])
                captured["mid_stream_content"] = fresh.content if fresh else None
            yield "Second fragment."

        with patch("app.services.llm.LLMService.stream_response", new=fake_stream):
            response = await client.post(
                f"/api/documents/sections/{section['id']}/draft",
                json={"instruction": None},
            )

        assert response.status_code == 200, response.text
        assert captured["mid_stream_content"] == "Premier fragment. "

    @pytest.mark.asyncio
    async def test_fermeture_generator_exit_persiste_le_partiel(self, client: AsyncClient):
        """Fermeture réelle du flux (déconnexion, fermeture d'app) :
        consomme directement le générateur `_draft_stream`, puis
        `aclose()` (lève GeneratorExit) - le partiel accumulé jusque-là
        doit être en base après coup, sans avoir eu besoin du flush
        périodique (intervalle par défaut, jamais écoulé ici)."""
        import app.models.database as db_module
        from app.models.entities import Document, DocumentSection
        from app.routers.documents import _draft_stream

        doc = await _create_document(client)
        section = await _create_section(client, doc["id"], "Financement bancaire", order=10.0)

        async def fake_stream(self, context, **kwargs) -> AsyncGenerator[str, None]:
            yield "Premier fragment. "
            yield "Second fragment."
            yield "Jamais consommé."

        async with db_module.AsyncSessionLocal() as session:
            document = await session.get(Document, doc["id"])
            target = await session.get(DocumentSection, section["id"])
            assert document is not None and target is not None
            sections = [target]

            with patch("app.services.llm.LLMService.stream_response", new=fake_stream):
                gen = _draft_stream(document, sections, target, None, session)
                await gen.__anext__()  # chunk "Premier fragment. "
                await gen.__anext__()  # chunk "Second fragment."
                await gen.aclose()

        async with db_module.AsyncSessionLocal() as fresh_session:
            reread = await fresh_session.get(DocumentSection, section["id"])
            assert reread is not None
            assert reread.content == "Premier fragment. Second fragment."
            assert reread.status == "brouillon"


class TestDraftRedigeDocumentTermine:
    """Revue adversariale lot B, finding 5 (MINEUR) : retoucher une section
    d'un document déjà 'termine' doit le repasser à 'en_cours' - sinon un
    document affiché comme terminé contiendrait une section 'brouillon'."""

    @pytest.mark.asyncio
    async def test_redraft_section_document_termine_repasse_en_cours(
        self, client: AsyncClient
    ):
        doc = await _create_document(client)
        section = await _create_section(client, doc["id"], "Section unique", order=10.0)
        await client.patch(
            f"/api/documents/sections/{section['id']}",
            json={"content": "Contenu suffisant pour valider."},
        )

        with patch(
            "app.services.llm.LLMService.generate_content",
            new_callable=AsyncMock,
            return_value="Résumé.",
        ):
            validate_resp = await client.post(f"/api/documents/sections/{section['id']}/validate")
        assert validate_resp.status_code == 200, validate_resp.text

        doc_after_validate = await client.get(f"/api/documents/{doc['id']}")
        assert doc_after_validate.json()["status"] == "termine"

        with patch(
            "app.services.llm.LLMService.stream_response",
            new=_fake_stream_response(["Nouveau texte retouché."]),
        ):
            draft_resp = await client.post(
                f"/api/documents/sections/{section['id']}/draft",
                json={"instruction": "Retouche."},
            )
        assert draft_resp.status_code == 200, draft_resp.text

        doc_after_draft = await client.get(f"/api/documents/{doc['id']}")
        assert doc_after_draft.json()["status"] == "en_cours"


class TestValidateSection:
    """POST /api/documents/sections/{id}/validate - résumé + statut 'validee'."""

    @pytest.mark.asyncio
    async def test_validate_nominal_genere_le_resume_et_valide(self, client: AsyncClient):
        doc = await _create_document(client)
        section = await _create_section(client, doc["id"], "Financement bancaire", order=10.0)
        await client.patch(
            f"/api/documents/sections/{section['id']}",
            json={"content": "Un contenu rédigé suffisant pour être validé."},
        )

        with patch(
            "app.services.llm.LLMService.generate_content",
            new_callable=AsyncMock,
            return_value="Résumé généré par le LLM en une phrase.",
        ):
            response = await client.post(f"/api/documents/sections/{section['id']}/validate")

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["status"] == "validee"
        assert body["summary"] == "Résumé généré par le LLM en une phrase."

    @pytest.mark.asyncio
    async def test_validate_llm_en_echec_fallback_300_premiers_caracteres(
        self, client: AsyncClient
    ):
        """La validation ne doit JAMAIS bloquer : un LLM en échec retombe
        sur les 300 premiers caractères, et la section est validée quand
        même."""
        doc = await _create_document(client)
        section = await _create_section(client, doc["id"], "Financement bancaire", order=10.0)
        long_content = "Phrase répétée sur le financement. " * 20
        assert len(long_content) > 300
        await client.patch(
            f"/api/documents/sections/{section['id']}",
            json={"content": long_content},
        )

        with patch(
            "app.services.llm.LLMService.generate_content",
            new_callable=AsyncMock,
            side_effect=RuntimeError("panne LLM"),
        ):
            response = await client.post(f"/api/documents/sections/{section['id']}/validate")

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["status"] == "validee"
        assert body["summary"] == long_content[:300]

    @pytest.mark.asyncio
    async def test_toutes_sections_validees_termine_le_document(self, client: AsyncClient):
        doc = await _create_document(client)
        section_a = await _create_section(client, doc["id"], "Section A", order=10.0)
        section_b = await _create_section(client, doc["id"], "Section B", order=20.0)
        for section in (section_a, section_b):
            await client.patch(
                f"/api/documents/sections/{section['id']}",
                json={"content": "Contenu rédigé."},
            )

        with patch(
            "app.services.llm.LLMService.generate_content",
            new_callable=AsyncMock,
            return_value="Résumé.",
        ):
            first = await client.post(f"/api/documents/sections/{section_a['id']}/validate")
            assert first.status_code == 200, first.text

            mid = await client.get(f"/api/documents/{doc['id']}")
            assert mid.json()["status"] == "en_cours"

            second = await client.post(f"/api/documents/sections/{section_b['id']}/validate")
            assert second.status_code == 200, second.text

        final = await client.get(f"/api/documents/{doc['id']}")
        assert final.json()["status"] == "termine"

    @pytest.mark.asyncio
    async def test_validate_bumps_document_updated_at_even_without_termine_transition(
        self, client: AsyncClient
    ):
        """Valider UNE section parmi plusieurs (document qui reste
        'en_cours', pas de transition vers 'termine') doit quand même faire
        remonter le document dans la liste triée par updated_at desc."""
        doc = await _create_document(client)
        section_a = await _create_section(client, doc["id"], "Section A", order=10.0)
        await _create_section(client, doc["id"], "Section B", order=20.0)
        await client.patch(
            f"/api/documents/sections/{section_a['id']}",
            json={"content": "Contenu rédigé."},
        )
        before = await _document_updated_at(client, doc["id"])

        with patch(
            "app.services.llm.LLMService.generate_content",
            new_callable=AsyncMock,
            return_value="Résumé.",
        ):
            response = await client.post(f"/api/documents/sections/{section_a['id']}/validate")
        assert response.status_code == 200, response.text

        mid = await client.get(f"/api/documents/{doc['id']}")
        assert mid.json()["status"] == "en_cours"  # pas de transition termine

        after = await _document_updated_at(client, doc["id"])
        assert after > before

    @pytest.mark.asyncio
    async def test_validate_section_vide_renvoie_400(self, client: AsyncClient):
        doc = await _create_document(client)
        section = await _create_section(client, doc["id"], "Section vide", order=10.0)

        response = await client.post(f"/api/documents/sections/{section['id']}/validate")

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_validate_section_introuvable_404(self, client: AsyncClient):
        response = await client.post("/api/documents/sections/id-inexistant/validate")
        assert response.status_code == 404
