"""Confinement des commandes des agents (B-1153).

Design : `docs/plans/2026-09-24-b1153-bac-a-sable-commandes-agents.md` (V5,
GO de revue le 24/09/2026). Les commandes permises à un agent (`pytest`,
`npm`, `vitest`, `ruff`, `make`) exécutent du code qu'il peut écrire
(`conftest.py`, `pytest.ini`, `package.json`, `Makefile`) : la garde des
arguments (P-100) ne suffit pas, l'exécution elle-même est confinée.

V1 : macOS seulement, par Seatbelt (`/usr/bin/sandbox-exec`) :

- écriture limitée au dossier de travail de l'agent et à un dossier
  temporaire neuf, propre à la commande ;
- aucun réseau, localhost et API du moteur compris ;
- aucune prise sur les autres processus (signaux vers soi et ses enfants
  directs seulement ; pas de création de tâche launchd, pas d'AppleEvent) ;
- lecture refusée du dossier de données de THÉRÈSE (clé maîtresse), des
  dossiers de l'application et des identifiants usuels ;
- environnement construit en liste blanche, jamais copié de celui du moteur.

Ailleurs (Linux, Windows) : refus explicite. Le confinement Linux (Landlock
et seccomp) est une V2, qui exige une liste blanche de lecture.

Fail-closed : une sonde jumelle, jouée une fois par processus, vérifie qu'une
commande témoin réussit hors confinement et échoue dedans (écriture hors du
dossier, connexion locale, signal à un processus extérieur). Toute autre
issue, ou toute erreur de préparation, refuse les commandes.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import shutil
import socket
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

SANDBOX_EXEC = "/usr/bin/sandbox-exec"
IDENTIFIANT_APP = "fr.synoptia.therese"

# Profil Seatbelt. Les chemins arrivent en paramètres (-D), jamais interpolés
# dans le texte : un chemin contenant une guillemet ne peut pas le modifier.
PROFIL_SEATBELT = """(version 1)
(allow default)
(deny file-write* (subpath "/"))
(allow file-write* (subpath (param "DEPOT")) (subpath (param "TMP"))
       (literal "/dev/null") (literal "/dev/zero") (literal "/dev/urandom")
       (regex #"^/dev/fd/"))
(deny network*)
(deny appleevent-send)
(deny job-creation)
(deny mach-lookup (global-name "com.apple.pasteboard.1"))
(deny signal)
(allow signal (target self))
(allow signal (target children))
(deny file-read* (subpath (param "DONNEES"))
       (subpath (string-append (param "HOME") "/Library/Application Support/fr.synoptia.therese"))
       (subpath (string-append (param "HOME") "/Library/Caches/fr.synoptia.therese"))
       (subpath (string-append (param "HOME") "/Library/WebKit/fr.synoptia.therese"))
       (subpath (string-append (param "HOME") "/.ssh"))
       (subpath (string-append (param "HOME") "/.aws"))
       (subpath (string-append (param "HOME") "/.gnupg"))
       (subpath (string-append (param "HOME") "/.docker"))
       (subpath (string-append (param "HOME") "/.kube"))
       (subpath (string-append (param "HOME") "/.config/gh"))
       (subpath (string-append (param "HOME") "/.config/gcloud"))
       (subpath (string-append (param "HOME") "/.config/git"))
       (subpath (string-append (param "HOME") "/.config/pip"))
       (subpath (string-append (param "HOME") "/.claude"))
       (subpath (string-append (param "HOME") "/.cargo/credentials"))
       (literal (string-append (param "HOME") "/.cargo/credentials.toml"))
       (literal (string-append (param "HOME") "/.claude.json"))
       (literal (string-append (param "HOME") "/.netrc"))
       (literal (string-append (param "HOME") "/.npmrc"))
       (literal (string-append (param "HOME") "/.pypirc"))
       (literal (string-append (param "HOME") "/.git-credentials"))
       (literal (string-append (param "HOME") "/.zsh_history"))
       (literal (string-append (param "HOME") "/.bash_history"))
       (subpath (string-append (param "HOME") "/Library/Keychains"))
       (subpath (string-append (param "HOME") "/Library/Cookies"))
       (subpath (string-append (param "HOME") "/Library/Safari"))
       (subpath (string-append (param "HOME") "/Library/Application Support/Google/Chrome"))
       (subpath (string-append (param "HOME") "/Library/Application Support/Firefox")))
"""

# Liste BLANCHE, comme le bac à sable des skills (B-250) : une variable
# ajoutée demain à l'environnement du moteur (clé, jeton, THERESE_DB_KEY,
# SSH_AUTH_SOCK) n'atteint jamais la commande.
_ENV_CONSERVE = frozenset({"PATH", "HOME", "USER", "LOGNAME", "LANG", "LANGUAGE", "TZ", "TERM"})
_ENV_PREFIXES_CONSERVES = ("LC_",)

MESSAGE_REFUS = (
    "Erreur : les commandes des agents sont désactivées sur ce système, faute de "
    "pouvoir les confiner ({raison}). L'agent peut toujours lire et modifier les "
    "fichiers de la mission."
)


@dataclass
class Lancement:
    """Ce qu'il faut pour lancer une commande confinée, et le ménage à faire."""

    argv: list[str]
    env: dict[str, str]
    tmp: Path | None = None
    _nettoye: bool = field(default=False, repr=False)

    def nettoyer(self) -> None:
        """Retire le dossier temporaire de la commande (créé vide par THÉRÈSE)."""
        if self._nettoye:
            return
        self._nettoye = True
        if self.tmp is not None:
            shutil.rmtree(self.tmp, ignore_errors=True)


def _resolu(chemin: str | Path) -> str:
    # Seatbelt compare des chemins réels : /tmp y est /private/tmp.
    return str(Path(chemin).resolve())


def _dossier_de_donnees() -> str:
    from app.config import settings

    return _resolu(settings.data_dir)


def environnement_confine(tmp: Path) -> dict[str, str]:
    """Environnement de la commande, en liste blanche (garantie 3)."""
    env = {
        cle: valeur
        for cle, valeur in os.environ.items()
        if cle in _ENV_CONSERVE or cle.startswith(_ENV_PREFIXES_CONSERVES)
    }
    dossier = str(tmp)
    env.update(
        {
            "TMPDIR": dossier,
            "TMP": dossier,
            "TEMP": dossier,
            "XDG_CACHE_HOME": dossier,
            "XDG_DATA_HOME": dossier,
            "UV_CACHE_DIR": str(tmp / "uv"),
            "npm_config_cache": str(tmp / "npm"),
            "PYTHONDONTWRITEBYTECODE": "1",
        }
    )
    return env


def argv_confine(parts: list[str], depot: str, tmp: str, profil: str | None = None) -> list[str]:
    """Préfixe `sandbox-exec` et paramètres du profil devant la commande."""
    parametres = {
        "DEPOT": depot,
        "TMP": tmp,
        "DONNEES": _dossier_de_donnees(),
        "HOME": _resolu(Path.home()),
    }
    argv = [SANDBOX_EXEC]
    for cle, valeur in parametres.items():
        argv += ["-D", f"{cle}={valeur}"]
    return [*argv, "-p", profil if profil is not None else PROFIL_SEATBELT, *parts]


def preparer_lancement(parts: list[str], depot: str | Path) -> Lancement:
    """Prépare une commande confinée dans `depot`. Lève en cas d'échec :
    l'appelant refuse alors la commande (fail-closed)."""
    tmp = Path(tempfile.mkdtemp(prefix="therese-cmd-")).resolve()
    try:
        return Lancement(argv=argv_confine(parts, _resolu(depot), str(tmp)), env=environnement_confine(tmp), tmp=tmp)
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise


# ------------------------------------------------------------------ sonde

_SONDE_VERROU: asyncio.Lock | None = None
_SONDE_RESULTAT: tuple[bool, str | None] | None = None


def _raison_de_plateforme() -> str | None:
    if sys.platform != "darwin":
        nom = "Windows" if sys.platform.startswith("win") else "Linux" if sys.platform.startswith("linux") else sys.platform
        return f"{nom} : confinement non disponible dans cette version"
    if not Path(SANDBOX_EXEC).exists():
        return "sandbox-exec absent"
    return None


async def _jouer(argv: list[str], env: dict[str, str], cwd: str) -> str:
    proc = await asyncio.create_subprocess_exec(
        *argv,
        cwd=cwd,
        env=env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
        close_fds=True,
    )
    sortie, _ = await asyncio.wait_for(proc.communicate(), timeout=20.0)
    return sortie.decode("utf-8", errors="replace").strip()


async def _sonde_jumelle(profil: str | None = None) -> str | None:
    """Vrai contrôle positif : la même commande témoin réussit hors
    confinement et échoue dedans, sur l'écriture, le réseau et les signaux.
    Rend None si le confinement tient, sinon la raison."""
    dossiers = [Path(tempfile.mkdtemp(prefix=f"therese-sonde-{nom}-")).resolve() for nom in ("depot", "tmp", "dehors")]
    depot, tmp, dehors = dossiers
    serveur = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    temoin: asyncio.subprocess.Process | None = None
    try:
        serveur.bind(("127.0.0.1", 0))
        serveur.listen(4)
        port = serveur.getsockname()[1]
        temoin = await asyncio.create_subprocess_exec("/bin/sleep", "60", close_fds=True)
        script = (
            f'echo x > "{dehors}/temoin"; e=$?; '
            f"/usr/bin/nc -z -w 2 127.0.0.1 {port} >/dev/null 2>&1; r=$?; "
            f"/bin/kill -0 {temoin.pid} >/dev/null 2>&1; s=$?; "
            'echo "$e $r $s"'
        )
        env = environnement_confine(tmp)
        libre = await _jouer(["/bin/sh", "-c", script], env, str(depot))
        if libre != "0 0 0":
            return f"sonde : témoin libre inattendu ({libre})"
        (dehors / "temoin").unlink(missing_ok=True)
        confine = await _jouer(argv_confine(["/bin/sh", "-c", script], str(depot), str(tmp), profil), env, str(depot))
        codes = confine.split()
        if len(codes) != 3 or "0" in codes or (dehors / "temoin").exists():
            return f"sonde : le confinement ne tient pas ({confine or 'aucune sortie'})"
        return None
    except Exception as exc:  # noqa: BLE001 - toute erreur de sonde refuse (fail-closed)
        return f"sonde en échec ({type(exc).__name__})"
    finally:
        serveur.close()
        if temoin is not None and temoin.returncode is None:
            with contextlib.suppress(ProcessLookupError):
                temoin.kill()
            with contextlib.suppress(Exception):
                await temoin.wait()
        for dossier in dossiers:
            shutil.rmtree(dossier, ignore_errors=True)


async def confinement_indisponible() -> str | None:
    """None si les commandes peuvent être confinées, sinon la raison.

    La plateforme est lue à chaque appel ; la sonde, coûteuse, est jouée une
    fois par processus et son verdict gardé, succès comme échec."""
    global _SONDE_VERROU, _SONDE_RESULTAT
    raison = _raison_de_plateforme()
    if raison:
        return raison
    if _SONDE_VERROU is None:
        _SONDE_VERROU = asyncio.Lock()
    async with _SONDE_VERROU:
        if _SONDE_RESULTAT is None:
            refus = await _sonde_jumelle()
            _SONDE_RESULTAT = (refus is None, refus)
            if refus:
                logger.warning("Commandes des agents désactivées : %s", refus)
        return _SONDE_RESULTAT[1]


def _oublier_la_sonde() -> None:
    """Pour les tests : la prochaine demande rejoue la sonde."""
    global _SONDE_VERROU, _SONDE_RESULTAT
    _SONDE_VERROU = None
    _SONDE_RESULTAT = None
