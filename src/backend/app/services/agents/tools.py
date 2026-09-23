"""
THÉRÈSE v2 - Agent Tools

Outils disponibles pour les agents Thérèse et Zézette.
Chaque outil est une fonction async qui retourne un résultat string.
"""

import asyncio
import fnmatch
import logging
import os
import signal
import stat
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

# `regex` plutôt que `re` : un motif émis par le modèle comme `(x+x+)+y` fait
# mouliner `re` sans fin, et un fil d'exécution ne s'annule pas. `regex` accepte
# un délai. Déjà livré avec transformers, déclaré explicitement dans pyproject.
import regex
from app.services.sous_processus import environnement_outils_systeme

logger = logging.getLogger(__name__)

# Commandes autorisées pour run_command
ALLOWED_COMMANDS = {
    "pytest",
    "npm",
    "vitest",
    "ruff",
    "make",
}

# Sous-commandes autorisées pour des commandes spécifiques
ALLOWED_SUBCOMMANDS = {
    "make": {"test", "test-backend", "test-frontend", "lint", "lint-fix", "typecheck"},
    "npm": {"test", "run"},
}

ALLOWED_NPM_SCRIPTS = {"test", "lint", "typecheck", "build"}
ALLOWED_SEARCH_GLOBS = {
    "*.css",
    "*.html",
    "*.js",
    "*.jsx",
    "*.json",
    "*.md",
    "*.py",
    "*.rs",
    "*.toml",
    "*.ts",
    "*.tsx",
    "*.yaml",
    "*.yml",
}

# Recherche des agents (search_codebase), faite en Python et non plus par grep :
# sous Windows, le grep de Git développait lui-même `*.py` contre le dossier
# courant et ne trouvait rien (CI Windows, run 35903233291).
DOSSIERS_EXCLUS_RECHERCHE = frozenset({".git", ".venv", "node_modules"})
SUFFIXES_SENSIBLES = frozenset({".key", ".pem", ".p12", ".pfx"})
TAILLE_MAX_FICHIER_RECHERCHE = 5 * 1024 * 1024
DELAI_RECHERCHE_S = 15.0
MAX_RESULTATS_RECHERCHE = 200


def _nom_de_fichier_sensible(nom: str) -> bool:
    """Fichier que ni read_file ni search_codebase ne rendent (B-969).

    Comparé en minuscules : `.ENV.yaml` ou `CLE.PEM` restent des secrets."""
    nom = nom.lower()
    return nom.startswith(".env") or Path(nom).suffix in SUFFIXES_SENSIBLES


class _DelaiDepasse(Exception):
    """La recherche a dépassé son délai ou a été abandonnée."""


@dataclass
class _ResultatRecherche:
    lignes: list[str] = field(default_factory=list)
    # Messages du système sans chemin : aucun chemin absolu n'atteint le modèle
    # (B-963, B-965).
    erreurs: list[str] = field(default_factory=list)
    trop_volumineux: bool = False


def _message_sans_chemin(exc: OSError) -> str:
    return exc.strerror or type(exc).__name__


# Sans suivre un lien final, sans bloquer sur une FIFO (drapeaux absents : 0).
_OUVERTURE_RECHERCHE = (
    os.O_RDONLY
    | getattr(os, "O_NOFOLLOW", 0)
    | getattr(os, "O_NONBLOCK", 0)
    | getattr(os, "O_BINARY", 0)
)


def _lire_octets(chemin: str, limite: int, identite: tuple[int, int] | None = None) -> bytes | None:
    """Contenu du fichier, ou None s'il dépasse `limite` octets.

    Entre le contrôle du parcours et l'ouverture, un autre processus peut
    remplacer le fichier, ou son dossier, par un lien vers l'extérieur du dépôt.
    On n'ouvre donc pas un lien final, et le fichier ouvert doit être celui qui
    a été contrôlé (`identite` = périphérique et inode relevés au parcours)."""
    descripteur = os.open(chemin, _OUVERTURE_RECHERCHE)
    with os.fdopen(descripteur, "rb") as fichier:
        etat = os.fstat(fichier.fileno())
        if not stat.S_ISREG(etat.st_mode) or (
            identite is not None and (etat.st_dev, etat.st_ino) != identite
        ):
            raise OSError(0, "fichier remplacé pendant la recherche")
        contenu = fichier.read(limite + 1)
    return None if len(contenu) > limite else contenu


def _est_un_lien(entree: os.DirEntry[str]) -> bool:
    """Lien symbolique ou jonction Windows : jamais suivi, comme `grep -r`."""
    if entree.is_symlink():
        return True
    est_jonction = getattr(entree, "is_junction", None)  # Python 3.12+
    if est_jonction is not None:
        return bool(est_jonction())
    jonction = getattr(stat, "IO_REPARSE_TAG_MOUNT_POINT", None)
    return jonction is not None and getattr(entree.stat(follow_symlinks=False), "st_reparse_tag", 0) == jonction


def _identite(etat: os.stat_result) -> tuple[int, int]:
    return (etat.st_dev, etat.st_ino)


def _identite_entree(entree: os.DirEntry[str]) -> tuple[int, int]:
    """Périphérique et inode d'une entrée, lien non suivi.

    Sous Windows, DirEntry.stat laisse l'inode à zéro : il vient alors de
    os.lstat, sinon aucun remplacement ne serait détectable."""
    etat = entree.stat(follow_symlinks=False)
    if not etat.st_ino:
        etat = os.lstat(entree.path)
    return _identite(etat)


def _etat_dossier(chemin: str, est_racine: bool) -> os.stat_result:
    # La racine peut être désignée par un lien (B-961) ; un sous-dossier jamais.
    return os.stat(chemin) if est_racine else os.lstat(chemin)


def _dossier_remplace() -> OSError:
    return OSError(0, "dossier remplacé pendant la recherche")


def _verifier_dossier(chemin: str, est_racine: bool, identite: tuple[int, int]) -> None:
    """Le dossier est toujours celui qui a été contrôlé.

    Le type compte autant que l'inode : un lien créé juste après la
    suppression du dossier récupère souvent son numéro d'inode (ext4)."""
    etat = _etat_dossier(chemin, est_racine)
    if not stat.S_ISDIR(etat.st_mode) or _identite(etat) != identite:
        raise _dossier_remplace()


def _rechercher(
    racine: str,
    pattern: str,
    glob_filter: str,
    max_results: int,
    echeance: float,
    arret: threading.Event,
) -> _ResultatRecherche:
    """Parcourt le dépôt ligne à ligne, hors de la boucle asyncio.

    Mêmes règles que l'ancien `grep -rn` : dossiers exclus, fichiers sensibles
    écartés, liens non suivis, binaires (octet nul) ignorés. S'arrête au
    nombre de résultats, à l'échéance ou quand `arret` est posé."""
    motif = regex.compile(pattern)
    resultat = _ResultatRecherche()
    # Pile (chemin, préfixe relatif, identité attendue) : parcours en
    # profondeur, trié par nom. Un autre processus peut remplacer un dossier ou
    # un fichier par un lien vers l'extérieur pendant le parcours : chaque
    # dossier est comparé à l'identité relevée chez son parent, avant et après
    # son listage, puis encore après l'ouverture de chacun de ses fichiers.
    a_parcourir: list[tuple[str, str, tuple[int, int] | None]] = [(racine, "", None)]
    while a_parcourir:
        dossier, prefixe, attendue = a_parcourir.pop()
        est_racine = attendue is None
        try:
            avant = _etat_dossier(dossier, est_racine)
            identite_dossier = _identite(avant)
            if not stat.S_ISDIR(avant.st_mode) or (
                attendue is not None and identite_dossier != attendue
            ):
                raise _dossier_remplace()
            with os.scandir(dossier) as contenu_du_dossier:
                entrees = sorted(contenu_du_dossier, key=lambda entree: entree.name)
            _verifier_dossier(dossier, est_racine, identite_dossier)
        except OSError as exc:
            resultat.erreurs.append(_message_sans_chemin(exc))
            continue
        sous_dossiers: list[tuple[str, str, tuple[int, int] | None]] = []
        for entree in entrees:
            if arret.is_set() or time.monotonic() >= echeance:
                raise _DelaiDepasse
            relatif = prefixe + entree.name
            try:
                if _est_un_lien(entree):
                    continue
                if entree.is_dir(follow_symlinks=False):
                    if entree.name.lower() not in DOSSIERS_EXCLUS_RECHERCHE:
                        sous_dossiers.append((entree.path, relatif + "/", _identite_entree(entree)))
                    continue
                if (
                    not entree.is_file(follow_symlinks=False)
                    or not fnmatch.fnmatchcase(entree.name, glob_filter)
                    or _nom_de_fichier_sensible(entree.name)
                ):
                    continue
                if entree.stat(follow_symlinks=False).st_size > TAILLE_MAX_FICHIER_RECHERCHE:
                    resultat.trop_volumineux = True
                    continue
                octets = _lire_octets(entree.path, TAILLE_MAX_FICHIER_RECHERCHE, _identite_entree(entree))
                _verifier_dossier(dossier, est_racine, identite_dossier)
            except OSError as exc:
                resultat.erreurs.append(_message_sans_chemin(exc))
                continue
            if octets is None:
                resultat.trop_volumineux = True
                continue
            if not octets or b"\x00" in octets:
                continue  # vide, ou binaire : jamais lu
            try:
                texte = octets.decode("utf-8").removesuffix("\n")
            except UnicodeDecodeError:
                continue  # pas du texte UTF-8 : binaire, comme pour grep en locale UTF-8
            for numero, ligne in enumerate(texte.split("\n"), start=1):
                ligne = ligne.removesuffix("\r")
                restant = echeance - time.monotonic()
                if restant <= 0 or arret.is_set():
                    raise _DelaiDepasse
                try:
                    trouve = motif.search(ligne, timeout=restant)
                except TimeoutError as exc:
                    raise _DelaiDepasse from exc
                if trouve:
                    resultat.lignes.append(f"{relatif}:{numero}:{ligne}")
                    if len(resultat.lignes) >= max_results:
                        return resultat
        a_parcourir.extend(reversed(sous_dossiers))
    return resultat


class _RecherchesBloquees(Exception):
    """Trop de recherches précédentes sont encore bloquées dans une lecture."""


# grep bloqué sur un lecteur réseau était tué ; un fil Python ne peut pas l'être.
# Chaque recherche a donc son fil démon : bloqué, il n'occupe pas le pool partagé
# de l'application (asyncio.to_thread) et ne retient pas sa fermeture. Au-delà de
# ce plafond de fils encore vivants PAR DÉPÔT, la recherche est refusée plutôt
# qu'empilée ; un partage figé ne bloque pas les autres dépôts. La racine sert de
# clé telle quelle : la résoudre toucherait le disque figé depuis la boucle.
MAX_RECHERCHES_EN_VOL = 4
_recherches_en_vol: dict[str, threading.BoundedSemaphore] = {}
_verrou_recherches_en_vol = threading.Lock()


def _places_de_recherche(racine: str) -> threading.BoundedSemaphore:
    with _verrou_recherches_en_vol:
        places = _recherches_en_vol.get(racine)
        if places is None:
            places = _recherches_en_vol[racine] = threading.BoundedSemaphore(MAX_RECHERCHES_EN_VOL)
        return places


async def _rechercher_dans_un_fil_demon(
    racine: str,
    pattern: str,
    glob_filter: str,
    max_results: int,
    echeance: float,
    arret: threading.Event,
) -> _ResultatRecherche:
    places = _places_de_recherche(racine)
    if not places.acquire(blocking=False):
        raise _RecherchesBloquees
    boucle = asyncio.get_running_loop()
    futur: asyncio.Future[_ResultatRecherche] = boucle.create_future()

    def rendre(resultat: _ResultatRecherche | None, erreur: BaseException | None) -> None:
        if futur.done():  # délai dépassé ou annulation : plus personne n'attend
            return
        if erreur is not None:
            futur.set_exception(erreur)
        elif resultat is not None:
            futur.set_result(resultat)

    def executer() -> None:
        resultat: _ResultatRecherche | None = None
        erreur: BaseException | None = None
        try:
            resultat = _rechercher(racine, pattern, glob_filter, max_results, echeance, arret)
        except BaseException as exc:
            erreur = exc
        finally:
            places.release()
        try:
            boucle.call_soon_threadsafe(rendre, resultat, erreur)
        except RuntimeError:
            pass  # boucle déjà fermée : l'application s'arrête

    try:
        threading.Thread(target=executer, name="recherche-agents", daemon=True).start()
    except BaseException:
        places.release()
        raise
    return await futur


async def _stop_process(proc: asyncio.subprocess.Process) -> None:
    """Arrête un processus de commande et ses descendants sur POSIX."""
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


class BranchGuard:
    """Vérifie qu'on est sur une branche agent avant tout write."""

    def __init__(self, git_service) -> None:
        self._git = git_service

    async def check(self) -> None:
        """Lève une erreur si on n'est pas sur une branche agent/."""
        branch = await self._git.current_branch()
        if branch is None:
            # B-027 : `None` = git n'a pas répondu. Une garde d'écriture qui
            # ne sait pas où elle écrit refuse ; elle ne lève pas un
            # AttributeError nu sur `None.startswith`.
            raise PermissionError(
                "Écriture interdite : Git n'a pas répondu, la branche courante "
                "n'a pas pu être lue."
            )
        if not branch.startswith("agent/"):
            raise PermissionError(
                f"Écriture interdite : branche actuelle '{branch}' "
                f"(seules les branches agent/* sont autorisées)"
            )


class AgentToolExecutor:
    """Exécute les outils pour un agent donné."""

    _NO_SOURCE_MSG = (
        "Dépôt non configuré. Le code source de THÉRÈSE n'est pas disponible localement. "
        "L'utilisateur peut configurer le chemin dans Paramètres > Agents > Chemin du code source."
    )

    def __init__(self, source_path: str | None, git_service=None) -> None:
        self.source_path = Path(source_path) if source_path else None
        self._git = git_service
        self._guard = BranchGuard(git_service) if git_service else None

    def _validate_path(self, file_path: str) -> Path:
        """Valide et résout un chemin de fichier dans le source tree."""
        if not self.source_path:
            raise FileNotFoundError(self._NO_SOURCE_MSG)
        requested = Path(file_path)
        if requested.is_absolute():
            raise PermissionError(f"Chemin absolu interdit : {file_path}")
        resolved = (self.source_path / requested).resolve()
        if not resolved.is_relative_to(self.source_path.resolve()):
            raise PermissionError(f"Chemin hors du source tree : {file_path}")
        lowered_parts = {part.lower() for part in requested.parts}
        if ".git" in lowered_parts or _nom_de_fichier_sensible(requested.name):
            raise PermissionError(f"Fichier sensible interdit : {file_path}")
        return resolved

    # --- Outils de lecture (Thérèse + Zézette) ---

    async def read_file(self, file_path: str, max_lines: int = 500) -> str:
        """Lit un fichier du source tree."""
        if not self.source_path:
            return self._NO_SOURCE_MSG
        resolved = self._validate_path(file_path)
        if not resolved.exists():
            return f"Erreur : fichier introuvable : {file_path}"
        if not resolved.is_file():
            return f"Erreur : {file_path} n'est pas un fichier"

        try:
            content = resolved.read_text(encoding="utf-8", errors="replace")
            lines = content.split("\n")
            if len(lines) > max_lines:
                return (
                    "\n".join(lines[:max_lines])
                    + f"\n\n[... tronqué à {max_lines} lignes, total: {len(lines)}]"
                )
            return content
        except Exception as e:
            return f"Erreur de lecture : {e}"

    async def list_directory(self, dir_path: str = ".", max_entries: int = 100) -> str:
        """Liste le contenu d'un répertoire."""
        if not self.source_path:
            return self._NO_SOURCE_MSG
        resolved = self._validate_path(dir_path)
        if not resolved.exists():
            return f"Erreur : répertoire introuvable : {dir_path}"
        if not resolved.is_dir():
            return f"Erreur : {dir_path} n'est pas un répertoire"

        try:
            entries = sorted(resolved.iterdir(), key=lambda p: (not p.is_dir(), p.name))
            lines = []
            for i, entry in enumerate(entries):
                if i >= max_entries:
                    lines.append(f"... et {len(list(resolved.iterdir())) - max_entries} autres")
                    break
                prefix = "📁 " if entry.is_dir() else "📄 "
                # B-961 : entrées résolues par _validate_path, donc racine résolue
                # aussi (dépôt désigné par un lien, /var -> /private/var sous macOS).
                rel = entry.relative_to(self.source_path.resolve())
                lines.append(f"{prefix}{rel}")
            return "\n".join(lines)
        except Exception as e:
            return f"Erreur : {e}"

    async def search_codebase(
        self, pattern: str, glob_filter: str = "*.py", max_results: int = 20
    ) -> str:
        """Recherche un motif (expression régulière) dans le code source.

        Faite en Python, sans lancer grep : le résultat ne dépend plus du poste
        (grep absent, ou grep de Git sous Windows qui développait `*.py`)."""
        if not self.source_path:
            return self._NO_SOURCE_MSG
        if glob_filter not in ALLOWED_SEARCH_GLOBS:
            return f"Erreur : filtre de recherche non autorisé : {glob_filter}"
        arret = threading.Event()
        try:
            limite = max(1, min(int(max_results), MAX_RESULTATS_RECHERCHE))
            echeance = time.monotonic() + DELAI_RECHERCHE_S
            # Hors de la boucle asyncio (BUG-155). Le délai de wait_for couvre
            # un disque qui ne répond plus ; l'échéance, un motif trop coûteux.
            resultat = await asyncio.wait_for(
                _rechercher_dans_un_fil_demon(
                    str(self.source_path), pattern, glob_filter, limite, echeance, arret
                ),
                timeout=DELAI_RECHERCHE_S + 1.0,
            )
        except (_DelaiDepasse, asyncio.TimeoutError):
            return "Erreur : timeout de recherche"
        except _RecherchesBloquees:
            return (
                "Erreur : recherche refusée, des recherches précédentes sont encore "
                "bloquées dans une lecture de fichier (disque lent ou injoignable)"
            )
        except regex.error as exc:
            # B-962 : un motif invalide est une erreur, pas « Aucun résultat ».
            # La syntaxe est celle de Python, plus celle de grep : le dire.
            return (
                f"Erreur : la recherche a échoué (motif invalide : {str(exc)[:200]} ; "
                "syntaxe Python, échapper un caractère spécial littéral : \\( \\[ \\{ \\. \\+)"
            )
        except asyncio.CancelledError:
            raise
        except Exception as e:
            return f"Erreur de recherche : {e}"
        finally:
            # Le fil s'arrête à son prochain point de contrôle (annulation, délai).
            arret.set()

        if not resultat.lignes and resultat.erreurs:
            # B-963 : rien trouvé et des fichiers illisibles, c'est un échec.
            detail = " ; ".join(dict.fromkeys(resultat.erreurs))[:300]
            return f"Erreur : la recherche a échoué ({detail})"
        lignes = resultat.lignes or [f"Aucun résultat pour '{pattern}' dans {glob_filter}"]
        if resultat.lignes and resultat.erreurs:
            # B-963 : les correspondances trouvées ailleurs sont rendues.
            lignes.append("(certains fichiers n'ont pas pu être lus)")
        if resultat.trop_volumineux:
            lignes.append("(certains fichiers trop volumineux n'ont pas été parcourus)")
        return "\n".join(lignes)

    # --- Outils d'écriture (Zézette uniquement) ---

    async def write_file(self, file_path: str, content: str) -> str:
        """Écrit ou modifie un fichier (branche agent uniquement)."""
        if not self.source_path:
            return self._NO_SOURCE_MSG
        try:
            if self._guard:
                await self._guard.check()

            resolved = self._validate_path(file_path)
            resolved.parent.mkdir(parents=True, exist_ok=True)
            resolved.write_text(content, encoding="utf-8")
            return f"Fichier écrit : {file_path} ({len(content)} caractères)"
        except PermissionError as e:
            return f"Permission refusée : {e}"
        except Exception as e:
            return f"Erreur d'écriture : {e}"

    async def run_command(self, command: str) -> str:
        """Exécute une commande autorisée (tests, lint)."""
        if not self.source_path:
            return self._NO_SOURCE_MSG
        try:
            if self._guard:
                await self._guard.check()
        except PermissionError as e:
            return f"Permission refusée : {e}"

        parts = command.strip().split()
        if not parts:
            return "Erreur : commande vide"

        base_cmd = parts[0]
        if base_cmd not in ALLOWED_COMMANDS:
            return f"Erreur : commande '{base_cmd}' non autorisée. Autorisées : {', '.join(sorted(ALLOWED_COMMANDS))}"

        # Vérifier les sous-commandes si nécessaire
        if base_cmd in ALLOWED_SUBCOMMANDS and len(parts) == 1:
            return f"Erreur : une sous-commande '{base_cmd}' autorisée doit être précisée"
        if base_cmd in ALLOWED_SUBCOMMANDS:
            sub = parts[1]
            if sub not in ALLOWED_SUBCOMMANDS[base_cmd]:
                return f"Erreur : sous-commande '{base_cmd} {sub}' non autorisée"
        if base_cmd == "npm":
            if parts[1] == "run":
                if len(parts) != 3 or parts[2] not in ALLOWED_NPM_SCRIPTS:
                    script = parts[2] if len(parts) > 2 else ""
                    return f"Erreur : script npm '{script}' non autorisé"
            elif len(parts) != 2:
                return "Erreur : les arguments supplémentaires de npm sont interdits"
        if base_cmd == "make" and len(parts) != 2:
            return "Erreur : une seule cible make autorisée peut être exécutée"

        proc: asyncio.subprocess.Process | None = None
        try:
            proc = await asyncio.create_subprocess_exec(
                *parts,
                cwd=str(self.source_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=environnement_outils_systeme(PYTHONDONTWRITEBYTECODE="1"),  # B-949
                start_new_session=os.name == "posix",
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120.0)
            out = stdout.decode("utf-8", errors="replace")
            err = stderr.decode("utf-8", errors="replace")

            # Limiter la sortie
            max_chars = 5000
            if len(out) > max_chars:
                out = out[:max_chars] + f"\n... tronqué ({len(out)} chars total)"
            if len(err) > max_chars:
                err = err[:max_chars] + f"\n... tronqué ({len(err)} chars total)"

            result = f"Code retour : {proc.returncode}\n"
            if out:
                result += f"\nStdout:\n{out}"
            if err:
                result += f"\nStderr:\n{err}"
            return result
        except asyncio.CancelledError:
            if proc is not None and proc.returncode is None:
                await _stop_process(proc)
            raise
        except asyncio.TimeoutError:
            if proc is not None and proc.returncode is None:
                await _stop_process(proc)
            return f"Erreur : timeout (120s) pour '{command}'"
        except Exception as e:
            return f"Erreur d'exécution : {e}"

    # --- Outils git (Zézette) ---

    async def git_status(self) -> str:
        """Affiche le statut git."""
        if not self._git:
            return "Erreur : service git non disponible"
        statut = await self._git.status()
        if statut is None:
            # B-027 : « Aucun changement » sur un git muet est un faux vert
            # servi directement au modèle, qui bâtit dessus.
            return "Erreur : Git n'a pas répondu, statut du dépôt inconnu"
        return statut or "Aucun changement"

    async def git_diff(self) -> str:
        """Affiche le diff des changements en cours."""
        if not self._git:
            return "Erreur : service git non disponible"
        ok, diff = await self._git.diff_ou_echec()
        if not ok:
            # B-960 : un échec de git n'est pas un diff vide.
            return f"Erreur : échec de git diff : {diff}"
        if len(diff) > 10000:
            return diff[:10000] + f"\n\n... diff tronqué ({len(diff)} chars total)"
        return diff or "Aucun diff"

    # --- Outil recherche web (agents preconfigures) ---

    async def web_search(self, query: str, max_results: int = 5) -> str:
        """Recherche sur le web via Brave Search ou DuckDuckGo."""
        try:
            from app.services.web_search import (
                RechercheWebRefusee,
                get_web_search_service,
            )

            search_service = get_web_search_service()

            response = await search_service.search(query, max_results=max_results)
            if not response.results:
                return f"Aucun resultat pour '{query}'"

            lines = [f"Resultats pour : {query}\n"]
            for i, r in enumerate(response.results, 1):
                lines.append(f"{i}. **{r.title}**")
                lines.append(f"   {r.url}")
                lines.append(f"   {r.snippet}\n")
            return "\n".join(lines)
        except RechercheWebRefusee as refus:
            # Un choix de l'utilisateur n'est pas une erreur : le préfixer
            # « Erreur » ferait croire à une panne et pousserait l'agent à
            # réessayer.
            logger.info(f"Recherche web refusée pour l'Atelier : {refus}")
            return f"Recherche web coupée par l'utilisateur. {refus}"
        except Exception as e:
            logger.error(f"Erreur web_search: {e}", exc_info=True)
            return f"Erreur de recherche web : {e}"

    # --- Outils Thérèse ---

    async def clarify(self, question: str) -> str:
        """Pose une question de clarification à l'utilisateur. Retourne un placeholder."""
        # Le swarm intercepte cet appel et le transmet à l'utilisateur via SSE
        return f"[CLARIFY]{question}"

    async def create_spec(
        self, title: str, description: str, files_to_change: str = "", acceptance_criteria: str = ""
    ) -> str:
        """Crée une spécification pour Zézette."""
        spec = f"# Spec : {title}\n\n"
        spec += f"## Description\n{description}\n\n"
        if files_to_change:
            spec += f"## Fichiers à modifier\n{files_to_change}\n\n"
        if acceptance_criteria:
            spec += f"## Critères d'acceptation\n{acceptance_criteria}\n\n"
        return f"[SPEC]{spec}"

    async def explain_change(self, summary: str, details: str = "") -> str:
        """Explique un changement à l'utilisateur en langage simple."""
        explanation = summary
        if details:
            explanation += f"\n\n{details}"
        return f"[EXPLAIN]{explanation}"


# Définitions d'outils au format OpenAI function calling (compatible LLM)
THERESE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "clarify",
            "description": "Pose une question de clarification à l'utilisateur",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "La question à poser"},
                },
                "required": ["question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_spec",
            "description": "Crée une spécification technique pour Zézette",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Titre court de la spec"},
                    "description": {
                        "type": "string",
                        "description": "Description détaillée du changement",
                    },
                    "files_to_change": {
                        "type": "string",
                        "description": "Liste des fichiers à modifier",
                    },
                    "acceptance_criteria": {
                        "type": "string",
                        "description": "Critères pour valider le changement",
                    },
                },
                "required": ["title", "description"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "explain_change",
            "description": "Explique un changement à l'utilisateur en langage simple",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "Résumé en 1-2 phrases"},
                    "details": {
                        "type": "string",
                        "description": "Détails supplémentaires (optionnel)",
                    },
                },
                "required": ["summary"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Lit un fichier du code source de Thérèse",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Chemin relatif du fichier"},
                    "max_lines": {
                        "type": "integer",
                        "description": "Nombre max de lignes (défaut: 500)",
                    },
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "Liste le contenu d'un répertoire du code source",
            "parameters": {
                "type": "object",
                "properties": {
                    "dir_path": {
                        "type": "string",
                        "description": "Chemin relatif du répertoire (défaut: racine)",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_codebase",
            "description": "Recherche un pattern dans le code source",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Pattern à rechercher (regex, syntaxe Python : échapper ( et [ littéraux)"},
                    "glob_filter": {
                        "type": "string",
                        "description": "Filtre de fichiers (défaut: *.py)",
                    },
                },
                "required": ["pattern"],
            },
        },
    },
]

ZEZETTE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Lit un fichier du code source",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Chemin relatif du fichier"},
                    "max_lines": {
                        "type": "integer",
                        "description": "Nombre max de lignes (défaut: 500)",
                    },
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Écrit ou modifie un fichier (branche agent uniquement)",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Chemin relatif du fichier"},
                    "content": {"type": "string", "description": "Contenu complet du fichier"},
                },
                "required": ["file_path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "Liste le contenu d'un répertoire",
            "parameters": {
                "type": "object",
                "properties": {
                    "dir_path": {
                        "type": "string",
                        "description": "Chemin relatif (défaut: racine)",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_codebase",
            "description": "Recherche un pattern dans le code source",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Pattern à rechercher (regex, syntaxe Python : échapper ( et [ littéraux)"},
                    "glob_filter": {
                        "type": "string",
                        "description": "Filtre de fichiers (défaut: *.py)",
                    },
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Exécute une commande autorisée (tests, lint)",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Commande à exécuter (ex: make test-backend, pytest tests/)",
                    },
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_status",
            "description": "Affiche le statut git actuel",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_diff",
            "description": "Affiche le diff des changements en cours",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]
