"""
Triage Discord 26/07/2026 - Le message d'erreur du dépôt de l'Atelier était
illisible pour un testeur non développeur.

Dr_logic avait téléchargé l'archive ZIP du dépôt depuis GitHub, décompressée :
elle contient `.gitignore` mais pas l'historique. THÉRÈSE répondait « existe
mais n'est pas un depot Git (.git absent) » (sans accents, sans marche à
suivre), et le testeur en a conclu qu'il manquait un fichier `.gitignore`.

Revue Soso 27/07 (F7) : la première version proposait de cloner DANS le dossier
existant - or `git clone` refuse une destination non vide, ce qui est justement
le cas d'une archive décompressée. La commande proposée aurait échoué.
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

    def test_le_clone_propose_vise_un_dossier_neuf(self):
        """F7 : cloner dans le dossier existant échouerait (destination non vide)."""
        from app.routers.agents import repo_error_message

        chemin = "C:/Users/toto/Documents/THERESE"
        message = repo_error_message(chemin)

        ligne_clone = next(
            (ligne for ligne in message.splitlines() if "git clone" in ligne), ""
        )
        assert ligne_clone, "aucune commande de clone dans le message"
        assert chemin not in ligne_clone, (
            "la commande clone dans le dossier existant : git refusera une "
            "destination non vide"
        )
        assert "vide" in message.lower() or "neuf" in message.lower() or "nouveau" in message.lower()


class TestStatutAtelierUtiliseLeMessage:
    @pytest.mark.asyncio
    async def test_le_statut_de_l_atelier_sert_ce_message(self, client, tmp_path, monkeypatch):
        """La route /api/agents/status doit renvoyer ce message, pas un autre."""
        from app.routers import agents as agents_router

        dossier = tmp_path / "THERESE-main"
        dossier.mkdir()
        (dossier / ".gitignore").write_text("node_modules\n", encoding="utf-8")

        class FauxGit:
            def __init__(self, *_args, **_kwargs):
                pass

            async def is_repo(self):
                return False

            async def current_branch(self):
                return "main"

            async def ensure_clean(self):
                return True

        monkeypatch.setattr(agents_router, "GitService", FauxGit)
        monkeypatch.setattr(agents_router, "_get_source_path", lambda: str(dossier))

        reponse = await client.get("/api/agents/status")

        assert reponse.status_code == 200, reponse.text
        repo_error = reponse.json().get("repo_error") or ""
        assert "git clone" in repo_error, (
            f"le statut ne sert pas le message explicatif : {repo_error!r}"
        )
