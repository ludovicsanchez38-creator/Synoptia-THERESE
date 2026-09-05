"""
THERESE v2 - Path Security Service

Validation des chemins de fichiers pour empecher le path traversal
et l'acces aux fichiers sensibles.
"""

import logging
import os
import tempfile
from collections.abc import Iterable, Mapping
from functools import lru_cache
from pathlib import Path, PurePath

logger = logging.getLogger(__name__)

# Repertoires interdits (relatifs au home directory)
DENIED_DIRECTORIES = [
    ".ssh",
    ".aws",
    ".gnupg",
    ".therese/.encryption_key",
    ".env",
]

# Patterns de fichiers sensibles
DENIED_PATTERNS = [
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "*.db",
    "*.sqlite",
    "*.sqlite3",
    ".env",
    ".env.*",
    ".encryption_key",
    ".session_token",
    "id_rsa",
    "id_ed25519",
    "id_ecdsa",
    "*.keystore",
    "credentials.json",
    "token.json",
]

# Repertoires systeme interdits (chemins absolus), famille POSIX.
DENIED_ABSOLUTE_PATHS_POSIX = [
    "/etc",
    "/var",
    "/usr",
    "/sys",
    "/proc",
    "/dev",
]

# B-255 : la liste n'existait que sous sa forme POSIX, et huit tests de la
# liste noire etaient rouges sur windows-latest (run 33668043946). Sous Windows,
# `Path("/etc/hosts").resolve()` donne `C:\etc\hosts` : un chemin qui ne
# designe aucun repertoire systeme, donc une garde qui ne garde rien. Les
# racines sont CHOISIES par plateforme et non cumulees : ajouter `/etc` a un
# Windows n'y protegerait rien tout en donnant l'illusion d'une couverture.
# Ces valeurs sont les defauts ; l'environnement les complete a l'execution,
# une installation pouvant vivre ailleurs que sur C:.
DENIED_ABSOLUTE_PATHS_WINDOWS = [
    r"C:\Windows",
    r"C:\Windows\System32",
    r"C:\ProgramData",
]

# Variables d'environnement qui designent une racine systeme Windows.
# `SystemRoot` et `windir` pointent le dossier Windows lui-meme (d'ou l'on
# derive System32), `ProgramData` les donnees d'application de la machine.
_VARIABLES_RACINES_WINDOWS = ("SystemRoot", "windir", "ProgramData")


def _racines_systeme(nom_os: str, environnement: Mapping[str, str]) -> tuple[str, ...]:
    """Les racines interdites de la plateforme, avant resolution.

    `os.name` et l'environnement sont recus en PARAMETRES plutot que lus :
    c'est ce qui rend la branche Windows verifiable depuis un Mac, ou aucun
    `C:\\Windows` n'existe et ou l'on ne peut meme pas instancier un
    `WindowsPath`.
    """
    if nom_os != "nt":
        return tuple(DENIED_ABSOLUTE_PATHS_POSIX)

    candidates = list(DENIED_ABSOLUTE_PATHS_WINDOWS)
    for variable in _VARIABLES_RACINES_WINDOWS:
        racine = (environnement.get(variable) or "").strip().rstrip("\\/")
        # `SystemRoot=C:\` donnerait la racine `C:`, soit le disque entier :
        # une garde qui refuse tout n'est plus une garde, c'est une panne.
        if not racine or racine.endswith(":"):
            continue
        candidates.append(racine)
        if variable != "ProgramData":
            candidates.append(racine + "\\System32")

    vues: set[str] = set()
    racines: list[str] = []
    for candidate in candidates:
        # La casse ne distingue pas deux chemins sous Windows : `C:\Windows`
        # et `C:\WINDOWS` sont la meme racine, inutile de la garder deux fois.
        cle = candidate.casefold()
        if cle in vues:
            continue
        vues.add(cle)
        racines.append(candidate)
    return tuple(racines)


def _sous_une_racine(chemin: PurePath, racines: Iterable[PurePath]) -> bool:
    """L'appartenance se juge en COMPOSANTS de chemin, pas en prefixe de chaine.

    B-255, seconde cause du rouge Windows : la comparaison etait
    `chemin_str.startswith(racine + "/")`. Le separateur POSIX y est ecrit en
    dur, si bien que sous Windows aucun FICHIER sous une racine interdite ne
    pouvait correspondre - seule la racine elle-meme, par egalite. C'est
    pourquoi le test des racines passait pendant que ses enfants echouaient,
    et ajouter des racines Windows sans corriger ce point les aurait laissees
    inertes. `is_relative_to` compare des composants : `/etcetera` ne tombe
    donc pas sous `/etc`, ni `C:\\WindowsApps` sous `C:\\Windows`, et la casse
    suit la regle de la plateforme du chemin.
    """
    return any(chemin.is_relative_to(racine) for racine in racines)


# Instantane pris a l'import pour la plateforme courante : c'est la liste que
# lisent les appelants et les tests. La verite d'execution reste
# `_racines_interdites()`, qui redemande `_racines_systeme(os.name, os.environ)`
# a chaque recalcul.
DENIED_ABSOLUTE_PATHS = list(_racines_systeme(os.name, os.environ))


def _dans_le_dossier_temporaire(chemin: Path) -> bool:
    """Le dossier temporaire du processus echappe a la liste noire.

    Sur macOS il vit sous /var/folders, soit /private/var une fois resolu :
    sans cette exception, fermer la faille des racines systeme fermait aussi
    l'ecriture de tout fichier temporaire. L'exception est bornee au dossier
    temporaire courant, pas a la branche /var entiere.
    """
    try:
        temporaire = Path(tempfile.gettempdir()).resolve()
    except OSError:
        return False
    return chemin == temporaire or chemin.is_relative_to(temporaire)


@lru_cache(maxsize=1)
def _racines_interdites() -> tuple[str, ...]:
    """Les racines interdites SOUS LEUR FORME RÉSOLUE, en plus de la littérale.

    Trouvé le 31/08/2026 : la comparaison portait sur le chemin déjà passé par
    `resolve()`, mais la liste restait littérale. Or sur macOS `/etc` se résout
    en `/private/etc` et `/var` en `/private/var` : plus aucune entrée ne
    pouvait correspondre, et `validate_file_path("/etc/passwd")` renvoyait le
    chemin au lieu de lever. La protection était inerte sur la plateforme
    principale de développement et de livraison, sans qu'aucun test la couvre.

    Les deux formes sont conservées : la littérale vaut sur les systèmes où
    ces répertoires ne sont pas des liens, la résolue vaut partout ailleurs.
    """
    racines: set[str] = set()
    for brut in _racines_systeme(os.name, os.environ):
        racines.add(brut)
        try:
            racines.add(str(Path(brut).resolve()))
        except OSError:
            # Une racine absente ou illisible reste interdite sous sa forme
            # littérale : on ne relâche jamais une garde parce qu'on n'a pas
            # pu la calculer.
            continue
    return tuple(sorted(racines))


def validate_file_path(file_path: str | Path, allowed_base: Path | None = None) -> Path:
    """
    Valide qu'un chemin de fichier est sur pour la lecture.

    Args:
        file_path: Chemin a valider
        allowed_base: Si fourni, le fichier doit etre sous ce repertoire

    Returns:
        Path resolu et valide

    Raises:
        PermissionError: Si le chemin est interdit
        FileNotFoundError: Si le fichier n'existe pas
    """
    path = Path(file_path).expanduser().resolve()
    home = Path.home()

    # Verifier les repertoires systeme interdits
    # 31/08 : sur macOS le dossier temporaire de l'utilisateur vit sous
    # /var/folders, donc sous /private/var une fois resolu. Refuser toute la
    # branche fermait la faille ET les fichiers temporaires legitimes. Le
    # dossier temporaire du processus prime donc sur la liste noire, et lui
    # seul : /private/var/log reste interdit.
    if _dans_le_dossier_temporaire(path):
        pass
    else:
      if _sous_une_racine(path, [Path(racine) for racine in _racines_interdites()]):
          logger.warning(f"Acces refuse (repertoire systeme) : {path}")
          raise PermissionError(
              "Acces interdit : les fichiers systeme ne sont pas accessibles"
          )

    # Verifier les repertoires sensibles dans le home
    try:
        rel_to_home = path.relative_to(home)
        rel_str = str(rel_to_home)
        for denied in DENIED_DIRECTORIES:
            if rel_str.startswith(denied) or rel_str == denied:
                logger.warning(f"Acces refuse (repertoire sensible) : {path}")
                raise PermissionError("Acces interdit : ce fichier contient des donnees sensibles")
    except ValueError:
        # Le fichier n'est pas sous le home directory - verifier qu'il n'est pas dans un chemin systeme
        pass

    # Verifier les patterns de fichiers sensibles
    for pattern in DENIED_PATTERNS:
        if path.match(pattern):
            logger.warning(f"Acces refuse (fichier sensible) : {path}")
            raise PermissionError("Acces interdit : ce type de fichier est protege")

    # Si un repertoire de base est specifie, verifier que le fichier est dedans
    if allowed_base is not None:
        allowed_base = allowed_base.expanduser().resolve()
        try:
            path.relative_to(allowed_base)
        except ValueError:
            logger.warning(f"Acces refuse (hors repertoire autorise) : {path} n'est pas sous {allowed_base}")
            raise PermissionError(f"Acces interdit : le fichier doit etre dans {allowed_base}")

    # B-037 : l'existence se verifie EN DERNIER, apres toutes les gardes.
    # Placee en tete, elle rendait FileNotFoundError pour un chemin interdit
    # absent et PermissionError pour un chemin interdit present : la
    # difference des deux messages est un oracle d'existence, qui permet
    # d'enumerer ~/.ssh sans jamais lire un fichier. Le message de cette
    # branche divulgue en outre le chemin absolu resolu, donc le nom du
    # dossier personnel - il ne doit donc etre atteint que sur un chemin
    # deja declare autorise.
    try:
        existe = path.exists()
    except OSError as erreur:
        # B-554 (05/09/2026) : un composant trop long lève OSError au lieu de
        # rendre False. Le chemin n'est pas repris : il serait aussi long.
        raise FileNotFoundError("Fichier non trouvé : chemin trop long ou mal formé") from erreur
    if not existe:
        raise FileNotFoundError(f"Fichier non trouvé : {path}")

    return path


# Extensions de fichiers autorisees pour l'indexation (SEC-002/003)
# Limite du pipeline d'indexation - au niveau module : le scanner de
# project.sync applique la MÊME règle (proposer un fichier que l'indexation
# refuserait ferait échouer chaque apply).
MAX_INDEXABLE_SIZE = 50 * 1024 * 1024

INDEXABLE_EXTENSIONS = {
    # Documents texte
    # `.markdown` était lisible par le parseur mais refusé à l'entrée : la
    # divergence inverse, trouvée par le test qui confronte les deux listes.
    ".txt", ".md", ".markdown", ".rst", ".csv", ".tsv", ".log",
    # Code source
    ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".scss",
    ".java", ".c", ".cpp", ".h", ".hpp", ".rs", ".go", ".rb", ".php",
    ".swift", ".kt", ".scala", ".r", ".sql", ".sh", ".bash", ".zsh",
    # Documents
    ".pdf", ".docx", ".xlsx", ".pptx",
    # Inventaire du 13/08/2026 : .xls, .ppt, .odt, .ods, .odp et .rtf étaient
    # acceptés alors qu'aucun chemin du parseur ne sait les ouvrir. Le fichier
    # était indexé à vide, sans le moindre signalement. Un refus net à l'entrée
    # vaut mieux qu'un succès mensonger : l'utilisateur peut convertir son
    # document et réessayer, ce qu'un silence ne lui permettait pas.
    # Donnees structurees
    ".json", ".yaml", ".yml", ".toml", ".xml", ".ini", ".cfg", ".conf",
    # Autres formats texte
    ".tex", ".org",
}


def validate_indexable_file(file_path: str | Path, allowed_base: Path | None = None) -> Path:
    """
    Valide qu'un fichier est sur ET indexable (type autorise).

    Combine la validation de chemin securise et la verification du type de fichier.

    Args:
        file_path: Chemin a valider
        allowed_base: Si fourni, le fichier doit etre sous ce repertoire

    Returns:
        Path resolu et valide

    Raises:
        PermissionError: Si le chemin est interdit
        FileNotFoundError: Si le fichier n'existe pas
        ValueError: Si le type de fichier n'est pas autorise pour l'indexation
    """
    # D'abord valider la sécurité du chemin
    path = validate_file_path(file_path, allowed_base)

    # Vérifier la taille (max 50 Mo)
    file_size = path.stat().st_size
    if file_size > MAX_INDEXABLE_SIZE:
        logger.warning(
            "Fichier trop volumineux pour l'indexation : %s (%d Mo)",
            path.name, file_size // (1024 * 1024),
        )
        raise ValueError(
            f"Fichier trop volumineux ({file_size // (1024 * 1024)} Mo). "
            f"Limite : {MAX_INDEXABLE_SIZE // (1024 * 1024)} Mo."
        )

    # Vérifier l'extension
    ext = path.suffix.lower()
    if ext not in INDEXABLE_EXTENSIONS:
        logger.warning(f"Type de fichier non indexable : {ext} ({path.name})")
        raise ValueError(
            f"Type de fichier non autorisé pour l'indexation : '{ext}'. "
            f"Types autorisés : {', '.join(sorted(INDEXABLE_EXTENSIONS))}"
        )

    return path
