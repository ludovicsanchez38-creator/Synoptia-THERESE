"""Lot 7 du cycle 3 (05/09/2026) : correctifs mécaniques confirmés par RP02,
RP03, RP04, RP06 et RP07. Une classe par bug.
"""

from __future__ import annotations

import asyncio
import inspect
import re
from pathlib import Path

import pytest


class TestB470LeCommentaireDuCliquetMypyDitLaVraieBaseline:
    def test_le_chiffre_commente_est_celui_de_la_baseline(self):
        texte = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
        baseline = re.search(r'MYPY_BASELINE: "(\d+)"', texte).group(1)
        bloc = texte[max(0, texte.index('MYPY_BASELINE: "') - 1200): texte.index('MYPY_BASELINE: "')]
        assert baseline in bloc, "le commentaire ne cite plus le chiffre en vigueur"
        assert "1001 = compte mesuré" not in bloc, "le commentaire annonce encore 1001"


class TestB484B515LeNomDUneCommandeEstCeluiDuFichier:
    def _service(self, tmp_path, monkeypatch):
        from app.config import settings
        from app.services.user_commands import UserCommandsService

        monkeypatch.setattr(settings, "data_dir", str(tmp_path))
        return UserCommandsService()

    def test_un_frontmatter_divergent_ne_rend_pas_la_commande_introuvable(self, tmp_path, monkeypatch):
        service = self._service(tmp_path, monkeypatch)
        (tmp_path / "commands" / "user").mkdir(parents=True, exist_ok=True)
        (tmp_path / "commands" / "user" / "resume.md").write_text(
            "---\nname: resum\ndescription: test\n---\nCorps", encoding="utf-8"
        )
        noms = [c.name for c in service.list_commands()]
        assert noms == ["resume"], noms
        assert service.get_command("resume") is not None
        assert service.delete_command("resume") is True

    def test_renommer_renomme_le_fichier_et_survit_au_rechargement(self, tmp_path, monkeypatch):
        service = self._service(tmp_path, monkeypatch)
        service.create_command(name="resume", description="d", content="Corps")

        maj = service.update_command(name="resume", new_name="resume-court")

        assert maj is not None and maj.name == "resume-court"
        assert (tmp_path / "commands" / "user" / "resume-court.md").exists()
        assert not (tmp_path / "commands" / "user" / "resume.md").exists()
        relu = self._service(tmp_path, monkeypatch)
        assert [c.name for c in relu.list_commands()] == ["resume-court"]
        assert relu.get_command("resume-court").content.strip() == "Corps"


class TestB502LesDossiersSpeciauxIMAPSontReconnusEnFrancais:
    class _Dossier:
        def __init__(self, name, flags=(), delim="/"):
            self.name, self.flags, self.delim = name, flags, delim

    class _Boite:
        def __init__(self, dossiers):
            self._dossiers = dossiers

            class _Folder:
                def __init__(inner, d):
                    inner._d = d

                def list(inner):
                    return inner._d

            self.folder = _Folder(dossiers)

    def test_brouillons_par_flag_special_use(self):
        from app.services.email.imap_smtp_provider import ImapSmtpProvider

        boite = self._Boite([self._Dossier("INBOX"), self._Dossier("Brouillons", ("\\Drafts",))])
        assert ImapSmtpProvider._dossier_brouillons(boite) == "Brouillons"

    def test_corbeille_par_nom_francais(self):
        from app.services.email.imap_smtp_provider import ImapSmtpProvider

        boite = self._Boite([self._Dossier("INBOX"), self._Dossier("Corbeille")])
        assert ImapSmtpProvider._dossier_corbeille(boite) == "Corbeille"


class TestB376LEchecDUnCommitNEstPasUnRienACommitter:
    def _git(self, monkeypatch, resultats, chemin):
        from app.services.agents.git_service import GitService

        git = GitService(str(chemin))
        appels = iter(resultats)

        async def faux_run(*_a, **_k):
            return next(appels)

        monkeypatch.setattr(git, "_run", faux_run)
        return git

    @pytest.mark.asyncio
    async def test_rien_a_committer_rend_none(self, tmp_path, monkeypatch):
        git = self._git(monkeypatch, [(0, "", ""), (1, "nothing to commit, working tree clean", "")], tmp_path)
        assert await git.commit("msg") is None

    @pytest.mark.asyncio
    async def test_une_identite_absente_leve_une_cause_lisible(self, tmp_path, monkeypatch):
        from app.services.agents.git_service import GitCommitEchoue

        git = self._git(monkeypatch, [(0, "", ""), (128, "", "Author identity unknown\n*** Please tell me who you are.")], tmp_path)
        with pytest.raises(GitCommitEchoue) as exc:
            await git.commit("msg")
        assert "identité" in str(exc.value).lower()

    def test_le_swarm_distingue_l_echec_du_vide(self):
        from app.services.agents import swarm as module

        source = inspect.getsource(module)
        assert "GitCommitEchoue" in source, "le swarm ne rattrape pas l'échec de commit"


class TestB387B411LeStatutDeFacturationLitLaBaseQuandLeCacheEstVide:
    @pytest.mark.asyncio
    async def test_les_deux_statuts_disent_complet_avec_un_cache_vide(self, client):
        from app.models import database as db_module
        from app.services.user_profile import UserProfile, set_cached_profile, set_user_profile

        async with db_module.AsyncSessionLocal() as session:
            await set_user_profile(
                session,
                UserProfile(name="Marie Exemple", company="Atelier Exemple", address="Manosque", siret="12345678900011"),
            )
        set_cached_profile(None)

        facturation = await client.get("/api/invoices/billing/profile-status")
        assert facturation.status_code == 200, facturation.text
        assert facturation.json()["is_complete"] is True

        set_cached_profile(None)
        accueil = await client.get("/api/dashboard/setup-status")
        assert accueil.status_code == 200, accueil.text
        assert accueil.json()["billing_complete"] is True


class TestB466B497B450LesAppelsBloquantsQuittentLaBoucle:
    def test_la_voix_locale_passe_par_un_thread(self):
        from app.routers import voice as module

        source = inspect.getsource(module)
        assert "await asyncio.to_thread(transcribe_local" in source
        assert "await asyncio.to_thread(synthesize_local" in source

    def test_la_generation_d_image_passe_par_un_thread(self):
        from app.services import image_generator as module

        source = inspect.getsource(module)
        assert source.count("await asyncio.to_thread(") >= 3, source.count("await asyncio.to_thread(")
        assert "result = client.images.generate(" not in source
        assert "response = client.models.generate_content(" not in source

    def test_l_export_crm_passe_par_un_thread(self):
        from app.services import crm_export as module

        source = inspect.getsource(module)
        assert source.count("await asyncio.to_thread(export_to_") == 6, source.count("await asyncio.to_thread(export_to_")


class TestB350LeMenageMCPRespecteLeDelaiDeChaqueRequete:
    @pytest.mark.asyncio
    async def test_une_requete_longue_encore_dans_son_delai_n_est_pas_tuee(self, tmp_path):
        from app.services.mcp_service import MCPService

        service = MCPService(config_path=tmp_path / "mcp.json")
        longue = asyncio.get_running_loop().create_future()
        courte = asyncio.get_running_loop().create_future()
        maintenant = 1000.0
        service._pending_requests[1] = longue
        service._pending_timestamps[1] = maintenant - 90  # posée il y a 90 s
        service._pending_deadlines[1] = maintenant + 30  # délai de 120 s : encore 30 s
        service._pending_requests[2] = courte
        service._pending_timestamps[2] = maintenant - 70
        service._pending_deadlines[2] = maintenant - 10  # délai de 60 s dépassé

        tuees = service._purger_les_requetes_echues(maintenant)

        assert tuees == [2]
        assert not longue.done(), "la requête longue a été tuée avant son délai"
        assert courte.done() and isinstance(courte.exception(), asyncio.TimeoutError)
