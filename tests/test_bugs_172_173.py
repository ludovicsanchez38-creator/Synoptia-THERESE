"""Bugs Dr_logic du 25/08 (triage 8h33), embarqués dans la 0.47.

BUG-172 : OverflowError volume Windows - couvert dans
test_project_sync_service.py (TestBug172VolumeWindows).
BUG-173 : le texte de l'outil generate_document contenait l'URL
`/api/skills/download/...` que le LLM recopiait en lien markdown - dans
l'app desktop, ce lien s'ouvre en navigateur externe sur tauri.localhost
et meurt. La carte native (BUG-136) est LE chemin de téléchargement.
"""

import pytest


class TestBug173LienMort:
    @pytest.mark.asyncio
    async def test_le_retour_de_generation_ne_contient_pas_d_url(
        self, client, tmp_path, monkeypatch
    ):
        from app.models.database import get_session_context
        from app.services import workspace_tools

        class FauxRegistry:
            output_dir = tmp_path

            async def execute(self, _skill_id, _req, _content):
                from app.services.skills.base import SkillExecuteResponse

                return SkillExecuteResponse(
                    success=True, file_id="f-9", file_name="rapport.docx",
                    file_size=7,
                    download_url="/api/skills/download/f-9",
                )

        monkeypatch.setattr(
            "app.services.skills.get_skills_registry", lambda: FauxRegistry()
        )
        monkeypatch.setattr(
            workspace_tools, "record_generated_file", lambda d: None
        )

        async with get_session_context() as session:
            retour = await workspace_tools.execute_workspace_tool(
                "generate_document",
                {"format": "docx", "content": "Rapport", "title": "Essai"},
                session,
            )

        assert "/api/skills/download" not in retour, (
            "le LLM recopie cette URL en lien markdown : dans l'app "
            "desktop il s'ouvre sur tauri.localhost et meurt (BUG-173)"
        )
        assert "rapport.docx" in retour
