"""
THERESE v2 - Path Security Service

Validation des chemins de fichiers pour empecher le path traversal
et l'acces aux fichiers sensibles.
"""

import logging
from pathlib import Path

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

# Repertoires systeme interdits (chemins absolus)
DENIED_ABSOLUTE_PATHS = [
    "/etc",
    "/var",
    "/usr",
    "/sys",
    "/proc",
    "/dev",
]


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

    # Verifier que le fichier existe
    if not path.exists():
        raise FileNotFoundError(f"Fichier non trouve : {path}")

    # Verifier les repertoires systeme interdits
    path_str = str(path)
    for denied in DENIED_ABSOLUTE_PATHS:
        if path_str.startswith(denied + "/") or path_str == denied:
            logger.warning(f"Acces refuse (repertoire systeme) : {path}")
            raise PermissionError("Acces interdit : les fichiers systeme ne sont pas accessibles")

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

    return path


# Extensions de fichiers autorisees pour l'indexation (SEC-002/003)
INDEXABLE_EXTENSIONS = {
    # Documents texte
    ".txt", ".md", ".rst", ".csv", ".tsv", ".log",
    # Code source
    ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".scss",
    ".java", ".c", ".cpp", ".h", ".hpp", ".rs", ".go", ".rb", ".php",
    ".swift", ".kt", ".scala", ".r", ".sql", ".sh", ".bash", ".zsh",
    # Documents
    ".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt",
    ".odt", ".ods", ".odp",
    # Donnees structurees
    ".json", ".yaml", ".yml", ".toml", ".xml", ".ini", ".cfg", ".conf",
    # Autres
    ".rtf", ".tex", ".org",
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
    MAX_INDEXABLE_SIZE = 50 * 1024 * 1024
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
            f"Type de fichier non autorise pour l'indexation : '{ext}'. "
            f"Types autorises : {', '.join(sorted(INDEXABLE_EXTENSIONS))}"
        )

    return path
