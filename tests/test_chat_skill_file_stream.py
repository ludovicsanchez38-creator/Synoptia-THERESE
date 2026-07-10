"""
Chantier « fichiers générés visibles » (suggestion Dr_logic, 10/07/2026).

Défaut de protocole SSE confirmé en revue : l'auto-exécution du skill (et son
événement `skill_file`) tournait APRÈS le yield de l'événement `done`, alors
que le client coupe la lecture du stream dès `done` (chat.ts) - l'événement
fichier n'atteignait donc JAMAIS l'UI en direct (le testeur découvrait ses
fichiers par hasard au rechargement, via la persistance extra_data).

Spec : `skill_file` émis AVANT `done` ; un échec d'auto-exécution émet un
événement `skill_file_error` visible AVANT `done` (pas seulement un log).
"""
import json
from unittest.mock import AsyncMock, patch

import pytest
from app.models.entities import Conversation
from app.services.providers.base import StreamEvent


class _FakeProvider:
    value = "anthropic"


class _FakeConfig:
    provider = _FakeProvider()
    model = "fake-model"


class _FakeLLM:
    """Service LLM minimal : streame un markdown puis termine."""

    config = _FakeConfig()

    def prepare_context(self, messages, memory_context=None):
        return []

    async def stream_response_with_tools(self, context, tools=None):
        yield StreamEvent(type="text", content="# Doc\n\nContenu du document.")
        yield StreamEvent(type="done", stop_reason="end_turn")


async def _collect_events(db_session, skill_id="docx-pro"):
    from app.routers.chat import _do_stream_response

    conv = Conversation(id=f"conv-sf-{skill_id}", title="test skill file")
    db_session.add(conv)
    await db_session.commit()

    with patch("app.routers.chat.get_llm_service", return_value=_FakeLLM()), \
         patch("app.routers.chat._get_memory_context", AsyncMock(return_value="")):
        raw = ""
        async for chunk in _do_stream_response(
            conv.id,
            "crée-moi un document word de test",
            db_session,
            skill_id=skill_id,
            disable_tools=True,
        ):
            raw += chunk

    events = []
    for block in raw.split("\n\n"):
        block = block.strip()
        if block.startswith("data: "):
            events.append(json.loads(block[len("data: "):]))
    return events


class TestSkillFileAvantDone:
    @pytest.mark.asyncio
    async def test_skill_file_emis_avant_done(self, client, db_session):
        """L'événement fichier doit précéder `done`, sinon le client ne le
        voit jamais (il arrête la lecture sur done)."""
        from app.services.skills import close_skills, init_skills

        await init_skills()
        try:
            events = await _collect_events(db_session)
        finally:
            await close_skills()

        types = [e["type"] for e in events]
        assert "done" in types
        assert "skill_file" in types, f"types reçus : {types}"
        assert types.index("skill_file") < types.index("done")
        skill_event = next(e for e in events if e["type"] == "skill_file")
        assert skill_event["skill_file"]["file_name"].endswith(".docx")
        # Chemin local exposé pour « Afficher dans le dossier » côté desktop.
        assert skill_event["skill_file"].get("local_dir"), "local_dir manquant"

    @pytest.mark.asyncio
    async def test_echec_auto_exec_emet_un_evenement_visible(self, client, db_session):
        """Un échec de génération ne doit plus finir seulement dans les logs :
        l'UI reçoit un événement `skill_file_error` AVANT done."""
        from app.services.skills import close_skills, init_skills
        from app.services.skills.base import SkillExecuteResponse

        await init_skills()
        try:
            fail = SkillExecuteResponse(
                success=False,
                error="disque plein (simulé)",
                skill_id="docx-pro",
                download_url="",
            )
            from app.services import skills as skills_module

            registry = skills_module.get_skills_registry()
            with patch.object(registry, "execute", AsyncMock(return_value=fail)):
                events = await _collect_events(db_session, skill_id="docx-pro")
        finally:
            await close_skills()

        types = [e["type"] for e in events]
        assert "skill_file_error" in types, f"types reçus : {types}"
        assert types.index("skill_file_error") < types.index("done")
        err_event = next(e for e in events if e["type"] == "skill_file_error")
        assert "disque plein" in err_event["content"]
