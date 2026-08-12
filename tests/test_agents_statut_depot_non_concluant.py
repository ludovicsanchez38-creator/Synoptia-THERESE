"""BUG-163 — « erreur sur le dépôt git » qui disparaît toute seule au redémarrage.

Un testeur voyait dans Paramètres > Agents embarqués une erreur affirmant que
son dépôt n'existe pas, avec la marche à suivre pour le recloner. Le lendemain,
sans qu'il ne touche à rien, l'erreur avait disparu.

La cause n'est pas l'intermittence elle-même, c'est la CONFUSION entre deux
états très différents :

- « j'ai vérifié, et il n'y a pas de dépôt » — un constat, qui mérite une
  marche à suivre ;
- « je n'ai pas réussi à vérifier » — une absence de réponse, qui ne mérite
  qu'un « réessaie ».

`GitService._run` renvoie `(1, "", "Timeout")` quand git ne répond pas, et
`is_repo` fait `return code == 0` : un git muet produit exactement le même
`False` qu'un dossier réellement dépourvu de `.git`. Le statut sert alors un
message affirmatif, qui envoie le testeur recloner un dépôt parfaitement sain.

Un outil qui affirme plus que ce qu'il sait fait perdre confiance dans tout ce
qu'il affirme par ailleurs. C'est ce que ces tests verrouillent.
"""
import pytest


class TestUnGitMuetNAffirmeRien:
    @pytest.mark.asyncio
    async def test_is_repo_distingue_le_timeout_de_l_absence(self, tmp_path, monkeypatch):
        """Le socle : sans tri-état ici, aucune couche au-dessus ne peut être honnête."""
        from app.services.agents.git_service import GitService

        git = GitService(str(tmp_path))

        async def faux_run(*_args, **_kwargs):
            return 1, "", "Timeout"

        monkeypatch.setattr(git, "_run", faux_run)

        assert await git.is_repo() is None, (
            "un git qui ne répond pas est rapporté comme « ce n'est pas un dépôt » : "
            "l'absence de réponse est confondue avec une réponse négative"
        )

    @pytest.mark.asyncio
    async def test_is_repo_reste_faux_quand_git_a_vraiment_repondu(
        self, tmp_path, monkeypatch
    ):
        """Verrou : le cas réel de l'archive ZIP doit continuer d'être détecté."""
        from app.services.agents.git_service import GitService

        git = GitService(str(tmp_path))

        async def faux_run(*_args, **_kwargs):
            return 128, "", "fatal: not a git repository"

        monkeypatch.setattr(git, "_run", faux_run)

        assert await git.is_repo() is False


class TestUnControleJamaisLanceNEstPasUnConstat:
    """Le cas réellement atteignable, trouvé en contre-vérifiant le diagnostic.

    La première analyse imputait le bug au timeout de git. Vérification faite,
    ce chemin est hors d'atteinte depuis cet écran : le délai HTTP du frontend
    (30 s, posé avant l'envoi) expire toujours avant celui de git (30 s, posé à
    l'arrivée de la requête, plus l'arrêt du processus et une requête SQL). Le
    testeur aurait vu un bandeau « indisponible », pas la croix rouge.

    Le vrai producteur est en amont : `repo_detected` était initialisé à `False`
    et renvoyé tel quel quand le bloc de vérification n'était pas exécuté du
    tout. L'écran peignait donc « dépôt absent » pour un contrôle jamais lancé.

    Et cela colle au symptôme « disparu au redémarrage » sans aucune
    coïncidence de minutage : `git_available` est mesuré sur le PATH hérité au
    démarrage du backend. Installer Git pendant que THÉRÈSE tourne laisse un
    environnement périmé jusqu'à la fermeture.
    """

    @pytest.mark.asyncio
    async def test_git_introuvable_ne_signifie_pas_depot_absent(
        self, client, tmp_path, monkeypatch
    ):
        import shutil

        from app.routers import agents as agents_router

        depot = tmp_path / "THERESE"
        (depot / ".git").mkdir(parents=True)

        monkeypatch.setattr(agents_router, "_get_source_path", lambda *a, **k: str(depot))
        monkeypatch.setattr(shutil, "which", lambda _nom: None)

        corps = client.get("/api/agents/status").json()

        assert corps.get("repo_detected") is not False, (
            "le dépôt est rapporté absent alors que la vérification n'a même "
            "pas été lancée : git étant introuvable, on ne sait rien du dépôt"
        )
        assert "git clone" not in (corps.get("repo_error") or "").lower()

    @pytest.mark.asyncio
    async def test_aucun_chemin_resolu_ne_signifie_pas_depot_absent(
        self, client, monkeypatch
    ):
        from app.routers import agents as agents_router

        monkeypatch.setattr(agents_router, "_get_source_path", lambda *a, **k: None)

        corps = client.get("/api/agents/status").json()

        assert corps.get("repo_detected") is not False, (
            "sans chemin résolu, aucun contrôle n'a eu lieu : le statut ne peut "
            "pas conclure à l'absence de dépôt"
        )


class TestLeStatutNeProposePasDeReclonerUnDepotSain:
    @pytest.mark.asyncio
    async def test_un_controle_empeche_ne_prescrit_pas_de_git_clone(
        self, client, tmp_path, monkeypatch
    ):
        """Le symptôme vu par le testeur, bout en bout."""
        from app.routers import agents as agents_router

        depot = tmp_path / "THERESE"
        (depot / ".git").mkdir(parents=True)

        class GitQuiNeRepondPas:
            def __init__(self, *_args, **_kwargs):
                pass

            async def is_repo(self):
                return None

            async def current_branch(self):
                return None

            async def ensure_clean(self):
                return None

        monkeypatch.setattr(agents_router, "GitService", GitQuiNeRepondPas)
        monkeypatch.setattr(
            agents_router, "_get_source_path", lambda *a, **k: str(depot)
        )

        reponse = client.get("/api/agents/status")
        assert reponse.status_code == 200
        corps = reponse.json()

        message = (corps.get("repo_error") or "").lower()
        assert "git clone" not in message, (
            "le statut envoie le testeur recloner un dépôt qui existe : "
            "un contrôle sans réponse est présenté comme un constat"
        )
        assert "archive" not in message
        assert message, "un contrôle empêché doit être signalé, pas passé sous silence"
        assert corps.get("repo_detected") is not False, (
            "le dépôt est rapporté comme absent alors qu'il n'a pas pu être vérifié"
        )
