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


async def _collect_events(db_session, skill_id="docx-pro", llm=None):
    from app.routers.chat import _do_stream_response

    conv = Conversation(id=f"conv-sf-{skill_id}", title="test skill file")
    db_session.add(conv)
    await db_session.commit()

    with patch("app.routers.chat.get_llm_service", return_value=llm or _FakeLLM()), \
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


class TestBUG136MultiFichiers:
    """BUG-136 (11/07, Dr_logic) : deux fichiers générés dans un tour = une
    seule carte. Racine (a) : l'outil generate_document (appelable N fois par
    le modèle) n'émettait JAMAIS skill_file ; racine (b) : extra_data ne
    persistait qu'un slot. Fix : collecteur par tour + skill_files (liste)."""

    @pytest.mark.asyncio
    async def test_fichiers_outil_emis_et_persistes_en_liste(self, db_session):

        from app.services.workspace_tools import (
            drain_generated_files,
            record_generated_file,
            start_generated_files_collection,
        )

        # Le collecteur accumule puis se vide au drain
        start_generated_files_collection()
        record_generated_file({"file_id": "a", "file_name": "a.docx"})
        record_generated_file({"file_id": "b", "file_name": "b.docx"})
        files = drain_generated_files()
        assert [f["file_id"] for f in files] == ["a", "b"]
        assert drain_generated_files() == []

    @pytest.mark.asyncio
    async def test_stream_emet_une_carte_par_fichier_outil(self, db_session):
        """Deux fichiers enregistrés pendant le tour (outil) -> deux événements
        skill_file AVANT done + extra_data.skill_files à deux entrées."""
        import json as _json

        from app.models.entities import Message
        from app.services.workspace_tools import (
            record_generated_file,
        )
        from sqlmodel import select

        class _ToolLLM(_FakeLLM):
            async def stream_response_with_tools(self, context, tools=None):
                # Simule un tour où le modèle a appelé generate_document 2x
                # (le collecteur est posé par le flux, comme en réel).
                record_generated_file(
                    {"skill_id": "docx-pro", "file_id": "f1", "file_name": "un.docx",
                     "file_size": 10, "download_url": "/api/skills/download/f1",
                     "format": "docx", "local_dir": "/tmp"}
                )
                record_generated_file(
                    {"skill_id": "docx-pro", "file_id": "f2", "file_name": "deux.docx",
                     "file_size": 12, "download_url": "/api/skills/download/f2",
                     "format": "docx", "local_dir": "/tmp"}
                )
                yield StreamEvent(type="text", content="Deux fichiers créés.")
                yield StreamEvent(type="done", stop_reason="end_turn")

        events = await _collect_events(db_session, skill_id=None, llm=_ToolLLM())
        types = [e["type"] for e in events]
        assert types.count("skill_file") == 2, f"types : {types}"
        assert types.index("done") > max(
            i for i, t in enumerate(types) if t == "skill_file"
        )
        names = [e["skill_file"]["file_name"] for e in events if e["type"] == "skill_file"]
        assert names == ["un.docx", "deux.docx"]

        done = next(e for e in events if e["type"] == "done")
        result = await db_session.execute(
            select(Message).where(Message.id == done["message_id"])
        )
        msg = result.scalars().first()
        extra = _json.loads(msg.extra_data)
        assert [f["file_id"] for f in extra["skill_files"]] == ["f1", "f2"]
