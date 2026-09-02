"""
THÉRÈSE v2 - Git Service

Opérations git via asyncio.create_subprocess_exec.
Pattern identique à mcp_service.py (subprocess async).
"""

import asyncio
import logging
import os
import re
import signal
from pathlib import Path

logger = logging.getLogger(__name__)


async def _stop_process(proc: asyncio.subprocess.Process) -> None:
    """Arrête git et ses éventuels descendants sur POSIX."""
    if proc.returncode is not None:
        return
    if os.name == "posix" and proc.pid:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
    else:
        proc.terminate()
    try:
        await asyncio.wait_for(proc.wait(), timeout=2.0)
    except asyncio.TimeoutError:
        if os.name == "posix" and proc.pid:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                return
        else:
            proc.kill()
        await proc.wait()


class GitService:
    """Service git pour les opérations sur le repo source."""

    def __init__(self, repo_path: str | Path) -> None:
        self.repo_path = Path(repo_path)

    async def _run(self, *args: str, timeout: float = 30.0) -> tuple[int, str, str]:
        """Exécute une commande git et retourne (returncode, stdout, stderr)."""
        cmd = ["git", "-C", str(self.repo_path), *args]
        logger.debug(f"Git: {' '.join(cmd)}")
        proc: asyncio.subprocess.Process | None = None
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                start_new_session=os.name == "posix",
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return (
                proc.returncode or 0,
                stdout.decode("utf-8", errors="replace").strip(),
                stderr.decode("utf-8", errors="replace").strip(),
            )
        except asyncio.CancelledError:
            if proc is not None and proc.returncode is None:
                await _stop_process(proc)
            raise
        except asyncio.TimeoutError:
            logger.error(f"Git timeout: {' '.join(cmd)}")
            if proc is not None and proc.returncode is None:
                await _stop_process(proc)
            return 1, "", "Timeout"

    async def is_repo(self) -> bool | None:
        """Vérifie si le chemin est un dépôt git. `None` = contrôle non concluant.

        BUG-163 : `return code == 0` écrasait tous les modes d'échec en `False`.
        Un git qui ne répond pas produisait donc le même verdict qu'un dossier
        réellement dépourvu de `.git`, et l'interface envoyait le testeur
        recloner un dépôt parfaitement sain.

        Le tri-état est étroit à dessein : seule l'impossibilité d'obtenir une
        réponse de git devient `None`. Un code de sortie git légitime reste un
        constat, faute de quoi on masquerait les vrais dépôts manquants.
        """
        code, _, stderr = await self._run("rev-parse", "--is-inside-work-tree")
        if code == 0:
            return True
        if stderr == "Timeout":
            return None
        return False

    #: Identite des commits produits par les agents. Ce sont EUX qui commitent,
    #: pas l'utilisateur : elle est donc posee localement au depot, sans jamais
    #: toucher la configuration globale de la machine.
    IDENTITE_AGENT = ("THÉRÈSE (agent)", "agent@therese.local")

    async def init(self) -> bool:
        """Initialise un nouveau dépôt git, avec une identité locale.

        01/09/2026 : `init` lançait un `git init` nu et `commit` ne posait
        aucune identité. Sur une machine où `user.email` et `user.name` ne
        sont pas configurés globalement, le commit échoue et la méthode rend
        None sans que rien ne le signale. Les agents commitent dans des arbres
        de travail : sur le poste d'un utilisateur qui n'a jamais configuré
        git, leur travail disparaissait.

        Deux tests le disaient déjà, mais ils vivaient dans un dossier que
        personne ne collectait.
        """
        code, _, err = await self._run("init")
        if code != 0:
            logger.error(f"Git init échoué : {err}")
            return False
        nom, courriel = self.IDENTITE_AGENT
        for cle, valeur in (("user.name", nom), ("user.email", courriel)):
            code_config, _, err_config = await self._run("config", "--local", cle, valeur)
            if code_config != 0:
                logger.warning(f"Identité git locale non posée ({cle}) : {err_config}")
        return True

    async def current_branch(self) -> str | None:
        """Le nom de la branche courante. `None` = git n'a pas répondu.

        B-027 : le repli `"main"` était une branche INVENTÉE. Elle repartait
        comme base de `create_worktree` (swarm.py) et satisfaisait la
        comparaison `!= "main"` qui autorise merge et rollback. Même tri-état
        que `is_repo` (BUG-163) : ne jamais confondre « je n'ai pas pu lire »
        avec un constat.
        """
        code, out, _ = await self._run("branch", "--show-current")
        return out if code == 0 else None

    async def create_branch(self, name: str) -> bool:
        """Crée et checkout une nouvelle branche."""
        code, _, err = await self._run("checkout", "-b", name)
        if code != 0:
            logger.error(f"Création branche {name} échouée : {err}")
        return code == 0

    async def create_worktree(self, path: str | Path, branch: str, base: str) -> bool:
        """Crée une branche agent dans un worktree isolé du dépôt utilisateur."""
        code, _, err = await self._run(
            "worktree", "add", "-b", branch, str(Path(path)), base,
        )
        if code != 0:
            logger.error("Création worktree %s échouée : %s", path, err)
        return code == 0

    async def remove_worktree(self, path: str | Path) -> bool:
        """Retire de force uniquement le worktree temporaire de l'agent."""
        code, _, err = await self._run("worktree", "remove", "--force", str(Path(path)))
        if code != 0:
            logger.error("Suppression worktree %s échouée : %s", path, err)
            return False
        await self._run("worktree", "prune")
        return True

    async def checkout(self, branch: str) -> bool:
        """Checkout une branche existante."""
        code, _, err = await self._run("checkout", branch)
        if code != 0:
            logger.error(f"Checkout {branch} échoué : {err}")
        return code == 0

    async def commit(self, message: str, files: list[str] | None = None) -> str | None:
        """Ajoute les fichiers et crée un commit. Retourne le hash ou None."""
        if files:
            for f in files:
                await self._run("add", f)
        else:
            await self._run("add", "-A")

        code, out, err = await self._run("commit", "-m", message)
        if code != 0:
            if "nothing to commit" in (out + err):
                logger.info("Rien à committer")
                return None
            logger.error(f"Commit échoué : {err}")
            return None

        # Extraire le hash
        code, hash_out, _ = await self._run("rev-parse", "HEAD")
        return hash_out if code == 0 else None

    async def diff(self, base: str = "main", head: str = "HEAD") -> str:
        """Retourne le diff unifié entre ``base`` et une branche donnée."""
        code, out, _ = await self._run("diff", f"{base}...{head}")
        return out if code == 0 else ""

    async def diff_stat(self, base: str = "main", head: str = "HEAD") -> str:
        """Retourne le diff stat (résumé des fichiers changés)."""
        code, out, _ = await self._run("diff", "--stat", f"{base}...{head}")
        return out if code == 0 else ""

    async def diff_files(
        self, base: str = "main", head: str = "HEAD"
    ) -> list[dict[str, str]]:
        """Retourne la liste des fichiers changés avec leur type de changement."""
        code, out, _ = await self._run("diff", "--name-status", f"{base}...{head}")
        if code != 0 or not out:
            return []

        files = []
        for line in out.split("\n"):
            if not line.strip():
                continue
            parts = line.split("\t", 1)
            if len(parts) == 2:
                status_code, filepath = parts
                change_type = {
                    "A": "added",
                    "M": "modified",
                    "D": "deleted",
                    "R": "renamed",
                }.get(status_code[0], "modified")
                files.append({"file_path": filepath, "change_type": change_type})
        return files

    async def diff_file(
        self, file_path: str, base: str = "main", head: str = "HEAD"
    ) -> str:
        """Retourne le diff d'un fichier spécifique."""
        code, out, _ = await self._run("diff", f"{base}...{head}", "--", file_path)
        return out if code == 0 else ""

    async def merge(self, branch: str, into: str = "main") -> bool:
        """Merge une branche dans la branche cible."""
        # Checkout la branche cible
        if not await self.checkout(into):
            return False

        code, _, err = await self._run("merge", branch, "--no-ff", "-m", f"Merge {branch}")
        if code != 0:
            logger.error(f"Merge {branch} → {into} échoué : {err}")
            await self._run("merge", "--abort")
            return False
        return True

    async def delete_branch(self, branch: str) -> bool:
        """Supprime une branche locale."""
        code, _, err = await self._run("branch", "-D", branch)
        if code != 0:
            logger.error(f"Suppression branche {branch} échouée : {err}")
        return code == 0

    async def rollback(self, commit_hash: str) -> bool:
        """Annule un commit de merge en conservant le parent principal."""
        code, _, err = await self._run("revert", "-m", "1", "--no-edit", commit_hash)
        if code != 0:
            logger.error(f"Rollback {commit_hash} échoué : {err}")
            await self._run("revert", "--abort")
        return code == 0

    async def stash(self) -> bool:
        """Stash les changements en cours."""
        code, _, _ = await self._run("stash")
        return code == 0

    async def stash_pop(self) -> bool:
        """Restaure le stash."""
        code, _, _ = await self._run("stash", "pop")
        return code == 0

    async def status(self) -> str | None:
        """Le statut court. `None` = git n'a pas répondu, `""` = rien à signaler.

        B-027 : `""` sur échec était indiscernable d'un dépôt réellement
        propre. `git status --short` sort 0 même sur un arbre sale : un code
        non nul n'est donc jamais un constat de propreté.
        """
        code, out, _ = await self._run("status", "--short")
        return out if code == 0 else None

    async def log(self, limit: int = 10) -> list[dict[str, str]]:
        """Retourne les derniers commits."""
        code, out, _ = await self._run(
            "log", f"--max-count={limit}", "--pretty=format:%H|%s|%ai"
        )
        if code != 0 or not out:
            return []

        commits = []
        for line in out.split("\n"):
            parts = line.split("|", 2)
            if len(parts) == 3:
                commits.append({
                    "hash": parts[0],
                    "message": parts[1],
                    "date": parts[2],
                })
        return commits

    async def find_merge_commit(self, branch: str) -> str | None:
        """Retrouve le merge exact d'une branche Atelier, sans limite temporelle."""
        code, out, _ = await self._run(
            "log",
            "--merges",
            "--max-count=1",
            "--format=%H",
            "--fixed-strings",
            f"--grep=Merge {branch}",
            "main",
        )
        return out if code == 0 and out else None

    async def ensure_clean(self) -> bool | None:
        """L'arbre est-il propre ? `None` = le contrôle n'a pas abouti.

        B-027 : `not "".strip()` rendait `True` sur un git muet, et l'Atelier
        lançait la mission sur les modifications non enregistrées de
        l'utilisateur.
        """
        status = await self.status()
        if status is None:
            return None
        return not status.strip()

    async def count_changes(
        self, base: str = "main", head: str = "HEAD"
    ) -> tuple[int, int]:
        """Compte les additions et suppressions par rapport à base."""
        code, out, _ = await self._run("diff", "--shortstat", f"{base}...{head}")
        if code != 0 or not out:
            return 0, 0

        additions = 0
        deletions = 0
        # Format: "3 files changed, 10 insertions(+), 5 deletions(-)"
        add_match = re.search(r"(\d+) insertion", out)
        del_match = re.search(r"(\d+) deletion", out)
        if add_match:
            additions = int(add_match.group(1))
        if del_match:
            deletions = int(del_match.group(1))
        return additions, deletions
