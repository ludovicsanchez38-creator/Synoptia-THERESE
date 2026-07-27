"""
Triage Discord 26/07/2026 - Le message d'erreur du dépôt de l'Atelier était
illisible pour un testeur non développeur.

Dr_logic avait téléchargé l'archive ZIP du dépôt depuis GitHub, décompressée :
elle contient `.gitignore` mais pas l'historique. THÉRÈSE répondait « existe
mais n'est pas un depot Git (.git absent) » (sans accents, sans marche à
suivre), et le testeur en a conclu qu'il manquait un fichier `.gitignore`.
"""
import pytest


class TestMessageDepotAbsent:
    def test_le_message_explique_le_cas_de_l_archive_zip(self):
        from app.routers.agents import repo_error_message

        message = repo_error_message("C:/Users/toto/Documents/THERESE")

        assert "C:/Users/toto/Documents/THERESE" in message
        # Le testeur doit comprendre la cause probable...
        assert "archive" in message.lower() or "zip" in message.lower()
        # ... et ce qu'il doit faire.
        assert "git clone" in message
        # Charte Synoptïa : accents obligatoires.
        assert "depot" not in message
        assert "dépôt" in message

    @pytest.mark.asyncio
    async def test_le_statut_de_l_atelier_sert_ce_message(self, monkeypatch, tmp_path):
        from app.routers import agents as agents_router

        dossier = tmp_path / "THERESE-main"
        dossier.mkdir()
        (dossier / ".gitignore").write_text("node_modules\n", encoding="utf-8")

        class FauxGit:
            def __init__(self, *_args, **_kwargs):
                pass

            async def is_repo(self):
                return False

        monkeypatch.setattr(agents_router, "GitService", FauxGit)

        message = agents_router.repo_error_message(str(dossier))
        assert str(dossier) in message
        assert "git clone" in message
